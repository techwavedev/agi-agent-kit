#!/usr/bin/env python3
"""
Script: god_mode.py
Purpose: AutoResearch God Mode — autonomous skill self-improvement orchestrator
         implementing Karpathy's generate->evaluate->select loop with compounding
         memory, parallel evaluation, and Telegram notifications.

Usage:
    # Run God Mode on a single skill
    python3 execution/god_mode.py run --skill skills/my-skill [--max-iterations 20] [--parallel-runs 10] [--notify]

    # Batch run on all skills
    python3 execution/god_mode.py batch --skills-dir skills/ [--parallel-skills 3] [--notify]

    # Show dashboard
    python3 execution/god_mode.py status [--skill skills/my-skill]

    # Get scheduling instructions
    python3 execution/god_mode.py schedule --interval 5m --skill skills/my-skill

Exit Codes:
    0 - Success (improvements made or perfect score)
    1 - No improvement / no skills found
    2 - Configuration error
    3 - Execution error
"""

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

# ─── Configuration ────────────────────────────────────────────────────────────

PROJECT_DIR = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
EXECUTION_DIR = PROJECT_DIR / "execution"
TMP_DIR = PROJECT_DIR / ".tmp"


# ─── Environment Loading ─────────────────────────────────────────────────────

def load_env() -> dict:
    """Load .env file manually (no dotenv dependency). Returns dict of key=value pairs."""
    env_vars = {}
    env_path = PROJECT_DIR / ".env"
    if not env_path.exists():
        return env_vars
    try:
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip().strip("'").strip('"')
                env_vars[key] = value
    except Exception:
        pass
    return env_vars


def get_env_var(name: str) -> str:
    """Get env var from os.environ first, then .env file."""
    val = os.environ.get(name)
    if val:
        return val
    return load_env().get(name, "")


# ─── Subprocess Helpers ──────────────────────────────────────────────────────

def run_script(script_name: str, args: list, timeout: int = 300, cwd: str = None) -> dict:
    """Run an execution/ script and return parsed result.

    Returns dict with keys: returncode, stdout, stderr, data (parsed JSON or None).
    """
    script_path = EXECUTION_DIR / script_name
    cmd = [sys.executable, str(script_path)] + args

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd or str(PROJECT_DIR),
        )
        data = None
        # Try to parse the last JSON object from stdout
        stdout = proc.stdout.strip()
        if stdout:
            # Some scripts output human text + JSON at the end
            for line in reversed(stdout.splitlines()):
                line = line.strip()
                if line.startswith("{"):
                    try:
                        data = json.loads(line)
                        break
                    except json.JSONDecodeError:
                        pass
            # Try full stdout as JSON
            if data is None:
                try:
                    data = json.loads(stdout)
                except json.JSONDecodeError:
                    pass

        return {
            "returncode": proc.returncode,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
            "data": data,
        }
    except subprocess.TimeoutExpired:
        return {
            "returncode": -1,
            "stdout": "",
            "stderr": f"Timeout after {timeout}s",
            "data": None,
        }
    except Exception as e:
        return {
            "returncode": -2,
            "stdout": "",
            "stderr": str(e),
            "data": None,
        }


def run_eval(evals_path: Path) -> dict:
    """Run skill eval and return structured result."""
    result = run_script("run_skill_eval.py", ["--evals", str(evals_path), "--json-only"])
    if result["data"]:
        return result["data"]
    return {
        "status": "error",
        "pass_rate": 0.0,
        "total_passed": 0,
        "total_assertions": 0,
        "error": result["stderr"] or "Failed to parse eval output",
    }


def run_parallel_eval(skill_path: Path, runs: int) -> dict:
    """Run parallel eval for statistical reliability."""
    result = run_script(
        "parallel_eval.py",
        ["--skill", str(skill_path), "--runs", str(runs), "--json"],
        timeout=600,
    )
    if result["data"]:
        return result["data"]
    # Fallback: run single eval if parallel_eval.py not available
    evals_path = skill_path / "eval" / "evals.json"
    if evals_path.exists():
        single = run_eval(evals_path)
        single["note"] = "parallel_eval.py unavailable, ran single eval"
        single["runs"] = 1
        return single
    return {
        "status": "error",
        "pass_rate": 0.0,
        "error": result["stderr"] or "parallel_eval.py failed",
    }


def run_karpathy_loop(skill_path: Path, max_iterations: int) -> dict:
    """Run the Karpathy Loop and return result."""
    result = run_script(
        "karpathy_loop.py",
        ["--skill", str(skill_path), "--max-iterations", str(max_iterations)],
        timeout=max_iterations * 30 + 60,
    )
    return {
        "returncode": result["returncode"],
        "data": result["data"],
        "stdout": result["stdout"],
        "stderr": result["stderr"],
    }


# ─── Resource File (Compounding Memory) ──────────────────────────────────────

def get_resource_path(skill_path: Path) -> Path:
    """Get the resource.md path for a skill."""
    return skill_path / "eval" / "resource.md"


def read_resource(skill_path: Path) -> str:
    """Read existing resource.md content."""
    path = get_resource_path(skill_path)
    if path.exists():
        return path.read_text()
    return ""


