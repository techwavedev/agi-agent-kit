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

    # Sync knowledge/*.md files to Qdrant (idempotent)
    python3 execution/memory_manager.py knowledge-sync --project myapp

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
from pathlib import Path
import time
from urllib.request import Request, urlopen
from urllib.error import URLError

# Resolve path to qdrant-memory scripts
# Resolve path to qdrant-memory scripts using dual-path (Issue #35)
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)
try:
    from resolve_paths import get_project_root, resolve_file
except ImportError:
    def get_project_root(): return Path.cwd()
    def resolve_file(path_str): return Path(path_str)

project_root = get_project_root()
# Try paths in order of likelihood
_candidates = [
    resolve_file("skills/qdrant-memory/scripts"),
    resolve_file("skills/core/qdrant-memory/scripts"),
    resolve_file("../skills/qdrant-memory/scripts"),
    resolve_file("../skills/core/qdrant-memory/scripts"),
]
SKILL_SCRIPTS_DIR = next((str(p) for p in _candidates if p.exists()), str(_candidates[0]))

sys.path.insert(0, SKILL_SCRIPTS_DIR)

from embedding_utils import check_embedding_service, get_embedding, get_embedding_dimension
from semantic_cache import check_cache, store_response, clear_cache
from memory_retrieval import retrieve_context, store_memory, list_memories, build_filter

# Langfuse Observability — use framework's shared client
try:
    from langfuse_tracing import observe_function, get_client as _get_langfuse
    _LANGFUSE_AVAILABLE = True
except ImportError:
    _LANGFUSE_AVAILABLE = False

# Fallback: try langfuse.decorators directly (backward compat)
try:
    from langfuse.decorators import observe
except ImportError:
    def observe(*args, **kwargs):
        def decorator(func):
            return func
        return decorator

# Import BM25 index (optional — graceful if unavailable)
try:
    from bm25_index import BM25Index
    _BM25_AVAILABLE = True
except ImportError:
    _BM25_AVAILABLE = False

# Import AAAK Dialect
try:
    from aaak_compressor import Dialect
    _AAAK_AVAILABLE = True
except ImportError:
    _AAAK_AVAILABLE = False

def _flush_langfuse():
    """Flush Langfuse events if available. Safe no-op otherwise."""
    if _LANGFUSE_AVAILABLE:
        try:
            from langfuse_tracing import flush
            flush()
        except Exception:
            pass

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


