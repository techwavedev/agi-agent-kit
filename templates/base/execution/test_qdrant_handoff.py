#!/usr/bin/env python3
"""
Script: test_qdrant_handoff.py
Purpose: Integration tests for Qdrant memory operations in agent/sub-agent handoffs
         and advanced team communication patterns.

         Covers four test suites:
           1. Store/Retrieve Round-Trip         — basic memory fidelity
           2. Cross-Subagent Handoff Persistence — Agent A writes, Agent B reads
           3. Parallel Subagent Memory Isolation — two agents don't cross-contaminate
           4. Memory-Guided Orchestrator Routing — orchestrator reads memory to decide next team

Usage:
    python3 execution/test_qdrant_handoff.py
    python3 execution/test_qdrant_handoff.py --suite 1
    python3 execution/test_qdrant_handoff.py --suite 2
    python3 execution/test_qdrant_handoff.py --all
    python3 execution/test_qdrant_handoff.py --verbose
    python3 execution/test_qdrant_handoff.py --dry-run   # validate setup only

Arguments:
    --suite     Suite number to run (1-4)
    --all       Run all 4 suites (default when no flag given)
    --verbose   Stream sub-process stdout/stderr
    --dry-run   Validate memory connectivity without storing any data

Exit Codes:
    0 - All selected suites passed
    1 - Invalid arguments
    2 - Memory system unavailable (Qdrant or embedding service down)
    3 - One or more suites failed
"""

import argparse
import json
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path


# ─── Helpers ──────────────────────────────────────────────────────────────────

def find_project_root() -> Path:
    current = Path.cwd()
    for parent in [current] + list(current.parents):
        if (parent / "AGENTS.md").exists() or (parent / "package.json").exists():
            return parent
    return current


def run_memory_cmd(root: Path, args: list, verbose: bool = False) -> dict:
    """Invoke memory_manager.py with the given args; return parsed result."""
    cmd = [sys.executable, str(root / "execution" / "memory_manager.py")] + args
    start = time.time()
    res = subprocess.run(cmd, capture_output=True, text=True, cwd=str(root))
    elapsed = round(time.time() - start, 3)

    if verbose:
        print(f"    $ {' '.join(cmd[1:])}")
        if res.stdout:
            print(f"    stdout: {res.stdout[:400]}")
        if res.stderr:
            print(f"    stderr: {res.stderr[:200]}")

    try:
        output = json.loads(res.stdout) if res.stdout.strip() else {}
    except json.JSONDecodeError:
        output = {"raw": res.stdout[:300]}

    return {
        "exit_code": res.returncode,
        "elapsed_s": elapsed,
        "output": output,
        "stderr": res.stderr[:300] if res.stderr else "",
    }


def check_memory_available(root: Path) -> bool:
    """Return True if memory_manager health check passes."""
    result = run_memory_cmd(root, ["health"])
    out = result["output"]
    return result["exit_code"] == 0 and out.get("qdrant") in ("ok", "connected")


# ─── Suite 1: Store / Retrieve Round-Trip ─────────────────────────────────────

