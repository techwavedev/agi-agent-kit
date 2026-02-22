#!/usr/bin/env python3
"""
Script: dispatch_agent_team.py
Purpose: Dispatch a named agent team by reading its directive and preparing
         a structured manifest of sub-agents to invoke, shared via Qdrant memory.

Usage:
    python3 execution/dispatch_agent_team.py \\
        --team <team_id> \\
        --payload '<json_string>'

Arguments:
    --team      Team ID matching a file in directives/teams/ (required)
    --payload   JSON string with task context (required)
    --dry-run   Print the manifest without storing to memory (optional)

Exit Codes:
    0 - Success, manifest printed to stdout
    1 - Invalid arguments
    2 - Team directive not found
    3 - Invalid payload JSON
    4 - Memory store error
"""

import argparse
import json
import sys
import uuid
import os
from pathlib import Path
from datetime import datetime, timezone


def find_project_root():
    """Walk up from CWD to find the project root (has AGENTS.md or package.json)."""
    current = Path.cwd()
    for parent in [current] + list(current.parents):
        if (parent / "AGENTS.md").exists() or (parent / "package.json").exists():
            return parent
    return current


def load_team_directive(root: Path, team_id: str) -> str:
    """Load the team directive markdown file."""
    directive_path = root / "directives" / "teams" / f"{team_id}.md"
    if not directive_path.exists():
        print(json.dumps({
            "status": "error",
            "message": f"Team directive not found: {directive_path}",
            "hint": f"Create directives/teams/{team_id}.md or check the team ID"
        }), file=sys.stderr)
        sys.exit(2)
    return directive_path.read_text(encoding="utf-8")


def extract_subagents(directive_text: str) -> list:
    """
    Parse sub-agent names from the directive's 'Sub-Agents' section.
    Returns ordered list of sub-agent IDs.
    """
    subagents = []
    in_subagents_section = False

    for line in directive_text.splitlines():
        stripped = line.strip()
        if "## Sub-Agents" in stripped:
            in_subagents_section = True
            continue
        if in_subagents_section:
            # Stop at next ## section
            if stripped.startswith("## ") and "Sub-Agent" not in stripped:
                break
            # Match lines like: ### 1. `doc-writer`
            if stripped.startswith("### ") and "`" in stripped:
                start = stripped.find("`") + 1
                end = stripped.find("`", start)
                if start > 0 and end > start:
                    subagents.append(stripped[start:end])

    return subagents


def load_subagent_directive(root: Path, subagent_id: str) -> dict:
    """Load sub-agent directive if it exists; return metadata."""
    # Normalize: doc-writer → doc_writer
    normalized = subagent_id.replace("-", "_")
    directive_path = root / "directives" / "subagents" / f"{normalized}.md"

    if directive_path.exists():
        return {
            "id": subagent_id,
            "directive_path": str(directive_path.relative_to(root)),
            "directive_exists": True
        }
    else:
        return {
            "id": subagent_id,
            "directive_path": f"directives/subagents/{normalized}.md",
            "directive_exists": False,
            "warning": f"Directive not found — create {normalized}.md"
        }


def build_manifest(team_id: str, payload: dict, subagents: list, root: Path) -> dict:
    """Build the full dispatch manifest."""
    run_id = str(uuid.uuid4())[:8]
    return {
        "team": team_id,
        "run_id": run_id,
        "dispatched_at": datetime.now(timezone.utc).isoformat(),
        "payload": payload,
        "sub_agents": [load_subagent_directive(root, sa) for sa in subagents],
        "execution_mode": "sequential",
        "instructions": (
            f"Invoke each sub-agent in order. Read their directive before invoking. "
            f"Pass the original payload JSON as context. If a sub-agent returns a 'handoff_state' "
            f"object, store it as raw JSON or optimized machine-readable format to Qdrant memory "
            f"via `python3 execution/memory_manager.py store` tagged with '{run_id}' so parallel/remote "
            f"agents can access it cleanly, AND pass it to the next sequential sub-agent. "
            f"Store final results to memory with tag '{team_id}'."
        ),
        "memory_query": f"python3 execution/memory_manager.py auto --query \"{team_id} {payload.get('commit_msg', '')}\"",
        "memory_store": (
            f"python3 execution/memory_manager.py store "
            f"--content \"{team_id} dispatched run {run_id}\" "
            f"--type decision --tags {team_id} agent-team"
        )
    }


def store_to_memory(root: Path, manifest: dict, dry_run: bool) -> bool:
    """Optionally store the dispatch event to Qdrant memory."""
    if dry_run:
        return True

    memory_script = root / "execution" / "memory_manager.py"
    if not memory_script.exists():
        print(json.dumps({
            "warning": "memory_manager.py not found — skipping memory store. Run session_boot.py first."
        }))
        return True

    import subprocess
    result = subprocess.run(
        [
            sys.executable, str(memory_script), "store",
            "--content", f"Agent team dispatched: {manifest['team']} run {manifest['run_id']}",
            "--type", "decision",
            "--tags", manifest["team"], "agent-team-dispatch"
        ],
        capture_output=True,
        text=True,
        cwd=str(root)
    )

    if result.returncode != 0:
        print(json.dumps({
            "warning": "Memory store failed — continuing anyway",
            "detail": result.stderr
        }))
    return True


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--team", required=True, help="Team ID (matches directives/teams/<id>.md)")
    parser.add_argument("--payload", required=True, help="JSON payload string with task context")
    parser.add_argument("--dry-run", action="store_true", help="Print manifest without storing to memory")
    args = parser.parse_args()

    # Parse payload
    try:
        payload = json.loads(args.payload)
    except json.JSONDecodeError as e:
        print(json.dumps({
            "status": "error",
            "message": f"Invalid JSON payload: {e}",
            "hint": "Wrap payload in single quotes and use double quotes inside"
        }), file=sys.stderr)
        sys.exit(3)

    root = find_project_root()
    directive_text = load_team_directive(root, args.team)
    subagents = extract_subagents(directive_text)

    if not subagents:
        print(json.dumps({
            "status": "warning",
            "message": f"No sub-agents found in directive for team '{args.team}'",
            "hint": "Check that the Sub-Agents section uses ### N. `name` format"
        }))

    manifest = build_manifest(args.team, payload, subagents, root)
    store_to_memory(root, manifest, args.dry_run)

    print(json.dumps(manifest, indent=2))
    sys.exit(0)


if __name__ == "__main__":
    main()