def append_resource_entry(skill_path: Path, entry: dict):
    """Prepend a new experiment entry to resource.md (newest first).

    entry keys: timestamp, baseline_rate, baseline_passed, baseline_total,
                challenger_rate, challenger_passed, challenger_total,
                result, hypothesis, failing_fixed, learnings
    """
    resource_path = get_resource_path(skill_path)
    resource_path.parent.mkdir(parents=True, exist_ok=True)

    skill_name = skill_path.name
    existing = ""
    header = f"# God Mode Resource — {skill_name}\n\n## Experiment Log\n"

    if resource_path.exists():
        existing = resource_path.read_text()
        # Strip header if present so we can re-add it
        if existing.startswith("# God Mode Resource"):
            # Find end of "## Experiment Log" line
            idx = existing.find("\n## Experiment Log\n")
            if idx >= 0:
                after_header = existing[idx + len("\n## Experiment Log\n"):]
                existing = after_header
            else:
                # Just strip the first header line
                existing = "\n".join(existing.split("\n")[2:])

    ts = entry.get("timestamp", datetime.now(timezone.utc).isoformat())
    baseline_rate = entry.get("baseline_rate", 0.0)
    baseline_passed = entry.get("baseline_passed", 0)
    baseline_total = entry.get("baseline_total", 0)
    challenger_rate = entry.get("challenger_rate", 0.0)
    challenger_passed = entry.get("challenger_passed", 0)
    challenger_total = entry.get("challenger_total", 0)
    result_label = entry.get("result", "UNKNOWN")
    hypothesis = entry.get("hypothesis", "N/A")
    failing_fixed = entry.get("failing_fixed", [])
    learnings = entry.get("learnings", "N/A")
    iterations = entry.get("iterations", 0)

    new_entry = f"""
### Run {ts}
- **Baseline:** {baseline_rate}% ({baseline_passed}/{baseline_total})
- **Challenger:** {challenger_rate}% ({challenger_passed}/{challenger_total})
- **Result:** {result_label}
- **Iterations used:** {iterations}
- **Hypothesis:** {hypothesis}
- **Failing criteria fixed:** {', '.join(failing_fixed) if failing_fixed else 'none'}
- **Learnings:** {learnings}
"""

    content = header + new_entry + existing
    resource_path.write_text(content)


# ─── Telegram Notification ───────────────────────────────────────────────────

def send_telegram(message: str) -> bool:
    """Send Telegram notification using urllib (no dependencies).

    Reads TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID from env.
    Returns True on success, False on failure (non-blocking).
    """
    bot_token = get_env_var("TELEGRAM_BOT_TOKEN")
    chat_id = get_env_var("TELEGRAM_CHAT_ID")

    if not bot_token or not chat_id:
        return False

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = json.dumps({
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown",
    }).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status == 200
    except (urllib.error.URLError, OSError):
        return False


def format_telegram_message(skill_name: str, baseline_rate: float,
                            final_rate: float, iterations: int,
                            max_iterations: int, winner: str,
                            hypothesis: str) -> str:
    """Format a concise Telegram notification message."""
    delta = final_rate - baseline_rate
    sign = "+" if delta >= 0 else ""
    emoji_result = "Winner" if delta > 0 else "No change"

    return (
        f"God Mode: {skill_name}\n"
        f"{baseline_rate}% -> {final_rate}% ({sign}{delta:.1f}%)\n"
        f"Iterations: {iterations}/{max_iterations}\n"
        f"Result: {emoji_result} — {winner}\n"
        f"Hypothesis: {hypothesis}"
    )


# ─── Skill Discovery ─────────────────────────────────────────────────────────

def discover_skills(skills_dir: Path) -> list:
    """Find all skill directories that have eval/evals.json."""
    skills = []
    if not skills_dir.exists():
        return skills

    for item in sorted(skills_dir.iterdir()):
        if item.is_dir():
            evals_path = item / "eval" / "evals.json"
            if evals_path.exists():
                skills.append(item)
    return skills


# ─── Qdrant Memory Storage ───────────────────────────────────────────────────

def store_to_memory(content: str, tags: list) -> dict:
    """Store result in Qdrant memory via memory_manager.py."""
    tag_str = " ".join(tags)
    result = run_script(
        "memory_manager.py",
        ["store", "--content", content, "--type", "decision", "--tags", tag_str],
        timeout=15,
    )
    return result.get("data") or {"status": "stored" if result["returncode"] == 0 else "error"}


# ─── Command: run ─────────────────────────────────────────────────────────────

