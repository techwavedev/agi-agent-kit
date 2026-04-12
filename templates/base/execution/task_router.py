#!/usr/bin/env python3
"""
Script: task_router.py
Purpose: Intelligent task router that classifies tasks and decides whether to
         execute them on a local model (Ollama/Gemma4) or delegate to a cloud
         model (Claude/Gemini). Security-first: tasks touching secrets, tokens,
         or credentials ALWAYS stay local. Cost-aware: small deterministic tasks
         go local to save cloud tokens.

Usage:
    # Classify a single task (returns routing decision)
    python3 execution/task_router.py classify --task "Read .env and extract the DB password"

    # Route and execute a task (runs local or returns cloud delegation)
    python3 execution/task_router.py route --task "Summarize this error log" --input-file error.log

    # Split a complex task into routable subtasks
    python3 execution/task_router.py split --task "Read the .env, extract API keys, then build a config summary"

    # Batch: classify multiple tasks from a JSON file
    python3 execution/task_router.py batch --tasks-file tasks.json

    # Show routing stats
    python3 execution/task_router.py stats

Exit Codes:
    0 - Success
    1 - Invalid arguments
    2 - Ollama unavailable (for local-only tasks, fatal)
    3 - Processing error
    4 - Security violation (attempted to send secrets to cloud)
"""

import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path

# ---------------------------------------------------------------------------
# Security patterns: tasks matching these MUST run locally, never cloud
# ---------------------------------------------------------------------------
SECURITY_PATTERNS = [
    # Secrets and credentials
    r"\.env\b", r"\.env\.\w+", r"credentials?\b", r"secret[s_]?\b",
    r"api[_\s-]?key", r"token[s]?\b", r"password[s]?\b", r"passwd\b",
    r"private[_\s-]?key", r"auth[_\s-]?(token|key|secret|code)",
    r"bearer\b", r"oauth\b", r"jwt\b", r"session[_\s-]?(id|token|key)",
    r"cookie[s]?\b", r"webhook[_\s-]?secret",
    # File patterns that contain secrets
    r"\.pem\b", r"\.key\b", r"\.p12\b", r"\.pfx\b", r"\.jks\b",
    r"id_rsa\b", r"id_ed25519\b", r"known_hosts\b",
    r"keystore\b", r"truststore\b",
    # Cloud provider secrets
    r"aws[_\s-]?(access|secret)", r"gcp[_\s-]?(key|credentials)",
    r"azure[_\s-]?(key|secret|tenant)", r"stripe[_\s-]?(key|secret)",
    r"twilio[_\s-]?(sid|token)", r"sendgrid[_\s-]?key",
    # Database connection strings
    r"connection[_\s-]?string", r"database[_\s-]?url",
    r"redis[_\s-]?url", r"mongo[_\s-]?uri",
    # Encryption
    r"encrypt", r"decrypt", r"hash[_\s-]?password", r"bcrypt\b",
    r"argon2\b", r"salt[_\s-]?(value|key)", r"cipher\b",
    # Sensitive operations
    r"redact\b", r"mask[_\s-]?(secret|token|key|password)",
    r"sanitize[_\s-]?(secret|credential|env)",
    r"rotate[_\s-]?(key|secret|token)", r"revoke[_\s-]?(token|key)",
]

# Compiled for performance
_SECURITY_RE = re.compile("|".join(SECURITY_PATTERNS), re.IGNORECASE)

# ---------------------------------------------------------------------------
# Task complexity signals: tasks matching these need cloud models
# ---------------------------------------------------------------------------
CLOUD_PATTERNS = [
    # Complex reasoning
    r"architect(ure)?\b", r"design\b.*\b(system|api|schema|database|architecture|service|module)\b",
    r"refactor\b", r"review\s+(code|pr|pull\s+request)",
    r"debug\s+(complex|race|concurrency|memory)",
    r"write\s+(a\s+)?(full|complete|comprehensive)",
    r"implement\s+(feature|system|service|module)",
    r"optimize\s+(algorithm|performance|query)",
    # Multi-file operations
    r"across\s+(all|multiple|every)\s+files?",
    r"entire\s+(codebase|project|repo)",
    r"search\s+and\s+replace\s+everywhere",
    # Creative / judgment tasks
    r"(best|better|optimal)\s+(approach|way|strategy|pattern)",
    r"trade.?off", r"pros?\s+and\s+cons?",
    r"(should\s+I|which\s+is\s+better)",
    # Long-form generation
    r"write\s+(documentation|readme|guide|tutorial)",
    r"(detailed|thorough|comprehensive)\s+(analysis|review|report)",
    r"create\s+(a\s+)?(plan|strategy|roadmap)",
]

