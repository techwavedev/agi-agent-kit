#!/usr/bin/env python3
"""
Script: security_scan.py
Purpose: Deterministic security scanning for pre-release gate.
         Three modes: secrets, dependencies, code.

Usage:
    python3 execution/security_scan.py secrets          --output .tmp/security/secret_scan.json
    python3 execution/security_scan.py dependencies    --output .tmp/security/dependency_audit.json
    python3 execution/security_scan.py code            --output .tmp/security/code_security.json
    python3 execution/security_scan.py blocked         --output .tmp/security/blocked_packages.json
    python3 execution/security_scan.py all             --output .tmp/security/full_report.json

Exit Codes:
    0 - All checks passed
    1 - Invalid arguments
    2 - Critical findings (release should be blocked)
    3 - Warnings only (release may proceed with caution)
"""

import argparse
import json
import math
import os
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent

# Directories to skip entirely
SKIP_DIRS = {"node_modules", ".git", ".venv", ".venv.test", ".idea", ".tmp", "__pycache__", ".mypy_cache", "venv", "env"}
# Extensions to scan for secrets and code
TEXT_EXTENSIONS = {".py", ".js", ".ts", ".jsx", ".tsx", ".json", ".yml", ".yaml", ".md",
                   ".sh", ".bash", ".cfg", ".ini", ".toml", ".env", ".txt", ".html", ".css"}
# Max file size to scan (skip large vendor bundles)
MAX_FILE_SIZE = 512_000  # 500KB

# ── Allowlist: files/dirs containing intentional examples, pattern definitions, or docs ──
# Findings in these paths are downgraded to "info" severity (non-blocking).
# These are framework files that teach security patterns or contain example code.
ALLOWLIST_PATHS = {
    "templates/skills/",               # Skill templates contain example code with intentional patterns
    "templates/base/",                 # Base templates shipped to users (contain example patterns)
    "execution/security_scan.py",      # This scanner's own pattern definitions
    ".agent/scripts/release_gate.py",  # Release gate's regex patterns
    "skills/qdrant-memory/",           # Qdrant skill docs and test fixtures
    "execution/enforce_teams.py",      # Uses os.system with hardcoded commands (no user input)
    "execution/fastapi_tool_bridge.py", # Intentional PoC with shell=True (documented)
}

def is_allowlisted(rel_path: str) -> bool:
    """Check if a file path is in the allowlist (findings downgraded to info)."""
    return any(rel_path.startswith(prefix) for prefix in ALLOWLIST_PATHS)

# ═══════════════════════════════════════════════════════════════════════════════
# SECRET SCANNING
# ═══════════════════════════════════════════════════════════════════════════════

SECRET_PATTERNS = [
    # AWS
    {"name": "AWS Access Key", "pattern": r"(?:^|['\"\s=])?(AKIA[0-9A-Z]{16})(?:['\"\s]|$)", "severity": "critical"},
    {"name": "AWS Secret Key", "pattern": r"(?i)aws_secret_access_key\s*[=:]\s*['\"]?([A-Za-z0-9/+=]{40})['\"]?", "severity": "critical"},
    # OpenAI / Anthropic
    {"name": "OpenAI API Key", "pattern": r"(?:^|['\"\s=])?(sk-[a-zA-Z0-9]{32,})", "severity": "critical"},
    {"name": "Anthropic API Key", "pattern": r"(?:^|['\"\s=])?(sk-ant-[a-zA-Z0-9-]{32,})", "severity": "critical"},
    # GitHub tokens
    {"name": "GitHub PAT", "pattern": r"(?:^|['\"\s=])?(ghp_[a-zA-Z0-9]{36})", "severity": "critical"},
    {"name": "GitHub OAuth", "pattern": r"(?:^|['\"\s=])?(gho_[a-zA-Z0-9]{36})", "severity": "critical"},
    {"name": "GitHub App Token", "pattern": r"(?:^|['\"\s=])?(ghs_[a-zA-Z0-9]{36})", "severity": "critical"},
    {"name": "GitLab PAT", "pattern": r"(?:^|['\"\s=])?(glpat-[a-zA-Z0-9\-]{20,})", "severity": "critical"},
    # Private keys
    {"name": "Private Key", "pattern": r"-----BEGIN\s+(RSA |DSA |EC |PGP )?PRIVATE KEY-----", "severity": "critical"},
    {"name": "Certificate", "pattern": r"-----BEGIN CERTIFICATE-----", "severity": "high"},
    # Generic secrets
    {"name": "Generic Secret Assignment", "pattern": r"(?i)(password|secret|token|apikey|api_key)\s*[=:]\s*['\"]([^'\"]{8,})['\"]", "severity": "high"},
    # Connection strings
    {"name": "Database URI", "pattern": r"(?i)(mongodb|postgres|mysql|redis)://[^\s'\"]+:[^\s'\"]+@", "severity": "critical"},
    # Stripe
    {"name": "Stripe Key", "pattern": r"(?:^|['\"\s=])?(sk_live_[a-zA-Z0-9]{24,})", "severity": "critical"},
    {"name": "Stripe Test Key", "pattern": r"(?:^|['\"\s=])?(sk_test_[a-zA-Z0-9]{24,})", "severity": "moderate"},
    # Twilio
    {"name": "Twilio Auth Token", "pattern": r"(?i)twilio.*['\"]([a-f0-9]{32})['\"]", "severity": "high"},
    # JWT
    {"name": "JWT Token", "pattern": r"eyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}", "severity": "high"},
]