def cmd_run(args) -> int:
    """Run God Mode on a single skill.

    Flow: HARVEST -> GENERATE -> EVALUATE -> LEARN -> NOTIFY
    """
    skill_path = Path(args.skill).resolve()
    evals_path = skill_path / "eval" / "evals.json"

    # Validate
    if not skill_path.exists():
        print(json.dumps({"status": "error", "message": f"Skill directory not found: {skill_path}"}),
              file=sys.stderr)
        return 2

    if not evals_path.exists():
        print(json.dumps({"status": "error", "message": f"No eval/evals.json at: {evals_path}",
                          "hint": "Create eval/evals.json with binary assertions first"}),
              file=sys.stderr)
        return 2

    skill_name = skill_path.name
    max_iterations = args.max_iterations
    parallel_runs = args.parallel_runs
    min_pass_rate = args.min_pass_rate
    notify = args.notify
    json_output = args.json

    ts_start = datetime.now(timezone.utc)

    if not json_output:
        print(f"\n{'='*60}")
        print(f"  GOD MODE: {skill_name}")
        print(f"  Max iterations: {max_iterations}  |  Parallel runs: {parallel_runs}")
        print(f"  Min pass rate target: {min_pass_rate}%")
        print(f"{'='*60}\n")

    # ─── PHASE 1: HARVEST (Baseline) ───────────────────────────────────────

    if not json_output:
        print("  [1/5] HARVEST — Checking current eval state...")

    baseline = run_eval(evals_path)
    baseline_rate = baseline.get("pass_rate", 0.0)
    baseline_passed = baseline.get("total_passed", 0)
    baseline_total = baseline.get("total_assertions", 0)

    if not json_output:
        print(f"         Baseline: {baseline_rate}% ({baseline_passed}/{baseline_total})")

    if baseline_rate >= 100.0:
        result = {
            "status": "perfect",
            "skill": skill_name,
            "pass_rate": 100.0,
            "message": "Already at perfect score. Nothing to improve.",
        }
        print(json.dumps(result, indent=2))
        return 0

    if baseline_rate >= min_pass_rate:
        if not json_output:
            print(f"         Already above min target ({min_pass_rate}%). Running anyway for improvement.")

    # Identify failing assertions for hypothesis tracking
    failing_names = []
    for evaluation in baseline.get("evaluations", []):
        for r in evaluation.get("results", []):
            if not r.get("passed", True):
                failing_names.append(r.get("assertion", "unknown"))

    # ─── PHASE 2: GENERATE (Karpathy Loop) ────────────────────────────────

    if not json_output:
        print(f"\n  [2/5] GENERATE — Running Karpathy Loop ({max_iterations} iterations)...")

    loop_result = run_karpathy_loop(skill_path, max_iterations)
    loop_data = loop_result.get("data") or {}

    loop_iterations = loop_data.get("iterations", 0)
    loop_improvements = loop_data.get("improvements", 0)
    loop_final_rate = loop_data.get("final_pass_rate", baseline_rate)

    if not json_output:
        print(f"         Completed: {loop_iterations} iterations, {loop_improvements} improvements")
        print(f"         Post-loop rate: {loop_final_rate}%")

    # ─── PHASE 3: EVALUATE (Parallel Statistical Eval) ────────────────────

    if not json_output:
        print(f"\n  [3/5] EVALUATE — Running parallel eval ({parallel_runs} runs)...")

    if parallel_runs > 1:
        eval_result = run_parallel_eval(skill_path, parallel_runs)
    else:
        eval_result = run_eval(evals_path)
        eval_result["runs"] = 1

    final_rate = eval_result.get("pass_rate", loop_final_rate)
    final_passed = eval_result.get("total_passed", 0)
    final_total = eval_result.get("total_assertions", baseline_total)

    if not json_output:
        runs_note = f" (over {eval_result.get('runs', 1)} runs)" if eval_result.get("runs", 1) > 1 else ""
        print(f"         Final rate: {final_rate}%{runs_note}")

    # ─── Determine outcome ─────────────────────────────────────────────────

    delta = final_rate - baseline_rate
    improved = delta > 0

    if final_rate >= 100.0:
        result_label = "PERFECT — all assertions pass"
        winner = "Challenger (perfect)"
    elif improved:
        result_label = f"WINNER — challenger improves by {delta:.1f}%"
        winner = f"Challenger (+{delta:.1f}%)"
    else:
        result_label = "REJECTED — no improvement over baseline"
        winner = "Baseline retained"

    # Identify which failing criteria were fixed
    post_eval = run_eval(evals_path)
    still_failing = []
    for evaluation in post_eval.get("evaluations", []):
        for r in evaluation.get("results", []):
            if not r.get("passed", True):
                still_failing.append(r.get("assertion", "unknown"))

    fixed = [f for f in failing_names if f not in still_failing]

    hypothesis = "Karpathy loop autonomous improvements"
    if loop_improvements > 0:
        hypothesis = f"Automated {loop_improvements} targeted changes via Karpathy loop"

    # ─── PHASE 4: LEARN (Store to Qdrant + Resource.md) ───────────────────

    if not json_output:
        print(f"\n  [4/5] LEARN — Storing results...")

    # Append to resource.md
    resource_entry = {
        "timestamp": ts_start.isoformat(),
        "baseline_rate": baseline_rate,
        "baseline_passed": baseline_passed,
        "baseline_total": baseline_total,
        "challenger_rate": final_rate,
        "challenger_passed": final_passed,
        "challenger_total": final_total,
        "result": result_label,
        "hypothesis": hypothesis,
        "failing_fixed": fixed,
        "learnings": f"{'Improved' if improved else 'No improvement'} after {loop_iterations} iterations. "
                     f"Fixed: {', '.join(fixed) if fixed else 'none'}. "
                     f"Still failing: {', '.join(still_failing) if still_failing else 'none'}.",
        "iterations": loop_iterations,
    }
    append_resource_entry(skill_path, resource_entry)

    if not json_output:
        print(f"         Resource.md updated at: {get_resource_path(skill_path)}")

    # Store to Qdrant
    memory_content = (
        f"God Mode run on {skill_name}: {baseline_rate}% -> {final_rate}% "
        f"({'+' if delta >= 0 else ''}{delta:.1f}%). "
        f"Iterations: {loop_iterations}. Improvements: {loop_improvements}. "
        f"Fixed: {', '.join(fixed) if fixed else 'none'}."
    )
    store_to_memory(memory_content, ["god-mode", "karpathy-loop", skill_name])

    if not json_output:
        print(f"         Qdrant memory stored.")

    # ─── PHASE 5: NOTIFY (Telegram) ───────────────────────────────────────

    if notify:
        if not json_output:
            print(f"\n  [5/5] NOTIFY — Sending Telegram notification...")

        telegram_msg = format_telegram_message(
            skill_name, baseline_rate, final_rate,
            loop_iterations, max_iterations, winner, hypothesis,
        )
        sent = send_telegram(telegram_msg)

        if not json_output:
            if sent:
                print(f"         Telegram notification sent.")
            else:
                print(f"         Telegram skipped (no credentials or send failed).")
    else:
        if not json_output:
            print(f"\n  [5/5] NOTIFY — Skipped (use --notify to enable)")

    # ─── Final Output ─────────────────────────────────────────────────────

    ts_end = datetime.now(timezone.utc)
    duration_s = (ts_end - ts_start).total_seconds()

    final_result = {
        "status": "improved" if improved else ("perfect" if final_rate >= 100.0 else "no_improvement"),
        "skill": skill_name,
        "baseline_pass_rate": baseline_rate,
        "final_pass_rate": final_rate,
        "delta": round(delta, 1),
        "iterations_used": loop_iterations,
        "iterations_max": max_iterations,
        "improvements_committed": loop_improvements,
        "assertions_fixed": fixed,
        "assertions_still_failing": still_failing,
        "parallel_runs": eval_result.get("runs", 1),
        "duration_seconds": round(duration_s, 1),
        "resource_file": str(get_resource_path(skill_path)),
        "winner": winner,
    }

    if not json_output:
        print(f"\n{'='*60}")
        print(f"  RESULT: {baseline_rate}% -> {final_rate}% ({'+' if delta >= 0 else ''}{delta:.1f}%)")
        print(f"  Winner: {winner}")
        print(f"  Duration: {duration_s:.1f}s")
        print(f"  Fixed: {', '.join(fixed) if fixed else 'none'}")
        if still_failing:
            print(f"  Still failing: {', '.join(still_failing)}")
        print(f"{'='*60}\n")

    print(json.dumps(final_result, indent=2))

    if final_rate >= 100.0:
        return 0
    return 0 if improved else 1


