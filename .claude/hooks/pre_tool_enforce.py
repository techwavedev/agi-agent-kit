#!/usr/bin/env python3
"""
Context Mode — PreToolUse Hook (Enforcement Gate)

Fires BEFORE every tool execution. Enforces:
1. Session boot check — blocks if session_boot.py hasn't run
2. Learnings injection — adds skill learnings as context before Bash calls
   that invoke skill-related scripts
3. Pending doc team warning — reminds if commits happened without doc team

Exit 0 = allow tool to proceed (with optional context injection)
Exit 2 = block tool (stderr sent as feedback to Claude)
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

HOOK_DIR = Path(__file__).resolve().parent
PROJECT_DIR = HOOK_DIR.parent.parent
TMP_DIR = PROJECT_DIR / ".tmp"
BOOT_MARKER = TMP_DIR / "session_booted.json"
PENDING_DOC = TMP_DIR / "pending_doc_team.json"
LEARNINGS_FILE = PROJECT_DIR / "learnings.md"


def check_session_booted() -> bool:
    """Verify session_boot.py ran this session."""
    if not BOOT_MARKER.exists():
        return False
    try:
        data = json.loads(BOOT_MARKER.read_text())
        # Marker is valid if created today
        ts = data.get("timestamp", "")
        if ts:
            today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            return ts.startswith(today)
    except Exception:
        pass
    return False


def get_skill_learnings(skill_name: str) -> str | None:
    """Read learnings for a skill from learnings.md."""
    if not LEARNINGS_FILE.exists():
        return None

    try:
        content = LEARNINGS_FILE.read_text()
    except Exception:
        return None

    # Parse the skill's section
    in_skill = False
    items = []
    for line in content.splitlines():
        if line.startswith("## "):
            if in_skill:
                break  # Done with our skill's section
            if line[3:].strip().lower() == skill_name.lower():
                in_skill = True
        elif in_skill and line.startswith("- "):
            items.append(line[2:])

    if not items:
        return None

    return f"[LEARNINGS for {skill_name}] Review before executing:\n" + "\n".join(f"  {i}" for i in items)


def detect_skill_from_bash(command: str) -> str | None:
    """Try to detect a skill name from a bash command."""
    # Pattern: skill name appears in paths like skills/<name>/ or SKILL_<name>
    import re

    # Match skills/<name>/scripts/ or skills/<name>/
    m = re.search(r'skills/([a-zA-Z0-9_-]+)/', command)
    if m:
        return m.group(1)

    # Match SKILL.md references
    m = re.search(r'SKILL_([a-zA-Z0-9_]+)', command)
    if m:
        return m.group(1)

    return None


def check_pending_doc_team() -> str | None:
    """Check if there's a pending doc team dispatch."""
    if not PENDING_DOC.exists():
        return None
    try:
        data = json.loads(PENDING_DOC.read_text())
        if data.get("status") == "pending":
            commit = data.get("commit", "?")
            return (
                f"[ENFORCEMENT] Documentation team dispatch is PENDING for commit {commit}. "
                "Run: python3 execution/dispatch_agent_team.py --team documentation_team --payload '...'"
            )
    except Exception:
        pass
    return None


def main():
    try:
        hook_input = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, EOFError):
        sys.exit(0)  # Can't parse, allow through

    tool_name = hook_input.get("tool_name", "")
    tool_input = hook_input.get("tool_input", {})

    context_parts = []

    # ─── Enforcement 1: Session Boot Check ────────────────────────────────
    # Only enforce for "heavy" tools that indicate real work has started
    # Don't block Read/Grep (needed to read CLAUDE.md and boot instructions)
    heavy_tools = {"Bash", "Edit", "Write", "NotebookEdit"}

    if tool_name in heavy_tools and not check_session_booted():
        # Check if this IS the boot command itself
        command = tool_input.get("command", "")
        if "session_boot" in command:
            sys.exit(0)  # Allow the boot command through

        # Soft enforcement: inject reminder, don't block
        context_parts.append(
            "[ENFORCEMENT] session_boot.py has NOT been run this session. "
            "Run: python3 execution/session_boot.py --auto-fix"
        )

    # ─── Enforcement 2: Learnings Injection ───────────────────────────────
    if tool_name == "Bash":
        command = tool_input.get("command", "")
        skill_name = detect_skill_from_bash(command)
        if skill_name:
            learnings = get_skill_learnings(skill_name)
            if learnings:
                context_parts.append(learnings)

    # ─── Enforcement 3: Pending Doc Team ──────────────────────────────────
    # Only remind on Edit/Write (actual code changes) to avoid noise
    if tool_name in {"Edit", "Write"}:
        doc_warning = check_pending_doc_team()
        if doc_warning:
            context_parts.append(doc_warning)

    # ─── Output ───────────────────────────────────────────────────────────
    if context_parts:
        hook_output = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "additionalContext": "\n\n".join(context_parts),
            }
        }
        print(json.dumps(hook_output))

    sys.exit(0)  # Always allow (soft enforcement via context injection)


if __name__ == "__main__":
    main()