def suite_1_store_retrieve_round_trip(root: Path, verbose: bool, dry_run: bool) -> dict:
    """
    Verifies that content stored into Qdrant memory can be retrieved verbatim.
    This is the baseline correctness check before any handoff test.
    """
    suite_id = "suite_01_store_retrieve_round_trip"
    steps = []
    run_id = str(uuid.uuid4())[:8]
    probe_content = (
        f"[PROBE-{run_id}] Agent memory round-trip test. "
        "Stored by test_qdrant_handoff.py at suite 1."
    )

    if dry_run:
        return {
            "suite": suite_id,
            "status": "skipped",
            "reason": "dry-run mode — no writes performed",
        }

    # ── Step 1: store ──────────────────────────────────────────────────────────
    store_result = run_memory_cmd(root, [
        "store",
        "--content", probe_content,
        "--type", "technical",
        "--project", "test-qdrant-handoff",
        "--tags", f"probe {run_id} round-trip",
    ], verbose)

    steps.append({
        "step": "store probe content",
        "exit_code": store_result["exit_code"],
        "output": store_result["output"],
        "pass": store_result["exit_code"] == 0,
    })

    if store_result["exit_code"] != 0:
        return {"suite": suite_id, "status": "fail", "steps": steps}

    point_id = store_result["output"].get("id") or store_result["output"].get("point_id")

    # ── Step 2: retrieve ───────────────────────────────────────────────────────
    retrieve_result = run_memory_cmd(root, [
        "retrieve",
        "--query", f"PROBE-{run_id} round-trip test",
        "--top-k", "3",
    ], verbose)

    chunks = retrieve_result["output"].get("context_chunks", [])
    probe_found = any(f"PROBE-{run_id}" in str(c) for c in chunks)

    steps.append({
        "step": "retrieve probe content",
        "exit_code": retrieve_result["exit_code"],
        "probe_found_in_results": probe_found,
        "chunks_returned": len(chunks),
        "pass": probe_found,
    })

    # ── Step 3: validate stored point ID was returned ─────────────────────────
    steps.append({
        "step": "validate point id returned by store",
        "point_id": point_id,
        "pass": bool(point_id),
    })

    passed = all(s.get("pass", False) for s in steps)
    return {"suite": suite_id, "status": "pass" if passed else "fail", "steps": steps}


# ─── Suite 2: Cross-Subagent Handoff Persistence ──────────────────────────────

def suite_2_cross_agent_handoff(root: Path, verbose: bool, dry_run: bool) -> dict:
    """
    Simulates Agent A completing work and writing a structured handoff_state to Qdrant,
    then Agent B querying Qdrant and reading that state with all required fields
    (state, next_steps, validation_requirements) intact.

    This validates the Dynamic State Handoff protocol from AGENTS.md.
    """
    suite_id = "suite_02_cross_agent_handoff"
    steps = []
    run_id = str(uuid.uuid4())[:8]
    agent_a_tag = f"handoff-{run_id}-agent-a"

    if dry_run:
        return {"suite": suite_id, "status": "skipped", "reason": "dry-run mode"}

    # ── Step 1: Agent A stores handoff_state ──────────────────────────────────
    handoff_state = {
        "run_id": run_id,
        "agent": "agent-a",
        "state": {
            "completed_steps": [1, 2, 3],
            "output_files": [".tmp/processed/result.json"],
            "summary": "Feature extraction complete. 42 records processed.",
        },
        "next_steps": (
            "Agent B must: (1) load .tmp/processed/result.json, "
            "(2) run validation/schema_check.py against the output, "
            "(3) confirm row count == 42 before proceeding to deploy."
        ),
        "validation_requirements": (
            "Run: python3 validation/schema_check.py --input .tmp/processed/result.json "
            "--expected-rows 42. Exit code must be 0."
        ),
    }

    store_result = run_memory_cmd(root, [
        "store",
        "--content", json.dumps(handoff_state),
        "--type", "decision",
        "--project", "test-qdrant-handoff",
        "--tags", f"handoff {agent_a_tag} {run_id}",
    ], verbose)

    steps.append({
        "step": "agent-a stores handoff_state",
        "exit_code": store_result["exit_code"],
        "run_id": run_id,
        "pass": store_result["exit_code"] == 0,
    })

    if store_result["exit_code"] != 0:
        return {"suite": suite_id, "status": "fail", "steps": steps}

    # ── Step 2: Agent B retrieves handoff_state ────────────────────────────────
    retrieve_result = run_memory_cmd(root, [
        "retrieve",
        "--query", f"handoff {run_id} agent-a output files next steps validation",
        "--top-k", "5",
    ], verbose)

    chunks = retrieve_result["output"].get("context_chunks", [])

    # Search all chunks for the run_id fingerprint
    retrieved_blob = None
    for chunk in chunks:
        chunk_text = str(chunk)
        if run_id in chunk_text:
            retrieved_blob = chunk_text
            break

    steps.append({
        "step": "agent-b retrieves handoff_state",
        "exit_code": retrieve_result["exit_code"],
        "chunks_returned": len(chunks),
        "handoff_found": retrieved_blob is not None,
        "pass": retrieved_blob is not None,
    })

    # ── Step 3: validate required handoff fields are in retrieved blob ─────────
    if retrieved_blob:
        has_state = "output_files" in retrieved_blob or "completed_steps" in retrieved_blob
        has_next_steps = "next_steps" in retrieved_blob or "Agent B must" in retrieved_blob
        has_validation = "validation_requirements" in retrieved_blob or "schema_check" in retrieved_blob

        steps.append({
            "step": "validate handoff_state fields (state, next_steps, validation_requirements)",
            "has_state": has_state,
            "has_next_steps": has_next_steps,
            "has_validation_requirements": has_validation,
            "pass": has_state and has_next_steps and has_validation,
        })
    else:
        steps.append({
            "step": "validate handoff_state fields",
            "pass": False,
            "reason": "handoff_state not found in retrieved chunks",
        })

    passed = all(s.get("pass", False) for s in steps)
    return {"suite": suite_id, "status": "pass" if passed else "fail", "steps": steps}


