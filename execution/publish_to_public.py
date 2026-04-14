#!/usr/bin/env python3
"""
publish_to_public.py — Physical Airgap Sync Script for Public Releases.

This script enforces a STRICT physical barrier between private development and
public release. It completely bypasses Git merges between branches.

How it works:
1. Validates the existence of the `public_release/` airgap folder.
2. Reads `.private` as the single source of truth for blocked files.
3. Wipes the `public_release/` folder clean (preserving its `.git`).
4. Copies all allowed files from the root repo into `public_release/`.
5. Runs the release gate ON the airgap folder to guarantee no leaks.
6. Commits the new state in the `public_release/` folder.

Usage:
  python3 execution/publish_to_public.py              # sync + commit (no push)
  python3 execution/publish_to_public.py --push       # sync + commit + push
  python3 execution/publish_to_public.py --dry-run    # show what would be blocked
"""

import argparse
import subprocess
import sys
import shutil
import os
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
MANIFEST = ROOT_DIR / ".private"
PUBLIC_DIR = ROOT_DIR / "public_release_repo"

IGNORED_ROOT_DIRS = {".git", "public_release", "public_release_repo", "node_modules", ".venv", ".idea", "__pycache__"}


def run(cmd, check=True, capture=True, cwd=None):
    """Run a shell command and return output."""
    if cwd is None:
        cwd = PUBLIC_DIR
    result = subprocess.run(
        cmd, shell=True, capture_output=capture, text=True, cwd=cwd
    )
    if check and result.returncode != 0:
        print(f"FAILED: {cmd}")
        print(result.stderr or result.stdout)
        sys.exit(1)
    return result


def load_private_files():
    """Read .private manifest, return list of relative paths."""
    if not MANIFEST.exists():
        print("ERROR: .private manifest not found at repo root.")
        sys.exit(1)

    paths = []
    for line in MANIFEST.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        paths.append(line)
    return set(paths)


def sync_directory(src_root, dest_root, private_files, dry_run=False):
    """Copy files from src to dest ONLY if they are tracked by git and not in .private."""
    copied = 0
    blocked = 0

    if not dry_run:
        # Wipe the destination clean (except .git)
        for item in dest_root.iterdir():
            if item.name == ".git":
                continue
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()

    # Get explicitly tracked files from Git
    tracked_files = subprocess.run(
        ["git", "ls-files"], cwd=src_root, capture_output=True, text=True, check=True
    ).stdout.splitlines()

    for rel_path in tracked_files:
        if not rel_path or rel_path.startswith("public_release"):
            continue

        if rel_path in private_files or rel_path == ".private":
            if dry_run:
                print(f"   🚫 BLOCKED: {rel_path}")
            blocked += 1
            continue

        # Ensure destination directory exists
        src_file = src_root / rel_path
        dest_file = dest_root / rel_path

        if not src_file.is_file():
            # Could be a submodule or missing file, skip
            continue

        if not dry_run:
            dest_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_file, dest_file)
        copied += 1

    return copied, blocked


def main():
    parser = argparse.ArgumentParser(description="Airgap Sync to Public Release folder")
    parser.add_argument("--push", action="store_true", help="Push to public remote after sync")
    parser.add_argument("--dry-run", action="store_true", help="Only show file blocking simulation")
    args = parser.parse_args()

    print("🛡️  AGI Airgap Sync Protocol Started\n")

    if not (PUBLIC_DIR / ".git").exists():
        print("❌ ERROR: 'public_release/' directory is not a valid Git repository.")
        print("   Initialize it first: git clone https://github.com/techwavedev/agi-agent-kit.git public_release")
        sys.exit(1)

    private_files = load_private_files()
    print(f"📋 Loaded {len(private_files)} blocked paths from .private manifest\n")

    if args.dry_run:
        print("🔍 DRY RUN — Simulation of file sync:")
        copied, blocked = sync_directory(ROOT_DIR, PUBLIC_DIR, private_files, dry_run=True)
        print(f"\n✅ Simulation complete. Would copy {copied} files. Blocked {blocked} private files.")
        return

    # --- Step 1: Wipe & Sync ---
    print("📦 Step 1: Syncing files across the airgap...")
    copied, blocked = sync_directory(ROOT_DIR, PUBLIC_DIR, private_files, dry_run=False)
    print(f"   ✅ Copied {copied} files securely. Excluded {blocked} private-only files.")

    # --- Step 2: Release Gate Validation ---
    print("\n🔒 Step 2: Scanning airgapped folder via Release Gate...")
    print("   Running `.agent/scripts/release_gate.py` against `public_release/` to guard against manifest misses.")
    
    # We must explicitly run the release gate within the public_release directory to scan its contents!
    release_gate_script = PUBLIC_DIR / ".agent" / "scripts" / "release_gate.py"
    if release_gate_script.exists():
        env = os.environ.copy()
        env["CI"] = "true"  # Force non-interactive evaluation
        validation = subprocess.run(
            [sys.executable, str(release_gate_script)],
            cwd=PUBLIC_DIR, capture_output=True, text=True, env=env
        )
        if validation.returncode != 0:
            print("❌ CRITICAL: Release Gate caught a security failure in the synchronized files!")
            print(validation.stdout)
            print(validation.stderr)
            print("⚠️ The public_release folder is tainted. Fix the source, add to .private if needed, and re-sync.")
            sys.exit(1)
        else:
            print("   ✅ Airgap scan passed. No leaked paths or security faults detected.")
    else:
        print("   ⚠️  Warning: Release Gate script not found in destination. Assuming safe.")

    # --- Step 3: Commit in public_release ---
    print("\n📝 Step 3: Committing to public_release local repository...")
    status = run("git status --porcelain").stdout.strip()
    if not status:
        print("   ℹ️  No changes detected between main repo and public release.")
    else:
        run("git add .")
        run('git commit -m "sync: airgap update from private development source"')
        print("   ✅ Committed changes to public_release local branch.")

    # --- Step 4: Push ---
    if args.push:
        print("\n🚀 Step 4: Pushing to public remote (NPM Release Trigger)...")
        run("git push origin public") # assuming default branch there is public
        print("   ✅ Push complete!")
    else:
        print("\n   ℹ️  Changes committed locally in public_release/ but not pushed yet.")
        print("      Run with --push to deploy, or cd into public_release and push manually.")


if __name__ == "__main__":
    main()
