#!/usr/bin/env python3
"""
Script: memory_manager.py
Purpose: Unified memory management wrapper for all qdrant-memory operations.
         Provides a single entry point for agents across any AI environment.

Usage:
    # Auto-decide: check cache first, then retrieve context
    python3 execution/memory_manager.py auto --query "How to set up auth middleware?"

    # Explicit store (decision, code, error, technical, conversation)
    python3 execution/memory_manager.py store --content "Chose PostgreSQL for relational model" --type decision --project myapp

    # Retrieve context only
    python3 execution/memory_manager.py retrieve --query "database architecture" --top-k 5

    # Cache a response
    python3 execution/memory_manager.py cache-store --query "How to X?" --response "Do Y..."

    # Health check (Qdrant + Ollama)
    python3 execution/memory_manager.py health

Environment Variables:
    EMBEDDING_PROVIDER  - "ollama" (default), "openai", or "bedrock"
    OLLAMA_URL          - Ollama server URL (default: http://localhost:11434)
    QDRANT_URL          - Qdrant server URL (default: http://localhost:6333)
    MEMORY_COLLECTION   - Memory collection name (default: agent_memory)
    CACHE_COLLECTION    - Cache collection name (default: semantic_cache)

Exit Codes:
    0 - Success
    1 - No results / cache miss
    2 - Connection error (Qdrant or embedding service down)
    3 - Operation error
"""

import argparse
import json
import os
import sys
from urllib.request import Request, urlopen
from urllib.error import URLError

# Resolve path to qdrant-memory scripts
# Resolve path to qdrant-memory scripts
# Adaptive path: try project root first (2 levels up), then repo template structure (3 levels up)
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
skills_path_project = os.path.join(project_root, "skills", "core", "qdrant-memory", "scripts")

if os.path.exists(skills_path_project):
    SKILL_SCRIPTS_DIR = skills_path_project
else:
    # Fallback to repo template structure (templates/base/execution -> templates/skills)
    repo_root = os.path.dirname(project_root)
    SKILL_SCRIPTS_DIR = os.path.join(repo_root, "skills", "core", "qdrant-memory", "scripts")

sys.path.insert(0, SKILL_SCRIPTS_DIR)

from embedding_utils import check_embedding_service, get_embedding_dimension
from semantic_cache import check_cache, store_response, clear_cache
from memory_retrieval import retrieve_context, store_memory, list_memories, build_filter

# Import BM25 index (optional — graceful if unavailable)
try:
    from bm25_index import BM25Index
    _BM25_AVAILABLE = True
except ImportError:
    _BM25_AVAILABLE = False

# Configuration
QDRANT_URL = os.environ.get("QDRANT_URL", "http://localhost:6333")


def health_check() -> dict:
    """Check Qdrant connectivity and embedding service status."""
    result = {"qdrant": "unknown", "embeddings": "unknown", "collections": []}

    # Check Qdrant
    try:
        req = Request(f"{QDRANT_URL}/collections", method="GET")
        with urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            collections = [
                c["name"] for c in data.get("result", {}).get("collections", [])
            ]
            result["qdrant"] = "ok"
            result["collections"] = collections
    except Exception as e:
        result["qdrant"] = f"error: {e}"

    # Check embedding service
    embed_status = check_embedding_service()
    result["embeddings"] = embed_status

    # Check expected collections
    expected = ["agent_memory", "semantic_cache"]
    result["missing_collections"] = [
        c for c in expected if c not in result.get("collections", [])
    ]

    # Check BM25 index
    if _BM25_AVAILABLE:
        try:
            with BM25Index() as bm25:
                bm25_stats = bm25.get_stats()
                result["bm25"] = {
                    "status": "ok",
                    "documents": bm25_stats["documents"],
                    "last_sync": bm25_stats["last_sync"],
                    "db_size": bm25_stats["db_size_human"]
                }
        except Exception as e:
            result["bm25"] = {"status": f"error: {e}"}
    else:
        result["bm25"] = {"status": "not_installed"}

    # Overall status
    result["ready"] = (
        result["qdrant"] == "ok"
        and embed_status.get("status") == "ok"
        and len(result["missing_collections"]) == 0
    )

    return result


