#!/usr/bin/env python3
"""
Script: workflow_engine.py
Purpose: Execute guided multi-skill playbooks from data/workflows.json with
         progress tracking, step notes, and skill availability warnings.

Usage:
    # List all available playbooks
    python3 execution/workflow_engine.py list

    # Start a playbook by ID
    python3 execution/workflow_engine.py start ship-saas-mvp

    # Show current step details (re-read without advancing)
    python3 execution/workflow_engine.py next

    # Show progress bar and step statuses
    python3 execution/workflow_engine.py status

    # Mark current step complete and advance
    python3 execution/workflow_engine.py complete --notes "Planned scope with brainstorming skill"

    # Skip the current step with a reason
    python3 execution/workflow_engine.py skip --reason "Already done in previous session"

    # Abort the active playbook
    python3 execution/workflow_engine.py abort

State is persisted to .tmp/playbook_state.json between sessions.

Exit Codes:
    0 - Success
    1 - Invalid arguments / playbook not found
    2 - No active playbook
    3 - Playbook already complete
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path


# ─── Paths ────────────────────────────────────────────────────────────────────

_SCRIPT_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _SCRIPT_DIR.parent
_WORKFLOWS_FILE = _PROJECT_ROOT / "data" / "workflows.json"
_STATE_FILE = _PROJECT_ROOT / ".tmp" / "playbook_state.json"
_SKILLS_DIR = _PROJECT_ROOT / "skills"


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_workflows() -> list:
    """Load playbooks from data/workflows.json."""
    if not _WORKFLOWS_FILE.exists():
        print(json.dumps({
            "status": "error",
            "message": f"workflows.json not found at {_WORKFLOWS_FILE}",
        }))
        sys.exit(1)
    with _WORKFLOWS_FILE.open(encoding="utf-8") as fh:
        data = json.load(fh)
    return data.get("workflows", [])


def _find_playbook(playbook_id: str, workflows: list) -> "dict | None":
    """Return the playbook dict matching the given id, or None."""
    for wf in workflows:
        if wf.get("id") == playbook_id:
            return wf
    return None


def _load_state() -> dict:
    """Load persisted playbook state, returning empty dict if none."""
    if _STATE_FILE.exists():
        try:
            with _STATE_FILE.open(encoding="utf-8") as fh:
                return json.load(fh)
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def _save_state(state: dict) -> None:
    """Persist playbook state to .tmp/playbook_state.json."""
    _STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with _STATE_FILE.open("w", encoding="utf-8") as fh:
        json.dump(state, fh, indent=2)


def _installed_skills() -> set:
    """Return a set of skill folder names present in the skills/ directory."""
    if not _SKILLS_DIR.exists():
        return set()
    return {p.name for p in _SKILLS_DIR.iterdir() if p.is_dir()}


def _skill_warnings(recommended: list, installed: set) -> list:
    """Return list of skill IDs that are recommended but not installed."""
    return [s for s in recommended if s not in installed]


def _step_status_icon(status: str) -> str:
    icons = {
        "pending": "⬜",
        "complete": "✅",
        "skipped": "⏭️",
        "active": "▶️",
    }
    return icons.get(status, "⬜")


def _progress_bar(done: int, total: int, width: int = 20) -> str:
    filled = int(width * done / max(total, 1))
    return "[" + "█" * filled + "░" * (width - filled) + "]"


# ─── Commands ─────────────────────────────────────────────────────────────────

def cmd_list(args) -> int:
    """List all available playbooks."""
    workflows = _load_workflows()
    if not workflows:
        print(json.dumps({"status": "ok", "playbooks": [], "message": "No playbooks found."}))
        return 0

    playbooks = [
        {
            "id": wf["id"],
            "name": wf.get("name", wf["id"]),
            "description": wf.get("description", ""),
            "category": wf.get("category", ""),
            "step_count": len(wf.get("steps", [])),
        }
        for wf in workflows
    ]

    if args.json:
        print(json.dumps({"status": "ok", "playbooks": playbooks}))
        return 0

    print("\n📋  Available Playbooks\n")
    for pb in playbooks:
        print(f"  {pb['id']}")
        print(f"     {pb['name']}  [{pb['category']}]  •  {pb['step_count']} steps")
        if pb["description"]:
            print(f"     {pb['description']}")
        print()
    print(f"  Use: python3 execution/workflow_engine.py start <id>\n")
    return 0


def cmd_start(args) -> int:
    """Start a playbook."""
    workflows = _load_workflows()
    playbook = _find_playbook(args.id, workflows)
    if playbook is None:
        ids = [wf["id"] for wf in workflows]
        print(json.dumps({
            "status": "error",
            "message": f"Playbook '{args.id}' not found.",
            "available_ids": ids,
        }))
        return 1

    steps = playbook.get("steps", [])
    state = {
        "playbook_id": playbook["id"],
        "playbook_name": playbook.get("name", playbook["id"]),
        "started_at": _now_iso(),
        "current_step": 0,
        "steps": [
            {
                "index": i,
                "title": s.get("title", f"Step {i + 1}"),
                "goal": s.get("goal", ""),
                "recommendedSkills": s.get("recommendedSkills", []),
                "notes": s.get("notes", ""),
                "status": "pending",
                "completed_at": None,
                "agent_notes": None,
            }
            for i, s in enumerate(steps)
        ],
    }
    if steps:
        state["steps"][0]["status"] = "active"
    _save_state(state)

    if args.json:
        print(json.dumps({"status": "ok", "state": state}))
        return 0

    _print_step(state, 0)
    return 0


def cmd_next(args) -> int:
    """Show current step details."""
    state = _load_state()
    if not state:
        print(json.dumps({"status": "error", "message": "No active playbook. Run: start <id>"}))
        return 2

    idx = state.get("current_step", 0)
    steps = state.get("steps", [])

    if idx >= len(steps):
        print(json.dumps({"status": "complete", "message": "Playbook is already finished."}))
        return 3

    if args.json:
        print(json.dumps({"status": "ok", "step": steps[idx]}))
        return 0

    _print_step(state, idx)
    return 0


def cmd_status(args) -> int:
    """Show overall playbook progress."""
    state = _load_state()
    if not state:
        print(json.dumps({"status": "error", "message": "No active playbook. Run: start <id>"}))
        return 2

    steps = state.get("steps", [])
    total = len(steps)
    done = sum(1 for s in steps if s["status"] in ("complete", "skipped"))
    current_idx = state.get("current_step", 0)

    if args.json:
        print(json.dumps({
            "status": "ok",
            "playbook_id": state["playbook_id"],
            "playbook_name": state.get("playbook_name", ""),
            "current_step": current_idx,
            "total_steps": total,
            "completed": done,
            "progress_pct": round(done / max(total, 1) * 100),
            "steps": steps,
        }))
        return 0

    bar = _progress_bar(done, total)
    pct = round(done / max(total, 1) * 100)
    print(f"\n📊  {state.get('playbook_name', state['playbook_id'])}")
    print(f"    Progress: {bar} {done}/{total} steps ({pct}%)\n")
    for s in steps:
        active_marker = " ◀ current" if s["index"] == current_idx and s["status"] == "active" else ""
        icon = _step_status_icon(s["status"])
        print(f"    {icon}  Step {s['index'] + 1}: {s['title']}{active_marker}")
        if s.get("agent_notes"):
            print(f"         Notes: {s['agent_notes']}")
    print()
    return 0


def cmd_complete(args) -> int:
    """Mark current step complete and advance to next."""
    state = _load_state()
    if not state:
        print(json.dumps({"status": "error", "message": "No active playbook. Run: start <id>"}))
        return 2

    steps = state.get("steps", [])
    idx = state.get("current_step", 0)

    if idx >= len(steps):
        print(json.dumps({"status": "complete", "message": "Playbook is already finished."}))
        return 3

    steps[idx]["status"] = "complete"
    steps[idx]["completed_at"] = _now_iso()
    if args.notes:
        steps[idx]["agent_notes"] = args.notes

    next_idx = idx + 1
    state["current_step"] = next_idx

    if next_idx < len(steps):
        steps[next_idx]["status"] = "active"
        _save_state(state)

        if args.json:
            print(json.dumps({"status": "ok", "advanced_to": next_idx, "step": steps[next_idx]}))
            return 0

        print(f"\n✅  Step {idx + 1} complete.\n")
        _print_step(state, next_idx)
    else:
        _save_state(state)
        if args.json:
            print(json.dumps({"status": "complete", "message": "All steps done! Playbook complete."}))
            return 0
        total = len(steps)
        print(f"\n🎉  All {total} steps complete! Playbook '{state.get('playbook_name', state['playbook_id'])}' finished.\n")

    return 0


def cmd_skip(args) -> int:
    """Skip the current step."""
    state = _load_state()
    if not state:
        print(json.dumps({"status": "error", "message": "No active playbook. Run: start <id>"}))
        return 2

    steps = state.get("steps", [])
    idx = state.get("current_step", 0)

    if idx >= len(steps):
        print(json.dumps({"status": "complete", "message": "Playbook is already finished."}))
        return 3

    steps[idx]["status"] = "skipped"
    steps[idx]["completed_at"] = _now_iso()
    if args.reason:
        steps[idx]["agent_notes"] = f"SKIPPED: {args.reason}"

    next_idx = idx + 1
    state["current_step"] = next_idx

    if next_idx < len(steps):
        steps[next_idx]["status"] = "active"
        _save_state(state)

        if args.json:
            print(json.dumps({"status": "ok", "skipped": idx, "advanced_to": next_idx}))
            return 0

        print(f"\n⏭️   Step {idx + 1} skipped.\n")
        _print_step(state, next_idx)
    else:
        _save_state(state)
        if args.json:
            print(json.dumps({"status": "complete", "message": "All steps processed. Playbook complete."}))
            return 0
        total = len(steps)
        print(f"\n🏁  All {total} steps processed. Playbook '{state.get('playbook_name', state['playbook_id'])}' finished.\n")

    return 0


def cmd_abort(args) -> int:
    """Abort the active playbook and clear state."""
    state = _load_state()
    if not state:
        print(json.dumps({"status": "error", "message": "No active playbook to abort."}))
        return 2

    playbook_name = state.get("playbook_name", state.get("playbook_id", "unknown"))
    _STATE_FILE.unlink(missing_ok=True)

    if args.json:
        print(json.dumps({"status": "ok", "message": f"Playbook '{playbook_name}' aborted."}))
        return 0

    print(f"\n🛑  Playbook '{playbook_name}' aborted. State cleared.\n")
    return 0


# ─── Display Helpers ──────────────────────────────────────────────────────────

def _print_step(state: dict, idx: int) -> None:
    """Pretty-print a single step with skill availability warnings."""
    steps = state.get("steps", [])
    if idx >= len(steps):
        return

    step = steps[idx]
    total = len(steps)
    playbook_name = state.get("playbook_name", state.get("playbook_id", ""))

    installed = _installed_skills()
    recommended = step.get("recommendedSkills", [])
    missing = _skill_warnings(recommended, installed)

    print(f"\n▶️   {playbook_name}  —  Step {idx + 1}/{total}")
    print(f"    {step['title']}")
    print(f"\n    Goal: {step['goal']}")

    if recommended:
        print("\n    Recommended skills:")
        for skill in recommended:
            warn = "  ⚠️  not installed" if skill in missing else ""
            print(f"      • {skill}{warn}")

    if step.get("notes"):
        print(f"\n    Notes: {step['notes']}")

    print()
    if missing:
        print(f"    ⚠️  Missing skills: {', '.join(missing)}")
        print(f"    Install with: npx @techwavedev/agi-agent-kit init\n")

    print(f"    When done: python3 execution/workflow_engine.py complete --notes \"<what you did>\"")
    print(f"    To skip:   python3 execution/workflow_engine.py skip --reason \"<why>\"\n")


# ─── CLI ──────────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Workflow Engine — execute guided multi-skill playbooks",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--json", action="store_true", help="Output JSON instead of human-readable text")
    sub = parser.add_subparsers(dest="command")

    # list
    p_list = sub.add_parser("list", help="List available playbooks")
    p_list.add_argument("--json", action="store_true")

    # start
    p_start = sub.add_parser("start", help="Start a playbook by ID")
    p_start.add_argument("id", help="Playbook ID (e.g. ship-saas-mvp)")
    p_start.add_argument("--json", action="store_true")

    # next
    p_next = sub.add_parser("next", help="Show current step details")
    p_next.add_argument("--json", action="store_true")

    # status
    p_status = sub.add_parser("status", help="Show overall progress")
    p_status.add_argument("--json", action="store_true")

    # complete
    p_complete = sub.add_parser("complete", help="Mark current step complete and advance")
    p_complete.add_argument("--notes", default="", help="Notes about what was done")
    p_complete.add_argument("--json", action="store_true")

    # skip
    p_skip = sub.add_parser("skip", help="Skip current step")
    p_skip.add_argument("--reason", default="", help="Reason for skipping")
    p_skip.add_argument("--json", action="store_true")

    # abort
    p_abort = sub.add_parser("abort", help="Abort the active playbook")
    p_abort.add_argument("--json", action="store_true")

    args = parser.parse_args()

    dispatch = {
        "list": cmd_list,
        "start": cmd_start,
        "next": cmd_next,
        "status": cmd_status,
        "complete": cmd_complete,
        "skip": cmd_skip,
        "abort": cmd_abort,
    }

    if args.command is None:
        parser.print_help()
        return 1

    fn = dispatch.get(args.command)
    if fn is None:
        parser.print_help()
        return 1

    return fn(args)


if __name__ == "__main__":
    sys.exit(main())
