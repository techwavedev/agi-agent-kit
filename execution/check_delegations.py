#!/usr/bin/env python3
"""
Script: check_delegations.py
Purpose: Scan .tmp/delegations/ for pending sub-agent delegation files and report
         them so the next session can resume interrupted work automatically.

         Two delegation file types are scanned:
           1. agent_runtime.py markdown delegations (subagent_*.md) with YAML frontmatter:
                  status: pending | completed
                  run_id: <id>
                  persona: <agent_id>
                  created_at: <ISO-8601 timestamp>
           2. copilot_pr_poller.py JSON delegations (<run_id>.json) with fields:
                  status: dispatched | polling | ...
                  run_id, issue_url, pr_url, state

Usage:
    python3 execution/check_delegations.py
    python3 execution/check_delegations.py --auto-resume
    python3 execution/check_delegations.py --json

Arguments:
    --auto-resume  Print a re-injection prompt block for each pending delegation
    --json         Output JSON only (for programmatic use)

Exit Codes:
    0 - No pending delegations
    1 - One or more pending delegations found
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

STALE_THRESHOLD_HOURS = 24

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from resolve_paths import get_project_root
except ImportError:
    def get_project_root():
        return Path.cwd()

PROJECT_DIR = get_project_root()
DELEGATIONS_DIR = PROJECT_DIR / ".tmp" / "delegations"


def _parse_frontmatter(text: str) -> dict:
    """Parse simple YAML frontmatter from a markdown string.

    Returns a dict of key/value pairs found between the opening and closing
    ``---`` fences.  Only scalar string values are supported (sufficient for
    the delegation file format).
    """
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    meta = {}
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if ":" in line:
            key, _, value = line.partition(":")
            meta[key.strip()] = value.strip()
    return meta


def scan_delegations() -> dict:
    """Scan DELEGATIONS_DIR and return categorized delegation lists.

    Scans two file types:
      - subagent_*.md  — agent_runtime.py markdown delegations (status: pending)
      - *.json         — copilot_pr_poller.py JSON delegations (status: dispatched|polling)

    Returns:
        {
            "pending": [...],   # active, not yet completed
            "stale": [...],     # pending but older than STALE_THRESHOLD_HOURS
        }
    """
    pending = []
    stale = []

    if not DELEGATIONS_DIR.exists():
        return {"pending": pending, "stale": stale}

    now = datetime.now(timezone.utc)
    stale_cutoff = now - timedelta(hours=STALE_THRESHOLD_HOURS)

    # ── 1. agent_runtime.py markdown delegations ──────────────────────────────
    for path in sorted(DELEGATIONS_DIR.glob("subagent_*.md")):
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue

        meta = _parse_frontmatter(text)
        if meta.get("status") != "pending":
            continue

        # Parse creation timestamp (fall back to file mtime)
        created_at_str = meta.get("created_at", "")
        try:
            created_at = datetime.fromisoformat(created_at_str)
            if created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=timezone.utc)
        except (ValueError, TypeError):
            mtime = path.stat().st_mtime
            created_at = datetime.fromtimestamp(mtime, tz=timezone.utc)
            created_at_str = created_at.isoformat()

        age_seconds = (now - created_at).total_seconds()
        age_hours = age_seconds / 3600

        entry = {
            "type": "subagent",
            "run_id": meta.get("run_id", path.stem),
            "persona": meta.get("persona", "unknown"),
            "created_at": created_at_str,
            "age_hours": round(age_hours, 2),
            "instructions_file": str(path.resolve()),
        }

        if created_at < stale_cutoff:
            stale.append(entry)
        else:
            pending.append(entry)

    # ── 2. copilot_pr_poller.py JSON delegations ───────────────────────────────
    for path in sorted(DELEGATIONS_DIR.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if data.get("status") not in ("dispatched", "polling"):
            continue

        # Determine age via file mtime (JSON files may not carry created_at)
        mtime = path.stat().st_mtime
        created_at = datetime.fromtimestamp(mtime, tz=timezone.utc)
        age_hours = (now - created_at).total_seconds() / 3600

        entry = {
            "type": "copilot",
            "run_id": data.get("run_id", path.stem),
            "issue_url": data.get("issue_url"),
            "pr_url": data.get("pr_url"),
            "state": data.get("state"),
            "instructions_file": str(path.resolve()),
            "age_hours": round(age_hours, 2),
        }

        if created_at < stale_cutoff:
            stale.append(entry)
        else:
            pending.append(entry)

    return {"pending": pending, "stale": stale}


def build_resume_block(entry: dict) -> str:
    """Return a markdown re-injection block for a single pending delegation."""
    run_id = entry["run_id"]
    instructions_file = entry["instructions_file"]

    if entry.get("type") == "copilot":
        issue_url = entry.get("issue_url") or "N/A"
        pr_url = entry.get("pr_url") or "N/A"
        state = entry.get("state") or "unknown"
        age_hours = entry.get("age_hours", "?")
        return (
            f"## ⚠️ Pending Copilot Delegation Detected\n\n"
            f"- **Run ID:** `{run_id}`\n"
            f"- **Type:** Copilot PR poller\n"
            f"- **Age:** {age_hours}h\n"
            f"- **Issue URL:** {issue_url}\n"
            f"- **PR URL:** {pr_url}\n"
            f"- **State:** `{state}`\n"
            f"- **Delegation file:** `{instructions_file}`\n\n"
            f"**Action required:** Review the delegation file above to check the "
            f"current Copilot PR state and take any required follow-up actions.\n"
        )

    # subagent delegation
    persona = entry.get("persona", "unknown")
    age_hours = entry.get("age_hours", "?")
    return (
        f"## ⚠️ Pending Delegation Detected\n\n"
        f"- **Run ID:** `{run_id}`\n"
        f"- **Persona:** `{persona}`\n"
        f"- **Age:** {age_hours}h\n"
        f"- **Instructions file:** `{instructions_file}`\n\n"
        f"**Action required:** Open the instructions file above and execute the task "
        f"as persona `{persona}`. When done, state: "
        f"**\"SUB-AGENT {persona} COMPLETED\"**.\n"
    )


def main():
    parser = argparse.ArgumentParser(
        description="Check for pending sub-agent delegations from previous sessions"
    )
    parser.add_argument("--auto-resume", action="store_true",
                        help="Print re-injection prompt blocks for each pending delegation")
    parser.add_argument("--json", action="store_true", dest="json_output",
                        help="JSON output only (for programmatic use)")
    args = parser.parse_args()

    result = scan_delegations()
    pending = result["pending"]
    stale = result["stale"]
    all_pending = pending + stale
    total = len(all_pending)

    if args.json_output:
        print(json.dumps({
            "pending": pending,
            "stale": stale,
            "total_pending": total,
        }, indent=2))
        sys.exit(0 if total == 0 else 1)

    if total == 0:
        print("✅ No pending delegations.")
        sys.exit(0)

    # Human-readable output
    print(f"⚠️  Pending Delegations: {len(pending)} active, {len(stale)} stale (>{STALE_THRESHOLD_HOURS}h)")

    if pending:
        print("\n📋 Active pending:")
        for entry in pending:
            if entry.get("type") == "copilot":
                print(f"   • [{entry['run_id']}] type=copilot  state={entry.get('state')}  age={entry['age_hours']}h")
                if entry.get("issue_url"):
                    print(f"     issue: {entry['issue_url']}")
                print(f"     file: {entry['instructions_file']}")
            else:
                print(f"   • [{entry['run_id']}] persona={entry['persona']}  age={entry['age_hours']}h")
                print(f"     file: {entry['instructions_file']}")

    if stale:
        print(f"\n🗑️  Stale (>{STALE_THRESHOLD_HOURS}h) — consider cleanup:")
        for entry in stale:
            if entry.get("type") == "copilot":
                print(f"   • [{entry['run_id']}] type=copilot  state={entry.get('state')}  age={entry['age_hours']}h")
            else:
                print(f"   • [{entry['run_id']}] persona={entry['persona']}  age={entry['age_hours']}h")

    if args.auto_resume:
        print("\n" + "=" * 60)
        print("AUTO-RESUME INJECTION BLOCKS")
        print("=" * 60)
        for entry in pending:
            print()
            print(build_resume_block(entry))

    sys.exit(1)


if __name__ == "__main__":
    main()
