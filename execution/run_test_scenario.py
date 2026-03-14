#!/usr/bin/env python3
"""
Script: run_test_scenario.py
Purpose: Run one or all test scenarios that validate sub-agent and team agent
         functionality in the AGI framework.

Usage:
    # Run a single scenario
    python3 execution/run_test_scenario.py --scenario 1

    # Run all scenarios
    python3 execution/run_test_scenario.py --all

    # Run with verbose output
    python3 execution/run_test_scenario.py --all --verbose

Arguments:
    --scenario  Scenario number to run (1-6)
    --all       Run all 6 scenarios
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
    for sa in ["doc_writer", "doc_reviewer", "changelog_updater", "spec_reviewer", "quality_reviewer", "asset_compiler", "cloud_deployer"]:
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


# ─── RUNNER ───────────────────────────────────────────────────────────────────

SCENARIOS = {
    1: scenario_1_single_subagent,
    2: scenario_2_parallel_subagents,
    3: scenario_3_doc_team_on_code,
    4: scenario_4_full_pipeline,
    5: scenario_5_failure_recovery,
    6: scenario_6_dynamic_handoff,
}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--scenario", type=int, choices=range(1, 7), help="Scenario number (1-6)")
    parser.add_argument("--all", action="store_true", help="Run all 6 scenarios")
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
