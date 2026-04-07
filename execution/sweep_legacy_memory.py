#!/usr/bin/env python3
"""
Script: sweep_legacy_memory.py
Purpose: Scans the Qdrant DB for legacy unstructured agent memories
         (missing 'wing' or 'room' metadata bounds) and optionally deletes
         them to prevent legacy context from corrupting new AI wing-ledgers.

Usage:
    python3 execution/sweep_legacy_memory.py             # Dry-run (count only)
    python3 execution/sweep_legacy_memory.py --force      # Actually delete
"""

import argparse
import json
import os
import sys
from urllib.request import Request, urlopen

QDRANT_URL = os.environ.get("QDRANT_URL", "http://localhost:6333")
COLLECTION = os.environ.get("MEMORY_COLLECTION", "agent_memory")

def count_legacy_points():
    """Count how many points lack wing or room metadata."""
    count_payload = {
        "filter": {
            "should": [
                {"is_empty": {"key": "wing"}},
                {"is_empty": {"key": "room"}}
            ]
        },
        "exact": True
    }
    req = Request(
        f"{QDRANT_URL}/collections/{COLLECTION}/points/count",
        data=json.dumps(count_payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urlopen(req, timeout=30) as response:
        result = json.loads(response.read().decode())
        return result.get("result", {}).get("count", 0)

def sweep_legacy_data():
    """Delete points missing 'wing' or 'room'."""
    payload = {
        "filter": {
            "should": [
                {"is_empty": {"key": "wing"}},
                {"is_empty": {"key": "room"}}
            ]
        }
    }
    req = Request(
        f"{QDRANT_URL}/collections/{COLLECTION}/points/delete",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urlopen(req, timeout=30) as response:
        return json.loads(response.read().decode())

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sweep legacy un-scoped memories from Qdrant")
    parser.add_argument("--force", action="store_true", help="Actually delete (default is dry-run)")
    args = parser.parse_args()

    try:
        count = count_legacy_points()
        print(f"🔍 Found {count} legacy points (missing wing/room metadata)")

        if count == 0:
            print("✅ Nothing to sweep.")
            sys.exit(0)

        if not args.force:
            print("⚠️  Dry-run mode. Use --force to actually delete these points.")
            sys.exit(0)

        print(f"🗑️  Deleting {count} legacy points...")
        result = sweep_legacy_data()
        print(json.dumps({
            "status": "success",
            "deleted_count": count,
            "qdrant_response": result
        }, indent=2))

    except Exception as e:
        print(json.dumps({
            "status": "error",
            "message": str(e)
        }, indent=2), file=sys.stderr)
        sys.exit(1)
