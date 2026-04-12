#!/usr/bin/env python3
"""
Script: system_checkup.py
Purpose: Verify structural integrity of the AGI Agent Kit framework.
         Checks that all required files, scripts, directories, and
         services are present and functional.

Usage:
    python3 execution/system_checkup.py
    python3 execution/system_checkup.py --verbose
    python3 execution/system_checkup.py --json
    python3 execution/system_checkup.py --fix

Exit Codes:
    0 - All checks passed
    1 - Some checks failed
"""

import argparse
import json
import subprocess
import sys
import urllib.request
from pathlib import Path


def find_project_root():
    current = Path(__file__).resolve().parent.parent
    for parent in [current] + list(current.parents):
        if (parent / "AGENTS.md").exists():
            return parent
    return current


def check_file(root: Path, path: str, required: bool = True) -> dict:
    """Check if a file exists."""
    full = root / path
    return {
        "check": f"file:{path}",
        "exists": full.exists(),
        "required": required,
        "status": "pass" if full.exists() else ("fail" if required else "warn"),
    }


def check_dir(root: Path, path: str, required: bool = True) -> dict:
    """Check if a directory exists."""
    full = root / path
    return {
        "check": f"dir:{path}",
        "exists": full.is_dir(),
        "required": required,
        "status": "pass" if full.is_dir() else ("fail" if required else "warn"),
    }


def check_service(name: str, url: str, timeout: int = 3) -> dict:
    """Check if an HTTP service is reachable."""
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return {"check": f"service:{name}", "url": url, "status": "pass",
                    "http_status": resp.status}
    except Exception as e:
        return {"check": f"service:{name}", "url": url, "status": "warn",
                "error": str(e)}


def check_command(name: str, cmd: list, timeout: int = 5, required: bool = True) -> dict:
    """Check if a command runs successfully."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        status = "pass" if result.returncode == 0 else ("fail" if required else "skip")
        return {"check": f"cmd:{name}", "status": status, "exit_code": result.returncode}
    except FileNotFoundError:
        return {"check": f"cmd:{name}", "status": "fail" if required else "skip", "error": "not found"}
    except Exception as e:
        return {"check": f"cmd:{name}", "status": "fail" if required else "skip", "error": str(e)}


def check_dependencies(root: Path) -> dict:
    """Run dependency vulnerability scan."""
    tracker = root / "execution" / "dependency_tracker.py"
    if not tracker.exists():
        return {"check": "dependencies", "status": "warn", "error": "dependency_tracker.py missing"}
    try:
        result = subprocess.run(
            [sys.executable, str(tracker), "scan"],
            capture_output=True, text=True, timeout=30, cwd=str(root)
        )
        data = json.loads(result.stdout)
        vuln_count = data.get("scan_summary", {}).get("vulnerable", 0)
        return {
            "check": "dependencies",
            "status": "pass" if vuln_count == 0 else "fail",
            "total": data.get("scan_summary", {}).get("total_dependencies", 0),
            "vulnerable": vuln_count,
        }
    except Exception as e:
        return {"check": "dependencies", "status": "warn", "error": str(e)}


def run_checkup(root: Path, verbose: bool = False) -> dict:
    """Run all checks and return results."""
    results = []

    # Core files
    core_files = [
        ("AGENTS.md", True), ("CLAUDE.md", True), ("CHANGELOG.md", True),
        ("README.md", True), ("package.json", True), ("requirements.txt", True),
        (".gitignore", True),
    ]
    for f, req in core_files:
        results.append(check_file(root, f, req))

    # Agent rules
    results.append(check_dir(root, ".agent/rules", True))
    results.append(check_file(root, ".agent/rules/core_rules.md", True))
    results.append(check_file(root, ".agent/rules/versioning_rules.md", False))

    # Directives
    results.append(check_dir(root, "directives", True))
    results.append(check_dir(root, "directives/teams", True))
    results.append(check_dir(root, "directives/subagents", False))

    # Execution scripts (core)
    exec_scripts = [
        "memory_manager.py", "session_boot.py", "session_init.py",
        "cross_agent_context.py", "memory_usage_proof.py",
        "dispatch_agent_team.py", "claude_dispatch.py",
        "task_router.py", "local_micro_agent.py",
        "dependency_tracker.py", "system_checkup.py",
    ]
    for s in exec_scripts:
        results.append(check_file(root, f"execution/{s}", True))

    # Skills
    results.append(check_dir(root, "skills", True))
    results.append(check_file(root, "skills/SKILLS_CATALOG.md", True))

    # Docs
    results.append(check_dir(root, "docs", True))

    # Data
    results.append(check_dir(root, "data", False))
    results.append(check_file(root, "data/workflows.json", False))

    # Services
    results.append(check_service("qdrant", "http://localhost:6333/collections"))
    results.append(check_service("ollama", "http://localhost:11434/api/tags"))

    # Commands
    results.append(check_command("git", ["git", "--version"]))
    results.append(check_command("python3", [sys.executable, "--version"]))
    results.append(check_command("docker", ["docker", "--version"], required=False))

    # Dependency scan
    results.append(check_dependencies(root))

    # Summarize
    passed = sum(1 for r in results if r["status"] == "pass")
    failed = sum(1 for r in results if r["status"] == "fail")
    warned = sum(1 for r in results if r["status"] == "warn")
    skipped = sum(1 for r in results if r["status"] == "skip")

    return {
        "summary": {
            "total": len(results),
            "passed": passed,
            "failed": failed,
            "warnings": warned,
            "skipped": skipped,
            "healthy": failed == 0,
        },
        "results": results if verbose else [r for r in results if r["status"] not in ("pass", "skip")],
    }


def main():
    parser = argparse.ArgumentParser(description="AGI Agent Kit system integrity checker")
    parser.add_argument("--verbose", action="store_true", help="Show all checks (not just failures)")
    parser.add_argument("--json", action="store_true", help="JSON output")
    parser.add_argument("--fix", action="store_true", help="Attempt auto-fixes")
    args = parser.parse_args()

    root = find_project_root()

    if args.fix:
        # Auto-fix: copy missing files from templates
        templates = root / "templates" / "base"
        fixes = []
        if templates.exists():
            rules_src = templates / ".agent" / "rules" / "core_rules.md"
            rules_dst = root / ".agent" / "rules" / "core_rules.md"
            if rules_src.exists() and not rules_dst.exists():
                rules_dst.parent.mkdir(parents=True, exist_ok=True)
                rules_dst.write_text(rules_src.read_text())
                fixes.append("Copied core_rules.md from templates")

        if fixes and not args.json:
            for f in fixes:
                print(f"  Fixed: {f}")

    report = run_checkup(root, args.verbose)

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        s = report["summary"]
        icon = "pass" if s["healthy"] else "FAIL"
        print(f"[{icon}] System Checkup: {s['passed']}/{s['total']} passed, "
              f"{s['failed']} failed, {s['warnings']} warnings, {s['skipped']} skipped")

        if report["results"]:
            for r in report["results"]:
                status = r["status"].upper()
                check = r["check"]
                extra = ""
                if "error" in r:
                    extra = f" ({r['error']})"
                elif "vulnerable" in r:
                    extra = f" ({r['vulnerable']} vulnerable)"
                print(f"  [{status}] {check}{extra}")

    sys.exit(0 if report["summary"]["healthy"] else 1)


if __name__ == "__main__":
    main()
