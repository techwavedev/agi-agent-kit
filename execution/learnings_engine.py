#!/usr/bin/env python3
"""
Script: learnings_engine.py
Purpose: Self-Correcting Memory Loop — the learnings.md pattern from NotebookLM.

         Each skill maintains a learnings section. When Claude fails or gets
         feedback, the learning is logged. Before each skill execution, Claude
         reads its learnings. At session end, accumulated feedback is used to
         permanently rewrite skill.md files.

Usage:
    # Record a learning for a skill
    python3 execution/learnings_engine.py log --skill brainstorming --learning "Keep outputs under 500 words" --severity warning

    # Read learnings for a skill (before executing it)
    python3 execution/learnings_engine.py read --skill brainstorming

    # Apply learnings: rewrite skill.md with accumulated feedback
    python3 execution/learnings_engine.py apply --skill brainstorming [--dry-run]

    # List all skills with learnings
    python3 execution/learnings_engine.py list

    # Bulk apply: process all skills with unapplied learnings
    python3 execution/learnings_engine.py apply-all [--dry-run]

    # Store learnings to Qdrant for cross-session persistence
    python3 execution/learnings_engine.py sync

Exit Codes:
    0 - Success
    1 - No data / skill not found
    2 - File error
    3 - Operation error
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_DIR = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LEARNINGS_FILE = PROJECT_DIR / "learnings.md"
SKILLS_DIRS = [
    PROJECT_DIR / "skills",
    PROJECT_DIR / "templates" / "skills" / "extended",
]


# ─── learnings.md Management ─────────────────────────────────────────────────

def load_learnings() -> dict:
    """Load learnings.md, parsing skill sections.

    Format:
    ## skill-name
    - [warning] Keep outputs under 500 words (2026-03-22)
    - [info] Users prefer bullet points over paragraphs (2026-03-22)
    """
    learnings = {}

    if not LEARNINGS_FILE.exists():
        return learnings

    current_skill = None
    for line in LEARNINGS_FILE.read_text().splitlines():
        line = line.strip()
        if line.startswith("## "):
            current_skill = line[3:].strip()
            learnings[current_skill] = []
        elif line.startswith("- ") and current_skill:
            learnings[current_skill].append(line[2:])

    return learnings


def save_learnings(learnings: dict):
    """Save learnings back to learnings.md."""
    lines = ["# Skill Learnings", "", "Auto-maintained by the self-correcting memory loop.", ""]

    for skill in sorted(learnings.keys()):
        lines.append(f"## {skill}")
        for item in learnings[skill]:
            lines.append(f"- {item}")
        lines.append("")

    LEARNINGS_FILE.write_text("\n".join(lines) + "\n")


def find_skill_md(skill_name: str) -> Path:
    """Find the SKILL.md file for a given skill name."""
    for skills_dir in SKILLS_DIRS:
        # Direct match
        candidate = skills_dir / skill_name / "SKILL.md"
        if candidate.exists():
            return candidate

        # Search subdirectories (for extended skills organized by category)
        for subdir in skills_dir.rglob(skill_name):
            skill_md = subdir / "SKILL.md"
            if skill_md.exists():
                return skill_md

    return None


# ─── Commands ─────────────────────────────────────────────────────────────────

def cmd_log(args):
    """Record a learning for a skill."""
    learnings = load_learnings()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    severity = args.severity or "info"
    entry = f"[{severity}] {args.learning} ({now})"

    if args.skill not in learnings:
        learnings[args.skill] = []

    # Avoid duplicates
    existing_texts = [l.split("] ", 1)[-1].rsplit(" (", 1)[0] for l in learnings[args.skill]]
    if args.learning in existing_texts:
        print(json.dumps({"status": "duplicate", "skill": args.skill}))
        return 0

    learnings[args.skill].append(entry)
    save_learnings(learnings)

    # Also track in context_mode SQLite if available
    ctx_script = PROJECT_DIR / "execution" / "context_mode.py"
    if ctx_script.exists():
        try:
            subprocess.run(
                ["python3", str(ctx_script), "learnings",
                 "--skill", args.skill, "--add", args.learning,
                 "--severity", severity],
                capture_output=True, text=True, timeout=5,
                cwd=str(PROJECT_DIR),
            )
        except Exception:
            pass

    print(json.dumps({"status": "logged", "skill": args.skill, "entry": entry}))
    return 0


def cmd_read(args):
    """Read learnings for a skill (pre-execution injection)."""
    learnings = load_learnings()
    skill_learnings = learnings.get(args.skill, [])

    if not skill_learnings:
        print(json.dumps({"skill": args.skill, "learnings": [], "count": 0}))
        return 1

    result = {
        "skill": args.skill,
        "learnings": skill_learnings,
        "count": len(skill_learnings),
        "injection": _format_injection(args.skill, skill_learnings),
    }
    print(json.dumps(result, indent=2))
    return 0


def cmd_apply(args):
    """Apply learnings to a skill's SKILL.md file."""
    learnings = load_learnings()
    skill_learnings = learnings.get(args.skill, [])

    if not skill_learnings:
        print(json.dumps({"status": "no_learnings", "skill": args.skill}))
        return 1

    skill_md = find_skill_md(args.skill)
    if not skill_md:
        print(json.dumps({"status": "skill_not_found", "skill": args.skill}))
        return 1

    # Read current SKILL.md
    content = skill_md.read_text()

    # Check if learnings section already exists
    learnings_header = "## Learnings"
    if learnings_header in content:
        # Replace existing learnings section
        before = content.split(learnings_header)[0]
        # Find next ## header after learnings
        after_parts = content.split(learnings_header)[1].split("\n## ")
        if len(after_parts) > 1:
            after = "\n## " + "\n## ".join(after_parts[1:])
        else:
            after = ""
        content = before + _build_learnings_section(skill_learnings) + after
    else:
        # Append learnings section before AGI-INTEGRATION block if present
        if "<!-- AGI-INTEGRATION-START -->" in content:
            parts = content.split("<!-- AGI-INTEGRATION-START -->")
            content = parts[0] + _build_learnings_section(skill_learnings) + "\n<!-- AGI-INTEGRATION-START -->" + parts[1]
        else:
            content = content.rstrip() + "\n\n" + _build_learnings_section(skill_learnings) + "\n"

    if args.dry_run:
        print(json.dumps({
            "status": "dry_run",
            "skill": args.skill,
            "skill_md": str(skill_md),
            "learnings_count": len(skill_learnings),
            "would_write": content[-500:],
        }, indent=2))
        return 0

    # Write updated SKILL.md
    skill_md.write_text(content)

    print(json.dumps({
        "status": "applied",
        "skill": args.skill,
        "skill_md": str(skill_md),
        "learnings_applied": len(skill_learnings),
    }))
    return 0


