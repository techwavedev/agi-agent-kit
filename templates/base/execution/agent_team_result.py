#!/usr/bin/env python3
"""
Script: agent_team_result.py
Purpose: Read and aggregate results from a completed agent team run.
         Queries Qdrant memory for each sub-agent's output and compiles
         an overall pass/fail report.

Usage:
    python3 execution/agent_team_result.py \\
        --team <team_id> \\
        [--run-id <run_id>]

Arguments:
    --team      Team ID to read results for (required)
    --run-id    Specific run ID to filter (optional, defaults to latest)
    --format    Output format: json | human (default: json)

Exit Codes:
    0 - All sub-agents passed
    1 - Invalid arguments
    2 - No results found for this team
    3 - One or more sub-agents failed
    4 - Memory query error
"""

import argparse
import json
import sys
import os
from pathlib import Path
from datetime import datetime, timezone


def find_project_root():
    """Walk up from CWD to find the project root."""
    current = Path.cwd()
    for parent in [current] + list(current.parents):
        if (parent / "AGENTS.md").exists() or (parent / "package.json").exists():
            return parent
    return current


def load_team_directive(root: Path, team_id: str) -> list:
    """Extract expected sub-agents from the team directive."""
    directive_path = root / "directives" / "teams" / f"{team_id}.md"
    if not directive_path.exists():
        return []

    subagents = []
    in_subagents_section = False
    for line in directive_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if "## Sub-Agents" in stripped:
            in_subagents_section = True
            continue
        if in_subagents_section:
            if stripped.startswith("## ") and "Sub-Agent" not in stripped:
                break
            if stripped.startswith("### ") and "`" in stripped:
                start = stripped.find("`") + 1
                end = stripped.find("`", start)
                if start > 0 and end > start:
                    subagents.append(stripped[start:end])
    return subagents


def query_memory_for_team(root: Path, team_id: str, run_id: str = None) -> list:
    """Query Qdrant memory for results tagged with this team."""
    memory_script = root / "execution" / "memory_manager.py"
    if not memory_script.exists():
        print(json.dumps({
            "warning": "memory_manager.py not found — cannot query results",
            "hint": "Run session_boot.py --auto-fix to set up memory"
        }))
        return []

    import subprocess
    query = f"{team_id} result"
    if run_id:
        query += f" {run_id}"

    result = subprocess.run(
        [sys.executable, str(memory_script), "auto", "--query", query],
        capture_output=True,
        text=True,
        cwd=str(root)
    )

    if result.returncode != 0:
        return []

    try:
        data = json.loads(result.stdout)
        chunks = data.get("context_chunks", [])
        return chunks
    except (json.JSONDecodeError, AttributeError):
        return []


def build_mock_results_from_tmp(root: Path, team_id: str, run_id: str = None) -> list:
    """
    Fallback: read agent result files from .tmp/agent_results/ if memory is unavailable.
    Files are written there by sub-agents that store their JSON output.
    """
    results_dir = root / ".tmp" / "agent_results" / team_id
    if not results_dir.exists():
        return []

    results = []
    for result_file in sorted(results_dir.glob("*.json")):
        try:
            data = json.loads(result_file.read_text(encoding="utf-8"))
            if run_id and data.get("run_id") != run_id:
                continue
            results.append(data)
        except (json.JSONDecodeError, IOError):
            pass
    return results


def compile_report(team_id: str, expected_subagents: list, raw_results: list, run_id: str = None) -> dict:
    """Compile aggregated report from sub-agent results."""
    sub_agent_map = {}

    # Try to parse structured results from memory chunks or result files
    for item in raw_results:
        if isinstance(item, dict):
            sa_id = item.get("sub_agent", item.get("id", "unknown"))
            sub_agent_map[sa_id] = item
        elif isinstance(item, str):
            # Memory chunk — try to parse embedded JSON
            try:
                start = item.find("{")
                if start >= 0:
                    parsed = json.loads(item[start:])
                    sa_id = parsed.get("sub_agent", "unknown")
                    sub_agent_map[sa_id] = parsed
            except json.JSONDecodeError:
                pass

    # Build per-sub-agent status
    sub_agent_statuses = {}
    overall_pass = True

    for sa_id in expected_subagents:
        if sa_id in sub_agent_map:
            result = sub_agent_map[sa_id]
            status = result.get("status", "unknown")
        else:
            status = "not_reported"

        sub_agent_statuses[sa_id.replace("-", "_")] = {
            "status": status,
            "details": sub_agent_map.get(sa_id, {})
        }

        if status not in ("pass", "skipped"):
            overall_pass = False

    return {
        "team": team_id,
        "run_id": run_id or "latest",
        "queried_at": datetime.now(timezone.utc).isoformat(),
        "expected_sub_agents": expected_subagents,
        "sub_agents": sub_agent_statuses,
        "results_found": len(raw_results),
        "overall_status": "pass" if overall_pass else "fail"
    }


def format_human(report: dict) -> str:
    """Human-readable summary of the team result."""
    lines = [
        f"\n{'='*50}",
        f" Team Report: {report['team']}",
        f" Run ID: {report['run_id']}",
        f"{'='*50}",
    ]

    for sa_name, data in report.get("sub_agents", {}).items():
        status = data.get("status", "?")
        icon = "✅" if status == "pass" else ("⏭️" if status == "skipped" else "❌")
        lines.append(f"  {icon}  {sa_name}: {status}")

    lines.append(f"\n  Overall: {'✅ PASS' if report['overall_status'] == 'pass' else '❌ FAIL'}")
    lines.append("")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--team", required=True, help="Team ID to get results for")
    parser.add_argument("--run-id", help="Specific run ID to query")
    parser.add_argument("--format", choices=["json", "human"], default="json", help="Output format")
    args = parser.parse_args()

    root = find_project_root()
    expected_subagents = load_team_directive(root, args.team)

    # Try memory first, fall back to .tmp files
    raw_results = query_memory_for_team(root, args.team, args.run_id)
    if not raw_results:
        raw_results = build_mock_results_from_tmp(root, args.team, args.run_id)

    report = compile_report(args.team, expected_subagents, raw_results, args.run_id)

    if args.format == "human":
        print(format_human(report))
    else:
        print(json.dumps(report, indent=2))

    sys.exit(0 if report["overall_status"] == "pass" else 3)


if __name__ == "__main__":
    main()
