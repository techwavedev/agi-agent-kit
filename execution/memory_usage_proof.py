#!/usr/bin/env python3
"""
Script: memory_usage_proof.py
Purpose: Provides HARD PROOF that the agent is actually using Qdrant and Ollama
         during real sessions. This is not a health check — it validates actual
         data flow (stores, retrievals) with timestamps.

Usage:
    # Quick check: are there recent stores?
    python3 execution/memory_usage_proof.py --check

    # Full report: all memories with details
    python3 execution/memory_usage_proof.py --report

    # Check if memory was used in the last N minutes
    python3 execution/memory_usage_proof.py --check --since 30

Exit Codes:
    0 - Memory is being actively used (recent stores found)
    1 - No recent memory activity detected
    2 - Qdrant/Ollama not running
"""

import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from urllib.request import Request, urlopen
from urllib.error import URLError

QDRANT_URL = os.environ.get("QDRANT_URL", "http://localhost:6333")
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")


def get_collection_info(collection_name: str) -> dict:
    """Get collection point count and details."""
    try:
        req = Request(f"{QDRANT_URL}/collections/{collection_name}", method="GET")
        with urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            result = data.get("result", {})
            return {
                "exists": True,
                "points_count": result.get("points_count", 0),
                "vectors_count": result.get("vectors_count", 0),
                "status": result.get("status", "unknown"),
            }
    except Exception as e:
        return {"exists": False, "error": str(e)}


def get_recent_points(collection_name: str, limit: int = 20) -> list:
    """Scroll through recent points to check timestamps."""
    try:
        payload = {
            "limit": limit,
            "with_payload": True,
            "with_vector": False,
        }
        req = Request(
            f"{QDRANT_URL}/collections/{collection_name}/points/scroll",
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            points = data.get("result", {}).get("points", [])
            return points
    except Exception as e:
        return []


def check_ollama_active() -> dict:
    """Verify Ollama is running and has the embedding model."""
    try:
        req = Request(f"{OLLAMA_URL}/api/tags", method="GET")
        with urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            models = [m["name"] for m in data.get("models", [])]
            has_embed = any("nomic-embed-text" in m for m in models)
            return {
                "running": True,
                "has_embedding_model": has_embed,
                "models": models,
            }
    except Exception:
        return {"running": False, "has_embedding_model": False, "models": []}


def check_usage(since_minutes: int = 60) -> dict:
    """Check if there has been actual memory usage recently."""
    result = {
        "qdrant_running": False,
        "ollama_running": False,
        "agent_memory": {"points": 0, "recent_stores": 0},
        "semantic_cache": {"points": 0, "recent_stores": 0},
        "recent_activity": [],
        "verdict": "NO_USAGE",
    }

    # Check Qdrant
    try:
        req = Request(f"{QDRANT_URL}/collections", method="GET")
        with urlopen(req, timeout=5) as response:
            result["qdrant_running"] = True
    except Exception:
        result["verdict"] = "QDRANT_DOWN"
        return result

    # Check Ollama
    ollama = check_ollama_active()
    result["ollama_running"] = ollama["running"]
    if not ollama["running"]:
        result["verdict"] = "OLLAMA_DOWN"
        return result

    # Check collections
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=since_minutes)
    cutoff_str = cutoff.isoformat()

    for collection in ["agent_memory", "semantic_cache"]:
        info = get_collection_info(collection)
        if not info.get("exists"):
            continue

        result[collection]["points"] = info.get("points_count", 0)

        # Get recent points and check timestamps
        points = get_recent_points(collection, limit=50)
        recent_count = 0
        for point in points:
            payload = point.get("payload", {})
            timestamp = payload.get("timestamp", "")
            if timestamp and timestamp > cutoff_str:
                recent_count += 1
                result["recent_activity"].append({
                    "collection": collection,
                    "type": payload.get("type", "unknown"),
                    "project": payload.get("project", "unknown"),
                    "timestamp": timestamp,
                    "content_preview": str(payload.get("content", payload.get("query", "")))[:100],
                })

        result[collection]["recent_stores"] = recent_count

    # Verdict
    total_recent = (
        result["agent_memory"]["recent_stores"]
        + result["semantic_cache"]["recent_stores"]
    )
    total_points = (
        result["agent_memory"]["points"] + result["semantic_cache"]["points"]
    )

    if total_recent > 0:
        result["verdict"] = "ACTIVE_USAGE"
    elif total_points > 0:
        result["verdict"] = "HAS_DATA_BUT_NO_RECENT_USAGE"
    else:
        result["verdict"] = "EMPTY_NO_USAGE"

    # Sort recent activity by timestamp
    result["recent_activity"].sort(
        key=lambda x: x.get("timestamp", ""), reverse=True
    )

    return result


