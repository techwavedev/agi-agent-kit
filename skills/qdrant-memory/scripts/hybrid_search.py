#!/usr/bin/env python3
"""
Script: hybrid_search.py
Purpose: Hybrid search combining vector similarity with keyword filtering.

Usage:
    python hybrid_search.py --query "kubernetes deployment failed" \
        --keyword error_code=ImagePullBackOff --keyword namespace=production

This is particularly useful for technical queries where you need:
- Semantic understanding (what is the user asking about?)
- Exact matching (specific error codes, variable names, identifiers)

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

# Configuration
QDRANT_URL = os.environ.get("QDRANT_URL", "http://localhost:6333")
COLLECTION = os.environ.get("MEMORY_COLLECTION", "agent_memory")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "text-embedding-3-small")


def get_embedding(text: str) -> list:
    """Generate embedding using OpenAI API."""
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY environment variable not set")
    
    payload = {
        "input": text,
        "model": EMBEDDING_MODEL
    }
    
    req = Request(
        "https://api.openai.com/v1/embeddings",
        data=json.dumps(payload).encode(),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {OPENAI_API_KEY}"
        },
        method="POST"
    )
    
    with urlopen(req, timeout=30) as response:
        result = json.loads(response.read().decode())
        return result["data"][0]["embedding"]


def hybrid_query(
    text_query: str,
    keyword_filters: Optional[Dict[str, str]] = None,
    must_not_filters: Optional[Dict[str, str]] = None,
    top_k: int = 10,
    score_threshold: float = 0.6
) -> Dict[str, Any]:
    """
    Perform hybrid search combining vector similarity with keyword filtering.
    
    Args:
        text_query: Natural language query for semantic search
        keyword_filters: Dict of field:value pairs that MUST match
        must_not_filters: Dict of field:value pairs that MUST NOT match
        top_k: Number of results
        score_threshold: Minimum similarity score
    
    Returns:
        Search results with hybrid scores
    """
    # Get embedding for semantic search
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
    
    # Build search payload
    search_payload = {
        "vector": embedding,
        "limit": top_k,
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
            "id": hit["id"],
            "score": hit["score"],
            "content": hit["payload"].get("content", ""),
            "type": hit["payload"].get("type"),
            "project": hit["payload"].get("project"),
            "tags": hit["payload"].get("tags", []),
            "timestamp": hit["payload"].get("timestamp"),
            "matched_filters": keyword_filters or {}
        })
    
    return {
        "query": text_query,
        "keyword_filters": keyword_filters,
        "results": results,
        "total": len(results),
        "search_type": "hybrid" if keyword_filters else "semantic"
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
        description="Hybrid search with vector + keyword filtering"
    )
    parser.add_argument(
        "--query", 
        required=True,
        help="Natural language query"
    )
    parser.add_argument(
        "--keyword",
        action="append",
        help="Keyword filter in key=value format (can be repeated)"
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
        default=0.6,
        help="Minimum score threshold (default: 0.6)"
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
            score_threshold=args.threshold
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
