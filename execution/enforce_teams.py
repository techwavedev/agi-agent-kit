#!/usr/bin/env python3
"""
enforce_teams.py — Session-level mandatory team checklist enforcer.

Called by Claude Code hooks at key moments to remind about mandatory
agent team runs. Tracks state in .tmp/session_teams_run.json.

Usage:
  python3 execution/enforce_teams.py check-commit   # after git commit
  python3 execution/enforce_teams.py mark <team>    # mark a team as run
  python3 execution/enforce_teams.py session-end    # Stop hook — final audit
  python3 execution/enforce_teams.py reset          # new session
"""

import json
import sys
import os
from datetime import datetime
from pathlib import Path

STATE_FILE = Path(".tmp/session_teams_run.json")

MANDATORY_AFTER_CODE_CHANGE = [
    "documentation_team",
    "code_review_team",
]

MANDATORY_AFTER_COMMIT = [
    "documentation_team",
]

MANDATORY_PER_SESSION = [
    "cross_agent_broadcast",
    "sync_to_template_check",
    "memory_usage_proof",
]


def load_state():
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {"teams_run": [], "session_start": datetime.now().isoformat(), "commits_since_review": 0}


def save_state(state):
    STATE_FILE.write_text(json.dumps(state, indent=2))


def mark(team: str):
    state = load_state()
    if team not in state["teams_run"]:
        state["teams_run"].append(team)
    if team == "code_review_team":
        state["commits_since_review"] = 0
    save_state(state)
    print(f"✅ Marked as run: {team}")


def check_commit():
    """Called after git commit. Prints mandatory reminders."""
    state = load_state()
    state["commits_since_review"] = state.get("commits_since_review", 0) + 1
    save_state(state)

    run = state["teams_run"]
    missing = [t for t in MANDATORY_AFTER_CODE_CHANGE if t not in run]

    if missing:
        print("\n⚠️  MANDATORY TEAMS NOT YET RUN THIS SESSION:")
        for t in missing:
            cmd = f"python3 execution/dispatch_agent_team.py --team {t} --payload '{{...}}'"
            print(f"   ❌ {t}  →  {cmd}")
        print("\nDo NOT proceed to merge/publish until these are complete.")
        print("Mark complete with: python3 execution/enforce_teams.py mark <team>\n")
    else:
        print("✅ All mandatory teams run. Safe to proceed.")


def session_end():
    """Called at Stop. Final audit."""
    state = load_state()
    run = state["teams_run"]

    all_mandatory = list(set(MANDATORY_AFTER_CODE_CHANGE + MANDATORY_PER_SESSION))
    missing = [t for t in all_mandatory if t not in run]

    print("\n─── SESSION END AUDIT ───────────────────────────────")
    print(f"Teams run: {run or 'none'}")

    if missing:
        print(f"\n⚠️  MISSED THIS SESSION:")
        for t in missing:
            print(f"   ❌ {t}")
        print("\nStore context before ending:")
        print("  python3 execution/memory_manager.py store --content '...' --type decision --project <project>")
        print("  python3 execution/cross_agent_context.py broadcast --agent claude --message '...' --project <project>")
    else:
        print("✅ All mandatory steps completed this session.")
    print("─────────────────────────────────────────────────────\n")

    # Always run memory proof
    os.system("python3 execution/memory_usage_proof.py --check --since 120 2>/dev/null | tail -3")


def reset():
    state = {"teams_run": [], "session_start": datetime.now().isoformat(), "commits_since_review": 0}
    save_state(state)
    print("✅ Session checklist reset.")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "check-commit"
    if cmd == "check-commit":
        check_commit()
    elif cmd == "mark" and len(sys.argv) > 2:
        mark(sys.argv[2])
    elif cmd == "session-end":
        session_end()
    elif cmd == "reset":
        reset()
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)
