#!/usr/bin/env python3
"""
Script: run_test_scenario.py
Purpose: Run one or all test scenarios that validate sub-agent and team agent
         (including output gate validation)
         functionality in the AGI framework.

Usage:
    # Run a single scenario
    python3 execution/run_test_scenario.py --scenario 1

    # Run all scenarios
    python3 execution/run_test_scenario.py --all

    # Run with verbose output
    python3 execution/run_test_scenario.py --all --verbose

Arguments:
    --scenario  Scenario number to run (1-11)
    --all       Run all scenarios
    --verbose   Show detailed output for each step
    --dry-run   Validate setup without dispatching agents

Exit Codes:
    0 - All selected scenarios passed
    1 - Invalid arguments
    2 - Setup validation failed
    3 - One or more scenarios failed
"""

import argparse
import json
import sys
import subprocess
import time
from pathlib import Path
from datetime import datetime, timezone


def find_project_root():
    current = Path.cwd()
    for parent in [current] + list(current.parents):
        if (parent / "AGENTS.md").exists() or (parent / "package.json").exists():
            return parent
    return current


def run_script(root: Path, script: str, args: list, verbose: bool = False) -> dict:
    """Run an execution script and return parsed JSON output."""
    cmd = [sys.executable, str(root / "execution" / script)] + args
    start = time.time()

    result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(root))
    elapsed = round(time.time() - start, 2)

    if verbose:
        print(f"    $ {' '.join(cmd[1:])}")
        if result.stdout:
            print(f"    stdout: {result.stdout[:300]}")

    try:
        output = json.loads(result.stdout) if result.stdout.strip() else {}
    except json.JSONDecodeError:
        output = {"raw": result.stdout[:200]}

    return {
        "exit_code": result.returncode,
        "elapsed_s": elapsed,
        "output": output,
        "stderr": result.stderr[:200] if result.stderr else ""
    }


def validate_setup(root: Path) -> dict:
    """Check that required scripts and directives exist."""
    checks = {}

    # Execution scripts
    for script in ["dispatch_agent_team.py", "agent_team_result.py"]:
        path = root / "execution" / script
        checks[f"script:{script}"] = path.exists()

    # Team directives
    for team in ["documentation_team", "code_review_team", "qa_team", "build_deploy_team"]:
        path = root / "directives" / "teams" / f"{team}.md"
        checks[f"team:{team}"] = path.exists()

    # Sub-agent directives
    for sa in ["doc_writer", "doc_reviewer", "changelog_updater", "spec_reviewer",
              "quality_reviewer", "asset_compiler", "cloud_deployer",
              "secret_scanner", "dependency_auditor", "code_security_reviewer",
              "test_generator", "test_verifier"]:
        path = root / "directives" / "subagents" / f"{sa}.md"
        checks[f"subagent:{sa}"] = path.exists()

    all_pass = all(checks.values())
    return {"pass": all_pass, "checks": checks}


# ─── SCENARIOS ────────────────────────────────────────────────────────────────

def scenario_1_single_subagent(root: Path, verbose: bool, dry_run: bool) -> dict:
    """
    Scenario 1: Single sub-agent with two-stage review
    Pattern: subagent-driven-development
    Validates: dispatch → spec-reviewer → quality-reviewer sequential flow
    """
    scenario_id = "scenario_01_single_subagent"
    steps = []

    # Step 1: dispatch code_review_team for a simulated task
    payload = json.dumps({
        "task_spec": "Add --dry-run flag to dispatch_agent_team.py that prints manifest without storing to memory",
        "changed_files": ["execution/dispatch_agent_team.py"],
        "git_shas": ["abc1234"],
        "task_id": "test-task-001"
    })

    dispatch_args = ["--team", "code_review_team", "--payload", payload]
    if dry_run:
        dispatch_args.append("--dry-run")

    result = run_script(root, "dispatch_agent_team.py", dispatch_args, verbose)
    steps.append({"step": "dispatch code_review_team", **result})

    manifest = result["output"]
    subagents_found = len(manifest.get("sub_agents", []))

    # Step 2: validate manifest structure
    manifest_valid = (
        "team" in manifest and
        "run_id" in manifest and
        "sub_agents" in manifest and
        subagents_found >= 2
    )

    steps.append({
        "step": "validate manifest",
        "pass": manifest_valid,
        "sub_agents_found": subagents_found,
        "expected": 2
    })

    passed = result["exit_code"] == 0 and manifest_valid
    return {
        "scenario": scenario_id,
        "pattern": "subagent-driven-development",
        "status": "pass" if passed else "fail",
        "steps": steps
    }


