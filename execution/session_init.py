#!/usr/bin/env python3
"""
Script: session_init.py
Purpose: Bootstrap script for AI agent sessions. Checks prerequisites and
         initializes Qdrant collections with correct dimensions for the
         configured embedding provider (defaults to Ollama/768d).

Usage:
    # Full initialization (check + create collections)
    python3 execution/session_init.py

    # Check only (no collection creation)
    python3 execution/session_init.py --check-only

    # Force re-initialization
    python3 execution/session_init.py --force

Environment Variables:
    EMBEDDING_PROVIDER  - "ollama" (default), "openai", or "bedrock"
    OLLAMA_URL          - Ollama server URL (default: http://localhost:11434)
    QDRANT_URL          - Qdrant server URL (default: http://localhost:6333)

Exit Codes:
    0 - Success (all systems ready)
    1 - Partial success (some checks failed but non-critical)
    2 - Critical failure (Qdrant or embeddings not available)
"""

import argparse
import json
import os
import sys
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

# Resolve path to qdrant-memory scripts
SKILL_SCRIPTS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "skills",
    "qdrant-memory",
    "scripts",
)
sys.path.insert(0, SKILL_SCRIPTS_DIR)

from embedding_utils import (
    check_embedding_service,
    get_embedding_dimension,
    EMBEDDING_PROVIDER,
    EMBEDDING_MODEL,
)
from init_collection import create_collection, create_payload_index

# Configuration
QDRANT_URL = os.environ.get("QDRANT_URL", "http://localhost:6333")
COLLECTIONS = ["agent_memory", "semantic_cache"]


def check_qdrant() -> dict:
    """Check if Qdrant is running and accessible."""
    try:
        req = Request(f"{QDRANT_URL}/collections", method="GET")
        with urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            existing = [
                c["name"] for c in data.get("result", {}).get("collections", [])
            ]
            return {"status": "ok", "url": QDRANT_URL, "existing_collections": existing}
    except URLError as e:
        return {
            "status": "error",
            "url": QDRANT_URL,
            "message": str(e),
            "fix": "docker run -d -p 6333:6333 -p 6334:6334 -v qdrant_storage:/qdrant/storage qdrant/qdrant",
        }


def check_ollama() -> dict:
    """Check if Ollama is running and has the embedding model."""
    embed_status = check_embedding_service()

    if embed_status.get("status") == "ok":
        return embed_status

    if embed_status.get("status") == "missing_model":
        embed_status["fix"] = f"ollama pull {EMBEDDING_MODEL}"
        return embed_status

    if embed_status.get("status") == "connection_error":
        embed_status["fix"] = "Install and start Ollama: https://ollama.ai"
        return embed_status

    return embed_status


def init_collections(force: bool = False) -> list:
    """Initialize required Qdrant collections with correct dimensions."""
    dimension = get_embedding_dimension()
    results = []

    for collection_name in COLLECTIONS:
        # Check if collection already exists
        try:
            req = Request(f"{QDRANT_URL}/collections/{collection_name}", method="GET")
            with urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())
                existing_dim = (
                    data.get("result", {})
                    .get("config", {})
                    .get("params", {})
                    .get("vectors", {})
                    .get("size")
                )

                if existing_dim and existing_dim != dimension and force:
                    # Delete and recreate with correct dimensions
                    del_req = Request(
                        f"{QDRANT_URL}/collections/{collection_name}", method="DELETE"
                    )
                    urlopen(del_req, timeout=10)
                    print(
                        f"  Deleted {collection_name} (was {existing_dim}d, need {dimension}d)"
                    )
                elif existing_dim == dimension:
                    results.append(
                        {
                            "collection": collection_name,
                            "status": "exists",
                            "dimension": existing_dim,
                        }
                    )
                    continue
                elif existing_dim and existing_dim != dimension and not force:
                    results.append(
                        {
                            "collection": collection_name,
                            "status": "dimension_mismatch",
                            "current": existing_dim,
                            "expected": dimension,
                            "fix": f"Run with --force to recreate with {dimension}d",
                        }
                    )
                    continue
        except HTTPError as e:
            if e.code != 404:
                results.append(
                    {
                        "collection": collection_name,
                        "status": "error",
                        "message": str(e),
                    }
                )
                continue
        except URLError:
            results.append(
                {
                    "collection": collection_name,
                    "status": "error",
                    "message": "Cannot connect to Qdrant",
                }
            )
            continue

        # Create collection
        try:
            create_result = create_collection(
                QDRANT_URL, collection_name, dimension, "cosine"
            )

            # Create standard payload indexes
            indexes = [
                ("type", "keyword"),
                ("project", "keyword"),
                ("timestamp", "datetime"),
                ("tags", "keyword"),
                ("model", "keyword"),
                ("token_count", "integer"),
            ]

            for field, field_type in indexes:
                create_payload_index(QDRANT_URL, collection_name, field, field_type)

            results.append(
                {
                    "collection": collection_name,
                    "status": "created",
                    "dimension": dimension,
                    "indexes": len(indexes),
                }
            )
        except Exception as e:
            results.append(
                {"collection": collection_name, "status": "error", "message": str(e)}
            )

    return results


