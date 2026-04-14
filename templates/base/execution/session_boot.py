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
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

# Configuration
QDRANT_URL = os.environ.get("QDRANT_URL", "http://localhost:6333")
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
EMBEDDING_MODEL = "nomic-embed-text"

# Generative models for local task routing (optional but recommended)
GENERATIVE_MODELS = [
    {"name": "gemma4:e4b", "tier": "fast", "required": False},
    {"name": "glm-4.7-flash:latest", "tier": "medium", "required": False},
]


sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from resolve_paths import get_project_root
except ImportError:
    def get_project_root(): return Path.cwd()

PROJECT_DIR = get_project_root()


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
            [sys.executable, str(init_script)],
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


def pull_generative_models(json_output: bool = False) -> tuple:
    """Pull generative models for local task routing. Returns (actions, issues)."""
    actions = []
    issues = []
    try:
        req = Request(f"{OLLAMA_URL}/api/tags", method="GET")
        with urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            installed = [m["name"] for m in data.get("models", [])]
    except Exception:
        return actions, issues

    for model_info in GENERATIVE_MODELS:
        model_name = model_info["name"]
        # Check if the exact requested model/tag is already installed.
        if model_name in installed:
            continue
        if not json_output:
            print(f"⏳ Pulling generative model {model_name} (for local task routing)...")
        try:
            proc = subprocess.run(
                ["ollama", "pull", model_name],
                capture_output=True, text=True, timeout=600,  # 10 min timeout for large models
            )
            if proc.returncode == 0:
                actions.append(f"Pulled generative model {model_name}")
            else:
                issues.append(f"Failed to pull {model_name}: {proc.stderr.strip()[:100]}")
        except subprocess.TimeoutExpired:
            issues.append(f"Timeout pulling {model_name} (try manually: ollama pull {model_name})")
        except Exception as e:
            issues.append(f"Error pulling {model_name}: {e}")
    return actions, issues


