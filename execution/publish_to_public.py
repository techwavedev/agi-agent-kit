#!/usr/bin/env python3
"""
publish_to_public.py — Safe filtered merge from main to public.

REPLACES: `git merge main` (which is unfiltered and leaks private files).

This script:
1. Reads .private manifest for the list of private-only files
2. Merges main into public
3. Removes all private-only files from the resulting tree
4. Commits the clean state
5. Optionally pushes to the public remote

Usage:
  python3 execution/publish_to_public.py              # merge + clean (no push)
  python3 execution/publish_to_public.py --push       # merge + clean + push
  python3 execution/publish_to_public.py --dry-run    # show what would happen
"""

import argparse
import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
MANIFEST = ROOT_DIR / ".private"


def run(cmd, check=True, capture=True):
    """Run a shell command and return output."""
    result = subprocess.run(
        cmd, shell=True, capture_output=capture, text=True, cwd=ROOT_DIR
    )
    if check and result.returncode != 0:
        print(f"FAILED: {cmd}")
        print(result.stderr)
        sys.exit(1)
    return result


def load_private_files():
    """Read .private manifest, return list of relative paths."""
    if not MANIFEST.exists():
        print("ERROR: .private manifest not found at repo root.")
        print("       Create it with the list of private-only file paths.")
        sys.exit(1)

    paths = []
    for line in MANIFEST.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        paths.append(line)
    return paths


def get_current_branch():
    result = run("git branch --show-current")
    return result.stdout.strip()


def main():
    parser = argparse.ArgumentParser(description="Safe filtered merge from main to public")
    parser.add_argument("--push", action="store_true", help="Push to public remote after merge")
    parser.add_argument("--dry-run", action="store_true", help="Show what would happen without doing it")
    args = parser.parse_args()

    private_files = load_private_files()
    print(f"📋 Loaded {len(private_files)} private-only paths from .private")

    # --- Pre-flight checks ---
    branch = get_current_branch()
    if branch != "public":
        print(f"ERROR: Must be on 'public' branch. Currently on '{branch}'.")
        print("       Run: git checkout public")
        sys.exit(1)

    # Check for uncommitted changes
    status = run("git status --porcelain").stdout.strip()
    if status:
        print("ERROR: Working tree is not clean. Commit or stash changes first.")
        print(status)
        sys.exit(1)

    if args.dry_run:
        print("\n🔍 DRY RUN — would perform these steps:")
        print("  1. git merge main --no-edit")
        print(f"  2. git rm {len(private_files)} private-only files:")
        for f in private_files:
            exists = (ROOT_DIR / f).exists()
            marker = "  (exists)" if exists else "  (not present)"
            print(f"       - {f}{marker}")
        print("  3. git commit --amend (clean merge)")
        if args.push:
            print("  4. git push public public")
        return

    # --- Step 1: Merge main into public ---
    print("\n📦 Step 1: Merging main into public...")
    merge_result = run("git merge main --no-edit", check=False)
    if merge_result.returncode != 0:
        if "CONFLICT" in merge_result.stdout or "CONFLICT" in merge_result.stderr:
            print("⚠️  Merge conflicts detected. Resolve them manually, then re-run this script.")
            sys.exit(1)
        elif "Already up to date" in merge_result.stdout:
            print("   Already up to date — nothing to merge.")
            return
        else:
            print(f"   Merge failed: {merge_result.stderr}")
            sys.exit(1)
    print("   ✅ Merge complete")

    # --- Step 2: Remove private-only files ---
    print(f"\n🔒 Step 2: Removing {len(private_files)} private-only files...")
    removed = []
    for rel_path in private_files:
        full_path = ROOT_DIR / rel_path
        if full_path.exists():
            run(f'git rm -f "{rel_path}"')
            removed.append(rel_path)
            print(f"   🗑️  Removed: {rel_path}")
        else:
            print(f"   ⏭️  Skipped (not present): {rel_path}")

    # --- Step 3: Amend the merge commit to include removals ---
    if removed:
        print(f"\n📝 Step 3: Amending merge commit with {len(removed)} removals...")
        removed_list = ", ".join(removed)
        run(f'git commit --amend --no-edit -m "Merge branch \'main\' into public (filtered)\n\nPrivate files excluded: {removed_list}"')
        print("   ✅ Clean merge committed")
    else:
        print("\n   ℹ️  No private files found to remove — merge is already clean.")

    # --- Step 4: Verify ---
    print("\n🔍 Step 4: Verification...")
    issues = []
    for rel_path in private_files:
        full_path = ROOT_DIR / rel_path
        if full_path.exists():
            issues.append(rel_path)

    if issues:
        print(f"   ❌ FAILED — these private files still exist:")
        for f in issues:
            print(f"      - {f}")
        sys.exit(1)
    else:
        print("   ✅ All private files confirmed absent from public branch")

    # --- Step 5: Push (optional) ---
    if args.push:
        print("\n🚀 Step 5: Pushing to public remote...")
        run("git push public public")
        run("git push synology public")
        print("   ✅ Pushed to public and synology")
    else:
        print("\n   ℹ️  Not pushing (use --push to auto-push)")

    print("\n✅ Publish to public complete!")


if __name__ == "__main__":
    main()