def scenario_2_parallel_subagents(root: Path, verbose: bool, dry_run: bool) -> dict:
    """
    Scenario 2: Parallel sub-agents on independent domains
    Pattern: dispatching-parallel-agents
    Validates: two documentation_team dispatches on different payloads (independent domains)
    """
    scenario_id = "scenario_02_parallel_subagents"
    steps = []

    dispatch_args_list = [
        ["--team", "documentation_team", "--payload",
            json.dumps({"changed_files": ["execution/session_boot.py"], "commit_msg": "feat: add auto-fix flag", "change_type": "feat"})],
        ["--team", "documentation_team", "--payload",
            json.dumps({"changed_files": ["execution/memory_manager.py"], "commit_msg": "fix: handle empty result", "change_type": "fix"})],
    ]

    for i, dispatch_args in enumerate(dispatch_args_list, 1):
        if dry_run:
            dispatch_args.append("--dry-run")
        result = run_script(root, "dispatch_agent_team.py", dispatch_args, verbose)
        steps.append({"step": f"dispatch domain_{i}", **result})

    all_pass = all(s.get("exit_code") == 0 for s in steps)
    manifests_valid = all(
        "run_id" in s.get("output", {}) for s in steps
    )
    run_ids = [s.get("output", {}).get("run_id") for s in steps]
    ids_unique = len(set(run_ids)) == len(run_ids)

    steps.append({
        "step": "validate parallel dispatches",
        "run_ids_unique": ids_unique,
        "run_ids": run_ids
    })

    passed = all_pass and manifests_valid and ids_unique
    return {
        "scenario": scenario_id,
        "pattern": "dispatching-parallel-agents",
        "status": "pass" if passed else "fail",
        "steps": steps
    }


def scenario_3_doc_team_on_code(root: Path, verbose: bool, dry_run: bool) -> dict:
    """
    Scenario 3: Documentation team triggered by a code change (the key pattern)
    Pattern: doc-team-on-code
    Validates: code change → documentation_team dispatched → manifest contains all 3 sub-agents
    """
    scenario_id = "scenario_03_doc_team_on_code"
    steps = []

    payload = json.dumps({
        "changed_files": ["execution/dispatch_agent_team.py", "execution/agent_team_result.py"],
        "commit_msg": "feat: add agent team dispatch and result scripts",
        "change_type": "feat"
    })

    dispatch_args = ["--team", "documentation_team", "--payload", payload]
    if dry_run:
        dispatch_args.append("--dry-run")

    result = run_script(root, "dispatch_agent_team.py", dispatch_args, verbose)
    steps.append({"step": "trigger documentation_team on code change", **result})

    manifest = result["output"]
    sub_agents = manifest.get("sub_agents", [])
    sub_agent_ids = [sa.get("id") for sa in sub_agents]

    expected = ["doc-writer", "doc-reviewer", "changelog-updater"]
    agents_present = all(ea in sub_agent_ids for ea in expected)

    steps.append({
        "step": "validate team has all 3 documentation sub-agents",
        "expected": expected,
        "found": sub_agent_ids,
        "pass": agents_present
    })

    # Validate directives exist for each sub-agent
    directives_valid = all(sa.get("directive_exists", False) for sa in sub_agents)
    steps.append({
        "step": "validate all sub-agent directives exist",
        "pass": directives_valid,
        "details": [{"id": sa["id"], "exists": sa.get("directive_exists")} for sa in sub_agents]
    })

    passed = result["exit_code"] == 0 and agents_present and directives_valid
    return {
        "scenario": scenario_id,
        "pattern": "doc-team-on-code",
        "status": "pass" if passed else "fail",
        "steps": steps
    }


