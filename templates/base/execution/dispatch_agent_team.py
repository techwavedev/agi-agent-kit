#!/usr/bin/env python3
"""
Script: dispatch_agent_team.py
Purpose: Dispatch a named agent team by reading its directive and preparing
         a structured manifest of sub-agents to invoke, shared via Qdrant memory.
         Supports --parallel mode using git worktrees for agent isolation.

Usage:
    python3 execution/dispatch_agent_team.py \\
        --team <team_id> \\
        --payload '<json_string>'

    # Parallel mode: each sub-agent gets its own git worktree
    python3 execution/dispatch_agent_team.py \\
        --team <team_id> \\
        --payload '<json_string>' \\
        --parallel [--partitions '<json>']

Arguments:
    --team        Team ID matching a file in directives/teams/ (required)
    --payload     JSON string with task context (required)
    --parallel    Run sub-agents in parallel using git worktree isolation
    --partitions  JSON mapping agent IDs to file globs they'll modify (optional)
    --dry-run     Print the manifest without storing to memory (optional)
    --execute-native Run the manifest directly through agent_runtime.py
    --project     Project name for Qdrant tagging (default: agi-agent-kit)


Exit Codes:
    0 - Success, manifest printed to stdout
    1 - Invalid arguments
    2 - Team directive not found
    3 - Invalid payload JSON
    4 - Memory store error
    5 - Partition overlap detected (parallel mode)
"""

import argparse
import json
import subprocess
import sys
import uuid
import os
from pathlib import Path
from datetime import datetime, timezone

# Optional: import team_state helper; we import lazily so the rest of the
# script works even if the helper has a syntax error during development.
def _load_team_state():
    """Lazily import team_state so we can fall back gracefully."""
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "team_state",
            Path(__file__).parent / "team_state.py",
        )
        if spec is None or spec.loader is None:
            return None
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    except Exception:
        return None


# Add the script's directory to sys.path so we can import local modules
sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    from resolve_paths import resolve_file, get_project_root
except ImportError:
    # Minimal fallback for standalone use or tests
    def resolve_file(rel_path):
        return Path.cwd() / rel_path
    def get_project_root():
        return Path.cwd()