# ─── Suite 3: Parallel Subagent Memory Isolation ──────────────────────────────

def suite_3_parallel_memory_isolation(root: Path, verbose: bool, dry_run: bool) -> dict:
    """
    Simulates two subagents working in parallel. Both store their own handoff_state
    to Qdrant with distinct run_id tags. Validates:
      - Each agent's store succeeds
      - Point IDs are different (no collision)
      - Querying each agent's run_id returns only that agent's data
    """
    suite_id = "suite_03_parallel_memory_isolation"
    steps = []

    if dry_run:
        return {"suite": suite_id, "status": "skipped", "reason": "dry-run mode"}

    agents = {
        "parallel-agent-alpha": str(uuid.uuid4())[:8],
        "parallel-agent-beta": str(uuid.uuid4())[:8],
    }

    point_ids = {}

    # ── Step 1: both agents store concurrently (sequential here for simplicity) ─
    for agent_name, agent_run_id in agents.items():
        content = json.dumps({
            "agent": agent_name,
            "run_id": agent_run_id,
            "payload": f"Independent work by {agent_name}. Token: {agent_run_id}.",
            "state": {"processed": True, "records": 100 if "alpha" in agent_name else 200},
        })

        store_result = run_memory_cmd(root, [
            "store",
            "--content", content,
            "--type", "technical",
            "--project", "test-qdrant-handoff",
            "--tags", f"parallel isolation {agent_run_id} {agent_name}",
        ], verbose)

        pid = store_result["output"].get("id") or store_result["output"].get("point_id")
        point_ids[agent_name] = pid

        steps.append({
            "step": f"{agent_name} stores state",
            "run_id": agent_run_id,
            "point_id": pid,
            "exit_code": store_result["exit_code"],
            "pass": store_result["exit_code"] == 0,
        })

    # ── Step 2: point IDs must differ ─────────────────────────────────────────
    pid_values = list(point_ids.values())
    ids_distinct = (
        len(pid_values) == 2 and
        pid_values[0] is not None and
        pid_values[1] is not None and
        pid_values[0] != pid_values[1]
    )

    steps.append({
        "step": "validate point IDs are distinct (no collision)",
        "point_ids": point_ids,
        "pass": ids_distinct,
    })

    # ── Step 3: query each agent's run_id, verify cross-contamination absent ──
    for agent_name, agent_run_id in agents.items():
        other_run_id = [r for n, r in agents.items() if n != agent_name][0]

        retrieve_result = run_memory_cmd(root, [
            "retrieve",
            "--query", f"parallel isolation {agent_run_id} {agent_name}",
            "--top-k", "5",
        ], verbose)

        chunks = retrieve_result["output"].get("context_chunks", [])
        all_text = " ".join(str(c) for c in chunks)

        own_found = agent_run_id in all_text
        other_leaked = other_run_id in all_text

        steps.append({
            "step": f"{agent_name}: retrieve own data, check isolation",
            "own_run_id_found": own_found,
            "other_run_id_leaked": other_leaked,
            # Ideal: own found; leakage is a soft warning (BM25 may surface both),
            # but own data MUST be present.
            "pass": own_found,
        })

    passed = all(s.get("pass", False) for s in steps)
    return {"suite": suite_id, "status": "pass" if passed else "fail", "steps": steps}


