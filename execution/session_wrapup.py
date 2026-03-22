#!/usr/bin/env python3
"""
Script: session_wrapup.py
Purpose: Session Close Protocol. Reviews session activity, verifies memory stores,
         broadcasts accomplishments to other agents, and checks for stale temp files.

         This is the LAST script an agent should run before ending a session.
         Counterpart to session_boot.py (Session Boot Protocol).

Usage:
    python3 execution/session_wrapup.py
    python3 execution/session_wrapup.py --json
    python3 execution/session_wrapup.py --agent gemini --project myapp --since 90
    python3 execution/session_wrapup.py --auto-broadcast

Arguments:
    --agent          Agent name (default: "claude")
    --project        Project name for Qdrant filter
    --since          How far back to look for session activity in minutes (default: 60)
    --json           JSON-only output
    --auto-broadcast Automatically broadcast accomplishments to all agents

Exit Codes:
    0 - Session wrapped up successfully (memories were stored)
    1 - Session wrapped up with warnings (zero stores detected)
    2 - Memory system unreachable
"""

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

# Configuration
QDRANT_URL = os.environ.get("QDRANT_URL", "http://localhost:6333")
PROJECT_DIR = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TMP_DIR = PROJECT_DIR / ".tmp"
STALE_THRESHOLD_HOURS = 24


def get_recent_memories(since_minutes: int = 60, project: str = None) -> dict:
    """Query Qdrant for memories stored in the last N minutes."""
    result = {"status": "ok", "memories": [], "count": 0}
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=since_minutes)
    cutoff_iso = cutoff.isoformat()

    try:
        # Scroll through agent_memory collection and filter by timestamp
        scroll_body = {
            "limit": 100,
            "with_payload": True,
            "with_vector": False,
        }

        # Build filter: timestamp >= cutoff
        filter_conditions = []
        if project:
            filter_conditions.append(
                {"key": "project", "match": {"value": project}}
            )

        if filter_conditions:
            scroll_body["filter"] = {"must": filter_conditions}

        req = Request(
            f"{QDRANT_URL}/collections/agent_memory/points/scroll",
            data=json.dumps(scroll_body).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())

        points = data.get("result", {}).get("points", [])

        # Filter by timestamp client-side (Qdrant range filter on ISO strings)
        recent = []
        for point in points:
            payload = point.get("payload", {})
            ts = payload.get("timestamp", "")
            if ts and ts >= cutoff_iso:
                recent.append({
                    "content": payload.get("content", "")[:200],
                    "type": payload.get("type", "unknown"),
                    "timestamp": ts,
                    "tags": payload.get("tags", []),
                    "agent_id": payload.get("agent_id", ""),
                })

        result["memories"] = recent
        result["count"] = len(recent)

    except (URLError, HTTPError) as e:
        result["status"] = f"error: {e}"
    except Exception as e:
        result["status"] = f"error: {e}"

    return result


def verify_memory_stores(since_minutes: int = 60, project: str = None) -> dict:
    """Check if the agent stored any decisions/learnings during the session."""
    memories = get_recent_memories(since_minutes, project)

    if memories["status"] != "ok":
        return {
            "status": memories["status"],
            "stores_found": 0,
            "warning": "Could not verify memory stores",
        }

    count = memories["count"]
    types_stored = {}
    for mem in memories["memories"]:
        t = mem.get("type", "unknown")
        types_stored[t] = types_stored.get(t, 0) + 1

    warning = None
    if count == 0:
        warning = (
            "ZERO memories stored this session. "
            "Per protocol, you MUST store at least one decision/learning per task. "
            "Run: python3 execution/memory_manager.py store --content '...' --type decision"
        )

    return {
        "status": "ok",
        "stores_found": count,
        "types": types_stored,
        "warning": warning,
    }


def summarize_accomplishments(memories: dict) -> list:
    """Extract a concise list of accomplishments from recent memories."""
    accomplishments = []
    for mem in memories.get("memories", []):
        content = mem.get("content", "").strip()
        if content:
            # Strip agent prefix if present (e.g., "[CLAUDE] ...")
            if content.startswith("[") and "]" in content:
                content = content[content.index("]") + 1:].strip()
            accomplishments.append(content)
    return accomplishments


