#!/usr/bin/env python3
"""
Data Cleanup Manager for NotebookLM RAG Skill
Handles cleaning browser data, auth state, and optionally library
"""

import argparse
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from config import DATA_DIR, BROWSER_STATE_DIR, STATE_FILE, AUTH_INFO_FILE, LIBRARY_FILE


def preview_cleanup(preserve_library: bool = False):
    """Show what would be cleaned up"""
    print("🔍 Cleanup Preview:")
    items = []

    if BROWSER_STATE_DIR.exists():
        size = sum(f.stat().st_size for f in BROWSER_STATE_DIR.rglob('*') if f.is_file())
        items.append(f"  Browser state: {size / 1024:.1f} KB")

    if STATE_FILE.exists():
        items.append(f"  State file: {STATE_FILE}")

    if AUTH_INFO_FILE.exists():
        items.append(f"  Auth info: {AUTH_INFO_FILE}")

    if not preserve_library and LIBRARY_FILE.exists():
        items.append(f"  Library: {LIBRARY_FILE}")
    elif preserve_library and LIBRARY_FILE.exists():
        items.append(f"  Library: PRESERVED ✓")

    if items:
        for item in items:
            print(item)
    else:
        print("  Nothing to clean up")

    return len(items) > 0


def execute_cleanup(preserve_library: bool = False):
    """Execute cleanup"""
    print("🗑️ Cleaning up...")

    if BROWSER_STATE_DIR.exists():
        shutil.rmtree(BROWSER_STATE_DIR)
        BROWSER_STATE_DIR.mkdir(parents=True, exist_ok=True)
        print("  ✅ Cleared browser state")

    if STATE_FILE.exists():
        STATE_FILE.unlink()
        print("  ✅ Removed state file")

    if AUTH_INFO_FILE.exists():
        AUTH_INFO_FILE.unlink()
        print("  ✅ Removed auth info")

    if not preserve_library and LIBRARY_FILE.exists():
        LIBRARY_FILE.unlink()
        print("  ✅ Removed library")
    elif preserve_library:
        print("  📚 Library preserved")

    print("  ✅ Cleanup complete!")


def main():
    parser = argparse.ArgumentParser(description='Clean up NotebookLM RAG skill data')
    parser.add_argument('--confirm', action='store_true', help='Execute cleanup (default: preview only)')
    parser.add_argument('--preserve-library', action='store_true', help='Keep notebook library')

    args = parser.parse_args()

    if args.confirm:
        execute_cleanup(preserve_library=args.preserve_library)
    else:
        has_items = preview_cleanup(preserve_library=args.preserve_library)
        if has_items:
            print("\nRun with --confirm to execute cleanup")


if __name__ == "__main__":
    main()