def scenario_4_full_pipeline(root: Path, verbose: bool, dry_run: bool) -> dict:
    """
    Scenario 4: Full team agent pipeline
    Pattern: code-change → code_review_team → documentation_team → qa_team
    Validates: all 3 teams can be dispatched sequentially with linked context
    """
    scenario_id = "scenario_04_full_pipeline"
    steps = []

    payload_base = {
        "changed_files": ["execution/run_test_scenario.py"],
        "commit_msg": "feat: add full agent team test runner",
        "change_type": "feat",
        "task_spec": "Create run_test_scenario.py that runs all 5 agent test scenarios and reports results"
    }

    pipeline = [
        ("code_review_team", {**payload_base, "git_shas": ["def5678"], "task_id": "test-task-004"}),
        ("documentation_team", {**payload_base}),
        ("qa_team", {**payload_base, "test_runner": "pytest"}),
    ]

    run_ids = []
    for team_id, team_payload in pipeline:
        dispatch_args = ["--team", team_id, "--payload", json.dumps(team_payload)]
        if dry_run:
            dispatch_args.append("--dry-run")

        result = run_script(root, "dispatch_agent_team.py", dispatch_args, verbose)
        run_id = result["output"].get("run_id", "missing")
        run_ids.append(run_id)
        steps.append({
            "step": f"dispatch {team_id}",
            "run_id": run_id,
            **result
        })

    all_pass = all(s.get("exit_code") == 0 for s in steps)
    steps.append({
        "step": "validate full pipeline completed",
        "teams_dispatched": [t for t, _ in pipeline],
        "all_passed": all_pass,
        "run_ids": run_ids
    })

    passed = all_pass
    return {
        "scenario": scenario_id,
        "pattern": "full-team-pipeline",
        "status": "pass" if passed else "fail",
        "steps": steps
    }


def scenario_5_failure_recovery(root: Path, verbose: bool, dry_run: bool) -> dict:
    """
    Scenario 5: Failure recovery — invalid team triggers graceful error
    Pattern: failure-recovery
    Validates: framework handles bad team ID gracefully, returns structured error
    """
    scenario_id = "scenario_05_failure_recovery"
    steps = []

    # Step 1: dispatch a nonexistent team — should fail with exit code 2
    bad_dispatch = run_script(
        root, "dispatch_agent_team.py",
        ["--team", "nonexistent_team_xyz", "--payload", '{"changed_files": []}'],
        verbose
    )
    steps.append({
        "step": "dispatch invalid team (expect fail)",
        "expected_exit_code": 2,
        "actual_exit_code": bad_dispatch["exit_code"],
        "pass": bad_dispatch["exit_code"] == 2
    })

    # Step 2: dispatch with invalid JSON payload — should fail with exit code 3
    bad_payload = run_script(
        root, "dispatch_agent_team.py",
        ["--team", "documentation_team", "--payload", "{invalid json"],
        verbose
    )
    steps.append({
        "step": "dispatch invalid payload JSON (expect exit 3)",
        "expected_exit_code": 3,
        "actual_exit_code": bad_payload["exit_code"],
        "pass": bad_payload["exit_code"] == 3
    })

    # Step 3: after failure, re-dispatch valid request — should recover
    valid_payload = json.dumps({"changed_files": ["README.md"], "commit_msg": "fix: typo", "change_type": "fix"})
    dispatch_args = ["--team", "documentation_team", "--payload", valid_payload]
    if dry_run:
        dispatch_args.append("--dry-run")

    recovery_dispatch = run_script(root, "dispatch_agent_team.py", dispatch_args, verbose)
    steps.append({
        "step": "recovery: re-dispatch valid request (expect pass)",
        "expected_exit_code": 0,
        "actual_exit_code": recovery_dispatch["exit_code"],
        "pass": recovery_dispatch["exit_code"] == 0
    })

    passed = all(s.get("pass", False) for s in steps)
    return {
        "scenario": scenario_id,
        "pattern": "failure-recovery",
        "status": "pass" if passed else "fail",
        "steps": steps
    }


