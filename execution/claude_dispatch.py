#!/usr/bin/env python3
"""
Script: claude_dispatch.py
Purpose: Translate standard dispatch manifests into Claude Code-native instructions.
         Supports native Agent tool calls (with worktree isolation), fallback to
         standard dispatch, and schedule mode for cloud task definitions.

Usage:
    # From a team ID + payload (generates manifest internally)
    python3 execution/claude_dispatch.py --team documentation_team \
        --payload '{"changed_files": ["execution/foo.py"], "commit_msg": "feat: add foo"}' \
        --mode native

    # From an existing manifest JSON file
    python3 execution/claude_dispatch.py --manifest .tmp/manifest.json --mode native

    # Schedule mode for cloud dispatch
    python3 execution/claude_dispatch.py --team qa_team \
        --payload '{"task": "nightly tests"}' --mode schedule

    # Health check
    python3 execution/claude_dispatch.py health

Arguments:
    --team        Team ID (matches directives/teams/<id>.md)
    --payload     JSON payload string with task context
    --manifest    Path to existing manifest JSON (alternative to --team/--payload)
    --mode        Output mode: native (default), fallback, schedule
    --cloud       Alias for --mode schedule
    --project     Project name for Qdrant tagging (default: agi-agent-kit)
    --dry-run     Output without storing to Qdrant memory

Exit Codes:
    0 - Success
    1 - Invalid arguments
    2 - Team directive or manifest not found
    3 - Invalid JSON
    4 - Processing error
    5 - Claude Code not detected (native mode only, non-fatal warning)
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import uuid
from pathlib import Path


def find_project_root():
    """Walk up from script location to find the project root."""
    current = Path(__file__).resolve().parent.parent
    for parent in [current] + list(current.parents):
        if (parent / "AGENTS.md").exists() or (parent / "package.json").exists():
            return parent
    return current


def detect_claude_code() -> dict:
    """Detect if running under Claude Code environment."""
    checks = {
        "CLAUDE_CODE": os.environ.get("CLAUDE_CODE") is not None,
        "CLAUDE_SESSION_ID": os.environ.get("CLAUDE_SESSION_ID") is not None,
        "cli_available": shutil.which("claude") is not None,
    }
    detected = any(checks.values())
    return {
        "detected": detected,
        "checks": checks,
        "session_id": os.environ.get("CLAUDE_SESSION_ID", ""),
    }


def load_manifest_from_file(path: str) -> dict:
    """Load an existing manifest from a JSON file."""
    p = Path(path)
    if not p.exists():
        print(json.dumps({
            "status": "error",
            "message": f"Manifest file not found: {path}"
        }), file=sys.stderr)
        sys.exit(2)
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(json.dumps({
            "status": "error",
            "message": f"Invalid manifest JSON: {e}"
        }), file=sys.stderr)
        sys.exit(3)


def generate_manifest(root: Path, team_id: str, payload: dict) -> dict:
    """Generate a manifest by calling dispatch_agent_team.py."""
    dispatch_script = root / "execution" / "dispatch_agent_team.py"
    if not dispatch_script.exists():
        print(json.dumps({
            "status": "error",
            "message": "dispatch_agent_team.py not found"
        }), file=sys.stderr)
        sys.exit(2)

    result = subprocess.run(
        [
            sys.executable, str(dispatch_script),
            "--team", team_id,
            "--payload", json.dumps(payload),
            "--dry-run"
        ],
        capture_output=True, text=True, cwd=str(root)
    )

    if result.returncode != 0:
        print(json.dumps({
            "status": "error",
            "message": f"Manifest generation failed (exit {result.returncode})",
            "stderr": result.stderr.strip()
        }), file=sys.stderr)
        sys.exit(result.returncode)

    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        print(json.dumps({
            "status": "error",
            "message": "dispatch_agent_team.py returned non-JSON output",
            "stdout": result.stdout[:500]
        }), file=sys.stderr)
        sys.exit(4)


def load_subagent_directive_content(root: Path, subagent_id: str) -> str:
    """Load the full text of a sub-agent's directive."""
    normalized = subagent_id.replace("-", "_")
    directive_path = root / "directives" / "subagents" / f"{normalized}.md"
    if directive_path.exists():
        return directive_path.read_text(encoding="utf-8")
    return f"[Directive not found: directives/subagents/{normalized}.md]"


