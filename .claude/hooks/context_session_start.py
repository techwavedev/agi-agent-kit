#!/usr/bin/env python3
"""
Context Mode — SessionStart Hook

Auto-initializes a context tracking session when Claude Code starts.
Creates the SQLite DB and registers the session.
"""

import json
import os
import subprocess
import sys
import time
from pathlib import Path

HOOK_DIR = Path(__file__).resolve().parent
PROJECT_DIR = HOOK_DIR.parent.parent
CONTEXT_MODE_SCRIPT = PROJECT_DIR / "execution" / "context_mode.py"


def main():
    try:
        hook_input = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, EOFError):
        hook_input = {}

    session_id = hook_input.get("session_id", f"s-{int(time.time())}")
    agent = os.environ.get("CTX_AGENT", "claude")
    project = os.environ.get("CTX_PROJECT", "agi-agent-kit")

    if not CONTEXT_MODE_SCRIPT.exists():
        sys.exit(0)

    try:
        subprocess.run(
            [
                "python3", str(CONTEXT_MODE_SCRIPT), "init",
                "--session-id", session_id,
                "--agent", agent,
                "--project", project,
            ],
            capture_output=True, text=True, timeout=5,
            cwd=str(PROJECT_DIR),
        )
    except Exception:
        pass  # Non-blocking

    # Output context mode status message
    hook_output = {
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": (
                f"[Context Mode] Session initialized (id: {session_id}). "
                "Heavy tool outputs will be sandbox-filtered to save tokens. "
                "Use `python3 execution/context_mode.py status` for savings report."
            ),
        }
    }

    print(json.dumps(hook_output))
    sys.exit(0)


if __name__ == "__main__":
    main()