# ─── Command: batch ───────────────────────────────────────────────────────────

def cmd_batch(args) -> int:
    """Run God Mode on all skills with evals.

    Discovers skills, optionally runs them in parallel using worktree isolation.
    """
    skills_dir = Path(args.skills_dir).resolve()
    max_iterations = args.max_iterations
    parallel_skills = args.parallel_skills
    notify = args.notify
    json_output = args.json

    if not skills_dir.exists():
        print(json.dumps({"status": "error", "message": f"Skills directory not found: {skills_dir}"}),
              file=sys.stderr)
        return 2

    skills = discover_skills(skills_dir)
    if not skills:
        print(json.dumps({"status": "error", "message": f"No skills with eval/evals.json found in {skills_dir}"}),
              file=sys.stderr)
        return 1

    if not json_output:
        print(f"\n{'='*60}")
        print(f"  GOD MODE BATCH")
        print(f"  Skills found: {len(skills)}")
        print(f"  Parallel: {parallel_skills}  |  Max iterations per skill: {max_iterations}")
        print(f"{'='*60}\n")
        for i, s in enumerate(skills, 1):
            print(f"  {i:3d}. {s.name}")
        print()

    ts_start = datetime.now(timezone.utc)
    results = []

    if parallel_skills <= 1:
        # Sequential mode — run each skill directly
        for i, skill_path in enumerate(skills, 1):
            if not json_output:
                print(f"\n  [{i}/{len(skills)}] Running: {skill_path.name}")
                print(f"  {'-'*56}")

            skill_result = _run_single_skill(skill_path, max_iterations, args)
            results.append(skill_result)

            if not json_output:
                rate = skill_result.get("final_pass_rate", 0)
                delta = skill_result.get("delta", 0)
                sign = "+" if delta >= 0 else ""
                print(f"  -> {skill_path.name}: {rate}% ({sign}{delta:.1f}%)")
    else:
        # Parallel mode — use worktree isolation
        if not json_output:
            print(f"  Running {parallel_skills} skills in parallel with worktree isolation...")

        run_id = f"godmode-{int(time.time())}"
        results = _run_parallel_batch(skills, max_iterations, parallel_skills, run_id, args)

    # ─── Aggregate Results ─────────────────────────────────────────────────

    ts_end = datetime.now(timezone.utc)
    duration_s = (ts_end - ts_start).total_seconds()

    improved_count = sum(1 for r in results if r.get("delta", 0) > 0)
    perfect_count = sum(1 for r in results if r.get("final_pass_rate", 0) >= 100.0)
    total_delta = sum(r.get("delta", 0) for r in results)

    aggregate = {
        "status": "completed",
        "total_skills": len(skills),
        "skills_improved": improved_count,
        "skills_perfect": perfect_count,
        "skills_unchanged": len(results) - improved_count,
        "average_delta": round(total_delta / max(len(results), 1), 1),
        "duration_seconds": round(duration_s, 1),
        "results": results,
    }

    if not json_output:
        print(f"\n{'='*60}")
        print(f"  BATCH RESULTS")
        print(f"  Skills processed: {len(results)}/{len(skills)}")
        print(f"  Improved: {improved_count}  |  Perfect: {perfect_count}  |  Unchanged: {len(results) - improved_count}")
        print(f"  Average delta: {'+' if total_delta >= 0 else ''}{aggregate['average_delta']}%")
        print(f"  Duration: {duration_s:.1f}s")
        print(f"{'='*60}\n")

        # Per-skill summary table
        print(f"  {'Skill':<30s} {'Before':>8s} {'After':>8s} {'Delta':>8s} {'Status':>10s}")
        print(f"  {'-'*30} {'-'*8} {'-'*8} {'-'*8} {'-'*10}")
        for r in results:
            name = r.get("skill", "unknown")[:30]
            before = r.get("baseline_pass_rate", 0)
            after = r.get("final_pass_rate", 0)
            delta = r.get("delta", 0)
            sign = "+" if delta >= 0 else ""
            status = "PERFECT" if after >= 100 else ("UP" if delta > 0 else "---")
            print(f"  {name:<30s} {before:>7.1f}% {after:>7.1f}% {sign}{delta:>6.1f}% {status:>10s}")
        print()

    # Store aggregate to Qdrant
    memory_content = (
        f"God Mode batch: {len(skills)} skills processed. "
        f"{improved_count} improved, {perfect_count} perfect, "
        f"avg delta {aggregate['average_delta']}%."
    )
    store_to_memory(memory_content, ["god-mode", "batch", "aggregate"])

    # Telegram notification for batch
    if notify:
        batch_msg = (
            f"God Mode Batch Complete\n"
            f"Skills: {len(results)}/{len(skills)}\n"
            f"Improved: {improved_count} | Perfect: {perfect_count}\n"
            f"Avg delta: {'+' if total_delta >= 0 else ''}{aggregate['average_delta']}%\n"
            f"Duration: {duration_s:.0f}s"
        )
        send_telegram(batch_msg)

    print(json.dumps(aggregate, indent=2))
    return 0 if improved_count > 0 or perfect_count > 0 else 1