# Prefixes that indicate test/example data (not real secrets)
SAFE_PREFIXES = ("test_", "fake_", "mock_", "example_", "dummy_", "xxx", "your_", "placeholder")

DANGEROUS_FILES = {".env", ".env.local", ".env.production", ".env.staging",
                   ".pem", ".p12", ".pfx", ".key", ".keystore"}


def shannon_entropy(s: str) -> float:
    """Calculate Shannon entropy of a string."""
    if not s:
        return 0.0
    freq = Counter(s)
    length = len(s)
    return -sum((count / length) * math.log2(count / length) for count in freq.values())


def is_safe_value(value: str) -> bool:
    """Check if a matched value looks like test/example data."""
    lower = value.lower().strip()
    return any(lower.startswith(p) for p in SAFE_PREFIXES)


def should_skip(path: Path) -> bool:
    """Check if a path should be skipped."""
    parts = set(path.parts)
    if parts & SKIP_DIRS:
        return True
    try:
        if path.stat().st_size > MAX_FILE_SIZE:
            return True
    except OSError:
        return True
    return False


def scan_secrets() -> dict:
    """Scan repository for hardcoded secrets."""
    findings = []
    files_scanned = 0

    # Check for dangerous files in tracked directories
    for path in ROOT_DIR.rglob("*"):
        if should_skip(path):
            continue
        if path.is_file() and path.name in DANGEROUS_FILES:
            # Check if it's gitignored
            try:
                result = subprocess.run(
                    ["git", "check-ignore", "-q", str(path)],
                    capture_output=True, cwd=ROOT_DIR
                )
                if result.returncode != 0:  # NOT ignored — it would be committed
                    findings.append({
                        "file": str(path.relative_to(ROOT_DIR)),
                        "line": 0,
                        "type": "dangerous_file",
                        "pattern": f"Sensitive file '{path.name}' is not in .gitignore",
                        "severity": "critical",
                        "recommendation": f"Add '{path.name}' to .gitignore or remove from repo"
                    })
            except Exception:
                pass

    # Scan text files for secret patterns
    for path in ROOT_DIR.rglob("*"):
        if should_skip(path) or not path.is_file():
            continue
        if path.suffix not in TEXT_EXTENSIONS:
            continue

        try:
            content = path.read_text(errors="ignore")
        except Exception:
            continue

        files_scanned += 1
        lines = content.split("\n")

        for i, line in enumerate(lines, 1):
            for pattern_def in SECRET_PATTERNS:
                match = re.search(pattern_def["pattern"], line)
                if match:
                    matched_value = match.group(1) if match.lastindex else match.group(0)
                    severity = pattern_def["severity"]
                    if is_safe_value(matched_value):
                        severity = "info"

                    findings.append({
                        "file": str(path.relative_to(ROOT_DIR)),
                        "line": i,
                        "type": "secret_pattern",
                        "pattern": pattern_def["name"],
                        "severity": severity,
                        "recommendation": "Move to .env and ensure .gitignore excludes it"
                    })

        # High-entropy string check (only in assignment contexts)
        for i, line in enumerate(lines, 1):
            # Look for variable assignments with long string values
            assign_match = re.search(
                r'(?:=|:)\s*["\']([A-Za-z0-9+/=_\-]{20,})["\']', line
            )
            if assign_match:
                value = assign_match.group(1)
                entropy = shannon_entropy(value)
                if entropy > 4.5 and not is_safe_value(value):
                    # Avoid duplicating findings already caught by regex patterns
                    already_found = any(
                        f["file"] == str(path.relative_to(ROOT_DIR)) and f["line"] == i + 1
                        for f in findings
                    )
                    if not already_found:
                        findings.append({
                            "file": str(path.relative_to(ROOT_DIR)),
                            "line": i,
                            "type": "high_entropy",
                            "pattern": f"High entropy string (entropy={entropy:.2f})",
                            "severity": "high",
                            "recommendation": "Verify this is not a secret. If it is, move to .env"
                        })

    # Downgrade allowlisted findings to "info" (non-blocking)
    for f in findings:
        if is_allowlisted(f["file"]) and f["severity"] in ("critical", "high"):
            f["severity"] = "info"
            f["allowlisted"] = True

    critical_count = sum(1 for f in findings if f["severity"] == "critical")
    high_count = sum(1 for f in findings if f["severity"] == "high")

    return {
        "scan": "secrets",
        "status": "fail" if (critical_count + high_count) > 0 else "pass",
        "findings": findings,
        "stats": {
            "files_scanned": files_scanned,
            "patterns_checked": len(SECRET_PATTERNS),
            "entropy_checks": True,
            "critical": critical_count,
            "high": high_count,
            "moderate": sum(1 for f in findings if f["severity"] == "moderate"),
            "info": sum(1 for f in findings if f["severity"] == "info"),
        }
    }