@observe(name="auto_query_memory", as_type="retrieval")
def auto_query(
    query: str, 
    project: str = None, 
    threshold: float = 0.92,
    vector_weight: float = None,
    text_weight: float = None,
    wing: str = None,
    room: str = None
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
        if project or wing or room:
            filters = {"must": []}
            if project:
                filters["must"].append({"key": "project", "match": {"value": project}})
            if wing:
                filters["must"].append({"key": "wing", "match": {"value": wing}})
            if room:
                filters["must"].append({"key": "room", "match": {"value": room}})

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


def _parse_markdown_sections(text: str, filename: str) -> list:
    """
    Split a markdown file into sections by H2 headings.
    Returns list of dicts: {section, content, filename}.
    Falls back to a single chunk if no H2 headings are found.
    """
    sections = []
    current_heading = filename.replace(".md", "").replace("-", " ").title()
    current_lines = []

    for line in text.splitlines():
        if line.startswith("## "):
            # Save previous section if it has content
            body = "\n".join(current_lines).strip()
            if body:
                sections.append({"section": current_heading, "content": body, "filename": filename})
            current_heading = line[3:].strip()
            current_lines = []
        else:
            current_lines.append(line)

    # Save last section
    body = "\n".join(current_lines).strip()
    if body:
        sections.append({"section": current_heading, "content": body, "filename": filename})

    return sections


def knowledge_sync(knowledge_dir: str, project: str, reset: bool = False) -> dict:
    """
    Sync knowledge/*.md files (excluding core.md) to Qdrant as type=knowledge.

    Uses deterministic UUIDs (project:filename:section) so re-runs are idempotent
    (Qdrant upsert behaviour — no duplicates).

    Args:
        knowledge_dir: Path to the knowledge/ directory.
        project:       Project name tag stored with each chunk.
        reset:         If True, delete existing knowledge chunks for this project first.

    Returns:
        dict with status, synced count, and any errors.
    """
    import hashlib
    import uuid as _uuid

    knowledge_path = Path(knowledge_dir)
    if not knowledge_path.exists():
        return {"status": "error", "message": f"Knowledge directory not found: {knowledge_dir}"}

    md_files = sorted(f for f in knowledge_path.glob("*.md") if f.name != "core.md")
    if not md_files:
        return {"status": "ok", "synced": 0, "message": "No non-core knowledge files found."}

    # Optional: delete existing knowledge points for this project before re-sync
    if reset:
        try:
            delete_filter = {
                "filter": {
                    "must": [
                        {"key": "type", "match": {"value": "knowledge"}},
                        {"key": "project", "match": {"value": project}},
                    ]
                }
            }
            req = Request(
                f"{QDRANT_URL}/collections/agent_memory/points/delete",
                data=json.dumps(delete_filter).encode(),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urlopen(req, timeout=30):
                pass
        except Exception as e:
            return {"status": "error", "message": f"Reset failed: {e}"}

    synced = 0
    errors = []
    points = []

    for md_file in md_files:
        text = md_file.read_text(encoding="utf-8")
        sections = _parse_markdown_sections(text, md_file.name)

        for chunk in sections:
            # Deterministic UUID from project + filename + section (SHA-256 → UUID5 namespace)
            uid_src = f"{project}:{chunk['filename']}:{chunk['section']}"
            sha = hashlib.sha256(uid_src.encode()).hexdigest()[:32]
            det_uuid = str(_uuid.UUID(sha))

            # Embed
            try:
                embedding = get_embedding(chunk["content"])
            except Exception as e:
                errors.append({"file": chunk["filename"], "section": chunk["section"], "error": str(e)})
                continue

            points.append({
                "id": det_uuid,
                "vector": embedding,
                "payload": {
                    "content": chunk["content"],
                    "type": "knowledge",
                    "project": project,
                    "source_file": chunk["filename"],
                    "section": chunk["section"],
                    "token_count": len(chunk["content"].split()),
                },
            })

    if not points:
        return {"status": "ok", "synced": 0, "errors": errors, "message": "Nothing to sync."}

    # Batch upsert
    try:
        upsert_body = json.dumps({"points": points}).encode()
        req = Request(
            f"{QDRANT_URL}/collections/agent_memory/points?wait=true",
            data=upsert_body,
            headers={"Content-Type": "application/json"},
            method="PUT",
        )
        with urlopen(req, timeout=60) as response:
            result = json.loads(response.read().decode())
            if result.get("status") != "ok" and result.get("result", {}).get("status") != "acknowledged":
                return {"status": "error", "message": f"Qdrant upsert failed: {result}", "errors": errors}
        synced = len(points)
    except Exception as e:
        return {"status": "error", "message": f"Qdrant upsert error: {e}", "errors": errors}

    # Rebuild BM25 index if available
    if _BM25_AVAILABLE:
        try:
            with BM25Index() as bm25:
                bm25.sync_from_qdrant()
        except Exception:
            pass

    return {
        "status": "ok",
        "synced": synced,
        "files": [f.name for f in md_files],
        "errors": errors,
        "message": f"Synced {synced} knowledge chunks from {len(md_files)} file(s) to Qdrant.",
    }


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
    auto_parser.add_argument("--wing", help="Filter by wing")
    auto_parser.add_argument("--room", help="Filter by room")
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
    store_parser.add_argument("--wing", help="Wing name")
    store_parser.add_argument("--room", help="Room name")
    store_parser.add_argument("--tags", nargs="+", help="Tags for the memory")
    store_parser.add_argument("--compress-aaak", action="store_true", help="Compress content using AAAK dialect")
    store_parser.add_argument("--expire-days", type=int, help="Number of days until this memory expires (temporal filters)")
    store_parser.add_argument("--resolve-contradictions", action="store_true", help="Check for and invalidate contradicting old facts before storing")

    # Retrieve command
    retrieve_parser = subparsers.add_parser(
        "retrieve", help="Retrieve relevant context"
    )
    retrieve_parser.add_argument("--query", required=True, help="Search query")
    retrieve_parser.add_argument("--type", help="Filter by memory type")
    retrieve_parser.add_argument("--project", help="Filter by project")
    retrieve_parser.add_argument("--wing", help="Filter by wing")
    retrieve_parser.add_argument("--room", help="Filter by room")
    retrieve_parser.add_argument(
        "--top-k", type=int, default=5, help="Number of results"
    )
    retrieve_parser.add_argument(
        "--threshold", type=float, default=0.45, help="Score threshold (default: 0.45)"
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

    # Knowledge sync command
    ks_parser = subparsers.add_parser(
        "knowledge-sync",
        help="Sync knowledge/*.md files to Qdrant for semantic retrieval at dispatch time",
    )
    ks_parser.add_argument("--project", required=True, help="Project name tag (used to scope chunks)")
    ks_parser.add_argument(
        "--dir",
        default=None,
        help="Path to knowledge directory (default: knowledge/ relative to project root)",
    )
    ks_parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete existing knowledge chunks for this project before syncing",
    )

    args = parser.parse_args()

    try:
        if args.command == "auto":
            result = auto_query(
                args.query, 
                args.project, 
                args.threshold,
                vector_weight=args.vector_weight,
                text_weight=args.text_weight,
                wing=getattr(args, "wing", None),
                room=getattr(args, "room", None)
            )
            print(json.dumps(result, indent=2))
            sys.exit(0 if result["source"] != "none" else 1)

        elif args.command == "store":
            metadata = {}
            if args.project:
                metadata["project"] = args.project
            if getattr(args, "wing", None):
                metadata["wing"] = args.wing
            if getattr(args, "room", None):
                metadata["room"] = args.room
            if args.tags:
                metadata["tags"] = args.tags
            if getattr(args, "expire_days", None):
                metadata["valid_until"] = int(time.time() + (args.expire_days * 86400))

            content = args.content
            if getattr(args, "compress_aaak", False) and _AAAK_AVAILABLE:
                metadata["original_text"] = content
                try:
                    dialect = Dialect()
                    content = dialect.compress(content, metadata=metadata)
                except Exception:
                    pass
                    
            if getattr(args, "resolve_contradictions", False) and getattr(args, "wing", None) and getattr(args, "room", None):
                if _LANGFUSE_AVAILABLE:
                    observe_function("ledger_contradiction_check", op_type="span")(lambda: "Initiated")()
                try:
                    # 1. Fetch top existing facts for this wing/room
                    filters = {"must": [
                        {"key": "wing", "match": {"value": args.wing}},
                        {"key": "room", "match": {"value": args.room}}
                    ]}
                    # Search using the new content to find semantically similar existing facts
                    old_context = retrieve_context(args.content, filters=filters, top_k=3)
                    
                    if old_context["total_chunks"] > 0:
                        from local_micro_agent import run_with_fallback

                        facts = []
                        valid_points = []
                        for i, chunk in enumerate(old_context["chunks"]):
                            if chunk.get("point_id"):
                                facts.append(f"[{i}] {chunk['content']}")
                                valid_points.append(chunk["point_id"])
                        
                        if facts:
                            prompt_context = "Existing Facts:\n" + "\n".join(facts)
                            task = (
                                f"Does this new fact strictly contradict any of the Existing Facts? "
                                f"New fact: '{args.content}'\n"
                                "If yes, reply ONLY with the exact index number in brackets (e.g. '[0]'). "
                                "If no contradiction, reply 'none'."
                            )
                            
                            res = run_with_fallback(task, prompt_context, None, 0.0, 50, False)
                            if res["status"] == "success":
                                resp_text = res["response"]
                                if "[" in resp_text and "]" in resp_text:
                                    idx_str = resp_text.split("[")[1].split("]")[0]
                                    if idx_str.isdigit() and int(idx_str) < len(valid_points):
                                        target_id = valid_points[int(idx_str)]
                                        # Issue deprecation update to Qdrant
                                        from memory_retrieval import QDRANT_URL, COLLECTION
                                        update_payload = {
                                            "payload": {"valid_until": int(time.time())},
                                            "points": [target_id]
                                        }
                                        req = Request(
                                            f"{QDRANT_URL}/collections/{COLLECTION}/points/payload",
                                            data=json.dumps(update_payload).encode(),
                                            headers={"Content-Type": "application/json"},
                                            method="POST"
                                        )
                                        with urlopen(req, timeout=10):
                                            pass
                except Exception as e:
                    print(f"WARN: Contradiction check failed: {e}", file=sys.stderr)

            # Trace the store operation
            if _LANGFUSE_AVAILABLE:
                _traced_store = observe_function("memory_store", op_type="span")(store_memory)
                result = _traced_store(content, args.type, metadata)
            else:
                result = store_memory(content, args.type, metadata)
            print(json.dumps(result, indent=2))
            _flush_langfuse()
            sys.exit(0)

        elif args.command == "retrieve":
            filters = build_filter(
                type_filter=getattr(args, "type", None), project=args.project
            )
            if filters is None:
                filters = {"must": []}
            if not isinstance(filters, dict) or "must" not in filters:
                filters = {"must": []}
            if "must_not" not in filters:
                filters["must_not"] = []
            
            if getattr(args, "wing", None):
                filters["must"].append({"key": "wing", "match": {"value": args.wing}})
            if getattr(args, "room", None):
                filters["must"].append({"key": "room", "match": {"value": args.room}})
            if not filters["must"] and not filters["must_not"]:
                filters = None

            # Trace the retrieve operation
            if _LANGFUSE_AVAILABLE:
                _traced_retrieve = observe_function("memory_retrieve", op_type="retrieval")(retrieve_context)
                result = _traced_retrieve(
                    args.query,
                    filters=filters,
                    top_k=args.top_k,
                    score_threshold=args.threshold,
                    vector_weight=args.vector_weight,
                    text_weight=args.text_weight
                )
            else:
                result = retrieve_context(
                    args.query,
                    filters=filters,
                    top_k=args.top_k,
                    score_threshold=args.threshold,
                    vector_weight=args.vector_weight,
                    text_weight=args.text_weight
                )
            print(json.dumps(result, indent=2))
            _flush_langfuse()
            sys.exit(0 if result.get("total_chunks", 0) > 0 else 1)

        elif args.command == "cache-store":
            metadata = {"model": args.model}
            if args.project:
                metadata["project"] = args.project
            # Trace the cache-store operation
            if _LANGFUSE_AVAILABLE:
                _traced_cache = observe_function("cache_store", op_type="span")(store_response)
                result = _traced_cache(args.query, args.response, metadata)
            else:
                result = store_response(args.query, args.response, metadata)
            print(json.dumps(result, indent=2))
            _flush_langfuse()
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

        elif args.command == "knowledge-sync":
            # Resolve knowledge directory
            if args.dir:
                kb_dir = Path(args.dir)
            else:
                # Default: project_root/knowledge/
                kb_dir = Path(current_dir).parent / "knowledge"
            result = knowledge_sync(str(kb_dir), args.project, reset=args.reset)
            print(json.dumps(result, indent=2))
            sys.exit(0 if result["status"] == "ok" else 3)

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