def _run_single_skill(skill_path: Path, max_iterations: int, args) -> dict:
    """Run God Mode on a single skill and return result dict (for batch use)."""
    evals_path = skill_path / "eval" / "evals.json"
    skill_name = skill_path.name

    # Baseline
    baseline = run_eval(evals_path)
    baseline_rate = baseline.get("pass_rate", 0.0)
    baseline_passed = baseline.get("total_passed", 0)
    baseline_total = baseline.get("total_assertions", 0)

    if baseline_rate >= 100.0:
        return {
            "skill": skill_name,
            "baseline_pass_rate": 100.0,
            "final_pass_rate": 100.0,
            "delta": 0.0,
            "status": "perfect",
            "iterations_used": 0,
        }

    # Karpathy loop
    loop_result = run_karpathy_loop(skill_path, max_iterations)
    loop_data = loop_result.get("data") or {}

    # Post-loop eval
    post_eval = run_eval(evals_path)
    final_rate = post_eval.get("pass_rate", baseline_rate)
    delta = final_rate - baseline_rate

    # Resource.md
    resource_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "baseline_rate": baseline_rate,
        "baseline_passed": baseline_passed,
        "baseline_total": baseline_total,
        "challenger_rate": final_rate,
        "challenger_passed": post_eval.get("total_passed", 0),
        "challenger_total": post_eval.get("total_assertions", baseline_total),
        "result": "WINNER" if delta > 0 else "REJECTED",
        "hypothesis": f"Batch Karpathy loop ({max_iterations} max iterations)",
        "failing_fixed": [],
        "learnings": f"{'Improved' if delta > 0 else 'No improvement'} ({'+' if delta >= 0 else ''}{delta:.1f}%)",
        "iterations": loop_data.get("iterations", 0),
    }
    append_resource_entry(skill_path, resource_entry)

    return {
        "skill": skill_name,
        "baseline_pass_rate": baseline_rate,
        "final_pass_rate": final_rate,
        "delta": round(delta, 1),
        "status": "improved" if delta > 0 else ("perfect" if final_rate >= 100 else "no_improvement"),
        "iterations_used": loop_data.get("iterations", 0),
        "improvements_committed": loop_data.get("improvements", 0),
    }