def cmd_list(args):
    """List all skills with learnings."""
    learnings = load_learnings()

    skills = []
    for skill, items in sorted(learnings.items()):
        warnings = sum(1 for i in items if "[warning]" in i)
        criticals = sum(1 for i in items if "[critical]" in i)
        skill_md = find_skill_md(skill)
        skills.append({
            "skill": skill,
            "total": len(items),
            "warnings": warnings,
            "criticals": criticals,
            "has_skill_md": skill_md is not None,
        })

    print(json.dumps({"skills": skills, "total_skills": len(skills)}, indent=2))
    return 0


def cmd_apply_all(args):
    """Apply learnings to all skills that have unapplied feedback."""
    learnings = load_learnings()
    results = []

    for skill in learnings:
        skill_md = find_skill_md(skill)
        if not skill_md:
            results.append({"skill": skill, "status": "skill_not_found"})
            continue

        args_obj = argparse.Namespace(skill=skill, dry_run=args.dry_run)
        status = cmd_apply(args_obj)
        results.append({"skill": skill, "status": "applied" if status == 0 else "failed"})

    print(json.dumps({"results": results, "total": len(results)}, indent=2))
    return 0


def cmd_sync(args):
    """Sync learnings to Qdrant for cross-session persistence."""
    learnings = load_learnings()
    if not learnings:
        print(json.dumps({"status": "empty"}))
        return 1

    memory_script = PROJECT_DIR / "execution" / "memory_manager.py"
    if not memory_script.exists():
        print(json.dumps({"status": "error", "message": "memory_manager.py not found"}))
        return 2

    # Build summary of all learnings
    summary_parts = []
    for skill, items in learnings.items():
        summary_parts.append(f"{skill}: {'; '.join(items[:3])}")
        if len(items) > 3:
            summary_parts[-1] += f" (+{len(items) - 3} more)"

    content = "Skill learnings: " + " | ".join(summary_parts[:20])

    try:
        proc = subprocess.run(
            [
                "python3", str(memory_script), "store",
                "--content", content,
                "--type", "decision",
                "--tags", "learnings,self-correcting,skill-feedback",
            ],
            capture_output=True, text=True, timeout=15,
            cwd=str(PROJECT_DIR),
        )
        if proc.returncode == 0:
            print(json.dumps({"status": "synced", "skills": len(learnings)}))
        else:
            print(json.dumps({"status": "error", "stderr": proc.stderr.strip()}))
            return 3
    except Exception as e:
        print(json.dumps({"status": "error", "message": str(e)}))
        return 3

    return 0


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _format_injection(skill: str, items: list) -> str:
    """Format learnings for pre-execution context injection."""
    lines = [f"[LEARNINGS for {skill}] Review before executing:"]
    for item in items:
        lines.append(f"  {item}")
    return "\n".join(lines)


def _build_learnings_section(items: list) -> str:
    """Build a Markdown learnings section."""
    lines = ["## Learnings", ""]
    lines.append("_Auto-maintained by the self-correcting memory loop. Do not edit manually._")
    lines.append("")
    for item in items:
        lines.append(f"- {item}")
    lines.append("")
    return "\n".join(lines)


# ─── CLI Entry Point ─────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Self-Correcting Memory Loop: learnings.md management"
    )
    sub = parser.add_subparsers(dest="command")

    # log
    p_log = sub.add_parser("log", help="Record a learning")
    p_log.add_argument("--skill", required=True, help="Skill name")
    p_log.add_argument("--learning", required=True, help="What was learned")
    p_log.add_argument("--severity", choices=["info", "warning", "critical"],
                       default="info", help="Severity level")

    # read
    p_read = sub.add_parser("read", help="Read learnings for a skill")
    p_read.add_argument("--skill", required=True, help="Skill name")

    # apply
    p_apply = sub.add_parser("apply", help="Apply learnings to SKILL.md")
    p_apply.add_argument("--skill", required=True, help="Skill name")
    p_apply.add_argument("--dry-run", action="store_true", help="Preview without writing")

    # list
    sub.add_parser("list", help="List all skills with learnings")

    # apply-all
    p_all = sub.add_parser("apply-all", help="Apply learnings to all skills")
    p_all.add_argument("--dry-run", action="store_true", help="Preview without writing")

    # sync
    sub.add_parser("sync", help="Sync learnings to Qdrant")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    commands = {
        "log": cmd_log,
        "read": cmd_read,
        "apply": cmd_apply,
        "list": cmd_list,
        "apply-all": cmd_apply_all,
        "sync": cmd_sync,
    }

    try:
        exit_code = commands[args.command](args)
        sys.exit(exit_code or 0)
    except Exception as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        sys.exit(3)


if __name__ == "__main__":
    main()
