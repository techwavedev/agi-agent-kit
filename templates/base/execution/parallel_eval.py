#!/usr/bin/env python3
"""
Script: parallel_eval.py
Purpose: Parallel skill evaluation runner that executes skill evals N times
         simultaneously and aggregates results for statistical reliability.

Usage:
    python3 execution/parallel_eval.py --skill skills/my-skill
    python3 execution/parallel_eval.py --skill skills/my-skill --runs 10 --workers 4
    python3 execution/parallel_eval.py --skill skills/my-skill --json
    python3 execution/parallel_eval.py --skill skills/my-skill --runs 10 --verbose

Arguments:
    --skill     Path to skill directory (required)
    --runs      Number of parallel eval runs (default: 5)
    --workers   Max parallel workers (default: min(runs, cpu_count))
    --json      JSON-only output
    --verbose   Show per-run details

Exit Codes:
    0 - Success (all runs completed)
    1 - All runs failed
    2 - Configuration error (missing evals.json, bad args)
    3 - Execution error (subprocess failures)
"""

import argparse
import json
import math
import os
import subprocess
import sys
import time
from concurrent.futures import ProcessPoolExecutor, TimeoutError as FuturesTimeoutError
from pathlib import Path

PROJECT_DIR = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
EVAL_SCRIPT = PROJECT_DIR / "execution" / "run_skill_eval.py"
TIMEOUT_SECONDS = 30


def run_single_eval(evals_path: str) -> dict:
    """Run a single eval via subprocess and return parsed JSON result."""
    try:
        result = subprocess.run(
            [sys.executable, str(EVAL_SCRIPT), "--evals", evals_path, "--json-only"],
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SECONDS,
            cwd=str(PROJECT_DIR),
        )
        # run_skill_eval.py prints JSON to stdout with --json-only
        output = result.stdout.strip()
        if output:
            return json.loads(output)
        # If stdout is empty, check stderr
        return {
            "status": "error",
            "pass_rate": 0.0,
            "error": result.stderr.strip() or "No output from eval script",
            "evaluations": [],
        }
    except subprocess.TimeoutExpired:
        return {
            "status": "error",
            "pass_rate": 0.0,
            "error": f"Eval timed out after {TIMEOUT_SECONDS}s",
            "evaluations": [],
        }
    except json.JSONDecodeError as e:
        return {
            "status": "error",
            "pass_rate": 0.0,
            "error": f"Invalid JSON from eval script: {e}",
            "evaluations": [],
        }
    except Exception as e:
        return {
            "status": "error",
            "pass_rate": 0.0,
            "error": str(e),
            "evaluations": [],
        }


