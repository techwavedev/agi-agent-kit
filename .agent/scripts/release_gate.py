#!/usr/bin/env python3
"""
Script: release_gate.py
Purpose: Enforce strict quality checks before release (npm publish or public merge).
Checks:
1. Documentation (README/CHANGELOG updated?)
2. Security (Secret scanning)
3. Code Integrity (Syntax check)
4. Version Consistency (package.json)
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path

# Configuration
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
SENSITIVE_PATTERNS = [
    r"(?i)aws_access_key_id\s*=\s*['\"](AKIA[0-9A-Z]{16})['\"]",
    r"(?i)api_key\s*=\s*['\"](sk-[a-zA-Z0-9]{32,})['\"]",
    r"(?i)private_key\s*=\s*['\"](-----BEGIN PRIVATE KEY-----)['\"]",
]
REQUIRED_DOCS = ["README.md", "CHANGELOG.md"]

# ── WIP LOCK ──────────────────────────────────────────────────────────────────
# Drop a file named PUBLISHING_BLOCKED in the repo root to hard-stop any release.
LOCK_FILE = ROOT_DIR / "PUBLISHING_BLOCKED"

def check_wip_lock():
    """Hard-fail if PUBLISHING_BLOCKED file is present in repo root."""
    if LOCK_FILE.exists():
        reason = LOCK_FILE.read_text(encoding="utf-8").strip() or "No reason specified."
        print("🚫 PUBLISHING BLOCKED")
        print("─" * 40)
        print(reason)
        print("─" * 40)
        print("Remove PUBLISHING_BLOCKED from the repo root to unblock.")
        sys.exit(1)

def check_release_branch():
    """Ensure we are on an allowed release branch (main or public)."""
    try:
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True, text=True, check=True, cwd=ROOT_DIR
        )
        branch = result.stdout.strip()
    except subprocess.CalledProcessError:
        branch = "unknown"

    # GitHub Actions tag releases run in detached HEAD (empty branch name)
    if not branch and os.environ.get("GITHUB_ACTIONS") == "true":
        print("✅ On release branch: GitHub Actions (Detached HEAD)")
        return

    allowed = {"main", "public"}
    if branch not in allowed:
        print(f"🚫 PUBLISHING BLOCKED — current branch is '{branch}'")
        print(f"   Publishing is only allowed from: {', '.join(sorted(allowed))}")
        print(f"   Merge your work to main/public before releasing.")
        sys.exit(1)
    print(f"✅ On release branch: {branch}")


def run_command(cmd, cwd=ROOT_DIR):
    """Run a shell command and return output."""
    try:
        result = subprocess.run(
            cmd, shell=True, check=True, capture_output=True, text=True, cwd=cwd
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"❌ Command failed: {cmd}")
        print(e.stderr)
        return None

def is_ci():
    return os.environ.get("CI") == "true" or os.environ.get("GITHUB_ACTIONS") == "true"

def check_git_status():
    """Ensure working directory is clean."""
    print("🔍 Checking Git status...")
    status = run_command("git status --porcelain")
    if status:
        print("⚠️  Uncommitted changes detected:")
        print(status)
        if is_ci():
            print("ℹ️  CI environment — skipping interactive prompt (detached HEAD checkout is expected).")
        elif not sys.stdin.isatty():
            print("ℹ️  Non-interactive environment — skipping prompt (e.g. pre-push hook).")
        else:
            response = input("Continue anyway? (y/N): ")
            if response.lower() != 'y':
                sys.exit(1)
    else:
        print("✅ Git working directory clean.")

def check_documentation():
    """Verify documentation updates."""
    print("🔍 Verifying documentation...")
    for doc in REQUIRED_DOCS:
        if not (ROOT_DIR / doc).exists():
            print(f"❌ Missing required document: {doc}")
            sys.exit(1)
        
        # Check if modified in last commit (optional but good practice)
        # diff = run_command(f"git diff head --name-only | grep {doc}")
        # if diff:
        #     print(f"✅ {doc} updated in staged/recent changes.")
        
    print("✅ Documentation present.")

def scan_secrets():
    """Scan for hardcoded secrets."""
    print("🔍 Scanning for secrets...")
    issues = []
    scanned = 0
    # Scan python, js, md files
    for ext in ["py", "js", "md", "json"]:
        for path in ROOT_DIR.rglob(f"*.{ext}"):
            if "node_modules" in str(path) or ".git" in str(path) or ".venv" in str(path) or ".idea" in str(path) or ".tmp" in str(path):
                continue
            try:
                content = path.read_text(errors="ignore")
                for pattern in SENSITIVE_PATTERNS:
                    match = re.search(pattern, content)
                    if match:
                        issues.append(f"{path}: Potential secret found via regex")
            except Exception:
                pass
            scanned += 1
            if scanned % 100 == 0:
                print(f"   ...scanned {scanned} files", flush=True)

    if issues:
        print(f"❌ Security issues found ({scanned} files scanned):")
        for issue in issues:
            print(f"   - {issue}")
        sys.exit(1)
    print(f"✅ No hardcoded secrets found ({scanned} files scanned).")

def check_versions():
    """Check package.json version matches changelog and enforce the Patch-99 limit."""
    print("🔍 Checking version consistency...")
    pkg_json = ROOT_DIR / "package.json"
    changelog = ROOT_DIR / "CHANGELOG.md"
    
    if pkg_json.exists():
        data = json.loads(pkg_json.read_text())
        version = data.get("version")
        print(f"ℹ️  Package version: {version}")
        
        # Enforce Patch-99 rule against main branch if available
        try:
            import subprocess
            result = subprocess.run(["git", "show", "main:package.json"], capture_output=True, text=True, cwd=str(ROOT_DIR))
            if result.returncode == 0:
                old_data = json.loads(result.stdout)
                old_version = old_data.get("version", "0.0.0")
                
                # Split versions into [major, minor, patch]
                old_parts = [int(v) for v in old_version.split(".")]
                new_parts = [int(v) for v in version.split(".")]
                
                if len(old_parts) == 3 and len(new_parts) == 3:
                    if new_parts[1] > old_parts[1]:
                        # Minor version bumped!
                        if old_parts[2] < 99 and new_parts[0] == old_parts[0]:
                            print(f"❌ MINOR BUMP REJECTED: You are trying to bump minor ({old_version} -> {version}), but patch has not reached .99 yet.")
                            print("   Our standard protocol is to exhaust the patch number up to .99 for bug fixes and small features before incrementing minor.")
                            if is_ci():
                                print("❌ CI environment — blocking release. Fix the version or override by setting FORCE_MINOR_BUMP=true.")
                                if os.environ.get("FORCE_MINOR_BUMP") != "true":
                                    sys.exit(1)
                            else:
                                response = input("Is this a mandated structural overhaul overriding this rule? (y/N): ")
                                if response.lower() != 'y':
                                    sys.exit(1)
        except Exception as e:
            print(f"⚠️  Could not run the Patch-99 git check: {e}")
        
        if changelog.exists():
            content = changelog.read_text()
            if version not in content:
                print(f"❌ Version {version} not found in CHANGELOG.md!")
                if is_ci():
                    print("❌ CI environment — blocking release. Add a CHANGELOG entry for this version before publishing.")
                    sys.exit(1)
                else:
                    response = input("Continue anyway? (y/N): ")
                    if response.lower() != 'y':
                        sys.exit(1)
            else:
                print("✅ Version present in CHANGELOG.")

def syntax_check():
    """Run basic syntax check."""
    print("🔍 Verifying Python syntax...")
    # Find all python files
    py_files = [py for py in ROOT_DIR.rglob("*.py")
                if "node_modules" not in str(py) and ".venv" not in str(py) and ".tmp" not in str(py)]
    total = len(py_files)
    print(f"   Checking {total} Python files...", flush=True)
    failed = False
    checked = 0
    for py in py_files:
        try:
            subprocess.run(["python3", "-m", "py_compile", str(py)], check=True, capture_output=True)
        except subprocess.CalledProcessError:
            print(f"❌ Syntax error in {py}")
            failed = True
        checked += 1
        if checked % 50 == 0:
            print(f"   ...checked {checked}/{total}", flush=True)
    
    if failed:
        sys.exit(1)
    print(f"✅ Python syntax valid ({total} files checked).")

def check_markdown_size():
    """Warn about excessively large Markdown files that may waste LLM tokens."""
    print("🔍 Checking Markdown file sizes (Token Optimization)...")
    exemptions = ["CHANGELOG.md", "README", "AGENTS.md", "SKILLS_CATALOG.md"]
    warnings = []
    MAX_SIZE = 15000  # bytes

    for path in ROOT_DIR.rglob("*.md"):
        if "node_modules" in str(path) or ".git" in str(path) or ".venv" in str(path) or ".tmp" in str(path):
            continue
        if any(ex in path.name for ex in exemptions):
            continue
            
        try:
            size = path.stat().st_size
            if size > MAX_SIZE:
                warnings.append(f"{path.relative_to(ROOT_DIR)} ({size // 1024} KB)")
        except Exception:
            pass

    if warnings:
        print(f"⚠️  Found {len(warnings)} large Markdown files. Consider modularizing these to save agent tokens:")
        for w in warnings:
            print(f"   - {w}")
        # Not exiting here as this is a token optimization warning
    else:
        print("✅ Markdown files are reasonably sized.")

def main():
    print("🚀 Starting Release Gate Protocol...")
    print("-----------------------------------")

    # ── Hard blocks (checked first, before anything else) ──
    check_wip_lock()
    check_release_branch()

    check_git_status()
    check_documentation()
    scan_secrets()
    check_versions()
    syntax_check()
    check_markdown_size()

    print("-----------------------------------")
    print("✅ All checks passed. Ready for release.")
    sys.exit(0)


if __name__ == "__main__":
    main()