def build_subagent_prompt(root: Path, subagent: dict, payload: dict,
                          run_id: str, team_id: str, project: str) -> str:
    """Build a complete prompt for a Claude Code Agent tool sub-agent."""
    sa_id = subagent.get("id", "unknown")
    directive_content = load_subagent_directive_content(root, sa_id)

    prompt_parts = [
        f"# Sub-Agent: {sa_id}",
        f"Team: {team_id} | Run: {run_id}",
        "",
        "## Your Directive",
        directive_content,
        "",
        "## Task Payload",
        "```json",
        json.dumps(payload, indent=2),
        "```",
        "",
        "## Memory Integration (MANDATORY)",
        f"Before starting, query memory for relevant context:",
        f"```bash",
        f'python3 execution/memory_manager.py auto --query "{team_id} {sa_id} {payload.get("commit_msg", payload.get("task", ""))}"',
        f"```",
        "",
        "After completing your work, store results:",
        "```bash",
        f'python3 execution/memory_manager.py store \\',
        f'  --content "[{sa_id}] Completed: <summary of what you did>" \\',
        f'  --type decision --project {project} \\',
        f'  --tags {team_id} {sa_id} {run_id}',
        "```",
        "",
        "## Cross-Agent Context (share with Gemma 4 and other LLMs)",
        "```bash",
        f'python3 execution/cross_agent_context.py store \\',
        f'  --agent "claude" \\',
        f'  --action "[{team_id}/{sa_id}] <summary of what you did>" \\',
        f'  --project {project} \\',
        f'  --tags claude-dispatch {team_id} {sa_id}',
        "```",
        "",
        "## Handoff Protocol",
        "When done, output a JSON object with:",
        '- `"status"`: "pass" or "fail"',
        '- `"handoff_state"`: { "state": {}, "next_steps": "", "validation_requirements": "" }',
        '- `"files_modified"`: list of files you changed',
    ]

    return "\n".join(prompt_parts)


def build_cloud_prompt(root: Path, subagent: dict, payload: dict,
                       run_id: str, team_id: str, project: str) -> str:
    """Build a self-contained prompt for cloud/schedule dispatch.

    Cloud tasks run in fresh clones with no local state, so the prompt
    must include session boot and Qdrant setup.
    """
    base = build_subagent_prompt(root, subagent, payload, run_id, team_id, project)

    cloud_preamble = "\n".join([
        "## Cloud Environment Setup (run first)",
        "This task runs in a fresh cloud clone. Initialize the environment:",
        "```bash",
        "python3 execution/session_boot.py --auto-fix",
        "```",
        "If Qdrant is not available, proceed without memory but note it in output.",
        "",
    ])

    return cloud_preamble + base