def _run_parallel_batch(skills: list, max_iterations: int, parallel_skills: int,
                        run_id: str, args) -> list:
    """Run skills in parallel using worktree isolation.

    Creates a worktree per skill, runs god_mode.py run inside each,
    merges results back.
    """
    results = []
    worktree_agents = []

    # Create worktrees for each skill
    for i, skill_path in enumerate(skills):
        agent_name = f"godmode-{skill_path.name}"
        worktree_agents.append((skill_path, agent_name))

    def process_skill(skill_path: Path, agent_name: str) -> dict:
        """Process a single skill in its own worktree."""
        # Create worktree
        create_result = run_script(
            "worktree_isolator.py",
            ["create", "--agent", agent_name, "--run-id", run_id],
        )

        if create_result["returncode"] != 0:
            # Fallback: run in main tree
            return _run_single_skill(skill_path, max_iterations, args)

        create_data = create_result.get("data") or {}
        worktree_path = create_data.get("worktree_path")

        if not worktree_path or not Path(worktree_path).exists():
            return _run_single_skill(skill_path, max_iterations, args)

        try:
            # Determine relative skill path within project
            try:
                rel_skill = skill_path.relative_to(PROJECT_DIR)
            except ValueError:
                rel_skill = Path("skills") / skill_path.name

            wt_skill_path = Path(worktree_path) / rel_skill

            if not (wt_skill_path / "eval" / "evals.json").exists():
                return _run_single_skill(skill_path, max_iterations, args)

            # Run god_mode.py run in worktree
            cmd = [
                sys.executable, str(EXECUTION_DIR / "god_mode.py"),
                "run",
                "--skill", str(wt_skill_path),
                "--max-iterations", str(max_iterations),
                "--json",
            ]
            proc = subprocess.run(
                cmd, capture_output=True, text=True,
                timeout=max_iterations * 30 + 120,
                cwd=worktree_path,
            )

            # Parse result
            data = None
            if proc.stdout.strip():
                for line in reversed(proc.stdout.strip().splitlines()):
                    line = line.strip()
                    if line.startswith("{"):
                        try:
                            data = json.loads(line)
                            break
                        except json.JSONDecodeError:
                            pass

            if data:
                # Merge worktree back
                run_script(
                    "worktree_isolator.py",
                    ["merge", "--agent", agent_name, "--run-id", run_id],
                )
                return data

            return _run_single_skill(skill_path, max_iterations, args)

        finally:
            # Cleanup worktree
            run_script(
                "worktree_isolator.py",
                ["cleanup", "--agent", agent_name, "--run-id", run_id],
            )

    # Run in thread pool
    with ThreadPoolExecutor(max_workers=parallel_skills) as executor:
        futures = {}
        for skill_path, agent_name in worktree_agents:
            future = executor.submit(process_skill, skill_path, agent_name)
            futures[future] = skill_path.name

        for future in as_completed(futures):
            skill_name = futures[future]
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                results.append({
                    "skill": skill_name,
                    "status": "error",
                    "error": str(e),
                    "baseline_pass_rate": 0.0,
                    "final_pass_rate": 0.0,
                    "delta": 0.0,
                })

    return results


# ─── Command: status ──────────────────────────────────────────────────────────

def cmd_status(args) -> int:
    """Show God Mode dashboard for one or all skills."""
    json_output = args.json

    if args.skill:
        # Single skill status
        return _status_single(Path(args.skill).resolve(), json_output)
    else:
        # Scan all skills
        skills_dir = PROJECT_DIR / "skills"
        if not skills_dir.exists():
            print(json.dumps({"status": "error", "message": "skills/ directory not found"}),
                  file=sys.stderr)
            return 2

        skills = discover_skills(skills_dir)
        if not skills:
            print(json.dumps({"status": "error", "message": "No skills with evals found"}),
                  file=sys.stderr)
            return 1

        all_statuses = []
        for skill_path in skills:
            status = _get_skill_status(skill_path)
            all_statuses.append(status)

        if json_output:
            print(json.dumps({"skills": all_statuses}, indent=2))
        else:
            print(f"\n{'='*60}")
            print(f"  GOD MODE DASHBOARD")
            print(f"  Skills with evals: {len(skills)}")
            print(f"{'='*60}\n")

            print(f"  {'Skill':<30s} {'Pass Rate':>10s} {'Experiments':>12s} {'Last Run':>20s}")
            print(f"  {'-'*30} {'-'*10} {'-'*12} {'-'*20}")

            for s in all_statuses:
                name = s["skill"][:30]
                rate = f"{s['pass_rate']:.1f}%"
                experiments = str(s["experiment_count"])
                last_run = s.get("last_run", "never")
                if last_run != "never" and len(last_run) > 20:
                    last_run = last_run[:19]
                print(f"  {name:<30s} {rate:>10s} {experiments:>12s} {last_run:>20s}")

            perfect = sum(1 for s in all_statuses if s["pass_rate"] >= 100.0)
            avg_rate = sum(s["pass_rate"] for s in all_statuses) / max(len(all_statuses), 1)
            print(f"\n  Perfect: {perfect}/{len(all_statuses)}  |  Average: {avg_rate:.1f}%\n")

        return 0