_CLOUD_RE = re.compile("|".join(CLOUD_PATTERNS), re.IGNORECASE)

# ---------------------------------------------------------------------------
# Local-friendly patterns: small deterministic tasks
# ---------------------------------------------------------------------------
LOCAL_PATTERNS = [
    r"summarize\b", r"classify\b", r"extract\b", r"parse\b",
    r"list\s+(all|the|every)", r"count\b", r"format\b", r"convert\b",
    r"rename\b", r"sort\b", r"filter\b", r"validate\b", r"lint\b",
    r"check\s+syntax", r"find\s+(error|typo|issue)s?\b",
    r"generate\s+(filename|slug|id|uuid|title|label)",
    r"(camel|snake|kebab|pascal)[_\s-]?case",
    r"(commit|changelog)\s+(message|entry)",
    r"(one[_\s-]?liner|tl;?dr|brief|short)\b",
    r"(json|yaml|toml|csv)\s+(schema|to|from|convert|parse|validate)",
    r"regex\b", r"glob\s+pattern",
    r"strip\b", r"trim\b", r"clean\b", r"normalize\b",
    r"(split|join|merge)\s+(string|text|line|array)",
    r"(hello|ping|test|echo)\b",
]

_LOCAL_RE = re.compile("|".join(LOCAL_PATTERNS), re.IGNORECASE)

# ---------------------------------------------------------------------------
# Stats file for tracking routing decisions
# ---------------------------------------------------------------------------
STATS_FILE = Path(__file__).resolve().parent.parent / ".tmp" / "task_router_stats.json"


def classify_task(task: str, context: str = "") -> dict:
    """Classify a task and return routing decision.

    Returns:
        {
            "route": "local" | "cloud" | "local_required",
            "reason": str,
            "security_flags": [str],
            "complexity": "low" | "medium" | "high",
            "suggested_model": str,
            "confidence": float (0-1),
        }
    """
    combined = f"{task} {context}"
    security_flags = []
    route = "cloud"  # Default: cloud (safer for quality)
    reason = ""
    complexity = "medium"
    confidence = 0.5

    # STEP 1: Security check (highest priority — overrides everything)
    security_matches = _SECURITY_RE.finditer(combined)
    security_hits = [m.group().lower() for m in security_matches]
    if security_hits:
        security_flags = list(set(security_hits))
        route = "local_required"
        reason = f"Security: task references sensitive data ({', '.join(security_flags[:3])}). Must stay local."
        complexity = "low"  # Security tasks are usually simple extraction/masking
        confidence = 0.95
        return {
            "route": route,
            "reason": reason,
            "security_flags": security_flags,
            "complexity": complexity,
            "suggested_model": "gemma4:e4b",
            "confidence": confidence,
        }

    # STEP 2: Check if task is explicitly complex (needs cloud)
    cloud_match = _CLOUD_RE.search(combined)
    if cloud_match:
        route = "cloud"
        reason = f"Complex task requiring reasoning/judgment: {cloud_match.group()}"
        complexity = "high"
        confidence = 0.8
        return {
            "route": route,
            "reason": reason,
            "security_flags": [],
            "complexity": complexity,
            "suggested_model": "claude-opus-4-6",
            "confidence": confidence,
        }

    # STEP 3: Check if task is small/deterministic (go local)
    local_match = _LOCAL_RE.search(combined)
    if local_match:
        route = "local"
        reason = f"Small deterministic task: {local_match.group()}"
        complexity = "low"
        confidence = 0.85

        # If context is very large, might need cloud for better handling
        if len(context) > 10000:
            route = "cloud"
            reason += " (but context too large for local model)"
            confidence = 0.6

        return {
            "route": route,
            "reason": reason,
            "security_flags": [],
            "complexity": complexity,
            "suggested_model": "gemma4:e4b" if route == "local" else "claude-sonnet-4-6",
            "confidence": confidence,
        }

    # STEP 4: Heuristic fallback — estimate by task length and keywords
    word_count = len(task.split())
    if word_count <= 15:
        route = "local"
        reason = "Short task, likely simple"
        complexity = "low"
        confidence = 0.6
    else:
        route = "cloud"
        reason = "Task appears to need deeper reasoning"
        complexity = "medium"
        confidence = 0.5

    suggested = "gemma4:e4b" if route == "local" else "claude-sonnet-4-6"

    return {
        "route": route,
        "reason": reason,
        "security_flags": [],
        "complexity": complexity,
        "suggested_model": suggested,
        "confidence": confidence,
    }