def broadcast_session(agent: str, accomplishments: list, project: str = None) -> dict:
    """Call cross_agent_context.py store to log session accomplishments."""
    if not accomplishments:
        return {"status": "skipped", "reason": "no accomplishments to broadcast"}

    # Summarize into a single broadcast message
    summary = "; ".join(accomplishments[:5])
    if len(accomplishments) > 5:
        summary += f" (and {len(accomplishments) - 5} more)"

    action = f"Session wrapup — accomplished: {summary}"

    cross_agent_script = PROJECT_DIR / "execution" / "cross_agent_context.py"
    if not cross_agent_script.exists():
        return {"status": "error", "reason": "cross_agent_context.py not found"}

    try:
        cmd = [
            "python3", str(cross_agent_script),
            "store",
            "--agent", agent,
            "--action", action,
        ]
        if project:
            cmd.extend(["--project", project])
        cmd.extend(["--tags", "session-wrapup"])

        proc = subprocess.run(
            cmd,
            capture_output=True, text=True, timeout=15,
            cwd=str(PROJECT_DIR),
        )
        if proc.returncode == 0:
            try:
                return json.loads(proc.stdout)
            except json.JSONDecodeError:
                return {"status": "stored", "raw": proc.stdout.strip()}
        else:
            return {"status": "error", "stderr": proc.stderr.strip()}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def check_stale_tmp_files() -> list:
    """Check .tmp/ for files older than STALE_THRESHOLD_HOURS."""
    stale_files = []
    if not TMP_DIR.exists():
        return stale_files

    cutoff = time.time() - (STALE_THRESHOLD_HOURS * 3600)

    for path in TMP_DIR.rglob("*"):
        if path.is_file():
            try:
                mtime = path.stat().st_mtime
                if mtime < cutoff:
                    age_hours = (time.time() - mtime) / 3600
                    stale_files.append({
                        "path": str(path.relative_to(PROJECT_DIR)),
                        "age_hours": round(age_hours, 1),
                        "size_bytes": path.stat().st_size,
                    })
            except OSError:
                continue

    # Sort by age descending
    stale_files.sort(key=lambda f: f["age_hours"], reverse=True)
    return stale_files


def apply_session_learnings() -> dict:
    """Apply accumulated learnings to skill.md files and sync to Qdrant."""
    learnings_script = PROJECT_DIR / "execution" / "learnings_engine.py"
    if not learnings_script.exists():
        return {"status": "skipped", "reason": "learnings_engine.py not found"}

    result = {"learnings_applied": 0, "qdrant_synced": False}

    # Apply learnings to all skills (dry-run safe)
    try:
        proc = subprocess.run(
            ["python3", str(learnings_script), "apply-all"],
            capture_output=True, text=True, timeout=30,
            cwd=str(PROJECT_DIR),
        )
        if proc.returncode == 0:
            try:
                data = json.loads(proc.stdout)
                applied = [r for r in data.get("results", []) if r.get("status") == "applied"]
                result["learnings_applied"] = len(applied)
            except json.JSONDecodeError:
                pass
    except Exception as e:
        result["apply_error"] = str(e)

    # Sync learnings to Qdrant
    try:
        proc = subprocess.run(
            ["python3", str(learnings_script), "sync"],
            capture_output=True, text=True, timeout=15,
            cwd=str(PROJECT_DIR),
        )
        result["qdrant_synced"] = proc.returncode == 0
    except Exception:
        pass

    # Export context_mode session data
    ctx_script = PROJECT_DIR / "execution" / "context_mode.py"
    if ctx_script.exists():
        try:
            subprocess.run(
                ["python3", str(ctx_script), "export"],
                capture_output=True, text=True, timeout=15,
                cwd=str(PROJECT_DIR),
            )
            result["context_exported"] = True
        except Exception:
            result["context_exported"] = False

    return result