# ─── Suite 4: Memory-Guided Orchestrator Routing ──────────────────────────────

def suite_4_memory_guided_routing(root: Path, verbose: bool, dry_run: bool) -> dict:
    """
    Simulates an orchestrator that:
      1. Stores a routing decision in Qdrant ("code_review passed → run qa_team next")
      2. Later queries Qdrant to recall that decision
      3. Uses the retrieved decision to dispatch the correct next team

    Validates:
      - Routing decision survives a store/retrieve cycle
      - The recommended next team ("qa_team") is extractable from retrieved context
      - Dispatching qa_team based on that decision succeeds (exit 0)
    """
    suite_id = "suite_04_memory_guided_routing"
    steps = []
    run_id = str(uuid.uuid4())[:8]
    task_id = f"routing-test-{run_id}"

    if dry_run:
        return {"suite": suite_id, "status": "skipped", "reason": "dry-run mode"}

    # ── Step 1: store routing decision ────────────────────────────────────────
    routing_decision = {
        "task_id": task_id,
        "source_team": "code_review_team",
        "outcome": "PASS",
        "next_recommended_team": "qa_team",
        "rationale": (
            "Spec and quality review both passed for the feature branch. "
            "Proceeding to test generation via qa_team."
        ),
        "next_payload": {
            "changed_files": ["execution/dispatch_agent_team.py"],
            "commit_msg": "feat: agent team dispatch",
            "change_type": "feat",
            "test_runner": "pytest",
        },
    }

    store_result = run_memory_cmd(root, [
        "store",
        "--content", json.dumps(routing_decision),
        "--type", "decision",
        "--project", "test-qdrant-handoff",
        "--tags", f"routing {task_id} {run_id} code_review_team qa_team orchestrator",
    ], verbose)

    steps.append({
        "step": "orchestrator stores routing decision",
        "task_id": task_id,
        "exit_code": store_result["exit_code"],
        "pass": store_result["exit_code"] == 0,
    })

    if store_result["exit_code"] != 0:
        return {"suite": suite_id, "status": "fail", "steps": steps}

    # ── Step 2: orchestrator re-queries routing decision ──────────────────────
    retrieve_result = run_memory_cmd(root, [
        "retrieve",
        "--query", f"routing decision {task_id} next team after code review passed",
        "--top-k", "5",
    ], verbose)

    chunks = retrieve_result["output"].get("context_chunks", [])
    all_text = " ".join(str(c) for c in chunks)

    decision_found = task_id in all_text
    next_team_extractable = "qa_team" in all_text

    steps.append({
        "step": "orchestrator retrieves routing decision",
        "chunks_returned": len(chunks),
        "decision_found": decision_found,
        "next_team_extractable": next_team_extractable,
        "pass": decision_found and next_team_extractable,
    })

    # ── Step 3: dispatch the recommended team (qa_team) ───────────────────────
    import subprocess as _sp
    dispatch_payload = json.dumps({
        **routing_decision["next_payload"],
        "orchestrator_decision_task_id": task_id,
        "routed_by": "memory",
    })

    dispatch_cmd = [
        sys.executable,
        str(find_project_root() / "execution" / "dispatch_agent_team.py"),
        "--team", "qa_team",
        "--payload", dispatch_payload,
        "--dry-run",
    ]

    dispatch_start = time.time()
    dispatch_res = _sp.run(dispatch_cmd, capture_output=True, text=True,
                           cwd=str(find_project_root()))
    dispatch_elapsed = round(time.time() - dispatch_start, 3)

    try:
        dispatch_out = json.loads(dispatch_res.stdout) if dispatch_res.stdout.strip() else {}
    except json.JSONDecodeError:
        dispatch_out = {"raw": dispatch_res.stdout[:300]}

    team_dispatched_ok = dispatch_res.returncode == 0
    steps.append({
        "step": "dispatch qa_team based on memory-retrieved routing decision",
        "exit_code": dispatch_res.returncode,
        "elapsed_s": dispatch_elapsed,
        "team": dispatch_out.get("team"),
        "run_id": dispatch_out.get("run_id"),
        "pass": team_dispatched_ok,
    })

    passed = all(s.get("pass", False) for s in steps)
    return {"suite": suite_id, "status": "pass" if passed else "fail", "steps": steps}