# ═══════════════════════════════════════════════════════════════════════════════
# DEPENDENCY AUDIT
# ═══════════════════════════════════════════════════════════════════════════════

def audit_npm() -> dict:
    """Run npm audit and parse results."""
    pkg_json = ROOT_DIR / "package.json"
    if not pkg_json.exists():
        return {"available": False, "reason": "No package.json found"}

    # Ensure lock file exists
    lock_file = ROOT_DIR / "package-lock.json"
    if not lock_file.exists():
        try:
            subprocess.run(
                ["npm", "install", "--package-lock-only", "--ignore-scripts"],
                capture_output=True, text=True, cwd=ROOT_DIR, timeout=120
            )
        except Exception as e:
            return {"available": False, "reason": f"Could not generate lock file: {e}"}

    try:
        result = subprocess.run(
            ["npm", "audit", "--json"],
            capture_output=True, text=True, cwd=ROOT_DIR, timeout=120
        )
        audit_data = json.loads(result.stdout) if result.stdout else {}
    except subprocess.TimeoutExpired:
        return {"available": False, "reason": "npm audit timed out"}
    except json.JSONDecodeError:
        return {"available": False, "reason": "npm audit returned invalid JSON"}
    except FileNotFoundError:
        return {"available": False, "reason": "npm not installed"}

    # Parse vulnerabilities summary
    vulnerabilities = audit_data.get("metadata", {}).get("vulnerabilities", {})
    advisories = []

    # npm audit v2+ format
    vulns = audit_data.get("vulnerabilities", {})
    for name, info in vulns.items():
        advisories.append({
            "package": name,
            "severity": info.get("severity", "unknown"),
            "title": info.get("via", [{}])[0].get("title", "Unknown") if isinstance(info.get("via", [{}])[0], dict) else str(info.get("via", ["Unknown"])[0]),
            "fixAvailable": info.get("fixAvailable", False),
        })

    return {
        "available": True,
        "critical": vulnerabilities.get("critical", 0),
        "high": vulnerabilities.get("high", 0),
        "moderate": vulnerabilities.get("moderate", 0),
        "low": vulnerabilities.get("low", 0),
        "info": vulnerabilities.get("info", 0),
        "total": vulnerabilities.get("total", 0),
        "advisories": advisories,
    }