def load_team_directive(team_id: str) -> str:
    """Load the team directive markdown file using dual-path resolution (project first, then global)."""
    rel_path = os.path.join("directives", "teams", f"{team_id}.md")
    directive_path = resolve_file(rel_path)
    
    if not directive_path.exists():
        print(json.dumps({
            "status": "error",
            "message": f"Team directive not found: {directive_path}",
            "hint": f"Create {rel_path} or check the team ID"
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


def load_knowledge_context(root: Path, task_summary: str = "", project: str = "") -> dict:
    """
    Hybrid knowledge injection:
    1. Always loads knowledge/core.md (≤500 tokens baseline).
    2. Attempts to retrieve semantically relevant chunks from Qdrant (type=knowledge).
    3. Falls back to loading all knowledge/*.md files when Qdrant is unreachable.

    Returns a dict to be embedded in the manifest under 'knowledge_context'.
    """
    kb_dir = root / "knowledge"
    result: dict = {"source": "none", "core": None, "retrieved": [], "fallback_files": {}}

    # --- Layer 1: always-loaded core ---
    core_path = kb_dir / "core.md"
    if core_path.exists():
        result["core"] = core_path.read_text(encoding="utf-8")

    if not kb_dir.exists():
        result["source"] = "none"
        return result

    # --- Layer 2: Qdrant semantic retrieval ---
    memory_script = root / "execution" / "memory_manager.py"
    if task_summary and memory_script.exists():
        try:
            query_filters = ["--type", "knowledge"]
            if project:
                query_filters += ["--project", project]
            proc = subprocess.run(
                [
                    sys.executable, str(memory_script), "retrieve",
                    "--query", task_summary,
                    "--top-k", "3",
                    "--threshold", "0.45",
                ] + query_filters,
                capture_output=True,
                text=True,
                timeout=15,
                cwd=str(root),
            )
            if proc.returncode == 0:
                data = json.loads(proc.stdout)
                chunks = data.get("chunks", [])
                if chunks:
                    result["retrieved"] = chunks
                    result["source"] = "qdrant"
                    return result
        except Exception:
            pass  # Fall through to markdown fallback

    # --- Layer 3: markdown fallback (Qdrant unreachable or no results) ---
    fallback = {}
    for md_file in sorted(kb_dir.glob("*.md")):
        if md_file.name == "core.md":
            continue  # already loaded as core
        try:
            fallback[md_file.name] = md_file.read_text(encoding="utf-8")
        except Exception:
            pass

    if fallback:
        result["fallback_files"] = fallback
        result["source"] = "fallback_markdown"
    elif result["core"]:
        result["source"] = "core_only"

    return result


def parse_output_gate(directive_text: str) -> list:
    """
    Parse the optional `## Output Gate` section from a sub-agent directive.

    A sub-agent may declare files it MUST produce. Format:

        ## Output Gate

        - path/to/file_one.md
        - path/to/{{run_id}}/report.json

    Lines starting with `-` or `*` inside the section are collected as paths.
    Paths may contain `{{payload.key}}` or `{{run_id}}` placeholders which the
    dispatcher substitutes at manifest build time.

    Returns an ordered list of declared output file paths (possibly empty).
    """
    outputs = []
    in_section = False
    for line in directive_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("## "):
            in_section = stripped.lower().startswith("## output gate")
            continue
        if not in_section:
            continue
        if stripped.startswith("- ") or stripped.startswith("* "):
            path = stripped[2:].strip().strip("`")
            if path:
                outputs.append(path)
    return outputs


def substitute_gate_placeholders(path: str, payload: dict, run_id: str) -> str:
    """Resolve `{{run_id}}` and `{{payload.key}}` placeholders in a gate path."""
    resolved = path.replace("{{run_id}}", run_id)
    # Very small templating: {{payload.key}} with flat string keys only.
    while "{{payload." in resolved:
        start = resolved.find("{{payload.")
        end = resolved.find("}}", start)
        if end == -1:
            break
        key = resolved[start + len("{{payload.") : end]
        value = payload.get(key, "")
        if not isinstance(value, str):
            value = str(value)
        resolved = resolved[:start] + value + resolved[end + 2 :]
    return resolved


def build_validation_gate(output_files: list) -> dict:
    """
    Build a bash-gate spec for a list of required output files.

    Returns a dict with:
      - output_files: the resolved paths
      - command: a single bash command that prints VALIDATION:PASS or
                 VALIDATION:FAIL:<path> and exits non-zero on failure
      - on_fail: the three-option user prompt the orchestrator must present
                 after one retry

    The orchestrator reads the bash stdout (NOT its own memory) to decide
    whether to advance. Hallucination-proof by design — inspired by
    opensquad's pipeline bash gates.
    """
    if not output_files:
        return {}

    # Shell-quote each path safely by wrapping in double quotes and
    # escaping embedded double quotes. Paths are author-controlled in the
    # directive, so we keep this simple.
    quoted = [f'"{p.replace(chr(34), chr(92) + chr(34))}"' for p in output_files]
    # Each check either echoes PASS for that file or echoes FAIL and exits 1.
    clauses = " && ".join(
        f'(test -s {q} || {{ echo "VALIDATION:FAIL:{output_files[i]}"; exit 1; }})'
        for i, q in enumerate(quoted)
    )
    command = f"set -e; {clauses} && echo 'VALIDATION:PASS'"

    return {
        "output_files": output_files,
        "command": command,
        "on_fail": {
            "retry": "Re-invoke the sub-agent once with the same payload.",
            "escalate": (
                "If the second attempt still reports VALIDATION:FAIL, present "
                "the user with three options: (1) Retry step, (2) Skip step "
                "and continue, (3) Abort team run. Wait for user choice."
            ),
        },
    }


def load_subagent_directive(root: Path, subagent_id: str,
                            payload: "dict | None" = None, run_id: str = "") -> dict:
    """Load sub-agent directive if it exists; return metadata + validation gate."""
    # Normalize: doc-writer → doc_writer
    normalized = subagent_id.replace("-", "_")
    directive_path = root / "directives" / "subagents" / f"{normalized}.md"

    if directive_path.exists():
        text = directive_path.read_text(encoding="utf-8")
        raw_outputs = parse_output_gate(text)
        resolved = [
            substitute_gate_placeholders(p, payload or {}, run_id)
            for p in raw_outputs
        ]
        entry = {
            "id": subagent_id,
            "directive_path": str(directive_path.relative_to(root)),
            "directive_exists": True,
        }
        if resolved:
            entry["validation_gate"] = build_validation_gate(resolved)
        return entry
    else:
        return {
            "id": subagent_id,
            "directive_path": f"directives/subagents/{normalized}.md",
            "directive_exists": False,
            "warning": f"Directive not found — create {normalized}.md"
        }


def build_manifest(team_id: str, payload: dict, subagents: list, root: Path,
                   parallel=False, worktree_info=None):
    """Build the full dispatch manifest."""
    run_id = str(uuid.uuid4())[:8]
    execution_mode = "parallel-worktree" if parallel else "sequential"

    state_update_cmd = (
        f"python3 execution/team_state.py update --run-id {run_id} "
        f"--agent-id <AGENT_ID> --agent-status <STATUS>"
    )

    # Derive task summary and project for knowledge injection
    task_summary = payload.get("task", payload.get("commit_msg", team_id))
    project = payload.get("project", "")

    if parallel:
        instructions = (
            f"You are the Orchestrator. Each sub-agent has its own isolated git worktree. "
            f"Dispatch ALL sub-agents in parallel — they cannot conflict because each works "
            f"in a separate directory on a separate branch. "
            f"Pass the original payload JSON as context plus the worktree_path for each agent. "
            f"Each sub-agent MUST work ONLY within its assigned worktree directory. "
            f"BEFORE dispatching each sub-agent, mark it running: "
            f"`python3 execution/team_state.py update --run-id {run_id} "
            f"--status running --agent-id <ID> --agent-status running`. "
            f"AFTER each sub-agent reports done, if it carries a 'validation_gate', you MUST "
            f"execute `validation_gate.command` via Bash IN ITS WORKTREE PATH and parse stdout. "
            f"Only a literal 'VALIDATION:PASS' line authorizes the merge of that sub-agent's branch. "
            f"On 'VALIDATION:FAIL:<path>', follow validation_gate.on_fail (retry once, then user prompt). "
            f"On sub-agent completion run: "
            f"`python3 execution/team_state.py update --run-id {run_id} "
            f"--agent-id <ID> --agent-status completed`. "
            f"When ALL sub-agents complete, run: "
            f"`python3 execution/worktree_isolator.py merge-all --run-id {run_id}` "
            f"to merge all branches back sequentially. Then run: "
            f"`python3 execution/worktree_isolator.py status --run-id {run_id}` to verify. "
            f"Finally, cleanup with: "
            f"`python3 execution/worktree_isolator.py merge-all --run-id {run_id}` followed by cleanup. "
            f"When the entire team run finishes mark it done: "
            f"`python3 execution/team_state.py update --run-id {run_id} --status completed`. "
            f"Store final results to memory with tag '{team_id}'."
        )
    else:
        instructions = (
            f"You are the Orchestrator. Invoke each sub-agent in order based on their specialized skills. "
            f"Pass the original payload JSON as context. "
            f"BEFORE invoking each sub-agent, update the run state: "
            f"`python3 execution/team_state.py update --run-id {run_id} "
            f"--status running --step <INDEX> --agent-id <ID> --agent-status running`. "
            f"AFTER each sub-agent returns, if its manifest entry carries a 'validation_gate', you MUST "
            f"execute `validation_gate.command` via the Bash tool and read the stdout. Do NOT rely on the "
            f"sub-agent's self-reported status. Only a literal 'VALIDATION:PASS' line authorizes advancing "
            f"to the next sub-agent. On 'VALIDATION:FAIL:<path>', follow validation_gate.on_fail: retry the "
            f"sub-agent once, then — on a second failure — present the three-option prompt (Retry / Skip / Abort) "
            f"and wait for user choice. Never fabricate a PASS. "
            f"After each sub-agent completes (pass or skip), mark it done: "
            f"`python3 execution/team_state.py update --run-id {run_id} "
            f"--agent-id <ID> --agent-status completed`. "
            f"If a sub-agent works on a divided task, it MUST return a 'handoff_state' object containing its "
            f"state, 'next_steps' for the following agent, and 'validation_requirements' for what must be tested. "
            f"Record the handoff in state.json: "
            f"`python3 execution/team_state.py update --run-id {run_id} "
            f"--handoff '<JSON_STRING>'`. "
            f"YOU MUST actively verify this plan, store the state as raw JSON to Qdrant memory via "
            f"`python3 execution/memory_manager.py store` tagged with '{run_id}' against conflicts, AND pass it "
            f"directly to the next sequential or testing sub-agent so they execute the required validation and "
            f"next steps precisely. "
            f"When the entire team run finishes mark it done: "
            f"`python3 execution/team_state.py update --run-id {run_id} --status completed`. "
            f"Store final results to memory with tag '{team_id}'."
        )

    state_file_path = f".tmp/team-runs/{run_id}/state.json"

    manifest = {
        "team": team_id,
        "run_id": run_id,
        "dispatched_at": datetime.now(timezone.utc).isoformat(),
        "payload": payload,
        "sub_agents": [load_subagent_directive(root, sa, payload, run_id) for sa in subagents],
        "execution_mode": execution_mode,
        "instructions": instructions,
        "state_file": state_file_path,
        "state_update_cmd": state_update_cmd,
        "memory_query": f"python3 execution/memory_manager.py auto --query \"{team_id} {payload.get('commit_msg', '')}\"",
        "memory_store": (
            f"python3 execution/memory_manager.py store "
            f"--content \"{team_id} dispatched run {run_id}\" "
            f"--type decision --tags {team_id} agent-team"
        ),
        "knowledge_context": load_knowledge_context(root, task_summary, project),
    }

    if parallel and worktree_info:
        manifest["worktree_isolation"] = worktree_info
        _attach_worktree_paths(manifest, worktree_info)

    return manifest


def _attach_worktree_paths(manifest, worktree_info):
    """Enrich sub-agent entries with their worktree paths."""
    wt_lookup = {}
    for wt_entry in worktree_info.get("agents", []):
        name = wt_entry.get("agent", "").replace("-", "_")
        wt_lookup[name] = wt_entry

    enriched = []
    for sa in manifest.get("sub_agents", []):
        agent_id = sa.get("id", "").replace("-", "_")
        entry = {**sa}
        if agent_id in wt_lookup:
            entry["worktree_path"] = wt_lookup[agent_id].get("worktree_path")
            entry["branch"] = wt_lookup[agent_id].get("branch")
        enriched.append(entry)
    manifest["sub_agents"] = enriched


def store_to_memory(root: Path, manifest: dict, dry_run: bool) -> bool:
    """Optionally store the dispatch event to Qdrant memory."""
    if dry_run:
        return True

    memory_script = root / "execution" / "memory_manager.py"
    if not memory_script.exists():
        print(json.dumps({
            "warning": "memory_manager.py not found — skipping memory store. Run session_boot.py first."
        }), file=sys.stderr)
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
        }), file=sys.stderr)
    return True