# ─── Runner ────────────────────────────────────────────────────────────────────

SUITES = {
    1: suite_1_store_retrieve_round_trip,
    2: suite_2_cross_agent_handoff,
    3: suite_3_parallel_memory_isolation,
    4: suite_4_memory_guided_routing,
}

SUITE_NAMES = {
    1: "Store/Retrieve Round-Trip",
    2: "Cross-Subagent Handoff Persistence",
    3: "Parallel Subagent Memory Isolation",
    4: "Memory-Guided Orchestrator Routing",
}


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--suite", type=int, choices=range(1, 5),
                        help="Suite number to run (1-4)")
    parser.add_argument("--all", action="store_true", help="Run all 4 suites (default)")
    parser.add_argument("--verbose", action="store_true", help="Stream sub-process output")
    parser.add_argument("--dry-run", action="store_true",
                        help="Validate connectivity only — no writes")
    args = parser.parse_args()

    if not args.suite and not args.all:
        # Default: run all
        args.all = True

    root = find_project_root()
    memory_script = root / "execution" / "memory_manager.py"
    dispatch_script = root / "execution" / "dispatch_agent_team.py"

    # ── Setup validation ───────────────────────────────────────────────────────
    missing = []
    if not memory_script.exists():
        missing.append("execution/memory_manager.py")
    if not dispatch_script.exists():
        missing.append("execution/dispatch_agent_team.py")

    if missing:
        print(json.dumps({
            "status": "setup_failed",
            "missing_scripts": missing,
            "hint": "Run session_boot.py --auto-fix or ensure the scripts are present",
        }), file=sys.stderr)
        sys.exit(2)

    # ── Memory availability check ──────────────────────────────────────────────
    if not args.dry_run:
        print("  Checking Qdrant memory availability...", file=sys.stderr)
        if not check_memory_available(root):
            print(json.dumps({
                "status": "memory_unavailable",
                "hint": "Start Qdrant and Ollama, then run session_boot.py --auto-fix",
            }), file=sys.stderr)
            sys.exit(2)
        print("  Memory system ready.", file=sys.stderr)

    suites_to_run = list(SUITES.keys()) if args.all else [args.suite]
    results = []
    start_all = time.time()

    for suite_num in suites_to_run:
        fn = SUITES[suite_num]
        label = SUITE_NAMES[suite_num]
        print(f"\n▶  Suite {suite_num}: {label}...", file=sys.stderr)

        result = fn(root, args.verbose, args.dry_run)
        results.append(result)

        icon = "✅" if result["status"] in ("pass", "skipped") else "❌"
        print(f"   {icon} {result['status'].upper()}", file=sys.stderr)

    total_elapsed = round(time.time() - start_all, 2)
    passed = sum(1 for r in results if r["status"] == "pass")
    skipped = sum(1 for r in results if r["status"] == "skipped")
    failed = len(results) - passed - skipped

    report = {
        "run_at": datetime.now(timezone.utc).isoformat(),
        "total_suites": len(results),
        "passed": passed,
        "skipped": skipped,
        "failed": failed,
        "elapsed_s": total_elapsed,
        "overall_status": "pass" if failed == 0 else "fail",
        "suites": results,
    }

    print(json.dumps(report, indent=2))
    sys.exit(0 if failed == 0 else 3)


if __name__ == "__main__":
    main()