def auto_query(
    query: str, 
    project: str = None, 
    threshold: float = 0.92,
    vector_weight: float = None,
    text_weight: float = None
) -> dict:
    """
    Smart query: check cache first, then retrieve context using Hybrid Search.
    This is the primary entry point for agents.

    Flow:
    1. Check semantic cache (exact match saves 100% tokens)
    2. If miss, retrieve context via Vector + BM25 Hybrid Search (saves 80-95% tokens)
    3. Return combined result with token savings estimate
    """
    result = {
        "source": "none",
        "cache_hit": False,
        "context_chunks": [],
        "tokens_saved_estimate": 0,
        "search_type": "hybrid"
    }

    # Step 1: Semantic cache check
    try:
        cached = check_cache(query, threshold)
        if cached and cached.get("cache_hit"):
            result["source"] = "cache"
            result["cache_hit"] = True
            result["cached_response"] = cached.get("response", "")
            result["cache_score"] = cached.get("score", 0)
            result["tokens_saved_estimate"] = cached.get("tokens_saved", 0)
            return result
    except Exception:
        pass  # Cache miss or error, continue to retrieval

    # Step 2: Context retrieval
    try:
        filters = None
        if project:
            filters = {"must": [{"key": "project", "match": {"value": project}}]}

        context = retrieve_context(
            query, 
            filters=filters, 
            top_k=5, 
            score_threshold=0.45,
            vector_weight=vector_weight,
            text_weight=text_weight
        )
        if context.get("total_chunks", 0) > 0:
            result["source"] = "memory"
            result["context_chunks"] = context.get("chunks", [])
            result["total_chunks"] = context.get("total_chunks", 0)
            result["tokens_saved_estimate"] = context.get("total_tokens_estimate", 0)
            result["search_type"] = context.get("search_type", "unknown")
    except Exception:
        pass  # No context available

    return result


