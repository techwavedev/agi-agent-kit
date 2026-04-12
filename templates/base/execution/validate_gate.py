#!/usr/bin/env python3
"""
Script: validate_gate.py
Purpose: Standalone Output Gate validator. Runs the bash gate command from
         a dispatch manifest and prints VALIDATION:PASS or VALIDATION:FAIL.

Usage:
    # Validate from a manifest JSON (stdin or file)
    python3 execution/validate_gate.py --manifest .tmp/manifest.json --agent doc-writer

    # Validate a list of files directly
    python3 execution/validate_gate.py --files CHANGELOG.md docs/execution/gates.md

    # Validate from a gate command string
    python3 execution/validate_gate.py --command 'set -e; test -s CHANGELOG.md && echo VALIDATION:PASS'

Exit Codes:
    0 - VALIDATION:PASS (all files exist and are non-empty)
    1 - VALIDATION:FAIL (one or more files missing or empty)
    2 - Invalid arguments
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


def validate_files(file_list: list) -> tuple:
    """Check that all files exist and are non-empty. Returns (pass, failed_path)."""
    for f in file_list:
        p = Path(f)
        if not p.exists() or p.stat().st_size == 0:
            return False, str(f)
    return True, None


def validate_command(command: str) -> tuple:
    """Run a bash gate command and parse stdout. Returns (pass, output)."""
    result = subprocess.run(
        ["bash", "-c", command],
        capture_output=True,
        text=True,
        timeout=30,
    )
    stdout = result.stdout.strip()
    if "VALIDATION:PASS" in stdout:
        return True, stdout
    return False, stdout


def validate_from_manifest(manifest_path: str, agent_id: str) -> tuple:
    """Extract and run the gate for a specific agent from a manifest."""
    with open(manifest_path, "r") as f:
        manifest = json.load(f)

    normalized = agent_id.replace("-", "_")
    for sa in manifest.get("sub_agents", []):
        sa_id = sa.get("id", "").replace("-", "_")
        if sa_id == normalized:
            gate = sa.get("validation_gate")
            if not gate:
                return True, f"Agent '{agent_id}' has no validation_gate — skipped"
            return validate_command(gate["command"])

    return False, f"Agent '{agent_id}' not found in manifest"


def main():
    parser = argparse.ArgumentParser(
        description="Validate Output Gates — hallucination-proof file checks"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--manifest", help="Path to dispatch manifest JSON")
    group.add_argument("--files", nargs="+", help="List of files to validate")
    group.add_argument("--command", help="Raw gate command to execute")
    parser.add_argument("--agent", help="Agent ID (required with --manifest)")
    args = parser.parse_args()

    if args.manifest:
        if not args.agent:
            print("Error: --agent required with --manifest", file=sys.stderr)
            sys.exit(2)
        passed, output = validate_from_manifest(args.manifest, args.agent)
    elif args.files:
        passed, failed = validate_files(args.files)
        if passed:
            output = "VALIDATION:PASS"
        else:
            output = f"VALIDATION:FAIL:{failed}"
    else:
        passed, output = validate_command(args.command)

    print(output)
    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