def scenario_6_dynamic_handoff(root: Path, verbose: bool, dry_run: bool) -> dict:
    """
    Scenario 6: Dynamic State Handoff
    Pattern: state-handoff
    Validates: build_deploy_team dispatch correctly instructs orchestrator to use Qdrant for handoff_state.
    """
    scenario_id = "scenario_06_state_handoff"
    steps = []

    payload = json.dumps({
        "target_branch": "main",
        "commit_sha": "fff9999",
        "task_spec": "Compile production assets and deploy them.",
        "task_id": "test-task-006"
    })

    dispatch_args = ["--team", "build_deploy_team", "--payload", payload]
    if dry_run:
        dispatch_args.append("--dry-run")

    result = run_script(root, "dispatch_agent_team.py", dispatch_args, verbose)
    steps.append({"step": "dispatch build_deploy_team", **result})

    manifest = result["output"]
    sub_agents = manifest.get("sub_agents", [])
    sub_agent_ids = [sa.get("id") for sa in sub_agents]

    expected = ["asset-compiler", "cloud-deployer"]
    agents_present = all(ea in sub_agent_ids for ea in expected)

    steps.append({
        "step": "validate team has compiler and deployer",
        "expected": expected,
        "found": sub_agent_ids,
        "pass": agents_present
    })

    # Validate the manifest actually references Qdrant / handoff_state
    instructions = manifest.get("instructions", "")
    handoff_supported = "handoff_state" in instructions and "Qdrant memory" in instructions
    
    steps.append({
        "step": "validate Qdrant handoff instructions present",
        "pass": handoff_supported
    })

    passed = result["exit_code"] == 0 and agents_present and handoff_supported
    return {
        "scenario": scenario_id,
        "pattern": "state-handoff",
        "status": "pass" if passed else "fail",
        "steps": steps
    }


def scenario_11_output_gates(root: Path, verbose: bool, dry_run: bool) -> dict:
    """
    Scenario 11: Output Gates
    Pattern: output-gate
    Validates: Sub-agents with ## Output Gate sections emit validation_gate entries
               in the dispatch manifest with executable bash commands.
    """
    scenario_id = "scenario_11_output_gates"
    steps = []

    # Step 1: Dispatch documentation_team (changelog-updater declares a gate)
    payload = json.dumps({
        "changed_files": ["execution/dispatch_agent_team.py"],
        "commit_msg": "test: output gate validation",
        "change_type": "test"
    })

    dispatch_args = ["--team", "documentation_team", "--payload", payload]
    if dry_run:
        dispatch_args.append("--dry-run")

    result = run_script(root, "dispatch_agent_team.py", dispatch_args, verbose)
    steps.append({"step": "dispatch documentation_team", **result})

    manifest = result["output"]
    sub_agents = manifest.get("sub_agents", [])

    # Step 2: At least one sub-agent must have a validation_gate
    gated = [sa for sa in sub_agents if "validation_gate" in sa]
    has_gated = len(gated) > 0
    steps.append({
        "step": "check for gated sub-agents",
        "gated_count": len(gated),
        "gated_ids": [sa.get("id") for sa in gated],
        "pass": has_gated
    })

    # Step 3: Validate gate structure for each gated sub-agent
    gates_valid = True
    for sa in gated:
        gate = sa["validation_gate"]
        required_keys = ["command", "output_files", "on_fail"]
        missing = [k for k in required_keys if k not in gate]
        valid = len(missing) == 0
        if not valid:
            gates_valid = False
        steps.append({
            "step": f"validate gate structure for {sa.get('id')}",
            "missing_keys": missing,
            "pass": valid
        })

    # Step 4: Execute the bash gate command — must print VALIDATION:PASS or VALIDATION:FAIL
    gate_exec_ok = False
    if gated:
        cmd = gated[0]["validation_gate"]["command"]
        try:
            gate_result = subprocess.run(
                ["bash", "-c", cmd],
                capture_output=True, text=True, timeout=10
            )
            stdout = gate_result.stdout.strip()
            gate_exec_ok = "VALIDATION:PASS" in stdout or "VALIDATION:FAIL" in stdout
            steps.append({
                "step": "execute bash gate command",
                "command": cmd[:120],
                "stdout": stdout[:200],
                "exit_code": gate_result.returncode,
                "pass": gate_exec_ok
            })
        except Exception as e:
            steps.append({
                "step": "execute bash gate command",
                "error": str(e),
                "pass": False
            })

    # Step 5: Validate orchestrator instructions mention validation_gate
    instructions = manifest.get("instructions", "")
    instructions_ok = "validation_gate" in instructions.lower() or "VALIDATION:PASS" in instructions
    steps.append({
        "step": "validate orchestrator instructions reference gates",
        "pass": instructions_ok
    })

    passed = (
        result["exit_code"] == 0 and
        has_gated and
        gates_valid and
        gate_exec_ok and
        instructions_ok
    )
    return {
        "scenario": scenario_id,
        "pattern": "output-gate",
        "status": "pass" if passed else "fail",
        "steps": steps
    }


