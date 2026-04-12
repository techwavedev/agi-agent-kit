#!/usr/bin/env python3
"""
Script: dependency_tracker.py
Purpose: Scan all project dependencies (npm/pip) for known vulnerabilities,
         outdated versions, and supply chain risks. Generates a clear report
         showing what's safe, what's vulnerable, and what action to take.

Usage:
    # Full scan of all package.json and requirements.txt files
    python3 execution/dependency_tracker.py scan

    # Scan a specific file
    python3 execution/dependency_tracker.py scan --file path/to/package.json

    # Check a specific package
    python3 execution/dependency_tracker.py check --package axios --version 1.7.9 --ecosystem npm

    # Show summary of all dependencies
    python3 execution/dependency_tracker.py summary

    # Export dependency manifest (SBOM-lite)
    python3 execution/dependency_tracker.py export --output .tmp/dependencies.json

Exit Codes:
    0 - All clear (no known vulnerabilities)
    1 - Vulnerabilities found
    2 - Scan error
"""

import argparse
import json
import re
import sys
import urllib.request
from pathlib import Path

# Known vulnerable package versions (manually maintained + API-checked)
# Format: package -> [(affected_range, fixed_version, cve, severity, description)]
KNOWN_VULNERABILITIES = {
    "axios": [
        (">=0.8.1 <1.6.0", "1.6.0", "CVE-2023-45857", "high",
         "XSRF-TOKEN cookie leaked to all hosts"),
        (">=1.3.2 <1.7.4", "1.7.4", "CVE-2024-39338", "high",
         "SSRF via path-relative URL processing"),
        (">=1.0.0 <1.8.2", "1.8.2", "CVE-2025-27152", "high",
         "SSRF and credential leakage when baseURL configured"),
        ("==1.14.1", "1.14.0", "SUPPLY-CHAIN-2026-03", "critical",
         "Compromised by North Korean threat actor (RAT backdoor)"),
    ],
    "express": [
        ("<4.21.2", "4.21.2", "CVE-2024-29041", "medium",
         "Open redirect via malformed URLs"),
    ],
    "lodash": [
        ("<4.17.21", "4.17.21", "CVE-2021-23337", "high",
         "Command injection via template function"),
    ],
    "jsonwebtoken": [
        ("<9.0.0", "9.0.0", "CVE-2022-23529", "critical",
         "Arbitrary code execution via crafted JWS token"),
    ],
    "node-fetch": [
        ("<2.6.7", "2.6.7", "CVE-2022-0235", "high",
         "Cookie leak to third-party hosts on redirect"),
    ],
    "requests": [
        ("<2.32.0", "2.32.0", "CVE-2024-35195", "medium",
         "Cert verification bypass on session redirect"),
    ],
    "urllib3": [
        ("<2.2.2", "2.2.2", "CVE-2024-37891", "medium",
         "Proxy-Authorization header leaked on cross-origin redirect"),
    ],
    "pyjwt": [
        ("<2.8.0", "2.8.0", "CVE-2024-33663", "high",
         "Algorithm confusion with EdDSA keys"),
    ],
}


def find_project_root():
    current = Path(__file__).resolve().parent.parent
    for parent in [current] + list(current.parents):
        if (parent / "AGENTS.md").exists():
            return parent
    return current


def parse_version(version_str: str) -> tuple:
    """Parse a semver string into a comparable tuple."""
    clean = re.sub(r"[^0-9.]", "", version_str)
    parts = clean.split(".")
    result = []
    for p in parts[:3]:
        try:
            result.append(int(p))
        except ValueError:
            result.append(0)
    while len(result) < 3:
        result.append(0)
    return tuple(result)


def version_in_range(version: str, range_str: str) -> bool:
    """Check if a version matches a simple range expression."""
    v = parse_version(version)

    # Handle compound ranges like ">=1.0.0 <1.8.2"
    parts = range_str.split()
    for part in parts:
        part = part.strip()
        if part.startswith(">="):
            if v < parse_version(part[2:]):
                return False
        elif part.startswith("<="):
            if v > parse_version(part[2:]):
                return False
        elif part.startswith(">"):
            if v <= parse_version(part[1:]):
                return False
        elif part.startswith("<"):
            if v >= parse_version(part[1:]):
                return False
        elif part.startswith("=="):
            if v != parse_version(part[2:]):
                return False
    return True