def emit_state_json(root: Path, manifest: dict, dry_run: bool) -> str:
    """
    Write the initial state.json for this run using team_state.py.

    Returns the path of the written file (relative to root), or an empty
    string if the write was skipped/failed.
    """
    if dry_run:
        return ""

    ts_mod = _load_team_state()
    if ts_mod is None:
        return ""

    run_id = manifest["run_id"]
    team = manifest["team"]
    sub_agents = manifest.get("sub_agents", [])
    payload = manifest.get("payload", {})

    try:
        ts_mod.write_initial_state(root, run_id, team, sub_agents, payload)
        return f".tmp/team-runs/{run_id}/state.json"
    except Exception as e:
        print(json.dumps({
            "warning": f"Could not write state.json: {e}"
        }), file=sys.stderr)
        return ""


def setup_parallel_worktrees(root, subagents, run_id=None):
    """Create worktrees for all sub-agents using worktree_isolator."""
    isolator = root / "execution" / "worktree_isolator.py"
    if not isolator.exists():
        print(json.dumps({
            "status": "error",
            "message": "worktree_isolator.py not found in execution/"
        }), file=sys.stderr)
        sys.exit(2)

    agent_names = json.dumps(subagents)
    cmd = [sys.executable, str(isolator), "create-all", "--agents", agent_names]
    if run_id:
        cmd.extend(["--run-id", run_id])

    result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(root))
    if result.returncode != 0:
        print(json.dumps({
            "status": "error",
            "message": f"Failed to create worktrees: {result.stderr.strip()}"
        }), file=sys.stderr)
        sys.exit(2)

    return json.loads(result.stdout)


