#!/usr/bin/env python3
"""
Script: team_state.py
Purpose: Helper for reading and writing per-run state.json files used by
         dispatch_agent_team.py and the lightweight team dashboard.

         State files live at: .tmp/team-runs/<run_id>/state.json

         Schema (opensquad-compatible, adapted for our team model):
           run_id       : str  — short UUID used for the run directory
           team         : str  — team_id (e.g. "documentation_team")
           status       : str  — "pending" | "running" | "completed" | "failed"
           current_step : int  — 0-based index of the active sub-agent
           total_steps  : int  — total number of sub-agents in the manifest
           sub_agents   : list — per-agent status objects (see below)
           handoff      : dict | null — last recorded handoff_state payload
           started_at   : str  — ISO-8601 timestamp when dispatch began
           updated_at   : str  — ISO-8601 timestamp of last update
           payload      : dict — original dispatch payload (sanitised)

         Sub-agent entry:
           id           : str  — agent id
           status       : str  — "pending" | "running" | "completed" | "failed"
           started_at   : str | null
           completed_at : str | null
           notes        : str | null — free-form progress note

Usage:
    # Write / update (upsert) state for a run
    python3 execution/team_state.py update \\
        --run-id abc12345 \\
        --status running \\
        --step 1 \\
        [--agent-id doc-writer] \\
        [--agent-status completed] \\
        [--notes "Wrote README section"] \\
        [--handoff '{"state": {...}, "next_steps": "..."}']

    # Read state for a specific run
    python3 execution/team_state.py read --run-id abc12345

    # List all currently-active runs (status == "running" | "pending")
    python3 execution/team_state.py list-active

    # Prune state files older than N days (default: 7)
    python3 execution/team_state.py prune [--days 7]

Exit Codes:
    0 - Success
    1 - Invalid arguments
    2 - State file not found (for read)
    3 - I/O error
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path


def find_project_root() -> Path:
    current = Path.cwd()
    for parent in [current] + list(current.parents):
        if (parent / "AGENTS.md").exists() or (parent / "package.json").exists():
            return parent
    return current


def runs_dir(root: Path) -> Path:
    return root / ".tmp" / "team-runs"


def state_path(root: Path, run_id: str) -> Path:
    return runs_dir(root) / run_id / "state.json"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ─── Public helpers ───────────────────────────────────────────────────────────

def write_initial_state(root: Path, run_id: str, team: str,
                        sub_agents: list, payload: dict) -> dict:
    """
    Called by dispatch_agent_team.py immediately after building the manifest.
    Creates .tmp/team-runs/<run_id>/state.json with status="pending".

    sub_agents must be a list of agent-id strings or dicts with at least "id".
    """
    now = now_iso()
    agent_entries = []
    for sa in sub_agents:
        if isinstance(sa, dict):
            agent_id = sa.get("id", str(sa))
        else:
            agent_id = str(sa)
        agent_entries.append({
            "id": agent_id,
            "status": "pending",
            "started_at": None,
            "completed_at": None,
            "notes": None,
        })

    # Sanitise payload: remove internal routing keys to keep state.json readable
    safe_payload = {k: v for k, v in payload.items()
                    if not k.startswith("_")}

    state = {
        "run_id": run_id,
        "team": team,
        "status": "pending",
        "current_step": 0,
        "total_steps": len(agent_entries),
        "sub_agents": agent_entries,
        "handoff": None,
        "started_at": now,
        "updated_at": now,
        "payload": safe_payload,
    }

    path = state_path(root, run_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2), encoding="utf-8")
    return state


def update_state(root: Path, run_id: str, *,
                 status: str = None,
                 current_step: int = None,
                 agent_id: str = None,
                 agent_status: str = None,
                 notes: str = None,
                 handoff: dict = None) -> dict:
    """
    Upsert fields in an existing state.json.  Safe to call from any sub-agent
    or from the orchestrator between steps.

    Returns the updated state dict.
    Raises FileNotFoundError if the state file does not exist.
    """
    path = state_path(root, run_id)
    if not path.exists():
        raise FileNotFoundError(f"State file not found: {path}")

    state = json.loads(path.read_text(encoding="utf-8"))
    now = now_iso()

    if status is not None:
        state["status"] = status

    if current_step is not None:
        state["current_step"] = current_step

    if handoff is not None:
        state["handoff"] = handoff

    if agent_id is not None and agent_status is not None:
        for entry in state.get("sub_agents", []):
            if entry["id"] == agent_id:
                entry["status"] = agent_status
                if notes is not None:
                    entry["notes"] = notes
                if agent_status == "running" and entry.get("started_at") is None:
                    entry["started_at"] = now
                elif agent_status in ("completed", "failed"):
                    entry["completed_at"] = now
                break

    state["updated_at"] = now
    path.write_text(json.dumps(state, indent=2), encoding="utf-8")
    return state


def read_state(root: Path, run_id: str) -> dict:
    """Read and return the state dict for a run, or raise FileNotFoundError."""
    path = state_path(root, run_id)
    if not path.exists():
        raise FileNotFoundError(f"State file not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def list_active(root: Path) -> list:
    """
    Return list of state dicts for runs whose status is "pending" or "running".
    """
    rdir = runs_dir(root)
    if not rdir.exists():
        return []

    active = []
    for state_file in sorted(rdir.glob("*/state.json")):
        try:
            state = json.loads(state_file.read_text(encoding="utf-8"))
            if state.get("status") in ("pending", "running"):
                active.append(state)
        except (json.JSONDecodeError, OSError):
            continue

    return active


def list_all(root: Path) -> list:
    """Return all run state dicts regardless of status."""
    rdir = runs_dir(root)
    if not rdir.exists():
        return []

    results = []
    for state_file in sorted(rdir.glob("*/state.json")):
        try:
            results.append(json.loads(state_file.read_text(encoding="utf-8")))
        except (json.JSONDecodeError, OSError):
            continue
    return results


def prune_old_states(root: Path, days: int = 7) -> dict:
    """
    Remove state directories older than `days` days.
    Returns {"pruned": N, "paths": [...]} for reporting.
    """
    rdir = runs_dir(root)
    if not rdir.exists():
        return {"pruned": 0, "paths": []}

    cutoff = time.time() - days * 86400
    pruned_paths = []

    for run_dir in rdir.iterdir():
        if not run_dir.is_dir():
            continue
        sf = run_dir / "state.json"
        if sf.exists():
            mtime = sf.stat().st_mtime
        else:
            # Use directory mtime as fallback
            mtime = run_dir.stat().st_mtime

        if mtime < cutoff:
            import shutil
            try:
                shutil.rmtree(run_dir)
                pruned_paths.append(str(run_dir.relative_to(root)))
            except OSError:
                pass

    return {"pruned": len(pruned_paths), "paths": pruned_paths}


# ─── CLI ─────────────────────────────────────────────────────────────────────

def cmd_update(args, root):
    try:
        handoff = json.loads(args.handoff) if args.handoff else None
    except json.JSONDecodeError as e:
        print(json.dumps({"status": "error", "message": f"Invalid --handoff JSON: {e}"}),
              file=sys.stderr)
        sys.exit(1)

    try:
        state = update_state(
            root, args.run_id,
            status=args.status,
            current_step=args.step,
            agent_id=args.agent_id,
            agent_status=args.agent_status,
            notes=args.notes,
            handoff=handoff,
        )
        print(json.dumps({"status": "ok", "run_id": args.run_id,
                          "updated_at": state["updated_at"]}))
    except FileNotFoundError as e:
        print(json.dumps({"status": "error", "message": str(e)}), file=sys.stderr)
        sys.exit(2)
    except OSError as e:
        print(json.dumps({"status": "error", "message": str(e)}), file=sys.stderr)
        sys.exit(3)


def cmd_read(args, root):
    try:
        state = read_state(root, args.run_id)
        print(json.dumps(state, indent=2))
    except FileNotFoundError as e:
        print(json.dumps({"status": "error", "message": str(e)}), file=sys.stderr)
        sys.exit(2)
    except OSError as e:
        print(json.dumps({"status": "error", "message": str(e)}), file=sys.stderr)
        sys.exit(3)


def cmd_list_active(args, root):
    active = list_active(root)
    print(json.dumps(active, indent=2))


def cmd_prune(args, root):
    days = args.days if hasattr(args, "days") and args.days else 7
    result = prune_old_states(root, days)
    print(json.dumps(result))


def main():
    parser = argparse.ArgumentParser(
        description="Read/write team-run state.json files"
    )
    sub = parser.add_subparsers(dest="command")

    # update
    p_update = sub.add_parser("update", help="Update state for a run")
    p_update.add_argument("--run-id", required=True)
    p_update.add_argument("--status",
                          choices=["pending", "running", "completed", "failed"])
    p_update.add_argument("--step", type=int, help="Current step index (0-based)")
    p_update.add_argument("--agent-id", help="Sub-agent id to update")
    p_update.add_argument("--agent-status",
                          choices=["pending", "running", "completed", "failed"])
    p_update.add_argument("--notes", help="Free-form note for the agent entry")
    p_update.add_argument("--handoff", help="JSON string for the handoff field")

    # read
    p_read = sub.add_parser("read", help="Read state for a run")
    p_read.add_argument("--run-id", required=True)

    # list-active
    sub.add_parser("list-active", help="List all pending/running runs")

    # prune
    p_prune = sub.add_parser("prune", help="Remove state files older than N days")
    p_prune.add_argument("--days", type=int, default=7,
                         help="Age threshold in days (default: 7)")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    root = find_project_root()

    if args.command == "update":
        cmd_update(args, root)
    elif args.command == "read":
        cmd_read(args, root)
    elif args.command == "list-active":
        cmd_list_active(args, root)
    elif args.command == "prune":
        cmd_prune(args, root)


if __name__ == "__main__":
    main()