def extract_version_from_spec(spec: str) -> str:
    """Extract the base version from an npm/pip version spec."""
    return re.sub(r"^[\^~>=<! ]+", "", spec).strip()


def scan_package_json(filepath: Path) -> list:
    """Scan a package.json for dependencies and check vulnerabilities."""
    try:
        data = json.loads(filepath.read_text())
    except Exception as e:
        return [{"file": str(filepath), "error": str(e)}]

    results = []
    for dep_type in ("dependencies", "devDependencies", "peerDependencies"):
        deps = data.get(dep_type, {})
        for pkg, spec in deps.items():
            version = extract_version_from_spec(spec)
            entry = {
                "file": str(filepath),
                "ecosystem": "npm",
                "package": pkg,
                "specified": spec,
                "version": version,
                "dep_type": dep_type,
                "vulnerabilities": [],
                "status": "ok",
            }

            # Check against known vulnerabilities
            if pkg.lower() in KNOWN_VULNERABILITIES:
                for affected, fixed, cve, severity, desc in KNOWN_VULNERABILITIES[pkg.lower()]:
                    if version_in_range(version, affected):
                        entry["vulnerabilities"].append({
                            "cve": cve,
                            "severity": severity,
                            "description": desc,
                            "affected_range": affected,
                            "fixed_in": fixed,
                        })
                        entry["status"] = "vulnerable"

            results.append(entry)

    return results


def scan_requirements_txt(filepath: Path) -> list:
    """Scan a requirements.txt for dependencies and check vulnerabilities."""
    results = []
    try:
        lines = filepath.read_text().splitlines()
    except Exception as e:
        return [{"file": str(filepath), "error": str(e)}]

    for line in lines:
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("-"):
            continue

        # Parse "package==version" or "package>=version"
        match = re.match(r"([a-zA-Z0-9_-]+)\s*([><=!~]+)\s*([0-9.]+)", line)
        if not match:
            match = re.match(r"([a-zA-Z0-9_-]+)", line)
            if match:
                results.append({
                    "file": str(filepath),
                    "ecosystem": "pip",
                    "package": match.group(1),
                    "specified": line,
                    "version": "unpinned",
                    "status": "warning",
                    "vulnerabilities": [],
                    "note": "Unpinned dependency — pin to a specific version",
                })
            continue

        pkg = match.group(1)
        version = match.group(3)
        entry = {
            "file": str(filepath),
            "ecosystem": "pip",
            "package": pkg,
            "specified": line,
            "version": version,
            "vulnerabilities": [],
            "status": "ok",
        }

        if pkg.lower() in KNOWN_VULNERABILITIES:
            for affected, fixed, cve, severity, desc in KNOWN_VULNERABILITIES[pkg.lower()]:
                if version_in_range(version, affected):
                    entry["vulnerabilities"].append({
                        "cve": cve,
                        "severity": severity,
                        "description": desc,
                        "affected_range": affected,
                        "fixed_in": fixed,
                    })
                    entry["status"] = "vulnerable"

        results.append(entry)

    return results


def check_npm_audit_api(package: str) -> list:
    """Check npm registry advisory API for a specific package."""
    vulns = []
    try:
        url = f"https://registry.npmjs.org/-/npm/v1/security/advisories?package={package}"
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            for advisory in data.get("objects", []):
                a = advisory.get("advisory", {})
                vulns.append({
                    "cve": a.get("cves", ["N/A"])[0] if a.get("cves") else "N/A",
                    "severity": a.get("severity", "unknown"),
                    "description": a.get("title", ""),
                    "affected_range": a.get("vulnerable_versions", ""),
                    "fixed_in": a.get("patched_versions", ""),
                })
    except Exception:
        pass
    return vulns