def main():
    parser = argparse.ArgumentParser(
        description="Session boot: check + initialize memory system"
    )
    parser.add_argument("--json", action="store_true", dest="json_output",
                        help="JSON output only")
    parser.add_argument("--auto-fix", action="store_true",
                        help="Auto-fix issues (pull model, create collections)")
    parser.add_argument("--no-generative", action="store_true",
                        help="Skip pulling large generative models during --auto-fix")
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
        if args.auto_fix:
            # Try restarting existing container first, then create new one
            import subprocess as _sp
            restarted = False
            try:
                check = _sp.run(["docker", "ps", "-a", "--filter", "name=^qdrant$", "--format", "{{.Names}}"],
                                capture_output=True, text=True, timeout=10)
                if "qdrant" in check.stdout.strip():
                    if not args.json_output:
                        print("⏳ Restarting existing Qdrant container...")
                    start = _sp.run(["docker", "start", "qdrant"], capture_output=True, text=True, timeout=30)
                    if start.returncode == 0:
                        import time as _time; _time.sleep(3)
                        qdrant = check_qdrant()
                        report["qdrant"] = qdrant
                        if qdrant["status"] == "ok":
                            restarted = True
                            report["actions_taken"].append("Restarted existing Qdrant container")
            except Exception:
                pass
            if not restarted:
                if not args.json_output:
                    print("⏳ Starting new Qdrant container...")
                try:
                    run_result = _sp.run(
                        ["docker", "run", "-d", "--name", "qdrant", "-p", "6333:6333",
                         "-v", "qdrant_storage:/qdrant/storage", "qdrant/qdrant"],
                        capture_output=True, text=True, timeout=30
                    )
                    if run_result.returncode == 0:
                        import time as _time; _time.sleep(3)
                        qdrant = check_qdrant()
                        report["qdrant"] = qdrant
                        if qdrant["status"] == "ok":
                            report["actions_taken"].append("Started new Qdrant container")
                        else:
                            report["issues"].append("Qdrant container started but not responding yet")
                    else:
                        report["issues"].append(f"Failed to start Qdrant: {run_result.stderr.strip()}")
                except Exception as e:
                    report["issues"].append(f"Failed to start Qdrant: {e}")
        else:
            report["issues"].append("Qdrant not running. Start with: docker start qdrant (or docker run -d --name qdrant -p 6333:6333 -v qdrant_storage:/qdrant/storage qdrant/qdrant)")

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

    # Step 2b: Pull generative models for local task routing (best-effort, opt-out with --no-generative)
    if ollama.get("status") == "ok" and args.auto_fix and not args.no_generative:
        gen_actions, gen_issues = pull_generative_models(json_output=args.json_output)
        report["actions_taken"].extend(gen_actions)
        report["issues"].extend(gen_issues)

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

    # Step 3.5: Check Langfuse observability (optional, for local dev)
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from langfuse_tracing import check_langfuse
        langfuse = check_langfuse()
        report["langfuse"] = langfuse
        if langfuse["status"] == "ok":
            report["actions_taken"].append("Langfuse tracing active")
        elif langfuse["status"] == "not_configured":
            report["langfuse"]["note"] = "Optional: set LANGFUSE_* in .env for observability"
        elif langfuse["status"] == "unreachable":
            report["langfuse"]["note"] = "Langfuse server not running (optional)"
    except Exception:
        report["langfuse"] = {"status": "skipped"}

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

    # Step 5: Write session boot marker (for PreToolUse enforcement)
    # Written AFTER memory_ready is evaluated so the value is accurate.
    try:
        tmp_dir = PROJECT_DIR / ".tmp"
        tmp_dir.mkdir(parents=True, exist_ok=True)
        boot_marker = tmp_dir / "session_booted.json"
        boot_marker.write_text(json.dumps({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "agent": os.environ.get("AGENT_NAME", "claude"),
            "memory_ready": report["memory_ready"],
        }, indent=2))
    except Exception:
        pass  # Non-blocking

    # Summary
    total_points = (
        agent_mem.get("points", 0) + sem_cache.get("points", 0)
    )
    report["summary"] = {
        "ready": report["memory_ready"],
        "total_memories": agent_mem.get("points", 0),
        "total_cached": sem_cache.get("points", 0),
        "agent_id": identity.get("agent_id"),
    }

    # Step 6: Check for pending delegations from previous sessions
    try:
        check_del_script = PROJECT_DIR / "execution" / "check_delegations.py"
        if check_del_script.exists():
            proc = subprocess.run(
                [sys.executable, str(check_del_script), "--json"],
                capture_output=True, text=True, timeout=10,
                cwd=str(PROJECT_DIR),
            )
            if proc.stdout.strip():
                del_data = json.loads(proc.stdout)
                report["pending_delegations"] = del_data
            else:
                report["pending_delegations"] = {"pending": [], "stale": [], "total_pending": 0}
        else:
            report["pending_delegations"] = {"pending": [], "stale": [], "total_pending": 0}
    except Exception:
        report["pending_delegations"] = {"pending": [], "stale": [], "total_pending": 0}

    if args.json_output:
        print(json.dumps(report, indent=2))
    else:
        if report["memory_ready"]:
            mem_pts = agent_mem.get("points", 0)
            cache_pts = sem_cache.get("points", 0)
            print(f"✅ Memory system ready — {mem_pts} memories, {cache_pts} cached responses")
            if identity.get("agent_id"):
                print(f"   Agent ID: {identity['agent_id'][:16]}...")
        else:
            print("❌ Memory system not ready:")
            for issue in report["issues"]:
                print(f"   • {issue}")

        if report["actions_taken"]:
            for action in report["actions_taken"]:
                print(f"   ✅ {action}")

        # Pending Delegations section
        del_report = report.get("pending_delegations", {})
        active = del_report.get("pending", [])
        stale = del_report.get("stale", [])
        if active or stale:
            print(f"\n⚠️  Pending Delegations: {len(active)} active, {len(stale)} stale (>24h)")
            for entry in active:
                if entry.get("type") == "copilot":
                    print(f"   • [{entry['run_id']}] type=copilot  state={entry.get('state')}  age={entry['age_hours']}h")
                    if entry.get("issue_url"):
                        print(f"     issue: {entry['issue_url']}")
                else:
                    print(f"   • [{entry['run_id']}] persona={entry.get('persona')}  age={entry['age_hours']}h")
                    print(f"     file: {entry['instructions_file']}")
            if stale:
                print("   🗑️  Stale (consider cleanup):")
                for entry in stale:
                    if entry.get("type") == "copilot":
                        print(f"   • [{entry['run_id']}] type=copilot  state={entry.get('state')}  age={entry['age_hours']}h")
                    else:
                        print(f"   • [{entry['run_id']}] persona={entry.get('persona')}  age={entry['age_hours']}h")
            print("   Run: python3 execution/check_delegations.py --auto-resume  to get re-injection blocks")

    sys.exit(0 if report["memory_ready"] else (1 if qdrant.get("status") == "ok" else 2))


if __name__ == "__main__":
    main()