def main():
    parser = argparse.ArgumentParser(
        description="Initialize AI agent session (Qdrant + Ollama check + collection setup)"
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Only check prerequisites, don't create collections",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-initialization (recreate collections)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON only (no human-readable messages)",
    )
    args = parser.parse_args()

    report = {
        "provider": EMBEDDING_PROVIDER,
        "model": EMBEDDING_MODEL,
        "dimension": get_embedding_dimension(),
        "qdrant": {},
        "embeddings": {},
        "collections": [],
        "ready": False,
    }

    # Step 1: Check Qdrant
    if not args.json:
        print(f"Checking Qdrant at {QDRANT_URL}...")
    qdrant_status = check_qdrant()
    report["qdrant"] = qdrant_status

    if qdrant_status["status"] != "ok":
        if not args.json:
            print(f"  FAILED: {qdrant_status.get('message', 'Unknown error')}")
            print(f"  FIX: {qdrant_status.get('fix', 'Check Qdrant installation')}")
        if args.json:
            print(json.dumps(report, indent=2))
        sys.exit(2)
    else:
        if not args.json:
            print(f"  OK. Collections: {qdrant_status.get('existing_collections', [])}")

    # Step 2: Check embedding service
    if not args.json:
        print(f"Checking embedding service ({EMBEDDING_PROVIDER}/{EMBEDDING_MODEL})...")
    embed_status = check_ollama()
    report["embeddings"] = embed_status

    if embed_status.get("status") != "ok":
        if not args.json:
            print(f"  FAILED: {embed_status.get('message', 'Unknown error')}")
            if embed_status.get("fix"):
                print(f"  FIX: {embed_status['fix']}")
        if args.json:
            print(json.dumps(report, indent=2))
        sys.exit(2)
    else:
        if not args.json:
            print(f"  OK. Model: {EMBEDDING_MODEL} ({get_embedding_dimension()}d)")

    # Step 3: Initialize collections
    if not args.check_only:
        if not args.json:
            print(
                f"Initializing collections (dimension={get_embedding_dimension()})..."
            )
        collection_results = init_collections(force=args.force)
        report["collections"] = collection_results

        for cr in collection_results:
            if not args.json:
                status = cr["status"]
                name = cr["collection"]
                if status == "created":
                    print(
                        f"  CREATED: {name} ({cr['dimension']}d, {cr['indexes']} indexes)"
                    )
                elif status == "exists":
                    print(f"  EXISTS: {name} ({cr['dimension']}d)")
                elif status == "dimension_mismatch":
                    print(
                        f"  MISMATCH: {name} (current={cr['current']}d, expected={cr['expected']}d)"
                    )
                    print(f"    FIX: {cr.get('fix', '')}")
                else:
                    print(f"  ERROR: {name} - {cr.get('message', '')}")
    else:
        if not args.json:
            print("Skipping collection initialization (--check-only)")

    # Final status
    all_ok = qdrant_status["status"] == "ok" and embed_status.get("status") == "ok"

    if not args.check_only:
        all_ok = all_ok and all(
            cr["status"] in ("created", "exists")
            for cr in report.get("collections", [])
        )

    report["ready"] = all_ok

    if not args.json:
        if all_ok:
            print(f"\nSession initialized. Memory system ready.")
            print(f"  Provider: {EMBEDDING_PROVIDER} ({EMBEDDING_MODEL})")
            print(f"  Dimension: {get_embedding_dimension()}")
            print(f"  Qdrant: {QDRANT_URL}")
        else:
            print(f"\nSession initialization incomplete. See errors above.")
    else:
        print(json.dumps(report, indent=2))

    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