def transform_native(root: Path, manifest: dict, project: str) -> dict:
    """Transform a manifest into Claude Code Agent tool call instructions."""
    team_id = manifest.get("team", "unknown")
    run_id = manifest.get("run_id", str(uuid.uuid4())[:8])
    payload = manifest.get("payload", {})
    sub_agents = manifest.get("sub_agents", [])
    execution_mode = manifest.get("execution_mode", "sequential")
    is_parallel = execution_mode == "parallel-worktree"

    agent_calls = []
    for sa in sub_agents:
        sa_id = sa.get("id", "unknown")
        prompt = build_subagent_prompt(root, sa, payload, run_id, team_id, project)

        call = {
            "agent_id": sa_id,
            "prompt": prompt,
            "subagent_type": "general-purpose",
        }

        if is_parallel:
            call["isolation"] = "worktree"
            if sa.get("worktree_path"):
                call["worktree_path"] = sa["worktree_path"]
                call["branch"] = sa.get("branch", "")

        agent_calls.append(call)

    orchestrator_instructions = manifest.get("instructions", "")
    if is_parallel:
        orchestrator_instructions += (
            "\n\nClaude Code Native: Use the Agent tool with `isolation: \"worktree\"` "
            "for each sub-agent call. All calls can be dispatched in parallel."
        )
    else:
        orchestrator_instructions += (
            "\n\nClaude Code Native: Use the Agent tool for each sub-agent call "
            "in sequence. Pass handoff_state from one agent to the next."
        )

    return {
        "status": "success",
        "mode": "native",
        "claude_code_detected": detect_claude_code()["detected"],
        "team": team_id,
        "run_id": run_id,
        "execution_mode": execution_mode,
        "orchestrator_instructions": orchestrator_instructions,
        "agent_calls": agent_calls,
        "post_dispatch": {
            "memory_store": (
                f'python3 execution/memory_manager.py store '
                f'--content "{team_id} native dispatch run {run_id} completed" '
                f'--type decision --project {project} '
                f'--tags claude-dispatch native-dispatch {team_id}'
            ),
            "cross_agent_broadcast": (
                f'python3 execution/cross_agent_context.py store '
                f'--agent "claude" '
                f'--action "[claude-dispatch] {team_id} run {run_id} completed" '
                f'--project {project} '
                f'--tags claude-dispatch native-dispatch {team_id}'
            ),
        },
    }


def transform_schedule(root: Path, manifest: dict, project: str) -> dict:
    """Transform a manifest into /schedule compatible task definitions."""
    team_id = manifest.get("team", "unknown")
    run_id = manifest.get("run_id", str(uuid.uuid4())[:8])
    payload = manifest.get("payload", {})
    sub_agents = manifest.get("sub_agents", [])

    # For schedule mode, produce a single self-contained task prompt
    # that orchestrates all sub-agents sequentially in the cloud
    all_prompts = []
    for i, sa in enumerate(sub_agents, 1):
        sa_id = sa.get("id", "unknown")
        prompt = build_cloud_prompt(root, sa, payload, run_id, team_id, project)
        all_prompts.append(f"## Step {i}: {sa_id}\n\n{prompt}")

    combined_prompt = "\n\n---\n\n".join(all_prompts)
    full_prompt = (
        f"# Scheduled Team Dispatch: {team_id}\n"
        f"Run ID: {run_id}\n\n"
        f"Execute each step in order. If a step fails, log the failure and continue.\n\n"
        f"{combined_prompt}\n\n"
        f"## Post-Completion\n"
        f"Store results to Qdrant:\n"
        f"```bash\n"
        f'python3 execution/cross_agent_context.py store \\\n'
        f'  --agent "claude" \\\n'
        f'  --action "[scheduled] {team_id} run {run_id} completed" \\\n'
        f'  --project {project} \\\n'
        f'  --tags claude-dispatch scheduled-dispatch {team_id}\n'
        f"```\n"
    )

    return {
        "status": "success",
        "mode": "schedule",
        "team": team_id,
        "run_id": run_id,
        "schedule_task": {
            "name": f"{team_id}-{run_id}",
            "prompt": full_prompt,
            "project": project,
        },
    }


def transform_fallback(manifest: dict) -> dict:
    """Fallback mode: return the standard manifest as-is."""
    return {
        "status": "success",
        "mode": "fallback",
        "team": manifest.get("team", "unknown"),
        "run_id": manifest.get("run_id", ""),
        "manifest": manifest,
        "hint": "Use dispatch_agent_team.py directly for non-Claude orchestrators.",
    }


def store_dispatch_event(root: Path, team_id: str, run_id: str,
                         mode: str, project: str, dry_run: bool):
    """Store the dispatch event to Qdrant memory."""
    if dry_run:
        return

    memory_script = root / "execution" / "memory_manager.py"
    if not memory_script.exists():
        return

    subprocess.run(
        [
            sys.executable, str(memory_script), "store",
            "--content", f"Claude dispatch: {team_id} run {run_id} mode={mode}",
            "--type", "decision",
            "--project", project,
            "--tags", "claude-dispatch", "native-dispatch", team_id,
        ],
        capture_output=True, text=True, cwd=str(root)
    )