def _status_single(skill_path: Path, json_output: bool) -> int:
    """Show detailed status for a single skill."""
    evals_path = skill_path / "eval" / "evals.json"
    if not evals_path.exists():
        print(json.dumps({"status": "error", "message": f"No evals at {evals_path}"}),
              file=sys.stderr)
        return 2

    status = _get_skill_status(skill_path)

    # Run current eval for detail
    eval_result = run_eval(evals_path)
    status["evaluations"] = eval_result.get("evaluations", [])

    # Read resource.md
    resource_content = read_resource(skill_path)
    if resource_content:
        status["resource_preview"] = resource_content[:2000]

    if json_output:
        print(json.dumps(status, indent=2))
    else:
        print(f"\n{'='*60}")
        print(f"  GOD MODE STATUS: {status['skill']}")
        print(f"{'='*60}\n")

        print(f"  Pass rate:    {status['pass_rate']:.1f}% ({eval_result.get('total_passed', 0)}/{eval_result.get('total_assertions', 0)})")
        print(f"  Experiments:  {status['experiment_count']}")
        print(f"  Last run:     {status.get('last_run', 'never')}")
        print(f"  Resource:     {get_resource_path(skill_path)}")

        # Show failing assertions
        failing = []
        for evaluation in eval_result.get("evaluations", []):
            for r in evaluation.get("results", []):
                if not r.get("passed", True):
                    failing.append(f"[{evaluation.get('name', '?')}] {r.get('assertion', '?')}: {r.get('detail', '')}")

        if failing:
            print(f"\n  Failing assertions ({len(failing)}):")
            for f in failing:
                print(f"    - {f}")

        if resource_content:
            # Show last 3 experiment entries
            lines = resource_content.split("\n### Run ")
            entries = lines[1:4] if len(lines) > 1 else []
            if entries:
                print(f"\n  Recent experiments:")
                for entry in entries:
                    first_lines = entry.strip().split("\n")[:4]
                    print(f"\n    ### Run {first_lines[0]}")
                    for line in first_lines[1:]:
                        print(f"    {line}")

        print()

    return 0


def _get_skill_status(skill_path: Path) -> dict:
    """Get status summary for a skill."""
    evals_path = skill_path / "eval" / "evals.json"
    eval_result = run_eval(evals_path)

    # Count experiments from resource.md
    resource_content = read_resource(skill_path)
    experiment_count = resource_content.count("### Run ") if resource_content else 0

    # Extract last run timestamp
    last_run = "never"
    if resource_content and "### Run " in resource_content:
        # Find first "### Run <timestamp>" (newest, since we prepend)
        import re
        match = re.search(r"### Run (\S+)", resource_content)
        if match:
            last_run = match.group(1)

    return {
        "skill": skill_path.name,
        "path": str(skill_path),
        "pass_rate": eval_result.get("pass_rate", 0.0),
        "total_passed": eval_result.get("total_passed", 0),
        "total_assertions": eval_result.get("total_assertions", 0),
        "experiment_count": experiment_count,
        "last_run": last_run,
    }


# ─── Command: schedule ────────────────────────────────────────────────────────

def cmd_schedule(args) -> int:
    """Output scheduling instructions for /loop or crontab."""
    skill = args.skill
    interval = args.interval
    max_iterations = args.max_iterations
    json_output = args.json

    # Parse interval to seconds for cron calculation
    interval_seconds = _parse_interval(interval)
    if interval_seconds is None:
        print(json.dumps({"status": "error", "message": f"Invalid interval: {interval}. Use formats like 5m, 1h, 30s"}),
              file=sys.stderr)
        return 2

    god_mode_cmd = f"python3 {EXECUTION_DIR / 'god_mode.py'} run --skill {skill} --max-iterations {max_iterations} --json"

    # Build loop command
    loop_cmd = f"/loop {interval} {god_mode_cmd}"

    # Build crontab entry
    cron_expr = _seconds_to_cron(interval_seconds)
    cron_entry = f"{cron_expr} cd {PROJECT_DIR} && {god_mode_cmd} >> .tmp/god_mode.log 2>&1"

    # Build launchd plist name
    plist_label = f"com.agi.godmode.{Path(skill).name}"

    result = {
        "skill": skill,
        "interval": interval,
        "interval_seconds": interval_seconds,
        "commands": {
            "loop": loop_cmd,
            "crontab": cron_entry,
            "manual": god_mode_cmd,
        },
    }

    if json_output:
        print(json.dumps(result, indent=2))
    else:
        print(f"\n{'='*60}")
        print(f"  GOD MODE SCHEDULING: {Path(skill).name}")
        print(f"  Interval: {interval} ({interval_seconds}s)")
        print(f"{'='*60}\n")

        print(f"  Option 1: Claude /loop (recommended)")
        print(f"  ──────────────────────────────────────")
        print(f"  {loop_cmd}\n")

        print(f"  Option 2: Crontab")
        print(f"  ──────────────────────────────────────")
        print(f"  crontab -e")
        print(f"  {cron_entry}\n")

        print(f"  Option 3: Manual one-shot")
        print(f"  ──────────────────────────────────────")
        print(f"  {god_mode_cmd}\n")

        print(f"  Option 4: Watch mode (terminal)")
        print(f"  ──────────────────────────────────────")
        print(f"  watch -n {interval_seconds} '{god_mode_cmd}'\n")

    return 0


