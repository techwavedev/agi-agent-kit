#!/usr/bin/env python3
"""
Script: session_boot.py
Purpose: Single entry point for session initialization. Checks memory system,
         initializes if needed, and returns a combined status report.

         This is the FIRST script an agent should run at session start.
         Combines: health check + session_init + platform detection.

Usage:
    python3 execution/session_boot.py
    python3 execution/session_boot.py --json
    python3 execution/session_boot.py --auto-fix

Arguments:
    --json       Output JSON only (for programmatic use)
    --auto-fix   Automatically fix issues (pull model, create collections)

Exit Codes:
    0 - Memory system ready
    1 - Memory available but degraded (missing model, empty collections)
    2 - Memory unavailable (Qdrant or Ollama not running)
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

# Configuration
QDRANT_URL = os.environ.get("QDRANT_URL", "http://localhost:6333")
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
EMBEDDING_MODEL = "nomic-embed-text"
PROJECT_DIR = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def check_qdrant() -> dict:
    """Check Qdrant connectivity and collection status."""
    result = {"status": "not_running", "collections": {}, "url": QDRANT_URL}
    try:
        req = Request(f"{QDRANT_URL}/collections", method="GET")
        with urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            names = [c["name"] for c in data.get("result", {}).get("collections", [])]
            result["status"] = "ok"

            for col_name in ["agent_memory", "semantic_cache"]:
                if col_name in names:
                    try:
                        col_req = Request(f"{QDRANT_URL}/collections/{col_name}", method="GET")
                        with urlopen(col_req, timeout=5) as col_resp:
                            col_data = json.loads(col_resp.read().decode())
                            points = col_data.get("result", {}).get("points_count", 0)
                            result["collections"][col_name] = {"exists": True, "points": points}
                    except Exception:
                        result["collections"][col_name] = {"exists": True, "points": -1}
                else:
                    result["collections"][col_name] = {"exists": False, "points": 0}
    except (URLError, HTTPError, Exception):
        pass
    return result


def check_ollama() -> dict:
    """Check Ollama connectivity and embedding model."""
    result = {"status": "not_running", "has_model": False, "url": OLLAMA_URL}
    try:
        req = Request(f"{OLLAMA_URL}/api/tags", method="GET")
        with urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            models = [m["name"] for m in data.get("models", [])]
            result["status"] = "ok"
            result["models"] = models
            result["has_model"] = any(EMBEDDING_MODEL in m for m in models)
    except (URLError, HTTPError, Exception):
        pass
    return result


def run_session_init() -> bool:
    """Run session_init.py to create collections."""
    init_script = PROJECT_DIR / "execution" / "session_init.py"
    if not init_script.exists():
        return False
    try:
        proc = subprocess.run(
            ["python3", str(init_script)],
            capture_output=True, text=True, timeout=30,
            cwd=str(PROJECT_DIR),
        )
        return proc.returncode == 0
    except Exception:
        return False


def pull_model() -> bool:
    """Pull the embedding model via Ollama."""
    try:
        proc = subprocess.run(
            ["ollama", "pull", EMBEDDING_MODEL],
            capture_output=True, text=True, timeout=120,
        )
        return proc.returncode == 0
    except Exception:
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Session boot: check + initialize memory system"
    )
    parser.add_argument("--json", action="store_true", dest="json_output",
                        help="JSON output only")
    parser.add_argument("--auto-fix", action="store_true",
                        help="Auto-fix issues (pull model, create collections)")
    args = parser.parse_args()

    report = {
        "qdrant": {},
        "ollama": {},
        "memory_ready": False,
        "actions_taken": [],
        "issues": [],
    }

    # Step 1: Check Qdrant
    qdrant = check_qdrant()
    report["qdrant"] = qdrant

    if qdrant["status"] != "ok":
        report["issues"].append("Qdrant not running. Start with: docker run -d -p 6333:6333 -v qdrant_storage:/qdrant/storage qdrant/qdrant")

    # Step 2: Check Ollama
    ollama = check_ollama()
    report["ollama"] = ollama

    if ollama["status"] != "ok":
        report["issues"].append("Ollama not running. Start with: ollama serve")
    elif not ollama["has_model"]:
        if args.auto_fix:
            if not args.json_output:
                print(f"⏳ Pulling {EMBEDDING_MODEL}...")
            if pull_model():
                report["actions_taken"].append(f"Pulled {EMBEDDING_MODEL}")
                ollama["has_model"] = True
            else:
                report["issues"].append(f"Failed to pull {EMBEDDING_MODEL}")
        else:
            report["issues"].append(f"Embedding model missing. Run: ollama pull {EMBEDDING_MODEL}")

    # Step 3: Initialize collections if needed
    if qdrant["status"] == "ok" and ollama["status"] == "ok" and ollama["has_model"]:
        agent_mem = qdrant["collections"].get("agent_memory", {})
        sem_cache = qdrant["collections"].get("semantic_cache", {})

        if not agent_mem.get("exists") or not sem_cache.get("exists"):
            if args.auto_fix:
                if not args.json_output:
                    print("⏳ Initializing collections...")
                if run_session_init():
                    report["actions_taken"].append("Created collections via session_init.py")
                    # Re-check
                    qdrant = check_qdrant()
                    report["qdrant"] = qdrant
                else:
                    report["issues"].append("Failed to initialize collections")
            else:
                report["issues"].append("Collections missing. Run: python3 execution/session_init.py")

    # Final readiness
    qdrant = report["qdrant"]
    ollama = report["ollama"]
    agent_mem = qdrant.get("collections", {}).get("agent_memory", {})
    sem_cache = qdrant.get("collections", {}).get("semantic_cache", {})

    report["memory_ready"] = (
        qdrant.get("status") == "ok"
        and ollama.get("status") == "ok"
        and ollama.get("has_model", False)
        and agent_mem.get("exists", False)
        and sem_cache.get("exists", False)
    )

    # Summary
    total_points = (
        agent_mem.get("points", 0) + sem_cache.get("points", 0)
    )
    report["summary"] = {
        "ready": report["memory_ready"],
        "total_memories": agent_mem.get("points", 0),
        "total_cached": sem_cache.get("points", 0),
    }

    if args.json_output:
        print(json.dumps(report, indent=2))
    else:
        if report["memory_ready"]:
            mem_pts = agent_mem.get("points", 0)
            cache_pts = sem_cache.get("points", 0)
            print(f"✅ Memory system ready — {mem_pts} memories, {cache_pts} cached responses")
        else:
            print("❌ Memory system not ready:")
            for issue in report["issues"]:
                print(f"   • {issue}")

        if report["actions_taken"]:
            for action in report["actions_taken"]:
                print(f"   ✅ {action}")

    sys.exit(0 if report["memory_ready"] else (1 if qdrant.get("status") == "ok" else 2))


if __name__ == "__main__":
    main()