def deregister_control_tower(agent: str, project: str = None) -> dict:
    """Best-effort heartbeat update via control_tower.py to mark session end."""
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from control_tower import heartbeat
        result = heartbeat(agent, task="session_ended", project=project)
        return {"status": "ok", "agent": agent, "timestamp": result.get("timestamp")}
    except ImportError:
        return {"status": "skipped", "reason": "control_tower.py not importable"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def main():
    parser = argparse.ArgumentParser(
        description="Session Close Protocol: review, verify, broadcast, cleanup"
    )
    parser.add_argument("--agent", default="claude",
                        help="Agent name (default: claude)")
    parser.add_argument("--project",
                        help="Project name for Qdrant filter")
    parser.add_argument("--since", type=int, default=60,
                        help="Look back N minutes for session activity (default: 60)")
    parser.add_argument("--json", action="store_true", dest="json_output",
                        help="JSON output only")
    parser.add_argument("--auto-broadcast", action="store_true",
                        help="Automatically broadcast accomplishments to all agents")
    args = parser.parse_args()

    report = {
        "session_wrapup": True,
        "agent": args.agent,
        "project": args.project,
        "since_minutes": args.since,
        "accomplishments": [],
        "memories_stored_count": 0,
        "memory_types": {},
        "stale_tmp_files": [],
        "broadcast_status": "not_requested",
        "control_tower": {},
        "warnings": [],
    }

    # Step 1: Review session activity
    memories = get_recent_memories(args.since, args.project)
    if memories["status"] != "ok":
        report["warnings"].append(f"Could not query memories: {memories['status']}")
    else:
        report["accomplishments"] = summarize_accomplishments(memories)

    # Step 2: Verify memory stores
    verification = verify_memory_stores(args.since, args.project)
    report["memories_stored_count"] = verification.get("stores_found", 0)
    report["memory_types"] = verification.get("types", {})
    if verification.get("warning"):
        report["warnings"].append(verification["warning"])

    # Step 3: Cross-agent broadcast (if requested)
    if args.auto_broadcast:
        broadcast_result = broadcast_session(
            args.agent, report["accomplishments"], args.project
        )
        report["broadcast_status"] = broadcast_result.get("status", "unknown")
        if broadcast_result.get("status") == "error":
            report["warnings"].append(
                f"Broadcast failed: {broadcast_result.get('message', broadcast_result.get('stderr', 'unknown'))}"
            )
    else:
        report["broadcast_status"] = "not_requested"

    # Step 4: Apply session learnings and export context
    learnings_result = apply_session_learnings()
    report["learnings"] = learnings_result

    # Step 5: Cleanup check for .tmp/
    stale = check_stale_tmp_files()
    report["stale_tmp_files"] = stale

    # Step 6: Control Tower deregister (best-effort)
    ct_result = deregister_control_tower(args.agent, args.project)
    report["control_tower"] = ct_result

    # Determine exit code
    has_warnings = len(report["warnings"]) > 0
    memory_unreachable = memories["status"] != "ok"

    if memory_unreachable:
        exit_code = 2
    elif report["memories_stored_count"] == 0:
        exit_code = 1
    else:
        exit_code = 0

    # Output
    if args.json_output:
        print(json.dumps(report, indent=2))
    else:
        print()
        if report["memories_stored_count"] > 0:
            print(f"  Session wrapup for [{args.agent}] — {report['memories_stored_count']} memories stored")
        else:
            print(f"  Session wrapup for [{args.agent}] — no memories stored this session")

        # Accomplishments
        if report["accomplishments"]:
            print(f"\n  Accomplishments ({len(report['accomplishments'])}):")
            for i, acc in enumerate(report["accomplishments"][:10], 1):
                print(f"    {i}. {acc}")
            if len(report["accomplishments"]) > 10:
                print(f"    ... and {len(report['accomplishments']) - 10} more")
        else:
            print("\n  No accomplishments recorded.")

        # Memory types
        if report["memory_types"]:
            types_str = ", ".join(f"{k}: {v}" for k, v in report["memory_types"].items())
            print(f"\n  Memory types: {types_str}")

        # Stale files
        if stale:
            total_size = sum(f["size_bytes"] for f in stale)
            size_mb = total_size / (1024 * 1024)
            print(f"\n  Stale .tmp/ files: {len(stale)} files ({size_mb:.1f} MB)")
            for f in stale[:5]:
                print(f"    - {f['path']} ({f['age_hours']}h old, {f['size_bytes']} bytes)")
            if len(stale) > 5:
                print(f"    ... and {len(stale) - 5} more")
        else:
            print("\n  No stale .tmp/ files.")

        # Learnings
        lr = report.get("learnings", {})
        applied = lr.get("learnings_applied", 0)
        synced = lr.get("qdrant_synced", False)
        ctx_exp = lr.get("context_exported", False)
        if applied > 0 or synced or ctx_exp:
            parts = []
            if applied > 0:
                parts.append(f"{applied} skills updated")
            if synced:
                parts.append("Qdrant synced")
            if ctx_exp:
                parts.append("context exported")
            print(f"\n  Self-correcting loop: {', '.join(parts)}")

        # Broadcast
        if args.auto_broadcast:
            if report["broadcast_status"] in ("stored", "ok"):
                print(f"\n  Broadcast: sent to other agents")
            else:
                print(f"\n  Broadcast: {report['broadcast_status']}")

        # Control Tower
        ct_status = report["control_tower"].get("status", "unknown")
        if ct_status == "ok":
            print(f"  Control Tower: session end registered")
        elif ct_status == "skipped":
            pass  # Silent skip
        else:
            print(f"  Control Tower: {ct_status}")

        # Warnings
        if report["warnings"]:
            print()
            for w in report["warnings"]:
                print(f"  WARNING: {w}")

        print()

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
