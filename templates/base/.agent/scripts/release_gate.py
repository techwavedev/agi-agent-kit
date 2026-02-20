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

def check_git_status():
    """Ensure working directory is clean."""
    print("🔍 Checking Git status...")
    status = run_command("git status --porcelain")
    if status:
        print("⚠️  Uncommitted changes detected:")
        print(status)
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
    # Scan python, js, md files
    for ext in ["py", "js", "md", "json"]:
        for path in ROOT_DIR.rglob(f"*.{ext}"):
            if "node_modules" in str(path) or ".git" in str(path) or ".venv" in str(path):
                continue
            try:
                content = path.read_text(errors="ignore")
                for pattern in SENSITIVE_PATTERNS:
                    match = re.search(pattern, content)
                    if match:
                        issues.append(f"{path}: Potential secret found via regex")
            except Exception:
                pass

    if issues:
        print("❌ Security issues found:")
        for issue in issues:
            print(f"   - {issue}")
        sys.exit(1)
    print("✅ No hardcoded secrets found.")

def check_versions():
    """Check package.json version matches changelog."""
    print("🔍 Checking version consistency...")
    pkg_json = ROOT_DIR / "package.json"
    changelog = ROOT_DIR / "CHANGELOG.md"
    
    if pkg_json.exists():
        data = json.loads(pkg_json.read_text())
        version = data.get("version")
        print(f"ℹ️  Package version: {version}")
        
        if changelog.exists():
            content = changelog.read_text()
            if version not in content:
                print(f"⚠️  Version {version} not found in CHANGELOG.md!")
                response = input("Continue anyway? (y/N): ")
                if response.lower() != 'y':
                    sys.exit(1)
            else:
                print("✅ Version present in CHANGELOG.")

def syntax_check():
    """Run basic syntax check."""
    print("🔍 verifying Python syntax...")
    # Find all python files
    py_files = list(ROOT_DIR.rglob("*.py"))
    failed = False
    for py in py_files:
        if "node_modules" in str(py) or ".venv" in str(py):
            continue
        try:
            subprocess.run(["python3", "-m", "py_compile", str(py)], check=True, capture_output=True)
        except subprocess.CalledProcessError:
            print(f"❌ Syntax error in {py}")
            failed = True
    
    if failed:
        sys.exit(1)
    print("✅ Python syntax valid.")

def main():
    print("🚀 Starting Release Gate Protocol...")
    print("-----------------------------------")
    
    check_git_status()
    check_documentation()
    scan_secrets()
    check_versions()
    syntax_check()
    
    print("-----------------------------------")
    print("✅ All checks passed. Ready for release.")
    sys.exit(0)

if __name__ == "__main__":
    main()