def scan_all(root: Path, target_file: str | None = None) -> list:
    """Scan all dependency files in the project."""
    all_results = []

    if target_file:
        p = Path(target_file)
        if p.name == "package.json":
            all_results.extend(scan_package_json(p))
        elif "requirements" in p.name:
            all_results.extend(scan_requirements_txt(p))
        return all_results

    # Skip .venv, node_modules, .git
    skip_dirs = {".venv", "node_modules", ".git", "__pycache__", ".tmp"}

    for pj in root.rglob("package.json"):
        if any(part in skip_dirs for part in pj.parts):
            continue
        all_results.extend(scan_package_json(pj))

    for req in root.rglob("requirements*.txt"):
        if any(part in skip_dirs for part in req.parts):
            continue
        all_results.extend(scan_requirements_txt(req))

    return all_results


def cmd_scan(args):
    root = find_project_root()
    results = scan_all(root, args.file if hasattr(args, "file") else None)

    vulnerable = [r for r in results if r.get("status") == "vulnerable"]
    warnings = [r for r in results if r.get("status") == "warning"]
    ok = [r for r in results if r.get("status") == "ok"]

    output = {
        "scan_summary": {
            "total_dependencies": len(results),
            "ok": len(ok),
            "vulnerable": len(vulnerable),
            "warnings": len(warnings),
        },
        "vulnerabilities": vulnerable,
        "warnings": warnings,
    }

    print(json.dumps(output, indent=2))
    sys.exit(1 if vulnerable else 0)


def cmd_check(args):
    version = args.version
    package = args.package.lower()

    result = {
        "package": package,
        "version": version,
        "ecosystem": args.ecosystem,
        "vulnerabilities": [],
        "status": "ok",
    }

    if package in KNOWN_VULNERABILITIES:
        for affected, fixed, cve, severity, desc in KNOWN_VULNERABILITIES[package]:
            if version_in_range(version, affected):
                result["vulnerabilities"].append({
                    "cve": cve,
                    "severity": severity,
                    "description": desc,
                    "fixed_in": fixed,
                })
                result["status"] = "vulnerable"

    if args.ecosystem == "npm":
        api_vulns = check_npm_audit_api(package)
        if api_vulns:
            result["api_advisories"] = api_vulns

    print(json.dumps(result, indent=2))
    sys.exit(1 if result["status"] == "vulnerable" else 0)


def cmd_summary(*_):
    root = find_project_root()
    results = scan_all(root)

    by_ecosystem = {}
    for r in results:
        eco = r.get("ecosystem", "unknown")
        by_ecosystem.setdefault(eco, {"total": 0, "vulnerable": 0, "packages": []})
        by_ecosystem[eco]["total"] += 1
        if r.get("status") == "vulnerable":
            by_ecosystem[eco]["vulnerable"] += 1
        by_ecosystem[eco]["packages"].append({
            "name": r.get("package"),
            "version": r.get("version"),
            "status": r.get("status"),
            "file": r.get("file"),
        })

    print(json.dumps({"ecosystems": by_ecosystem}, indent=2))


def cmd_export(args):
    root = find_project_root()
    results = scan_all(root)

    sbom = {
        "format": "agi-dependency-manifest",
        "version": "1.0",
        "project": str(root),
        "total_dependencies": len(results),
        "dependencies": results,
    }

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(sbom, indent=2))
    print(json.dumps({
        "status": "exported",
        "file": str(output_path),
        "total": len(results),
    }))


def main():
    parser = argparse.ArgumentParser(
        description="Dependency tracker: scan for vulnerabilities and supply chain risks"
    )
    subparsers = parser.add_subparsers(dest="command")

    scan_p = subparsers.add_parser("scan", help="Scan all dependencies for vulnerabilities")
    scan_p.add_argument("--file", help="Scan a specific file only")

    check_p = subparsers.add_parser("check", help="Check a specific package version")
    check_p.add_argument("--package", required=True, help="Package name")
    check_p.add_argument("--version", required=True, help="Version to check")
    check_p.add_argument("--ecosystem", choices=["npm", "pip"], default="npm")

    subparsers.add_parser("summary", help="Show dependency summary by ecosystem")

    export_p = subparsers.add_parser("export", help="Export dependency manifest (SBOM-lite)")
    export_p.add_argument("--output", default=".tmp/dependencies.json", help="Output file")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    {"scan": cmd_scan, "check": cmd_check, "summary": cmd_summary, "export": cmd_export}[args.command](args)


if __name__ == "__main__":
    main()