def scenario_12_state_json(root: Path, verbose: bool, dry_run: bool) -> dict:
    """
    Scenario 12: state.json Emission
    Pattern: state-observability
    Validates: dispatch_agent_team.py writes .tmp/team-runs/<run_id>/state.json at dispatch time
               and team_state.py can read, list, and update state correctly.
    """
    import shutil

    scenario_id = "scenario_12_state_json"
    steps = []

    # Step 1: Dispatch documentation_team (real write, not dry-run)
    payload = json.dumps({
        "changed_files": ["execution/dispatch_agent_team.py"],
        "commit_msg": "test: state.json emission",
        "change_type": "test"
    })

    dispatch_args = ["--team", "documentation_team", "--payload", payload, "--no-claude"]
    result = run_script(root, "dispatch_agent_team.py", dispatch_args, verbose)
    steps.append({"step": "dispatch documentation_team", "exit_code": result["exit_code"]})

    manifest = result.get("output", {})
    run_id = manifest.get("run_id", "")

    # Step 2: state.json must exist at the expected path
    state_path = root / ".tmp" / "team-runs" / run_id / "state.json"
    state_exists = state_path.exists() if run_id else False
    steps.append({"step": "state.json exists", "path": str(state_path.relative_to(root)) if run_id else "N/A", "pass": state_exists})

    # Step 3: Validate schema
    schema_ok = False
    state_data = {}
    if state_exists:
        try:
            state_data = json.loads(state_path.read_text())
            required = {"run_id", "team", "status", "sub_agents", "started_at", "updated_at", "total_steps"}
            missing = required - set(state_data.keys())
            schema_ok = (
                len(missing) == 0 and
                state_data.get("status") == "pending" and
                isinstance(state_data.get("sub_agents"), list) and
                state_data.get("run_id") == run_id and
                state_data.get("team") == "documentation_team"
            )
            steps.append({
                "step": "validate schema",
                "missing_keys": list(missing),
                "initial_status": state_data.get("status"),
                "pass": schema_ok
            })
        except Exception as e:
            steps.append({"step": "validate schema", "error": str(e), "pass": False})
    else:
        steps.append({"step": "validate schema", "pass": False, "reason": "file missing"})

    # Step 4: manifest state_file key matches
    manifest_state_file = manifest.get("state_file", "")
    manifest_key_ok = (
        run_id in manifest_state_file and
        "team-runs" in manifest_state_file
    ) if run_id else False
    steps.append({"step": "manifest state_file key", "value": manifest_state_file, "pass": manifest_key_ok})

    # Step 5: team_state.py read returns matching data
    read_ok = False
    if run_id:
        read_result = run_script(root, "team_state.py", ["read", "--run-id", run_id], verbose)
        read_state = read_result.get("output", {})
        read_ok = (
            read_result["exit_code"] == 0 and
            read_state.get("run_id") == run_id and
            read_state.get("team") == "documentation_team"
        )
    steps.append({"step": "team_state read", "pass": read_ok})

    # Step 6: team_state.py list-active includes the run
    list_ok = False
    if run_id:
        list_result = run_script(root, "team_state.py", ["list-active"], verbose)
        active_runs = list_result.get("output")
        if isinstance(active_runs, list):
            list_ok = any(r.get("run_id") == run_id for r in active_runs)
        elif list_result["exit_code"] == 0 and isinstance(list_result.get("output"), dict):
            # Possibly raw list wrapped in dict — check raw output
            try:
                raw = list_result.get("output", {})
                list_ok = any(r.get("run_id") == run_id for r in (raw if isinstance(raw, list) else []))
            except Exception:
                pass
    steps.append({"step": "team_state list-active", "pass": list_ok})

    # Step 7: team_state.py update transitions state
    update_ok = False
    if run_id and state_data.get("sub_agents"):
        first_agent = state_data["sub_agents"][0]["id"]
        upd = run_script(root, "team_state.py", [
            "update", "--run-id", run_id,
            "--status", "running",
            "--step", "0",
            "--agent-id", first_agent,
            "--agent-status", "running",
        ], verbose)
        if upd["exit_code"] == 0:
            # Re-read to verify
            verify = run_script(root, "team_state.py", ["read", "--run-id", run_id], verbose)
            vs = verify.get("output", {})
            first_sa = next((a for a in vs.get("sub_agents", []) if a["id"] == first_agent), None)
            update_ok = (
                vs.get("status") == "running" and
                first_sa is not None and
                first_sa.get("status") == "running"
            )
    steps.append({"step": "team_state update", "pass": update_ok})

    # Cleanup: remove run directory so test doesn't pollute .tmp/
    if run_id and (root / ".tmp" / "team-runs" / run_id).exists():
        try:
            shutil.rmtree(root / ".tmp" / "team-runs" / run_id)
        except OSError:
            pass

    passed = (
        result["exit_code"] == 0 and
        state_exists and
        schema_ok and
        manifest_key_ok and
        read_ok and
        list_ok and
        update_ok
    )
    return {
        "scenario": scenario_id,
        "pattern": "state-observability",
        "status": "pass" if passed else "fail",
        "steps": steps
    }