def validate_partitions(root, partitions_json):
    """Validate file partitions don't overlap before parallel dispatch."""
    isolator = root / "execution" / "worktree_isolator.py"
    result = subprocess.run(
        [sys.executable, str(isolator), "validate-partitions",
         "--partitions", partitions_json],
        capture_output=True, text=True, cwd=str(root)
    )
    if result.returncode == 4:
        print(result.stdout)
        sys.exit(5)
    return result.returncode == 0


def main():
    parser = argparse.ArgumentParser(
        description="Dispatch agent teams (sequential or parallel with worktree isolation)"
    )
    parser.add_argument("--team", required=True, help="Team ID (matches directives/teams/<id>.md)")
    parser.add_argument("--payload", required=True, help="JSON payload string with task context")
    parser.add_argument("--parallel", action="store_true",
                        help="Run sub-agents in parallel using git worktree isolation")
    parser.add_argument("--partitions",
                        help="JSON mapping agent IDs to file globs (validates no overlap)")
    parser.add_argument("--dry-run", action="store_true", help="Print manifest without storing to memory")
    parser.add_argument("--execute-native", action="store_true",
                        help="Pass the generated manifest directly to agent_runtime.py")
    parser.add_argument("--project", default="agi-agent-kit",
                        help="Project name for Qdrant tagging")
    parser.add_argument("--local-route", action="store_true",
                        help="Pre-classify subtasks via task_router.py and tag local-eligible ones")
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

    root = get_project_root()
    directive_text = load_team_directive(args.team)
    subagents = extract_subagents(directive_text)

    if not subagents:
        print(json.dumps({
            "status": "warning",
            "message": f"No sub-agents found in directive for team '{args.team}'",
            "hint": "Check that the Sub-Agents section uses ### N. `name` format"
        }))

    worktree_info = None

    if args.parallel:
        # Validate partitions if provided
        if args.partitions:
            validate_partitions(root, args.partitions)

        # Create worktrees for all sub-agents
        worktree_info = setup_parallel_worktrees(root, subagents)

    # Pre-classify subtasks for local routing if requested
    if args.local_route:
        task_router = root / "execution" / "task_router.py"
        if task_router.exists():
            task_desc = payload.get("commit_msg", payload.get("task", ""))
            try:
                route_result = subprocess.run(
                    [sys.executable, str(task_router), "classify", "--task", task_desc],
                    capture_output=True, text=True, timeout=10, cwd=str(root)
                )
                if route_result.returncode == 0:
                    classification = json.loads(route_result.stdout)
                    payload["_routing"] = classification
                    if classification.get("route") == "local_required":
                        payload["_local_only"] = True
                        payload["_routing_reason"] = classification.get("reason", "")
            except Exception:
                pass

    manifest = build_manifest(args.team, payload, subagents, root,
                              parallel=args.parallel, worktree_info=worktree_info)
    store_to_memory(root, manifest, args.dry_run)

    # Emit per-run state.json for dashboard / cross-agent observability
    emitted_path = emit_state_json(root, manifest, args.dry_run)
    if emitted_path and not args.dry_run:
        manifest["state_file"] = emitted_path

    if args.execute_native:
        runtime_script = root / "execution" / "agent_runtime.py"
        if runtime_script.exists():
            import tempfile
            with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
                json.dump(manifest, f)
                tmp_path = f.name
            try:
                cmd = [sys.executable, str(runtime_script), "dispatch", "--manifest", tmp_path]
                result = subprocess.run(cmd, cwd=str(root))
                if result.returncode != 0:
                    print(json.dumps({
                        "warning": "agent_runtime.py error occurred",
                    }), file=sys.stderr)
            finally:
                os.unlink(tmp_path)
            sys.exit(0)
        else:
            print(json.dumps({
                "warning": "agent_runtime.py not found, outputting standard manifest"
            }), file=sys.stderr)


    print(json.dumps(manifest, indent=2))
    sys.exit(0)


if __name__ == "__main__":
    main()
