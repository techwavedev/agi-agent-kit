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
MEMORY_MODE = os.environ.get("MEMORY_MODE", "team").lower()
MODE_LABELS = {"solo": "Solo (Ollama+Qdrant)", "team": "Team (multi-tenancy)", "pro": "Pro (blockchain auth)"}


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


def check_blockchain() -> dict:
    """Check Aries (ACA-Py) connectivity (optional — does not affect readiness)."""
    result = {"status": "not_running", "optional": True, "agent": "ACA-Py (Hyperledger Aries)"}
    try:
        aries_url = os.environ.get("ARIES_ADMIN_URL", "http://localhost:8031")
        aries_key = os.environ.get("ARIES_ADMIN_KEY", "changeme_set_in_dotenv")
        req = Request(
            f"{aries_url}/status",
            headers={"X-API-Key": aries_key},
            method="GET"
        )
        with urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            result["status"] = "ok"
            result["version"] = data.get("version", "unknown")
            result["label"] = data.get("label", "unknown")
    except Exception:
        pass
    return result


def check_pulsar() -> dict:
    """Check Apache Pulsar connectivity (optional)."""
    result = {"status": "not_running", "optional": True}
    try:
        pulsar_url = os.environ.get("PULSAR_HTTP_URL", "http://localhost:8080")
        req = Request(f"{pulsar_url}/admin/v2/brokers/healthcheck", method="GET")
        with urlopen(req, timeout=5) as resp:
            if resp.status == 200:
                result["status"] = "ok"
    except Exception:
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


def check_identity(auto_fix: bool = False) -> dict:
    """Check/create agent identity keypair."""
    result = {"status": "not_found", "agent_id": None}
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from agent_identity import load_identity, get_or_create_identity

        identity = load_identity()
        if identity:
            result["status"] = "ok"
            result["agent_id"] = identity["agent_id"]
            result["public_key_hex"] = identity["public_key_hex"]
        elif auto_fix:
            identity = get_or_create_identity()
            result["status"] = "created"
            result["agent_id"] = identity["agent_id"]
            result["public_key_hex"] = identity["public_key_hex"]
        else:
            result["status"] = "not_found"
    except ImportError:
        result["status"] = "missing_cryptography"
        result["hint"] = "pip install cryptography"
    except Exception as e:
        result["status"] = f"error: {e}"
    return result


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
        "blockchain": {},
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

    # Step 2.5: Check agent identity
    identity = check_identity(args.auto_fix)
    report["identity"] = identity
    if identity["status"] == "created":
        report["actions_taken"].append(f"Generated agent identity: {identity['agent_id'][:16]}...")
    elif identity["status"] not in ("ok", "created"):
        report["issues"].append(f"Agent identity: {identity['status']}" +
                                (f" — {identity.get('hint', '')}" if identity.get("hint") else ""))

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

    # Step 4: Check blockchain (optional — does not affect readiness)
    blockchain = check_blockchain()
    report["blockchain"] = blockchain

    # Step 5: Check Pulsar (optional — does not affect readiness)
    pulsar = check_pulsar()
    report["pulsar"] = pulsar

    # Step 6: Auto-sync BM25 index from shared Qdrant (ensures keyword search works on every machine)
    bm25_result = {"status": "skipped"}
    if report.get("qdrant", {}).get("status") == "ok":
        try:
            import subprocess
            bm25_script = PROJECT_DIR / "execution" / "memory_manager.py"
            proc = subprocess.run(
                ["python3", str(bm25_script), "bm25-sync"],
                capture_output=True, text=True, timeout=60,
                cwd=str(PROJECT_DIR)
            )
            if proc.returncode == 0:
                import json as _json
                bm25_result = _json.loads(proc.stdout)
            else:
                bm25_result = {"status": "error", "message": proc.stderr[:200]}
        except Exception as e:
            bm25_result = {"status": "error", "message": str(e)}
    report["bm25_sync"] = bm25_result
    # Step 4: Register with Control Tower (best-effort)
    try:
        from control_tower import register_agent
        agent_name = os.environ.get("AGENT_NAME", "claude")
        ct_project = os.environ.get("AGENT_PROJECT", None)
        ct_result = register_agent(agent_name, project=ct_project)
        report["control_tower"] = {"status": "registered", "agent_id": ct_result.get("agent_id")}
        report["actions_taken"].append(f"Registered with Control Tower as {agent_name}")
    except Exception:
        report["control_tower"] = {"status": "skipped"}

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
        "memory_mode": MEMORY_MODE,
        "mode_label": MODE_LABELS.get(MEMORY_MODE, MEMORY_MODE),
        "total_memories": agent_mem.get("points", 0),
        "total_cached": sem_cache.get("points", 0),
        "agent_id": identity.get("agent_id"),
    }

    if args.json_output:
        print(json.dumps(report, indent=2))
    else:
        if report["memory_ready"]:
            mem_pts = agent_mem.get("points", 0)
            cache_pts = sem_cache.get("points", 0)
            mode_label = MODE_LABELS.get(MEMORY_MODE, MEMORY_MODE)
            print(f"✅ Memory system ready — {mem_pts} memories, {cache_pts} cached responses")
            print(f"   Mode: {mode_label}")
            bc = report.get("blockchain", {})
            if bc.get("status") == "ok":
                print(f"   🔗 Aries: connected (v{bc.get('version')}, {bc.get('label')})")
            elif MEMORY_MODE == "pro":
                print(f"   ⚠️  Aries: not running (start: docker compose -f docker-compose.aries.yml up -d)")
            ps = report.get("pulsar", {})
            if ps.get("status") == "ok":
                print(f"   📡 Pulsar: connected (real-time events)")
            elif MEMORY_MODE in ("team", "pro"):
                print(f"   ℹ️  Pulsar: not running (optional: docker compose -f docker-compose.pulsar.yml up -d)")
            bm25 = report.get("bm25_sync", {})
            if bm25.get("status") == "synced":
                print(f"   🔍 BM25: synced from Qdrant ({bm25.get('indexed', 0)} indexed, {bm25.get('total', 0)} total)")
            if identity.get("agent_id"):
                print(f"   Agent ID: {identity['agent_id'][:16]}...")
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
