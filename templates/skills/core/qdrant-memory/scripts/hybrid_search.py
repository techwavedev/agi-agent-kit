#!/usr/bin/env python3
"""
Script: hybrid_search.py
Purpose: True hybrid search combining BM25 keyword matching with vector similarity.

This is the core of the hybrid memory system. It runs BOTH:
1. Vector search via Qdrant (semantic similarity)
2. BM25 search via SQLite FTS5 (exact keyword matching)

Results are merged using weighted scoring:
    finalScore = vectorWeight * vectorScore + textWeight * textScore

This catches things pure vector search misses:
- Exact error codes: ImagePullBackOff, ECONNREFUSED
- Environment variables: QDRANT_URL, OPENAI_API_KEY
- IDs and hashes: sg-018f20ea63e82eeb5, a828e60
- Code symbols: memory_retrieval.retrieve_context

Supports both Ollama (local/private) and OpenAI (cloud) embeddings.
Default: Ollama with nomic-embed-text model.

Usage:
    # True hybrid search (BM25 + vector)
    python3 hybrid_search.py --query "ImagePullBackOff error" --mode hybrid

    # Vector-only (original behavior)
    python3 hybrid_search.py --query "deployment strategies" --mode vector

    # BM25-only (keyword matching)
    python3 hybrid_search.py --query "sg-018f20ea63e82eeb5" --mode keyword

    # With metadata filters (Qdrant payload filtering)
    python3 hybrid_search.py --query "kubernetes error" --keyword project=k8s

    # Custom weights
    python3 hybrid_search.py --query "error" --vector-weight 0.6 --text-weight 0.4

Environment Variables:
    EMBEDDING_PROVIDER  - "ollama" (default) or "openai"
    OLLAMA_URL          - Ollama server URL (default: http://localhost:11434)
    OPENAI_API_KEY      - Required for OpenAI provider
    QDRANT_URL          - Qdrant server URL (default: http://localhost:6333)
    MEMORY_COLLECTION   - Collection name (default: agent_memory)
    BM25_INDEX_PATH     - SQLite FTS5 index path (default: ~/.agi/memory_bm25.sqlite)
    HYBRID_VECTOR_WEIGHT - Vector weight (default: 0.7)
    HYBRID_TEXT_WEIGHT   - Text weight (default: 0.3)

Exit Codes:
    0 - Success (results found)
    1 - No results
    2 - Connection error
    3 - Search error
"""

import argparse
import json
import os
import sys
from typing import List, Dict, Any, Optional
from urllib.request import Request, urlopen
from urllib.error import URLError

# Import shared embedding utilities (supports Ollama and OpenAI)
try:
    from embedding_utils import get_embedding
except ImportError:
    # Fallback if run from different directory
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from embedding_utils import get_embedding

# Import BM25 index
try:
    from bm25_index import BM25Index
except ImportError:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    try:
        from bm25_index import BM25Index
    except ImportError:
        BM25Index = None

# Configuration
QDRANT_URL = os.environ.get("QDRANT_URL", "http://localhost:6333")
COLLECTION = os.environ.get("MEMORY_COLLECTION", "agent_memory")

# Hybrid search weights (must sum to 1.0)
DEFAULT_VECTOR_WEIGHT = float(os.environ.get("HYBRID_VECTOR_WEIGHT", "0.7"))
DEFAULT_TEXT_WEIGHT = float(os.environ.get("HYBRID_TEXT_WEIGHT", "0.3"))


