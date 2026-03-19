#!/usr/bin/env python3
"""
Script: karpathy_loop.py
Purpose: Autonomous self-improvement loop for skills (Karpathy Loop).
         Reads SKILL.md, makes targeted changes, runs evals, and uses git
         commit/reset to keep improvements and discard regressions.

Usage:
    # Run improvement loop on a skill
    python3 execution/karpathy_loop.py --skill skills/my-skill --max-iterations 10

    # Dry run (no git operations)
    python3 execution/karpathy_loop.py --skill skills/my-skill --dry-run

    # Target a specific file within the skill
    python3 execution/karpathy_loop.py --skill skills/my-skill --target SKILL.md

    # Set minimum improvement threshold
    python3 execution/karpathy_loop.py --skill skills/my-skill --min-improvement 2.0

Karpathy Loop (per iteration):
    1. Read SKILL.md and current pass rate
    2. AI makes a targeted change to SKILL.md (or target file)
    3. Run evals.json assertions
    4. If pass_rate > previous_best → git commit (keep change)
       If pass_rate <= previous_best → git reset (discard change)
    5. Loop until max iterations or perfect score

Prerequisites:
    - Skill must have eval/evals.json with binary assertions
    - Git repository must be initialized
    - run_skill_eval.py must be available in execution/

Exit Codes:
    0 - Loop completed (improvements made or perfect score reached)
    1 - No evals.json found
    2 - Git not initialized or dirty state
    3 - Execution error
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def get_pass_rate(evals_path: Path) -> dict:
    """Run eval and return results."""
    script_dir = Path(__file__).resolve().parent
    eval_script = script_dir / "run_skill_eval.py"

    try:
        result = subprocess.run(
            [sys.executable, str(eval_script), "--evals", str(evals_path), "--json-only"],
            capture_output=True, text=True, timeout=60
        )
        data = json.loads(result.stdout)
        return {
            "pass_rate": data.get("pass_rate", 0.0),
            "status": data.get("status", "error"),
            "total_passed": data.get("total_passed", 0),
            "total_assertions": data.get("total_assertions", 0),
            "evaluations": data.get("evaluations", []),
        }
    except (subprocess.TimeoutExpired, json.JSONDecodeError, Exception) as e:
        return {"pass_rate": 0.0, "status": "error", "error": str(e)}


def git_is_clean(cwd: Path) -> bool:
    """Check if git working directory is clean."""
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True, text=True, cwd=str(cwd)
        )
        return result.stdout.strip() == ""
    except Exception:
        return False


def git_commit(message: str, files: list, cwd: Path) -> bool:
    """Stage files and commit."""
    try:
        for f in files:
            subprocess.run(
                ["git", "add", str(f)],
                capture_output=True, cwd=str(cwd), check=True
            )
        subprocess.run(
            ["git", "commit", "-m", message],
            capture_output=True, cwd=str(cwd), check=True
        )
        return True
    except Exception:
        return False


def git_reset_file(file_path: Path, cwd: Path) -> bool:
    """Reset a single file to last committed version."""
    try:
        subprocess.run(
            ["git", "checkout", "HEAD", "--", str(file_path)],
            capture_output=True, cwd=str(cwd), check=True
        )
        return True
    except Exception:
        return False


def get_failing_assertions(eval_result: dict) -> list:
    """Extract failing assertion details for targeted improvement."""
    failures = []
    for evaluation in eval_result.get("evaluations", []):
        for result in evaluation.get("results", []):
            if not result.get("passed", True):
                failures.append({
                    "test": evaluation.get("name", "unknown"),
                    "assertion": result.get("assertion", ""),
                    "detail": result.get("detail", ""),
                })
    return failures


def generate_improvement_report(history: list) -> dict:
    """Generate summary report from iteration history."""
    if not history:
        return {"iterations": 0, "improvements": 0, "final_pass_rate": 0.0}

    improvements = sum(1 for h in history if h.get("action") == "commit")
    regressions = sum(1 for h in history if h.get("action") == "reset")

    return {
        "iterations": len(history),
        "improvements": improvements,
        "regressions": regressions,
        "initial_pass_rate": history[0].get("pass_rate_before", 0.0),
        "final_pass_rate": history[-1].get("pass_rate_after", 0.0),
        "history": history,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Karpathy Loop: Autonomous skill self-improvement via binary assertions + git",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
The Karpathy Loop automates the cycle:
  Read → Change → Eval → Commit/Reset → Repeat

It requires:
  1. A skill with eval/evals.json containing binary assertions
  2. A git repository (for commit/reset of changes)
  3. An AI agent to make the actual SKILL.md modifications (this script
     orchestrates the loop — the agent provides the intelligence)

Example workflow:
  1. Agent reads SKILL.md and failing assertions
  2. Agent modifies SKILL.md to fix failures
  3. This script runs evals and commits or resets
  4. Script reports results back to agent
  5. Loop continues until perfect or max iterations
        """,
    )
    parser.add_argument("--skill", required=True, help="Path to skill directory")
    parser.add_argument("--target", default="SKILL.md", help="Target file within skill (default: SKILL.md)")
    parser.add_argument("--max-iterations", type=int, default=20, help="Maximum improvement iterations")
    parser.add_argument("--min-improvement", type=float, default=0.0,
                        help="Minimum pass rate improvement to commit (default: any improvement)")
    parser.add_argument("--dry-run", action="store_true", help="Run evals without git operations")
    parser.add_argument("--status-only", action="store_true",
                        help="Just show current eval status, don't loop")

    args = parser.parse_args()

    skill_dir = Path(args.skill).resolve()
    evals_path = skill_dir / "eval" / "evals.json"
    target_file = skill_dir / args.target

    # Validate paths
    if not skill_dir.exists():
        print(json.dumps({"status": "error", "message": f"Skill directory not found: {skill_dir}"}),
              file=sys.stderr)
        sys.exit(1)

    if not evals_path.exists():
        print(json.dumps({"status": "error", "message": f"No eval/evals.json found at: {evals_path}",
                          "hint": "Create eval/evals.json with binary assertions first"}),
              file=sys.stderr)
        sys.exit(1)

    if not target_file.exists():
        print(json.dumps({"status": "error", "message": f"Target file not found: {target_file}"}),
              file=sys.stderr)
        sys.exit(1)

    # Find git root
    try:
        git_root_result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, cwd=str(skill_dir)
        )
        git_root = Path(git_root_result.stdout.strip())
    except Exception:
        print(json.dumps({"status": "error", "message": "Not a git repository"}), file=sys.stderr)
        sys.exit(2)

    # Get baseline pass rate
    print(f"\n{'='*60}")
    print(f"  Karpathy Loop: {skill_dir.name}")
    print(f"  Target: {args.target}")
    print(f"  Evals: {evals_path}")
    print(f"{'='*60}\n")

    baseline = get_pass_rate(evals_path)
    best_pass_rate = baseline["pass_rate"]

    print(f"  📊 Baseline pass rate: {best_pass_rate}% "
          f"({baseline.get('total_passed', 0)}/{baseline.get('total_assertions', 0)})")

    if baseline["pass_rate"] == 100.0:
        print(f"\n  ✅ Perfect score! Nothing to improve.")
        print(json.dumps({"status": "perfect", "pass_rate": 100.0}))
        sys.exit(0)

    if args.status_only:
        # Show failing assertions and exit
        failures = get_failing_assertions(baseline)
        print(f"\n  ❌ Failing assertions ({len(failures)}):")
        for f in failures:
            print(f"    • [{f['test']}] {f['assertion']} — {f['detail']}")

        print(json.dumps({
            "status": "report",
            "pass_rate": best_pass_rate,
            "failing_assertions": failures,
            "target_file": str(target_file),
        }, indent=2))
        sys.exit(1)

    # Print failing assertions for the agent to work on
    failures = get_failing_assertions(baseline)
    print(f"\n  ❌ Failing assertions ({len(failures)}):")
    for f in failures:
        print(f"    • [{f['test']}] {f['assertion']} — {f['detail']}")

    print(f"\n  🔄 Starting improvement loop (max {args.max_iterations} iterations)")
    print(f"  {'─'*56}")

    # The loop: agent modifies file externally, we evaluate and commit/reset
    history = []

    for iteration in range(1, args.max_iterations + 1):
        # Wait for agent to modify the target file
        # In practice, this script is called by the agent after each modification
        # For now, we run eval on current state

        current = get_pass_rate(evals_path)
        current_rate = current["pass_rate"]

        entry = {
            "iteration": iteration,
            "timestamp": datetime.now().isoformat(),
            "pass_rate_before": best_pass_rate,
            "pass_rate_after": current_rate,
        }

        improvement = current_rate - best_pass_rate

        if current_rate > best_pass_rate and improvement >= args.min_improvement:
            # Improvement! Commit.
            entry["action"] = "commit"
            entry["improvement"] = round(improvement, 1)

            if not args.dry_run:
                msg = (f"karpathy-loop: {skill_dir.name} "
                       f"{best_pass_rate}% → {current_rate}% (+{improvement:.1f}%)")
                committed = git_commit(msg, [target_file], git_root)
                entry["git_committed"] = committed
            else:
                entry["git_committed"] = False
                entry["dry_run"] = True

            best_pass_rate = current_rate
            print(f"  #{iteration:02d} ✅ {current_rate}% (+{improvement:.1f}%) → committed")

        else:
            # No improvement or regression. Reset.
            entry["action"] = "reset"
            entry["regression"] = round(current_rate - best_pass_rate, 1)

            if not args.dry_run:
                git_reset_file(target_file, git_root)
                entry["git_reset"] = True
            else:
                entry["git_reset"] = False
                entry["dry_run"] = True

            print(f"  #{iteration:02d} ❌ {current_rate}% (best={best_pass_rate}%) → reset")

        history.append(entry)

        # Check for perfect score
        if best_pass_rate == 100.0:
            print(f"\n  🎯 Perfect score reached at iteration {iteration}!")
            break

        # Show remaining failures
        if current_rate < 100.0:
            remaining = get_failing_assertions(current)
            entry["remaining_failures"] = len(remaining)

    # Final report
    report = generate_improvement_report(history)
    print(f"\n{'='*60}")
    print(f"  Results: {report['initial_pass_rate']}% → {report['final_pass_rate']}%")
    print(f"  Iterations: {report['iterations']} "
          f"({report['improvements']} improvements, {report['regressions']} regressions)")
    print(f"{'='*60}\n")

    print(json.dumps({
        "status": "completed",
        "skill": skill_dir.name,
        "initial_pass_rate": report["initial_pass_rate"],
        "final_pass_rate": report["final_pass_rate"],
        "iterations": report["iterations"],
        "improvements": report["improvements"],
    }, indent=2))

    sys.exit(0 if report["final_pass_rate"] == 100.0 else 1)


if __name__ == "__main__":
    main()
