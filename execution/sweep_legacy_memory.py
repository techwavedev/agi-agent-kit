#!/usr/bin/env python3
"""
Script: sweep_legacy_memory.py
Purpose: Scans the Qdrant DB for legacy unstructured agent memories
         (missing 'wing' or 'room' metadata bounds) and forcefully deletes
         them to prevent legacy context from corrupting new AI wing-ledgers.
"""

import json
import os
import sys
from urllib.request import Request, urlopen

QDRANT_URL = os.environ.get("QDRANT_URL", "http://localhost:6333")
COLLECTION = os.environ.get("MEMORY_COLLECTION", "agent_memory")

def sweep_legacy_data():
    try:
        # Find points missing 'wing' or 'room'
        # In Qdrant, we can use IsEmpty condition
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
            result = json.loads(response.read().decode())
            print(json.dumps({
                "status": "success",
                "message": "Successfully swept legacy Qdrant data.",
                "qdrant_response": result
            }, indent=2))
            
    except Exception as e:
        print(json.dumps({
            "status": "error",
            "message": str(e)
        }, indent=2), file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    sweep_legacy_data()