def check_licenses() -> list:
    """Check for problematic licenses in dependencies."""
    issues = []
    pkg_json = ROOT_DIR / "package.json"
    if not pkg_json.exists():
        return issues

    pkg_data = json.loads(pkg_json.read_text())
    project_license = pkg_data.get("license", "").upper()

    # If project is MIT/ISC/BSD, flag GPL dependencies
    permissive_licenses = {"MIT", "ISC", "BSD-2-CLAUSE", "BSD-3-CLAUSE", "APACHE-2.0"}
    copyleft_licenses = {"GPL-2.0", "GPL-3.0", "AGPL-3.0", "GPL-2.0-ONLY", "GPL-3.0-ONLY",
                         "AGPL-3.0-ONLY", "GPL-2.0-OR-LATER", "GPL-3.0-OR-LATER", "AGPL-3.0-OR-LATER"}

    if project_license in permissive_licenses:
        # Check node_modules for GPL deps
        nm_dir = ROOT_DIR / "node_modules"
        if nm_dir.exists():
            for dep_pkg in nm_dir.glob("*/package.json"):
                try:
                    dep_data = json.loads(dep_pkg.read_text())
                    dep_license = dep_data.get("license", "")
                    if isinstance(dep_license, dict):
                        dep_license = dep_license.get("type", "")
                    dep_license_upper = dep_license.upper()
                    if dep_license_upper in copyleft_licenses:
                        issues.append({
                            "package": dep_data.get("name", dep_pkg.parent.name),
                            "license": dep_license,
                            "issue": f"Copyleft license '{dep_license}' incompatible with project license '{project_license}'",
                            "severity": "critical"
                        })
                except Exception:
                    pass

    return issues


def scan_dependencies() -> dict:
    """Full dependency audit."""
    npm_result = audit_npm()
    license_issues = check_licenses()

    # Determine overall status
    if not npm_result.get("available", False):
        status = "pass"  # Can't audit what doesn't exist
        if npm_result.get("reason", "").startswith("npm"):
            status = "fail"  # npm exists but failed
    elif npm_result.get("critical", 0) > 0 or npm_result.get("high", 0) > 0:
        status = "fail"
    elif npm_result.get("moderate", 0) > 0:
        status = "warn"
    else:
        status = "pass"

    if license_issues:
        has_critical_license = any(i["severity"] == "critical" for i in license_issues)
        if has_critical_license:
            status = "fail"

    return {
        "scan": "dependencies",
        "status": status,
        "npm_audit": npm_result,
        "license_issues": license_issues,
        "recommendations": _dependency_recommendations(npm_result, license_issues),
    }


def _dependency_recommendations(npm_result: dict, license_issues: list) -> list:
    """Generate actionable recommendations."""
    recs = []
    if npm_result.get("critical", 0) > 0:
        recs.append("Run 'npm audit fix' to auto-fix critical vulnerabilities")
    if npm_result.get("high", 0) > 0:
        recs.append("Run 'npm audit fix' or update affected packages manually")
    if license_issues:
        recs.append("Replace copyleft-licensed dependencies with permissive alternatives")
    return recs


# ═══════════════════════════════════════════════════════════════════════════════
# CODE SECURITY REVIEW
# ═══════════════════════════════════════════════════════════════════════════════

CODE_PATTERNS = {
    "python": [
        {"name": "Command Injection (os.system)", "pattern": r"\bos\.system\s*\(", "severity": "critical", "cwe": "CWE-78",
         "recommendation": "Use subprocess.run() with shell=False and pass args as a list"},
        {"name": "Command Injection (shell=True)", "pattern": r"subprocess\.\w+\(.*shell\s*=\s*True", "severity": "high", "cwe": "CWE-78",
         "recommendation": "Use shell=False and pass command as a list"},
        {"name": "Code Injection (eval)", "pattern": r"\beval\s*\(", "severity": "critical", "cwe": "CWE-95",
         "recommendation": "Use ast.literal_eval() for data or avoid eval entirely"},
        {"name": "Code Injection (exec)", "pattern": r"\bexec\s*\(", "severity": "high", "cwe": "CWE-95",
         "recommendation": "Avoid exec(); use structured alternatives"},
        {"name": "Unsafe Deserialization (pickle)", "pattern": r"\bpickle\.loads?\s*\(", "severity": "critical", "cwe": "CWE-502",
         "recommendation": "Use json.loads() or a safe serialization format"},
        {"name": "Unsafe YAML (yaml.load)", "pattern": r"\byaml\.load\s*\([^)]*(?!Loader)", "severity": "high", "cwe": "CWE-502",
         "recommendation": "Use yaml.safe_load() instead of yaml.load()"},
        {"name": "SSL Verification Disabled", "pattern": r"verify\s*=\s*False", "severity": "high", "cwe": "CWE-295",
         "recommendation": "Enable SSL verification (verify=True)"},
        {"name": "Debug Mode in Production", "pattern": r"(?i)DEBUG\s*=\s*True", "severity": "moderate", "cwe": "CWE-489",
         "recommendation": "Ensure DEBUG is False in production"},
        {"name": "Unsafe XML Parsing", "pattern": r"\bxml\.etree\.ElementTree\.parse\s*\(", "severity": "moderate", "cwe": "CWE-611",
         "recommendation": "Use defusedxml library for XML parsing"},
        {"name": "Hardcoded Temp Path", "pattern": r"['\"]\/tmp\/[^'\"]+['\"]", "severity": "low", "cwe": "CWE-377",
         "recommendation": "Use tempfile.mkstemp() or tempfile.NamedTemporaryFile()"},
    ],
    "javascript": [
        {"name": "Code Injection (eval)", "pattern": r"\beval\s*\(", "severity": "critical", "cwe": "CWE-95",
         "recommendation": "Avoid eval(); use JSON.parse() for data"},
        {"name": "Code Injection (Function constructor)", "pattern": r"\bnew\s+Function\s*\(", "severity": "critical", "cwe": "CWE-95",
         "recommendation": "Avoid dynamic code generation via Function()"},
        {"name": "XSS (innerHTML)", "pattern": r"\.innerHTML\s*=", "severity": "high", "cwe": "CWE-79",
         "recommendation": "Use textContent or a sanitization library"},
        {"name": "XSS (dangerouslySetInnerHTML)", "pattern": r"dangerouslySetInnerHTML", "severity": "high", "cwe": "CWE-79",
         "recommendation": "Sanitize HTML with DOMPurify before rendering"},
        {"name": "Prototype Pollution", "pattern": r"Object\.assign\s*\(\s*\{\}", "severity": "moderate", "cwe": "CWE-1321",
         "recommendation": "Validate input objects before merging"},
        {"name": "Child Process (exec)", "pattern": r"child_process.*\bexec\s*\(", "severity": "high", "cwe": "CWE-78",
         "recommendation": "Use execFile() or spawn() with explicit args array"},
    ]
}