def _vector_search(
    text_query: str,
    keyword_filters: Optional[Dict[str, str]] = None,
    must_not_filters: Optional[Dict[str, str]] = None,
    top_k: int = 10,
    score_threshold: float = 0.5,
    candidate_multiplier: int = 4
) -> List[Dict[str, Any]]:
    """
    Vector similarity search via Qdrant.

    Args:
        text_query: Natural language query for semantic search
        keyword_filters: Dict of field:value pairs that MUST match (payload filter)
        must_not_filters: Dict of field:value pairs that MUST NOT match
        top_k: Number of results (multiplied by candidate_multiplier for merging)
        score_threshold: Minimum similarity score
        candidate_multiplier: Fetch extra candidates for better merge

    Returns:
        List of results with doc_id and vector_score
    """
    embedding = get_embedding(text_query)

    # Build filter conditions
    filter_conditions = {"must": [], "must_not": []}

    if keyword_filters:
        for field, value in keyword_filters.items():
            filter_conditions["must"].append({
                "key": field,
                "match": {"value": value}
            })

    if must_not_filters:
        for field, value in must_not_filters.items():
            filter_conditions["must_not"].append({
                "key": field,
                "match": {"value": value}
            })

    # Fetch more candidates than needed for better merge results
    fetch_limit = top_k * candidate_multiplier

    search_payload = {
        "vector": embedding,
        "limit": fetch_limit,
        "score_threshold": score_threshold,
        "with_payload": True
    }

    # Only add filter if we have conditions
    if filter_conditions["must"] or filter_conditions["must_not"]:
        search_payload["filter"] = {
            k: v for k, v in filter_conditions.items() if v
        }

    req = Request(
        f"{QDRANT_URL}/collections/{COLLECTION}/points/search",
        data=json.dumps(search_payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    with urlopen(req, timeout=30) as response:
        result = json.loads(response.read().decode())

    results = []
    for hit in result.get("result", []):
        results.append({
            "doc_id": str(hit["id"]),
            "vector_score": hit["score"],
            "content": hit["payload"].get("content", ""),
            "type": hit["payload"].get("type"),
            "project": hit["payload"].get("project"),
            "tags": hit["payload"].get("tags", []),
            "timestamp": hit["payload"].get("timestamp"),
        })

    return results


def _bm25_search(
    query: str,
    top_k: int = 10,
    candidate_multiplier: int = 4
) -> List[Dict[str, Any]]:
    """
    BM25 keyword search via SQLite FTS5.

    Args:
        query: Keyword query
        top_k: Number of results (multiplied for merge)
        candidate_multiplier: Fetch extra candidates

    Returns:
        List of results with doc_id and text_score, or empty if BM25 unavailable
    """
    if BM25Index is None:
        return []

    try:
        with BM25Index() as index:
            fetch_limit = top_k * candidate_multiplier
            return index.search(query, top_k=fetch_limit)
    except Exception:
        # BM25 index not available — graceful fallback
        return []


def hybrid_query(
    text_query: str,
    keyword_filters: Optional[Dict[str, str]] = None,
    must_not_filters: Optional[Dict[str, str]] = None,
    top_k: int = 10,
    score_threshold: float = 0.5,
    vector_weight: float = DEFAULT_VECTOR_WEIGHT,
    text_weight: float = DEFAULT_TEXT_WEIGHT,
    mode: str = "hybrid"
) -> Dict[str, Any]:
    """
    True hybrid search combining vector similarity with BM25 keyword matching.

    Args:
        text_query: Natural language query
        keyword_filters: Qdrant payload field filters (MUST match)
        must_not_filters: Qdrant payload field filters (MUST NOT match)
        top_k: Number of results to return
        score_threshold: Minimum vector similarity score
        vector_weight: Weight for vector scores (0.0-1.0)
        text_weight: Weight for BM25 text scores (0.0-1.0)
        mode: Search mode - "hybrid", "vector", or "keyword"

    Returns:
        Merged search results with hybrid scores
    """
    # Normalize weights
    total_weight = vector_weight + text_weight
    if total_weight > 0:
        vector_weight = vector_weight / total_weight
        text_weight = text_weight / total_weight

    vector_results = []
    bm25_results = []

    # Run searches based on mode
    if mode in ("hybrid", "vector"):
        try:
            vector_results = _vector_search(
                text_query,
                keyword_filters=keyword_filters,
                must_not_filters=must_not_filters,
                top_k=top_k,
                score_threshold=score_threshold
            )
        except (URLError, Exception) as e:
            if mode == "vector":
                raise
            # In hybrid mode, continue with BM25 only

    if mode in ("hybrid", "keyword"):
        bm25_results = _bm25_search(text_query, top_k=top_k)

    # If only one source, return directly
    if mode == "vector" or (not bm25_results and vector_results):
        return {
            "query": text_query,
            "results": vector_results[:top_k],
            "total": min(len(vector_results), top_k),
            "search_type": "vector",
            "weights": {"vector": 1.0, "text": 0.0}
        }

    if mode == "keyword" or (not vector_results and bm25_results):
        formatted = []
        for r in bm25_results[:top_k]:
            formatted.append({
                "doc_id": r["doc_id"],
                "score": r["text_score"],
                "content": r["content"],
                "type": r.get("type"),
                "project": r.get("project"),
                "tags": r.get("tags", []),
                "search_source": "bm25"
            })
        return {
            "query": text_query,
            "results": formatted,
            "total": len(formatted),
            "search_type": "keyword",
            "weights": {"vector": 0.0, "text": 1.0}
        }

    # === MERGE: Union by doc_id, compute weighted score ===
    merged = {}

    # Add vector results
    for r in vector_results:
        doc_id = r["doc_id"]
        merged[doc_id] = {
            "doc_id": doc_id,
            "content": r["content"],
            "type": r.get("type"),
            "project": r.get("project"),
            "tags": r.get("tags", []),
            "timestamp": r.get("timestamp"),
            "vector_score": r["vector_score"],
            "text_score": 0.0,
            "search_sources": ["vector"]
        }

    # Add/merge BM25 results
    for r in bm25_results:
        doc_id = r["doc_id"]
        if doc_id in merged:
            merged[doc_id]["text_score"] = r["text_score"]
            merged[doc_id]["search_sources"].append("bm25")
        else:
            merged[doc_id] = {
                "doc_id": doc_id,
                "content": r["content"],
                "type": r.get("type"),
                "project": r.get("project"),
                "tags": r.get("tags", []),
                "timestamp": None,
                "vector_score": 0.0,
                "text_score": r["text_score"],
                "search_sources": ["bm25"]
            }

    # Compute final hybrid score
    for doc_id, entry in merged.items():
        entry["score"] = round(
            vector_weight * entry["vector_score"] +
            text_weight * entry["text_score"],
            4
        )

    # Sort by hybrid score, take top_k
    sorted_results = sorted(
        merged.values(), key=lambda x: x["score"], reverse=True
    )[:top_k]

    return {
        "query": text_query,
        "keyword_filters": keyword_filters,
        "results": sorted_results,
        "total": len(sorted_results),
        "search_type": "hybrid",
        "weights": {"vector": vector_weight, "text": text_weight},
        "sources": {
            "vector_candidates": len(vector_results),
            "bm25_candidates": len(bm25_results),
            "merged_unique": len(merged)
        }
    }


def parse_keyword_args(keyword_args: List[str]) -> Dict[str, str]:
    """Parse keyword arguments in format key=value."""
    filters = {}
    for kv in keyword_args or []:
        if "=" in kv:
            key, value = kv.split("=", 1)
            filters[key.strip()] = value.strip()
    return filters


def main():
    parser = argparse.ArgumentParser(
        description="True hybrid search: BM25 keyword + vector similarity"
    )
    parser.add_argument(
        "--query",
        required=True,
        help="Search query (natural language or keywords)"
    )
    parser.add_argument(
        "--keyword",
        action="append",
        help="Qdrant payload filter in key=value format (can be repeated)"
    )
    parser.add_argument(
        "--exclude",
        action="append",
        help="Exclusion filter in key=value format (can be repeated)"
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=10,
        help="Number of results (default: 10)"
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.5,
        help="Minimum vector score threshold (default: 0.5)"
    )
    parser.add_argument(
        "--mode",
        choices=["hybrid", "vector", "keyword"],
        default="hybrid",
        help="Search mode (default: hybrid)"
    )
    parser.add_argument(
        "--vector-weight",
        type=float,
        default=DEFAULT_VECTOR_WEIGHT,
        help=f"Vector score weight (default: {DEFAULT_VECTOR_WEIGHT})"
    )
    parser.add_argument(
        "--text-weight",
        type=float,
        default=DEFAULT_TEXT_WEIGHT,
        help=f"BM25 text score weight (default: {DEFAULT_TEXT_WEIGHT})"
    )

    args = parser.parse_args()

    try:
        keyword_filters = parse_keyword_args(args.keyword)
        exclude_filters = parse_keyword_args(args.exclude)

        result = hybrid_query(
            text_query=args.query,
            keyword_filters=keyword_filters if keyword_filters else None,
            must_not_filters=exclude_filters if exclude_filters else None,
            top_k=args.top_k,
            score_threshold=args.threshold,
            vector_weight=args.vector_weight,
            text_weight=args.text_weight,
            mode=args.mode
        )

        print(json.dumps(result, indent=2))
        sys.exit(0 if result["total"] > 0 else 1)

    except URLError as e:
        print(json.dumps({
            "status": "error",
            "type": "connection_error",
            "message": str(e)
        }), file=sys.stderr)
        sys.exit(2)
    except Exception as e:
        print(json.dumps({
            "status": "error",
            "type": type(e).__name__,
            "message": str(e)
        }), file=sys.stderr)
        sys.exit(3)


if __name__ == "__main__":
    main()
