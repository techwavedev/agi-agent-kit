#!/usr/bin/env python3
"""
Script: chain_anchor.py
Purpose: Anchor memory content hashes to local MultiChain stream (async, optional).
         If MultiChain is not available, hashes are queued to a local JSONL file
         for later batch anchoring.

Usage:
    python3 execution/chain_anchor.py anchor --hash <sha256> --agent-id <id> --point-id <uuid>
    python3 execution/chain_anchor.py flush
    python3 execution/chain_anchor.py status

Exit Codes:
    0 - Success
    1 - Chain unavailable (hash queued)
    2 - Operation error
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

MULTICHAIN_RPC = os.environ.get("MULTICHAIN_RPC", "http://localhost:4770")
CHAIN_NAME = os.environ.get("MULTICHAIN_NAME", "agentrust")
STREAM_NAME = "memory_anchors"
QUEUE_FILE = Path.home() / ".agi-agent-kit" / "anchor_queue.jsonl"


def _rpc_call(method: str, params: list = None) -> dict:
    """Make a JSON-RPC call to MultiChain."""
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": method,
        "params": params or [],
    }
    req = Request(
        MULTICHAIN_RPC,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(req, timeout=10) as response:
        return json.loads(response.read().decode())


def check_chain() -> dict:
    """Check if MultiChain is running and the anchor stream exists."""
    try:
        info = _rpc_call("getinfo")
        if "error" in info and info["error"]:
            return {"status": "error", "message": str(info["error"])}

        # Check if stream exists
        try:
            _rpc_call("liststreams", [STREAM_NAME])
            stream_exists = True
        except Exception:
            stream_exists = False

        return {
            "status": "ok",
            "chain": info.get("result", {}).get("chainname", CHAIN_NAME),
            "stream_exists": stream_exists,
            "rpc_url": MULTICHAIN_RPC,
        }
    except (URLError, HTTPError, ConnectionError, OSError):
        return {"status": "not_running", "rpc_url": MULTICHAIN_RPC}


def _queue_hash(content_hash: str, agent_id: str, point_id: str) -> dict:
    """Append hash to local queue file for later anchoring."""
    QUEUE_FILE.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "content_hash": content_hash,
        "agent_id": agent_id,
        "point_id": point_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    with open(QUEUE_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")
    return {"status": "queued", "queue_file": str(QUEUE_FILE), **entry}


def anchor_hash(content_hash: str, agent_id: str, point_id: str) -> dict:
    """
    Anchor a content hash to the chain.
    If chain unavailable, append to queue for later flush.
    """
    chain = check_chain()
    if chain["status"] != "ok":
        return _queue_hash(content_hash, agent_id, point_id)

    # Ensure stream exists
    if not chain.get("stream_exists"):
        try:
            _rpc_call("create", ["stream", STREAM_NAME, True])
        except Exception:
            return _queue_hash(content_hash, agent_id, point_id)

    # Publish to stream: key=agent_id, data=hex-encoded JSON
    data_hex = json.dumps({
        "content_hash": content_hash,
        "point_id": point_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }).encode().hex()

    try:
        result = _rpc_call("publish", [STREAM_NAME, agent_id, data_hex])
        if result.get("error"):
            return _queue_hash(content_hash, agent_id, point_id)
        return {
            "status": "anchored",
            "txid": result.get("result"),
            "content_hash": content_hash,
            "agent_id": agent_id,
        }
    except Exception:
        return _queue_hash(content_hash, agent_id, point_id)


def flush_queue() -> dict:
    """Read queue, anchor all pending hashes, clear processed entries."""
    if not QUEUE_FILE.exists():
        return {"status": "ok", "processed": 0, "message": "No pending entries"}

    entries = []
    with open(QUEUE_FILE, "r") as f:
        for line in f:
            line = line.strip()
            if line:
                entries.append(json.loads(line))

    if not entries:
        return {"status": "ok", "processed": 0}

    chain = check_chain()
    if chain["status"] != "ok":
        return {"status": "chain_unavailable", "pending": len(entries)}

    anchored = 0
    failed = []
    for entry in entries:
        result = anchor_hash(entry["content_hash"], entry["agent_id"], entry["point_id"])
        if result["status"] == "anchored":
            anchored += 1
        else:
            failed.append(entry)

    # Rewrite queue with only failed entries
    if failed:
        with open(QUEUE_FILE, "w") as f:
            for entry in failed:
                f.write(json.dumps(entry) + "\n")
    else:
        QUEUE_FILE.unlink(missing_ok=True)

    return {"status": "ok", "processed": anchored, "remaining": len(failed)}


def get_status() -> dict:
    """Return chain connectivity, queue depth, last anchor time."""
    chain = check_chain()
    queue_depth = 0
    if QUEUE_FILE.exists():
        with open(QUEUE_FILE, "r") as f:
            queue_depth = sum(1 for line in f if line.strip())

    return {
        "chain": chain,
        "queue_depth": queue_depth,
        "queue_file": str(QUEUE_FILE),
    }


def main():
    parser = argparse.ArgumentParser(description="Chain anchor for memory hashes")
    subparsers = parser.add_subparsers(dest="command", required=True)

    anchor_p = subparsers.add_parser("anchor", help="Anchor a content hash")
    anchor_p.add_argument("--hash", required=True, dest="content_hash")
    anchor_p.add_argument("--agent-id", required=True)
    anchor_p.add_argument("--point-id", required=True)

    subparsers.add_parser("flush", help="Flush queued hashes to chain")
    subparsers.add_parser("status", help="Check chain and queue status")

    args = parser.parse_args()

    try:
        if args.command == "anchor":
            result = anchor_hash(args.content_hash, args.agent_id, args.point_id)
            print(json.dumps(result, indent=2))
            sys.exit(0 if result["status"] == "anchored" else 1)

        elif args.command == "flush":
            result = flush_queue()
            print(json.dumps(result, indent=2))
            sys.exit(0)

        elif args.command == "status":
            result = get_status()
            print(json.dumps(result, indent=2))
            sys.exit(0)

    except Exception as e:
        print(json.dumps({"status": "error", "message": str(e)}), file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