# ─── RUNNER ───────────────────────────────────────────────────────────────────

SCENARIOS = {
    1: scenario_1_single_subagent,
    2: scenario_2_parallel_subagents,
    3: scenario_3_doc_team_on_code,
    4: scenario_4_full_pipeline,
    5: scenario_5_failure_recovery,
    6: scenario_6_dynamic_handoff,
    11: scenario_11_output_gates,
    12: scenario_12_state_json,
}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    valid_scenarios = sorted(SCENARIOS.keys())
    parser.add_argument("--scenario", type=int, choices=valid_scenarios,
                        help=f"Scenario number ({', '.join(map(str, valid_scenarios))})")
    parser.add_argument("--all", action="store_true", help=f"Run all {len(valid_scenarios)} scenarios")
    parser.add_argument("--verbose", action="store_true", help="Show detailed step output")
    parser.add_argument("--dry-run", action="store_true", help="Validate setup without dispatching")
    args = parser.parse_args()

    if not args.scenario and not args.all:
        parser.print_help()
        sys.exit(1)

    root = find_project_root()

    # Validate setup first
    setup = validate_setup(root)
    if not setup["pass"]:
        missing = [k for k, v in setup["checks"].items() if not v]
        print(json.dumps({
            "status": "setup_failed",
            "missing": missing,
            "hint": "Ensure all directives and execution scripts are in place"
        }), file=sys.stderr)
        sys.exit(2)

    scenarios_to_run = list(SCENARIOS.keys()) if args.all else [args.scenario]
    results = []
    start_all = time.time()

    for scenario_num in scenarios_to_run:
        fn = SCENARIOS[scenario_num]
        print(f"\n▶  Running Scenario {scenario_num}: {fn.__name__}...", file=sys.stderr)
        result = fn(root, args.verbose, args.dry_run)
        results.append(result)
        icon = "✅" if result["status"] == "pass" else "❌"
        print(f"   {icon} {result['status'].upper()}", file=sys.stderr)

    total_elapsed = round(time.time() - start_all, 2)
    passed = sum(1 for r in results if r["status"] == "pass")
    failed = len(results) - passed

    report = {
        "run_at": datetime.now(timezone.utc).isoformat(),
        "total": len(results),
        "passed": passed,
        "failed": failed,
        "elapsed_s": total_elapsed,
        "overall_status": "pass" if failed == 0 else "fail",
        "scenarios": results
    }

    print(json.dumps(report, indent=2))
    sys.exit(0 if failed == 0 else 3)


if __name__ == "__main__":
    main()