def split_task(task: str) -> list:
    """Split a compound task into independent subtasks for parallel routing.

    Uses simple heuristics (sentence splitting, conjunction detection).
    For complex splitting, delegate to a local model.
    """
    # First try numbered steps
    numbered = re.split(r"(?:\d+[\.\)]\s*)", task)
    numbered = [s.strip() for s in numbered if s.strip() and len(s.strip()) > 5]
    if len(numbered) > 1:
        return _classify_subtasks(numbered)

    # Then try conjunction splitting
    parts = re.split(r"\b(?:then|after that|next|finally|and then|followed by)\b", task, flags=re.IGNORECASE)
    parts = [s.strip().rstrip(",. ") for s in parts if s.strip() and len(s.strip()) > 5]
    if len(parts) > 1:
        return _classify_subtasks(parts)

    # Then try sentence splitting
    sentences = re.split(r"\.\s+(?=[A-Z])", task)
    sentences = [s.strip().rstrip(".") for s in sentences if s.strip() and len(s.strip()) > 5]
    if len(sentences) > 1:
        return _classify_subtasks(sentences)

    # Can't split — return as single task
    return _classify_subtasks([task])


def _classify_subtasks(parts: list) -> list:
    """Classify each subtask independently."""
    subtasks = []
    for i, part in enumerate(parts):
        classification = classify_task(part)
        subtasks.append({
            "step": i + 1,
            "task": part,
            "route": classification["route"],
            "reason": classification["reason"],
            "security_flags": classification["security_flags"],
            "suggested_model": classification["suggested_model"],
        })
    return subtasks


def route_and_execute(task: str, context: str = "", preferred_model: str | None = None,
                      json_mode: bool = False, raw: bool = False) -> dict:
    """Classify a task, and if local, execute it immediately.

    If cloud, return the classification so the orchestrator can delegate.
    """
    classification = classify_task(task, context)
    route = classification["route"]

    # Track the decision
    _track_decision(classification)

    # Cloud tasks: return classification for orchestrator to handle
    if route == "cloud":
        return {
            "status": "delegate_to_cloud",
            "classification": classification,
            "message": "Task requires cloud model. Orchestrator should handle.",
        }

    # Local tasks (local or local_required): execute via local_micro_agent
    micro_agent = Path(__file__).resolve().parent / "local_micro_agent.py"
    if not micro_agent.exists():
        return {
            "status": "error",
            "classification": classification,
            "message": "local_micro_agent.py not found in execution registry.",
            "fallback_blocked": route == "local_required"
        }
        
    cmd = [sys.executable, str(micro_agent), "--task", task]

    if preferred_model:
        cmd.extend(["--model", preferred_model])
    elif classification["suggested_model"] in ("gemma4:e4b", "glm-4.7-flash:latest"):
        cmd.extend(["--model", classification["suggested_model"]])

    if context:
        cmd.extend(["--input-text", context])

    if json_mode:
        cmd.append("--json")

    if raw:
        cmd.append("--raw")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode == 0:
            try:
                output = json.loads(result.stdout)
            except json.JSONDecodeError:
                output = {"response": result.stdout.strip()}

            return {
                "status": "executed_locally",
                "classification": classification,
                "result": output,
            }
        else:
            error_msg = result.stderr.strip() or result.stdout.strip()
            # If local_required and local failed, do NOT fall back to cloud
            if route == "local_required":
                return {
                    "status": "error",
                    "classification": classification,
                    "message": f"Security-sensitive task failed locally: {error_msg}",
                    "fallback_blocked": True,
                    "reason": "Task contains sensitive data and cannot be sent to cloud.",
                }
            # For optional-local, suggest cloud fallback
            return {
                "status": "local_failed_suggest_cloud",
                "classification": classification,
                "message": f"Local execution failed: {error_msg}",
                "suggestion": "Orchestrator may delegate to cloud model.",
            }
    except subprocess.TimeoutExpired:
        return {
            "status": "error",
            "classification": classification,
            "message": "Local model timed out after 120s",
        }
    except Exception as e:
        return {
            "status": "error",
            "classification": classification,
            "message": str(e),
        }