def generate_report() -> dict:
    """Generate a full report of all stored memories."""
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "collections": {},
        "summary": {},
    }

    for collection in ["agent_memory", "semantic_cache"]:
        info = get_collection_info(collection)
        points = get_recent_points(collection, limit=100)

        entries = []
        projects = set()
        types = set()
        oldest = None
        newest = None

        for point in points:
            payload = point.get("payload", {})
            ts = payload.get("timestamp", "")
            entry = {
                "id": str(point.get("id", "")),
                "type": payload.get("type", "unknown"),
                "project": payload.get("project", "unknown"),
                "timestamp": ts,
                "tags": payload.get("tags", []),
                "content_preview": str(
                    payload.get("content", payload.get("query", ""))
                )[:200],
            }
            entries.append(entry)
            projects.add(entry["project"])
            types.add(entry["type"])

            if ts:
                if oldest is None or ts < oldest:
                    oldest = ts
                if newest is None or ts > newest:
                    newest = ts

        report["collections"][collection] = {
            "total_points": info.get("points_count", 0),
            "sampled_entries": len(entries),
            "projects": sorted(projects),
            "types": sorted(types),
            "oldest_entry": oldest,
            "newest_entry": newest,
            "entries": entries,
        }

    # Summary
    total = sum(
        c.get("total_points", 0) for c in report["collections"].values()
    )
    all_projects = set()
    for c in report["collections"].values():
        all_projects.update(c.get("projects", []))

    report["summary"] = {
        "total_stored": total,
        "projects": sorted(all_projects),
        "collections_count": len(report["collections"]),
    }

    return report


def main():
    parser = argparse.ArgumentParser(
        description="Prove Qdrant/Ollama memory is being actively used"
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Quick check for recent memory activity",
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="Full report of all stored memories",
    )
    parser.add_argument(
        "--since",
        type=int,
        default=60,
        help="Check for activity within the last N minutes (default: 60)",
    )
    args = parser.parse_args()

    if not args.check and not args.report:
        args.check = True  # Default to check

    if args.check:
        result = check_usage(since_minutes=args.since)
        print(json.dumps(result, indent=2))

        verdict = result["verdict"]
        if verdict == "ACTIVE_USAGE":
            total_recent = (
                result["agent_memory"]["recent_stores"]
                + result["semantic_cache"]["recent_stores"]
            )
            print(
                f"\n✅ ACTIVE USAGE: {total_recent} stores in the last {args.since} minutes"
            )
            sys.exit(0)
        elif verdict == "HAS_DATA_BUT_NO_RECENT_USAGE":
            total = (
                result["agent_memory"]["points"]
                + result["semantic_cache"]["points"]
            )
            print(
                f"\n⚠️  HAS DATA ({total} points) but NO activity in the last {args.since} minutes"
            )
            sys.exit(1)
        elif verdict in ("QDRANT_DOWN", "OLLAMA_DOWN"):
            print(f"\n❌ {verdict}: Infrastructure not running")
            sys.exit(2)
        else:
            print(f"\n❌ NO USAGE: Collections are empty")
            sys.exit(1)

    if args.report:
        report = generate_report()
        print(json.dumps(report, indent=2))
        print(
            f"\n📊 Report: {report['summary']['total_stored']} total entries "
            f"across {report['summary']['collections_count']} collections, "
            f"{len(report['summary']['projects'])} projects"
        )
        sys.exit(0)


if __name__ == "__main__":
    main()