# File extension to language mapping
EXT_TO_LANG = {
    ".py": "python",
    ".js": "javascript", ".ts": "javascript", ".jsx": "javascript", ".tsx": "javascript",
    ".mjs": "javascript", ".cjs": "javascript",
}


def scan_code() -> dict:
    """Scan code for security vulnerability patterns."""
    findings = []
    files_scanned = 0
    patterns_checked = set()

    for path in ROOT_DIR.rglob("*"):
        if should_skip(path) or not path.is_file():
            continue
        lang = EXT_TO_LANG.get(path.suffix)
        if not lang:
            continue

        try:
            content = path.read_text(errors="ignore")
        except Exception:
            continue

        files_scanned += 1
        lines = content.split("\n")
        rel_path = str(path.relative_to(ROOT_DIR))

        for pattern_def in CODE_PATTERNS.get(lang, []):
            patterns_checked.add(pattern_def["name"])
            for i, line in enumerate(lines, 1):
                # Skip comments
                stripped = line.strip()
                if stripped.startswith("#") or stripped.startswith("//"):
                    continue

                if re.search(pattern_def["pattern"], line):
                    # Context-aware severity adjustment
                    severity = pattern_def["severity"]

                    # If in a test file, downgrade severity
                    if "/test" in rel_path or "test_" in path.name or "_test." in path.name:
                        if severity == "critical":
                            severity = "moderate"
                        elif severity == "high":
                            severity = "moderate"

                    findings.append({
                        "file": rel_path,
                        "line": i,
                        "category": pattern_def["name"],
                        "severity": severity,
                        "description": f"{pattern_def['name']} detected",
                        "recommendation": pattern_def["recommendation"],
                        "cwe": pattern_def.get("cwe", ""),
                    })

    # Downgrade allowlisted findings to "info" (non-blocking)
    for f in findings:
        if is_allowlisted(f["file"]) and f["severity"] in ("critical", "high"):
            f["severity"] = "info"
            f["allowlisted"] = True

    critical_count = sum(1 for f in findings if f["severity"] == "critical")
    high_count = sum(1 for f in findings if f["severity"] == "high")

    return {
        "scan": "code",
        "status": "fail" if (critical_count + high_count) > 0 else "pass",
        "findings": findings,
        "stats": {
            "files_scanned": files_scanned,
            "patterns_checked": len(patterns_checked),
            "critical": critical_count,
            "high": high_count,
            "moderate": sum(1 for f in findings if f["severity"] == "moderate"),
            "low": sum(1 for f in findings if f["severity"] == "low"),
        }
    }


# ═══════════════════════════════════════════════════════════════════════════════
# BLOCKED PACKAGES SCAN
# ═══════════════════════════════════════════════════════════════════════════════