def _track_decision(classification: dict):
    """Track routing decisions for stats."""
    try:
        STATS_FILE.parent.mkdir(parents=True, exist_ok=True)
        stats = {}
        if STATS_FILE.exists():
            stats = json.loads(STATS_FILE.read_text())

        route = classification["route"]
        stats.setdefault("total", 0)
        stats.setdefault("by_route", {})
        stats.setdefault("tokens_saved", 0)

        stats["total"] += 1
        stats["by_route"][route] = stats["by_route"].get(route, 0) + 1
        stats["last_updated"] = time.strftime("%Y-%m-%dT%H:%M:%S")

        STATS_FILE.write_text(json.dumps(stats, indent=2))
    except Exception:
        pass  # Stats are best-effort, never block routing


def cmd_stats():
    """Show routing statistics."""
    if not STATS_FILE.exists():
        print(json.dumps({"status": "no_data", "message": "No routing decisions recorded yet."}))
        sys.exit(0)

    stats = json.loads(STATS_FILE.read_text())
    total = stats.get("total", 0)
    by_route = stats.get("by_route", {})

    local_count = by_route.get("local", 0) + by_route.get("local_required", 0)
    cloud_count = by_route.get("cloud", 0)

    output = {
        "total_decisions": total,
        "local_routed": local_count,
        "cloud_routed": cloud_count,
        "security_blocked": by_route.get("local_required", 0),
        "local_percentage": round(local_count / total * 100, 1) if total > 0 else 0,
        "last_updated": stats.get("last_updated", ""),
    }
    print(json.dumps(output, indent=2))


def main():
    parser = argparse.ArgumentParser(
        description="Intelligent task router: local models vs cloud, security-first"
    )
    subparsers = parser.add_subparsers(dest="command")

    # classify
    classify_p = subparsers.add_parser("classify", help="Classify a task without executing")
    classify_p.add_argument("--task", required=True, help="Task to classify")
    classify_p.add_argument("--context", default="", help="Additional context")

    # route
    route_p = subparsers.add_parser("route", help="Classify and execute (local) or delegate (cloud)")
    route_p.add_argument("--task", required=True, help="Task to route")
    route_p.add_argument("--input-file", help="File to include as context")
    route_p.add_argument("--input-text", default="", help="Text context")
    route_p.add_argument("--model", default=None, help="Force a specific model")
    route_p.add_argument("--json", action="store_true", help="JSON output from model")
    route_p.add_argument("--raw", action="store_true", help="Raw text output only")

    # split
    split_p = subparsers.add_parser("split", help="Split compound task into routable subtasks")
    split_p.add_argument("--task", required=True, help="Compound task to split")

    # batch
    batch_p = subparsers.add_parser("batch", help="Classify tasks from a JSON file")
    batch_p.add_argument("--tasks-file", required=True, help="JSON file with task list")

    # stats
    subparsers.add_parser("stats", help="Show routing statistics")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == "classify":
        result = classify_task(args.task, args.context)
        _track_decision(result)
        print(json.dumps(result, indent=2))

    elif args.command == "route":
        context = args.input_text
        if args.input_file:
            p = Path(args.input_file)
            if not p.exists():
                print(json.dumps({"status": "error", "message": f"File not found: {args.input_file}"}),
                      file=sys.stderr)
                sys.exit(2)
            context = p.read_text(encoding="utf-8", errors="replace")

        result = route_and_execute(
            task=args.task, context=context,
            preferred_model=args.model,
            json_mode=args.json, raw=args.raw,
        )
        print(json.dumps(result, indent=2))

        if result["status"] == "error" and result.get("fallback_blocked"):
            sys.exit(4)

    elif args.command == "split":
        subtasks = split_task(args.task)
        output = {
            "original_task": args.task,
            "subtask_count": len(subtasks),
            "subtasks": subtasks,
            "local_count": sum(1 for s in subtasks if s["route"] in ("local", "local_required")),
            "cloud_count": sum(1 for s in subtasks if s["route"] == "cloud"),
            "security_sensitive": sum(1 for s in subtasks if s["security_flags"]),
        }
        print(json.dumps(output, indent=2))

    elif args.command == "batch":
        p = Path(args.tasks_file)
        if not p.exists():
            print(json.dumps({"status": "error", "message": f"File not found: {args.tasks_file}"}),
                  file=sys.stderr)
            sys.exit(2)
        tasks = json.loads(p.read_text())
        if isinstance(tasks, dict):
            tasks = tasks.get("tasks", [])
        results = []
        for t in tasks:
            task_str = t if isinstance(t, str) else t.get("task", "")
            classification = classify_task(task_str)
            _track_decision(classification)
            results.append({"task": task_str, **classification})
        print(json.dumps({"results": results}, indent=2))

    elif args.command == "stats":
        cmd_stats()

    sys.exit(0)


if __name__ == "__main__":
    main()
