#!/usr/bin/env python3
"""
Script: update_kit.py
Purpose: Update AGI Agent Kit to the latest version

Usage:
    python3 skills/self-update/scripts/update_kit.py [--check-only] [--force]

Arguments:
    --check-only  Only check for updates, don't install
    --force       Skip confirmation prompt

Exit Codes:
    0 - Success (or no update needed)
    1 - Error during update
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path


def run_cmd(cmd: list, capture=True) -> tuple:
    """Run command and return (success, output)"""
    try:
        result = subprocess.run(cmd, capture_output=capture, text=True)
        return result.returncode == 0, result.stdout.strip()
    except Exception as e:
        return False, str(e)


def get_installed_version(root: Path) -> str:
    """Get installed version from .agi.json"""
    agi_json = root / ".agi.json"
    if agi_json.exists():
        try:
            data = json.loads(agi_json.read_text())
            return data.get("version", "unknown")
        except:
            pass
    return "unknown"


def get_latest_version() -> str:
    """Get latest version from NPM"""
    success, output = run_cmd(["npm", "view", "@techwavedev/agi-agent-kit", "version"])
    return output if success else "unknown"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check-only', action='store_true', help='Only check for updates')
    parser.add_argument('--force', action='store_true', help='Skip confirmation')
    args = parser.parse_args()

    root = Path(__file__).resolve().parent.parent.parent.parent
    
    print("🔍 Checking versions...")
    installed = get_installed_version(root)
    latest = get_latest_version()
    
    print(f"   Installed: {installed}")
    print(f"   Latest:    {latest}")
    
    if installed == latest:
        print("\n✅ Already up to date!")
        sys.exit(0)
    
    if args.check_only:
        if installed != latest and latest != "unknown":
            print(f"\n📦 Update available: {installed} → {latest}")
            print("   Run without --check-only to update")
        sys.exit(0)
    
    # Confirm update
    if not args.force:
        print(f"\n📦 Update available: {installed} → {latest}")
        response = input("Proceed with update? [y/N]: ").strip().lower()
        if response != 'y':
            print("Update cancelled.")
            sys.exit(0)
    
    # Run update
    print("\n🚀 Updating AGI Agent Kit...")
    print("   Running: npx @techwavedev/agi-agent-kit@latest init --pack=full\n")
    
    result = subprocess.run(
        ["npx", "@techwavedev/agi-agent-kit@latest", "init", "--pack=full"],
        cwd=root
    )
    
    if result.returncode == 0:
        print("\n✅ Update complete!")
        print("   Run 'python3 execution/system_checkup.py' to verify")
    else:
        print("\n❌ Update failed. Check output above.")
        sys.exit(1)


if __name__ == '__main__':
    main()