# Packages banned due to confirmed supply chain compromises.
# To add a new entry: append here AND update SECURITY_GUARDRAILS.md.
BLOCKED_PACKAGES = [
    {
        "name": "litellm",
        "pattern": r"\blitellm\b",
        "reason": "TeamPCP supply chain backdoor (versions 1.82.7-1.82.8) — credential harvesting, K8s lateral movement",
        "date_blocked": "2026-03-25",
        "alternative": "Direct SDK wrappers (OpenAI SDK, Langfuse SDK)",
    },
    {
        "name": "trivy",
        "pattern": r"\btrivy\b",
        "reason": "Compromised CI/CD credentials used as attack vector in TeamPCP campaign",
        "date_blocked": "2026-03-25",
        "alternative": "Snyk, Checkov, CodeQL, Semgrep",
    },
    {
        "name": "aquasecurity/trivy-action",
        "pattern": r"aquasecurity/trivy-action",
        "reason": "75 of 76 version tags force-pushed to credential stealer by TeamPCP",
        "date_blocked": "2026-03-25",
        "alternative": "Snyk GitHub Action, CodeQL Action",
    },
    {
        "name": "aquasecurity/setup-trivy",
        "pattern": r"aquasecurity/setup-trivy",
        "reason": "Tags v0.2.0-v0.2.6 force-pushed to malicious commits — exfiltrates CI/CD secrets",
        "date_blocked": "2026-03-25",
        "alternative": "Snyk GitHub Action, CodeQL Action",
    },
]


def scan_blocked_packages() -> dict:
    """Scan repository for references to blocked/compromised packages."""
    findings = []
    files_scanned = 0

    for path in ROOT_DIR.rglob("*"):
        if should_skip(path) or not path.is_file():
            continue
        if path.suffix not in TEXT_EXTENSIONS:
            continue
        # Skip this scanner's own definitions
        rel_path = str(path.relative_to(ROOT_DIR))
        if rel_path == "execution/security_scan.py":
            continue
        if rel_path == "SECURITY_GUARDRAILS.md":
            continue

        try:
            content = path.read_text(errors="ignore")
        except Exception:
            continue

        files_scanned += 1
        lines = content.split("\n")

        for blocked in BLOCKED_PACKAGES:
            for i, line in enumerate(lines, 1):
                if re.search(blocked["pattern"], line, re.IGNORECASE):
                    findings.append({
                        "file": rel_path,
                        "line": i,
                        "blocked_package": blocked["name"],
                        "reason": blocked["reason"],
                        "alternative": blocked["alternative"],
                        "severity": "critical",
                        "recommendation": f"Remove reference to '{blocked['name']}'. Use '{blocked['alternative']}' instead.",
                    })

    critical_count = len(findings)

    return {
        "scan": "blocked_packages",
        "status": "fail" if critical_count > 0 else "pass",
        "findings": findings,
        "stats": {
            "files_scanned": files_scanned,
            "blocked_patterns": len(BLOCKED_PACKAGES),
            "critical": critical_count,
        }
    }


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="Security scanning for pre-release gate",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument("mode", choices=["secrets", "dependencies", "code", "blocked", "all"],
                        help="Scan mode")
    parser.add_argument("--output", required=True, help="Output JSON file path")
    args = parser.parse_args()

    # Ensure output directory exists
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    scanners = {
        "secrets": scan_secrets,
        "dependencies": scan_dependencies,
        "code": scan_code,
        "blocked": scan_blocked_packages,
    }

    if args.mode == "all":
        results = {}
        overall_status = "pass"
        for name, scanner in scanners.items():
            print(f"🔍 Running {name} scan...", flush=True)
            result = scanner()
            results[name] = result
            if result["status"] == "fail":
                overall_status = "fail"
            elif result["status"] == "warn" and overall_status == "pass":
                overall_status = "warn"
            print(f"   → {result['status'].upper()}", flush=True)

        report = {
            "scan": "all",
            "overall_status": overall_status,
            "release_blocked": overall_status == "fail",
            "scans": results,
        }
    else:
        print(f"🔍 Running {args.mode} scan...", flush=True)
        report = scanners[args.mode]()
        report["release_blocked"] = report["status"] == "fail"

    # Write output
    output_path.write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))

    # Exit code
    if report.get("release_blocked") or report.get("overall_status") == "fail" or report.get("status") == "fail":
        sys.exit(2)
    elif report.get("overall_status") == "warn" or report.get("status") == "warn":
        sys.exit(3)
    sys.exit(0)


if __name__ == "__main__":
    main()
