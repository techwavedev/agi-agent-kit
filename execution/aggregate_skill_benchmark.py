#!/usr/bin/env python3
"""
Script: aggregate_skill_benchmark.py
Purpose: Runs a skill trigger evaluation N times to calculate statistical
         confidence, mean, and stddev of the trigger pass rate.
"""

import argparse
import json
import math
import subprocess
import sys
from pathlib import Path

def run_iteration(skill_path: str, queries_path: str, iteration: int) -> float:
    """Run `run_skill_trigger_eval.py` once and return the pass rate."""
    eval_script = Path(__file__).resolve().parent / "run_skill_trigger_eval.py"
    
    result = subprocess.run(
        [sys.executable, str(eval_script), "--skill", skill_path, "--queries", queries_path],
        capture_output=True,
        text=True
    )
    
    if result.returncode not in [0, 1]:
        print(f"Error in iteration {iteration}: {result.stderr}", file=sys.stderr)
        return -1.0
        
    try:
        data = json.loads(result.stdout)
        return data.get("pass_rate", -1.0)
    except json.JSONDecodeError:
        print(f"Invalid JSON from iteration {iteration}", file=sys.stderr)
        return -1.0

def calculate_stats(rates: list) -> dict:
    valid_rates = [r for r in rates if r >= 0]
    n = len(valid_rates)
    if n == 0:
        return {"n": 0, "mean": 0, "stddev": 0, "min": 0, "max": 0}
        
    mean = sum(valid_rates) / n
    variance = sum((r - mean) ** 2 for r in valid_rates) / n if n > 1 else 0.0
    stddev = math.sqrt(variance)
    
    return {
        "n": n,
        "mean": mean,
        "stddev": stddev,
        "min": min(valid_rates),
        "max": max(valid_rates)
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--skill", required=True, help="Path to skill to bench")
    parser.add_argument("--queries", required=True, help="Path to JSON queries list")
    parser.add_argument("--n", type=int, default=10, help="Number of iterations")
    parser.add_argument("--baseline", type=float, help="Previous baseline mean to compare against")
    args = parser.parse_args()

    print(f"Running {args.n} benchmark iterations...", file=sys.stderr)
    
    rates = []
    for i in range(args.n):
        rate = run_iteration(args.skill, args.queries, i + 1)
        if rate >= 0:
            rates.append(rate)
            print(f" - Iteration {i+1}: pass rate = {rate:.2f}", file=sys.stderr)
            
    stats = calculate_stats(rates)
    
    if args.baseline is not None:
        delta = stats["mean"] - args.baseline
        stats["baseline_delta"] = delta
        
        # Simple thresholding: is it a statistically meaningful regression?
        # A drop greater than 1 stddev might be a regression.
        if delta < 0 and abs(delta) > stats["stddev"]:
            stats["status"] = "regression"
        elif delta > 0 and delta > stats["stddev"]:
            stats["status"] = "improvement"
        else:
            stats["status"] = "neutral"
            
    # Try logging to Qdrant memory
    try:
        memory_mgr = Path(__file__).resolve().parent / "memory_manager.py"
        if memory_mgr.exists():
            content = f"Skill benchmark for {args.skill}: Mean={stats['mean']:.2f}, N={args.n}"
            subprocess.run([
                sys.executable, str(memory_mgr), "store",
                "--content", content,
                "--type", "technical",
                "--tags", "skill-eval-history", Path(args.skill).name
            ], capture_output=True)
    except Exception:
        pass
        
    print(json.dumps(stats, indent=2))
    
    if stats.get("status") == "regression":
        sys.exit(2)
        
    sys.exit(0)

if __name__ == "__main__":
    main()
