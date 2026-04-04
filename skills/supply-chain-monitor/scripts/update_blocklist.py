#!/usr/bin/env python3
"""
Script: update_blocklist.py
Purpose: Patch BLOCKED_PACKAGES in security_scan.py and the blocked packages
         table in SECURITY_GUARDRAILS.md with newly discovered threats.

Usage:
    # Dry run (default) — preview changes
    python3 skills/supply-chain-monitor/scripts/update_blocklist.py \
      --input .tmp/supply-chain/extracted_packages.json

    # Apply changes
    python3 skills/supply-chain-monitor/scripts/update_blocklist.py \
      --input .tmp/supply-chain/extracted_packages.json --confirm

Arguments:
    --input, -i    Extracted packages JSON from extract_packages.py (required)
    --confirm      Actually write changes (default: dry-run only)
    --verbose      Enable detailed logging

Exit Codes:
    0 - Success (changes applied or nothing to do)
    1 - Invalid arguments
    2 - Input file not found
    3 - Target file parse error
"""

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
SECURITY_SCAN_PATH = ROOT_DIR / "execution" / "security_scan.py"
GUARDRAILS_PATH = ROOT_DIR / "SECURITY_GUARDRAILS.md"


def get_existing_blocked_names() -> set:
    """Parse existing BLOCKED_PACKAGES from security_scan.py."""
    content = SECURITY_SCAN_PATH.read_text()
    names = set()

    # Find all "name": "..." entries in BLOCKED_PACKAGES
    block_match = re.search(r"BLOCKED_PACKAGES\s*=\s*\[(.+?)\]", content, re.DOTALL)
    if block_match:
        block_text = block_match.group(1)
        for name_match in re.finditer(r'"name":\s*"([^"]+)"', block_text):
            names.add(name_match.group(1).lower())

    return names


def generate_scan_entry(pkg: dict) -> str:
    """Generate a Python dict entry for BLOCKED_PACKAGES."""
    name = pkg["name"]
    pattern = pkg.get("pattern", rf"\b{re.escape(name)}\b")
    reason = pkg.get("reason", "Supply chain compromise detected by TheHackerNews monitor")[:200]
    reason = reason.replace('"', '\\"')
    date = pkg.get("source_date", datetime.now(timezone.utc).strftime("%Y-%m-%d"))[:10]
    alt = pkg.get("alternative", "")

    return f"""    {{
        "name": "{name}",
        "pattern": r"{pattern}",
        "reason": "{reason}",
        "date_blocked": "{date}",
        "alternative": "{alt}",
    }},"""


def generate_guardrails_row(pkg: dict) -> str:
    """Generate a markdown table row for SECURITY_GUARDRAILS.md."""
    name = f"`{pkg['name']}`"
    reason = pkg.get("reason", "Supply chain compromise")[:80]
    date = pkg.get("source_date", datetime.now(timezone.utc).strftime("%Y-%m-%d"))[:10]
    alt = pkg.get("alternative", "TBD")
    return f"| {name} | {reason} | {date} | {alt} |"


def patch_security_scan(new_packages: list, dry_run: bool) -> dict:
    """Patch BLOCKED_PACKAGES list in security_scan.py."""
    content = SECURITY_SCAN_PATH.read_text()

    # Find the closing bracket of BLOCKED_PACKAGES
    marker = re.search(r"(BLOCKED_PACKAGES\s*=\s*\[.+?)(^\])", content, re.DOTALL | re.MULTILINE)
    if not marker:
        return {"status": "error", "message": "Could not find BLOCKED_PACKAGES closing bracket"}

    insert_point = marker.start(2)
    new_entries = "\n".join(generate_scan_entry(pkg) for pkg in new_packages)
    new_content = content[:insert_point] + new_entries + "\n" + content[insert_point:]

    if dry_run:
        return {"status": "dry_run", "diff_preview": new_entries, "file": str(SECURITY_SCAN_PATH)}

    SECURITY_SCAN_PATH.write_text(new_content)
    return {"status": "applied", "entries_added": len(new_packages), "file": str(SECURITY_SCAN_PATH)}


def patch_guardrails(new_packages: list, dry_run: bool) -> dict:
    """Patch blocked packages table in SECURITY_GUARDRAILS.md."""
    content = GUARDRAILS_PATH.read_text()

    # Find the table — look for the line before "### Enforcement"
    enforcement_match = re.search(r"^### Enforcement", content, re.MULTILINE)
    if not enforcement_match:
        return {"status": "error", "message": "Could not find '### Enforcement' marker in SECURITY_GUARDRAILS.md"}

    insert_point = enforcement_match.start()
    new_rows = "\n".join(generate_guardrails_row(pkg) for pkg in new_packages)
    new_content = content[:insert_point] + new_rows + "\n\n" + content[insert_point:]

    if dry_run:
        return {"status": "dry_run", "diff_preview": new_rows, "file": str(GUARDRAILS_PATH)}

    GUARDRAILS_PATH.write_text(new_content)
    return {"status": "applied", "rows_added": len(new_packages), "file": str(GUARDRAILS_PATH)}


def main():
    parser = argparse.ArgumentParser(description="Update blocked packages list")
    parser.add_argument("--input", "-i", required=True, help="Extracted packages JSON")
    parser.add_argument("--confirm", action="store_true", help="Apply changes (default: dry-run)")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(json.dumps({"status": "error", "message": f"Input not found: {args.input}"}), file=sys.stderr)
        sys.exit(2)

    packages = json.loads(input_path.read_text())
    if not isinstance(packages, list):
        print(json.dumps({"status": "error", "message": "Input must be a JSON array"}), file=sys.stderr)
        sys.exit(1)

    # Check what's already blocked
    existing = get_existing_blocked_names()
    new_packages = [p for p in packages if p["name"].lower() not in existing]
    already_blocked = [p["name"] for p in packages if p["name"].lower() in existing]

    if not new_packages:
        result = {
            "status": "no_changes",
            "message": "All extracted packages are already blocked",
            "already_blocked": already_blocked,
        }
        print(json.dumps(result, indent=2))
        sys.exit(0)

    dry_run = not args.confirm

    if args.verbose or dry_run:
        print(f"{'[DRY RUN] ' if dry_run else ''}Processing {len(new_packages)} new packages:", file=sys.stderr)
        for pkg in new_packages:
            print(f"  - {pkg['name']} ({pkg.get('ecosystem', 'unknown')}, {pkg.get('confidence', '?')})", file=sys.stderr)

    # Patch both files
    scan_result = patch_security_scan(new_packages, dry_run)
    guardrails_result = patch_guardrails(new_packages, dry_run)

    result = {
        "status": "dry_run" if dry_run else "applied",
        "new_packages": [p["name"] for p in new_packages],
        "already_blocked": already_blocked,
        "security_scan": scan_result,
        "guardrails": guardrails_result,
    }

    if dry_run:
        result["message"] = "Run with --confirm to apply these changes"

    print(json.dumps(result, indent=2))
    sys.exit(0)


if __name__ == "__main__":
    main()