def run_health(root: Path) -> dict:
    """Health check: Claude Code detection, Qdrant, team directives."""
    claude_info = detect_claude_code()

    # Check Qdrant
    qdrant_ok = False
    try:
        from urllib.request import urlopen
        qdrant_url = os.environ.get("QDRANT_URL", "http://localhost:6333")
        resp = urlopen(f"{qdrant_url}/collections", timeout=3)
        qdrant_ok = resp.status == 200
    except Exception:
        pass

    # Check team directives
    teams_dir = root / "directives" / "teams"
    teams_found = []
    if teams_dir.exists():
        teams_found = [f.stem for f in teams_dir.glob("*.md")]

    # Check dispatch_agent_team.py
    dispatch_exists = (root / "execution" / "dispatch_agent_team.py").exists()

    all_ok = claude_info["detected"] and qdrant_ok and dispatch_exists and len(teams_found) > 0

    return {
        "status": "healthy" if all_ok else "degraded",
        "claude_code": claude_info,
        "qdrant_available": qdrant_ok,
        "dispatch_script_exists": dispatch_exists,
        "teams_found": teams_found,
        "teams_count": len(teams_found),
    }


def main():
    parser = argparse.ArgumentParser(
        description="Claude Code-native dispatch adapter for agent teams"
    )
    subparsers = parser.add_subparsers(dest="command")

    # Health subcommand
    subparsers.add_parser("health", help="Check Claude Code, Qdrant, teams")

    # Default dispatch (no subcommand)
    parser.add_argument("--team", help="Team ID (matches directives/teams/<id>.md)")
    parser.add_argument("--payload", help="JSON payload string")
    parser.add_argument("--manifest", help="Path to existing manifest JSON file")
    parser.add_argument("--mode", choices=["native", "fallback", "schedule"],
                        default="native", help="Output mode (default: native)")
    parser.add_argument("--cloud", action="store_true",
                        help="Alias for --mode schedule")
    parser.add_argument("--project", default="agi-agent-kit",
                        help="Project name for Qdrant tagging")
    parser.add_argument("--dry-run", action="store_true",
                        help="Output without storing to Qdrant")

    args = parser.parse_args()
    root = find_project_root()

    # Health subcommand
    if args.command == "health":
        result = run_health(root)
        print(json.dumps(result, indent=2))
        sys.exit(0 if result["status"] == "healthy" else 1)

    # Determine mode
    mode = args.mode
    if args.cloud:
        mode = "schedule"

    # Get or generate manifest
    if args.manifest:
        manifest = load_manifest_from_file(args.manifest)
    elif args.team and args.payload:
        try:
            payload = json.loads(args.payload)
        except json.JSONDecodeError as e:
            print(json.dumps({
                "status": "error",
                "message": f"Invalid JSON payload: {e}"
            }), file=sys.stderr)
            sys.exit(3)
        manifest = generate_manifest(root, args.team, payload)
    else:
        parser.error("Either --manifest or both --team and --payload are required")

    # Warn if native mode and Claude Code not detected
    if mode == "native":
        claude_info = detect_claude_code()
        if not claude_info["detected"]:
            print(json.dumps({
                "warning": "Claude Code not detected. Native output generated but may not work outside Claude Code.",
                "detection": claude_info["checks"]
            }), file=sys.stderr)

    # Transform based on mode
    if mode == "native":
        output = transform_native(root, manifest, args.project)
    elif mode == "schedule":
        output = transform_schedule(root, manifest, args.project)
    else:
        output = transform_fallback(manifest)

    # Store dispatch event
    store_dispatch_event(
        root, manifest.get("team", "unknown"),
        manifest.get("run_id", ""), mode, args.project,
        args.dry_run
    )

    print(json.dumps(output, indent=2))
    sys.exit(0)


if __name__ == "__main__":
    main()