def _parse_interval(interval: str) -> int:
    """Parse interval string like '5m', '1h', '30s' to seconds."""
    import re
    match = re.match(r"^(\d+)(s|m|h|d)?$", interval.strip().lower())
    if not match:
        return None

    value = int(match.group(1))
    unit = match.group(2) or "s"

    multipliers = {"s": 1, "m": 60, "h": 3600, "d": 86400}
    return value * multipliers.get(unit, 1)


def _seconds_to_cron(seconds: int) -> str:
    """Convert seconds to a reasonable cron expression."""
    if seconds < 60:
        return "* * * * *"  # Every minute (cron min granularity)
    elif seconds < 3600:
        minutes = max(1, seconds // 60)
        return f"*/{minutes} * * * *"
    elif seconds < 86400:
        hours = max(1, seconds // 3600)
        return f"0 */{hours} * * *"
    else:
        days = max(1, seconds // 86400)
        return f"0 0 */{days} * *"


# ─── CLI Entry Point ─────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="God Mode: AutoResearch orchestrator for autonomous skill self-improvement",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Subcommands:
  run       Run God Mode on a single skill (harvest -> generate -> evaluate -> learn -> notify)
  batch     Run God Mode on all skills with evals
  status    Show God Mode dashboard (pass rates, experiments, history)
  schedule  Output scheduling instructions for /loop or crontab

Examples:
  python3 execution/god_mode.py run --skill skills/my-skill --max-iterations 20 --notify
  python3 execution/god_mode.py batch --skills-dir skills/ --parallel-skills 3
  python3 execution/god_mode.py status
  python3 execution/god_mode.py schedule --interval 5m --skill skills/my-skill
        """,
    )
    sub = parser.add_subparsers(dest="command")

    # ─── run ───────────────────────────────────────────────────────────────

    p_run = sub.add_parser("run", help="Run God Mode on a single skill")
    p_run.add_argument("--skill", required=True, help="Path to skill directory")
    p_run.add_argument("--max-iterations", type=int, default=20,
                       help="Maximum Karpathy Loop iterations (default: 20)")
    p_run.add_argument("--parallel-runs", type=int, default=10,
                       help="Number of parallel eval runs for statistical reliability (default: 10)")
    p_run.add_argument("--min-pass-rate", type=float, default=95.0,
                       help="Minimum pass rate target (default: 95.0)")
    p_run.add_argument("--notify", action="store_true",
                       help="Send Telegram notification on completion")
    p_run.add_argument("--json", action="store_true",
                       help="JSON-only output (suppress human-readable text)")

    # ─── batch ─────────────────────────────────────────────────────────────

    p_batch = sub.add_parser("batch", help="Run God Mode on all skills with evals")
    p_batch.add_argument("--skills-dir", default="skills/",
                         help="Directory containing skills (default: skills/)")
    p_batch.add_argument("--max-iterations", type=int, default=10,
                         help="Max iterations per skill (default: 10)")
    p_batch.add_argument("--parallel-skills", type=int, default=1,
                         help="Number of skills to process in parallel (default: 1, sequential)")
    p_batch.add_argument("--notify", action="store_true",
                         help="Send Telegram notification on completion")
    p_batch.add_argument("--json", action="store_true",
                         help="JSON-only output")

    # ─── status ────────────────────────────────────────────────────────────

    p_status = sub.add_parser("status", help="Show God Mode dashboard")
    p_status.add_argument("--skill", help="Show detailed status for a specific skill")
    p_status.add_argument("--json", action="store_true",
                          help="JSON-only output")

    # ─── schedule ──────────────────────────────────────────────────────────

    p_schedule = sub.add_parser("schedule", help="Output scheduling instructions")
    p_schedule.add_argument("--interval", required=True,
                            help="Run interval (e.g., 5m, 1h, 30s)")
    p_schedule.add_argument("--skill", required=True,
                            help="Skill path to schedule")
    p_schedule.add_argument("--max-iterations", type=int, default=20,
                            help="Max iterations per run (default: 20)")
    p_schedule.add_argument("--json", action="store_true",
                            help="JSON-only output")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(2)

    commands = {
        "run": cmd_run,
        "batch": cmd_batch,
        "status": cmd_status,
        "schedule": cmd_schedule,
    }

    try:
        exit_code = commands[args.command](args)
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print(json.dumps({"status": "interrupted"}), file=sys.stderr)
        sys.exit(3)
    except Exception as e:
        print(json.dumps({"status": "error", "type": type(e).__name__, "message": str(e)}),
              file=sys.stderr)
        sys.exit(3)


if __name__ == "__main__":
    main()