def main():
    parser = argparse.ArgumentParser(
        description="Unified memory manager for AI agents",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Smart auto-query (cache + context retrieval)
  python3 execution/memory_manager.py auto --query "How to handle JWT refresh?"

  # Store a key decision
  python3 execution/memory_manager.py store --content "Chose Supabase for auth" --type decision

  # Health check
  python3 execution/memory_manager.py health
        """,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Auto command (primary entry point)
    auto_parser = subparsers.add_parser(
        "auto", help="Smart query: cache check + Hybrid Memory retrieval"
    )
    auto_parser.add_argument("--query", required=True, help="Natural language query")
    auto_parser.add_argument("--project", help="Filter by project name")
    auto_parser.add_argument(
        "--threshold", type=float, default=0.92, help="Cache similarity threshold"
    )
    auto_parser.add_argument("--vector-weight", type=float, help="Hybrid search vector weight")
    auto_parser.add_argument("--text-weight", type=float, help="Hybrid search text weight")

    # Store command
    store_parser = subparsers.add_parser(
        "store", help="Store memory (decision, code, error, technical, conversation)"
    )
    store_parser.add_argument("--content", required=True, help="Memory content")
    store_parser.add_argument(
        "--type",
        required=True,
        choices=["decision", "code", "error", "conversation", "technical"],
        help="Memory type",
    )
    store_parser.add_argument("--project", help="Project name")
    store_parser.add_argument("--tags", nargs="+", help="Tags for the memory")

    # Retrieve command
    retrieve_parser = subparsers.add_parser(
        "retrieve", help="Retrieve relevant context"
    )
    retrieve_parser.add_argument("--query", required=True, help="Search query")
    retrieve_parser.add_argument("--type", help="Filter by memory type")
    retrieve_parser.add_argument("--project", help="Filter by project")
    retrieve_parser.add_argument(
        "--top-k", type=int, default=5, help="Number of results"
    )
    retrieve_parser.add_argument(
        "--threshold", type=float, default=0.7, help="Score threshold"
    )
    retrieve_parser.add_argument("--vector-weight", type=float, help="Hybrid search vector weight")
    retrieve_parser.add_argument("--text-weight", type=float, help="Hybrid search text weight")

    # Cache store command
    cache_parser = subparsers.add_parser(
        "cache-store", help="Store query-response in semantic cache"
    )
    cache_parser.add_argument("--query", required=True, help="Original query")
    cache_parser.add_argument("--response", required=True, help="LLM response to cache")
    cache_parser.add_argument("--model", default="agent", help="Model identifier")
    cache_parser.add_argument("--project", help="Project name")

    # List command
    list_parser = subparsers.add_parser("list", help="List stored memories")
    list_parser.add_argument("--type", help="Filter by memory type")
    list_parser.add_argument("--project", help="Filter by project")
    list_parser.add_argument("--limit", type=int, default=20, help="Max results")

    # Health command
    subparsers.add_parser("health", help="Check Qdrant + embedding service health")

    # Cache clear command
    clear_parser = subparsers.add_parser("cache-clear", help="Clear old cache entries")
    clear_parser.add_argument(
        "--older-than", type=int, default=7, help="Delete entries older than N days"
    )

    # BM25 sync command
    subparsers.add_parser(
        "bm25-sync", help="Rebuild BM25 keyword index from Qdrant (for hybrid search)"
    )

    args = parser.parse_args()

    try:
        if args.command == "auto":
            result = auto_query(
                args.query, 
                args.project, 
                args.threshold,
                vector_weight=args.vector_weight,
                text_weight=args.text_weight
            )
            print(json.dumps(result, indent=2))
            sys.exit(0 if result["source"] != "none" else 1)

        elif args.command == "store":
            metadata = {}
            if args.project:
                metadata["project"] = args.project
            if args.tags:
                metadata["tags"] = args.tags
            result = store_memory(args.content, args.type, metadata)
            print(json.dumps(result, indent=2))
            sys.exit(0)

        elif args.command == "retrieve":
            filters = build_filter(
                type_filter=getattr(args, "type", None), project=args.project
            )
            result = retrieve_context(
                args.query,
                filters={"must": filters["must"]} if filters else None,
                top_k=args.top_k,
                score_threshold=args.threshold,
                vector_weight=args.vector_weight,
                text_weight=args.text_weight
            )
            print(json.dumps(result, indent=2))
            sys.exit(0 if result.get("total_chunks", 0) > 0 else 1)

        elif args.command == "cache-store":
            metadata = {"model": args.model}
            if args.project:
                metadata["project"] = args.project
            result = store_response(args.query, args.response, metadata)
            print(json.dumps(result, indent=2))
            sys.exit(0)

        elif args.command == "list":
            filters = build_filter(
                type_filter=getattr(args, "type", None), project=args.project
            )
            result = list_memories(
                filters={"must": filters["must"]} if filters else None, limit=args.limit
            )
            print(json.dumps(result, indent=2))
            sys.exit(0)

        elif args.command == "health":
            result = health_check()
            print(json.dumps(result, indent=2))
            sys.exit(0 if result["ready"] else 2)

        elif args.command == "cache-clear":
            result = clear_cache(args.older_than)
            print(json.dumps(result, indent=2))
            sys.exit(0)

        elif args.command == "bm25-sync":
            if not _BM25_AVAILABLE:
                print(json.dumps({
                    "status": "error",
                    "message": "BM25 index module not found. Check bm25_index.py exists in qdrant-memory/scripts/"
                }), file=sys.stderr)
                sys.exit(3)
            with BM25Index() as bm25:
                result = bm25.sync_from_qdrant()
            print(json.dumps(result, indent=2))
            sys.exit(0 if result["status"] == "synced" else 2)

    except URLError as e:
        print(
            json.dumps(
                {
                    "status": "error",
                    "type": "connection_error",
                    "message": str(e),
                    "hint": "Is Qdrant running? Try: docker run -p 6333:6333 qdrant/qdrant",
                }
            ),
            file=sys.stderr,
        )
        sys.exit(2)
    except Exception as e:
        print(
            json.dumps(
                {"status": "error", "type": type(e).__name__, "message": str(e)}
            ),
            file=sys.stderr,
        )
        sys.exit(3)


if __name__ == "__main__":
    main()