def calc_median(values: list) -> float:
    """Calculate median without numpy."""
    if not values:
        return 0.0
    s = sorted(values)
    n = len(s)
    if n % 2 == 1:
        return s[n // 2]
    return (s[n // 2 - 1] + s[n // 2]) / 2.0


def calc_std_dev(values: list, mean: float) -> float:
    """Calculate population standard deviation without numpy."""
    if len(values) < 2:
        return 0.0
    variance = sum((x - mean) ** 2 for x in values) / len(values)
    return math.sqrt(variance)


def aggregate_failures(runs: list, num_runs: int) -> dict:
    """Aggregate assertion failure patterns across all runs.

    Returns dict of assertion_type -> {"count": N, "rate": pct}.
    """
    failure_counts = {}
    for run in runs:
        if run.get("status") == "error":
            continue
        # Track which assertion types failed in THIS run
        failed_in_run = set()
        for evaluation in run.get("evaluations", []):
            for result in evaluation.get("results", []):
                if not result.get("passed", True):
                    # Extract assertion type from the assertion string
                    assertion_str = result.get("assertion", "unknown")
                    # The assertion string looks like "contains 'x'" or "max_words <= 300"
                    # Extract the type (first word)
                    atype = assertion_str.split()[0] if assertion_str else "unknown"
                    failed_in_run.add(atype)
        for atype in failed_in_run:
            failure_counts[atype] = failure_counts.get(atype, 0) + 1

    # Convert to rate
    result = {}
    for atype, count in sorted(failure_counts.items(), key=lambda x: -x[1]):
        result[atype] = {"count": count, "rate": round(count / num_runs * 100, 1)}
    return result


def main():
    parser = argparse.ArgumentParser(
        description="Parallel skill evaluation runner for statistical reliability",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run 5 parallel evals (default)
  python3 execution/parallel_eval.py --skill skills/my-skill

  # Run 10 evals with 4 workers, JSON output
  python3 execution/parallel_eval.py --skill skills/my-skill --runs 10 --workers 4 --json

  # Verbose output showing per-run details
  python3 execution/parallel_eval.py --skill skills/my-skill --runs 10 --verbose
        """,
    )
    parser.add_argument("--skill", required=True, help="Path to skill directory")
    parser.add_argument(
        "--runs", type=int, default=5, help="Number of parallel eval runs (default: 5)"
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=None,
        help="Max parallel workers (default: min(runs, cpu_count))",
    )
    parser.add_argument(
        "--json", action="store_true", dest="json_output", help="JSON-only output"
    )
    parser.add_argument(
        "--verbose", action="store_true", help="Show per-run details"
    )

    args = parser.parse_args()

    # Validate skill directory
    skill_dir = Path(args.skill)
    if not skill_dir.is_absolute():
        skill_dir = PROJECT_DIR / skill_dir
    if not skill_dir.is_dir():
        print(
            json.dumps(
                {"status": "error", "message": f"Skill directory not found: {skill_dir}"}
            ),
            file=sys.stderr,
        )
        sys.exit(2)

    # Validate evals.json exists
    evals_path = skill_dir / "eval" / "evals.json"
    if not evals_path.exists():
        print(
            json.dumps(
                {
                    "status": "error",
                    "message": f"evals.json not found: {evals_path}",
                }
            ),
            file=sys.stderr,
        )
        sys.exit(2)

    # Validate runs
    if args.runs < 1:
        print(
            json.dumps({"status": "error", "message": "runs must be >= 1"}),
            file=sys.stderr,
        )
        sys.exit(2)

    # Determine worker count
    cpu_count = os.cpu_count() or 4
    workers = args.workers if args.workers else min(args.runs, cpu_count)
    workers = max(1, min(workers, args.runs))

    # Extract skill name from evals.json
    try:
        evals_data = json.loads(evals_path.read_text())
        skill_name = evals_data.get("skill", skill_dir.name)
    except (json.JSONDecodeError, OSError):
        skill_name = skill_dir.name

    # Run evals in parallel
    start_time = time.time()
    evals_path_str = str(evals_path)
    individual_runs = []
    errors = []

    try:
        with ProcessPoolExecutor(max_workers=workers) as executor:
            futures = [
                executor.submit(run_single_eval, evals_path_str)
                for _ in range(args.runs)
            ]
            for i, future in enumerate(futures):
                try:
                    result = future.result(timeout=TIMEOUT_SECONDS + 5)
                    individual_runs.append(result)
                    if result.get("status") == "error" and result.get("error"):
                        errors.append(f"Run {i + 1}: {result['error']}")
                except FuturesTimeoutError:
                    err_result = {
                        "status": "error",
                        "pass_rate": 0.0,
                        "error": "Future timed out",
                        "evaluations": [],
                    }
                    individual_runs.append(err_result)
                    errors.append(f"Run {i + 1}: timed out")
                except Exception as e:
                    err_result = {
                        "status": "error",
                        "pass_rate": 0.0,
                        "error": str(e),
                        "evaluations": [],
                    }
                    individual_runs.append(err_result)
                    errors.append(f"Run {i + 1}: {e}")
    except Exception as e:
        print(
            json.dumps({"status": "error", "message": f"Execution error: {e}"}),
            file=sys.stderr,
        )
        sys.exit(3)

    duration = round(time.time() - start_time, 1)

    # Extract pass rates (only from successful runs)
    pass_rates = [
        r.get("pass_rate", 0.0) for r in individual_runs if r.get("status") != "error"
    ]

    # If all runs errored, include zeros so stats still compute
    if not pass_rates:
        pass_rates = [0.0] * len(individual_runs)
        all_failed = True
    else:
        all_failed = False

    # Calculate statistics
    median_pass_rate = round(calc_median(pass_rates), 1)
    mean_pass_rate = round(sum(pass_rates) / len(pass_rates), 1) if pass_rates else 0.0
    min_pass_rate = round(min(pass_rates), 1) if pass_rates else 0.0
    max_pass_rate = round(max(pass_rates), 1) if pass_rates else 0.0
    std_dev = round(calc_std_dev(pass_rates, mean_pass_rate), 1)

    # Aggregate failure patterns
    failure_frequency = aggregate_failures(individual_runs, args.runs)

    # Build output
    output = {
        "status": "completed",
        "skill": skill_name,
        "runs": args.runs,
        "workers": workers,
        "pass_rates": [round(r, 1) for r in pass_rates],
        "median_pass_rate": median_pass_rate,
        "mean_pass_rate": mean_pass_rate,
        "min_pass_rate": min_pass_rate,
        "max_pass_rate": max_pass_rate,
        "std_dev": std_dev,
        "failure_frequency": failure_frequency,
        "individual_runs": individual_runs,
        "duration_seconds": duration,
    }

    if errors:
        output["errors"] = errors

    if args.json_output:
        print(json.dumps(output, indent=2))
    else:
        # Human-readable output
        print(f"\n  Parallel Eval \u2014 {skill_name} ({args.runs} runs, {workers} workers)\n")

        rates_str = "  ".join(f"{r}" for r in pass_rates)
        print(f"  Pass rates: {rates_str}")
        print(f"  Median:     {median_pass_rate}%")
        print(f"  Mean:       {mean_pass_rate}%")
        print(f"  Min:        {min_pass_rate}%")
        print(f"  Max:        {max_pass_rate}%")
        print(f"  Std Dev:    {std_dev}%")

        if failure_frequency:
            print(f"\n  Most common failures:")
            for atype, info in failure_frequency.items():
                print(f"    \"{atype}\" \u2014 failed in {info['count']}/{args.runs} runs")

        if args.verbose:
            print(f"\n  Per-run details:")
            for i, run in enumerate(individual_runs):
                status = run.get("status", "unknown")
                rate = run.get("pass_rate", 0.0)
                if status == "error":
                    print(f"    Run {i + 1}: ERROR - {run.get('error', 'unknown')}")
                else:
                    passed = run.get("total_passed", 0)
                    total = run.get("total_assertions", 0)
                    print(f"    Run {i + 1}: {rate}% ({passed}/{total} assertions)")

        if errors and not args.verbose:
            print(f"\n  Errors: {len(errors)} run(s) had errors (use --verbose for details)")

        print(f"\n  Reliability: {median_pass_rate}% (median pass rate)")
        print(f"  Duration:    {duration}s\n")

    # Exit code
    if all_failed:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()