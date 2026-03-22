#!/usr/bin/env python3
"""
Context Mode — PostCompact Hook (Re-injection)

Fires after Claude's context is auto-compacted.
Queries SQLite for critical session state and re-injects it,
optionally also pulling from Qdrant for cross-session context.

Reads JSON from stdin (Claude Code hook protocol), outputs JSON to stdout.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

HOOK_DIR = Path(__file__).resolve().parent
PROJECT_DIR = HOOK_DIR.parent.parent
CONTEXT_MODE_SCRIPT = PROJECT_DIR / "execution" / "context_mode.py"
MEMORY_MANAGER_SCRIPT = PROJECT_DIR / "execution" / "memory_manager.py"


def get_sqlite_context(max_tokens: int = 2000) -> str:
    """Re-inject from SQLite via context_mode.py reinject."""
    if not CONTEXT_MODE_SCRIPT.exists():
        return ""

    try:
        proc = subprocess.run(
            ["python3", str(CONTEXT_MODE_SCRIPT), "reinject", "--max-tokens", str(max_tokens)],
            capture_output=True, text=True, timeout=10,
            cwd=str(PROJECT_DIR),
        )
        if proc.returncode == 0:
            result = json.loads(proc.stdout)
            return result.get("payload", "")
    except Exception:
        pass
    return ""


def get_qdrant_context(query: str = "current session decisions and progress") -> str:
    """Pull recent context from Qdrant memory."""
    if not MEMORY_MANAGER_SCRIPT.exists():
        return ""

    try:
        proc = subprocess.run(
            [
                "python3", str(MEMORY_MANAGER_SCRIPT), "retrieve",
                "--query", query,
                "--top-k", "5",
            ],
            capture_output=True, text=True, timeout=15,
            cwd=str(PROJECT_DIR),
        )
        if proc.returncode == 0:
            result = json.loads(proc.stdout)
            chunks = result.get("context_chunks", [])
            if chunks:
                lines = ["## Qdrant Memory (cross-session)"]
                for chunk in chunks[:5]:
                    content = chunk.get("content", "")[:200]
                    lines.append(f"- {content}")
                return "\n".join(lines)
    except Exception:
        pass
    return ""


def main():
    try:
        hook_input = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, EOFError):
        hook_input = {}

    # Get max tokens from env or default
    max_tokens = int(os.environ.get("CTX_REINJECT_TOKENS", "2000"))
    qdrant_enabled = os.environ.get("CTX_QDRANT_PERSIST", "false").lower() == "true"

    # Build re-injection payload
    parts = []

    # 1. SQLite session context (primary)
    sqlite_ctx = get_sqlite_context(max_tokens)
    if sqlite_ctx:
        parts.append(sqlite_ctx)

    # 2. Qdrant cross-session context (if enabled)
    if qdrant_enabled:
        qdrant_ctx = get_qdrant_context()
        if qdrant_ctx:
            parts.append(qdrant_ctx)

    if not parts:
        # Nothing to reinject — just log
        sys.exit(0)

    payload = "\n\n".join(parts)

    hook_output = {
        "hookSpecificOutput": {
            "hookEventName": "PostCompact",
            "additionalContext": payload,
        }
    }

    print(json.dumps(hook_output))
    sys.exit(0)


if __name__ == "__main__":
    main()