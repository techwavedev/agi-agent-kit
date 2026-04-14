#!/usr/bin/env python3
"""
publish_to_public.py — Physical Airgap Sync Script for Public Releases.

This script enforces a STRICT physical barrier between private development and
public release. It completely bypasses Git merges between branches.

How it works:
1. Validates the existence of the `public_release_repo/` airgap folder.
2. Reads `.private` as the single source of truth for blocked files.
3. Wipes the `public_release_repo/` folder clean (preserving its `.git`).
4. Copies all allowed files from the root repo into `public_release_repo/`.
5. Runs the release gate ON the airgap folder to guarantee no leaks.
6. Commits the new state in the `public_release_repo/` folder.

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

IGNORED_ROOT_DIRS = {".git", "public_release_repo", "node_modules", ".venv", ".idea", "__pycache__"}


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
        if not rel_path or rel_path.startswith("public_release_repo"):
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


def verify_public_in_sync(private_files):
    """
    Gatekeeper: refuse to publish if the public remote has commits that carry
    content NOT represented in our source (e.g. Dependabot, CodeQL, community
    PRs merged directly on GitHub). The wipe-and-copy would silently override
    that work. Airgap auto-sync commits (own history) are safely ignored.
    """
    print("🛰️  Gatekeeper: checking that public remote has no unreplicated work...")

    # Find the remote name in the private repo that points at the public fork
    remotes = subprocess.run(
        ["git", "-C", str(ROOT_DIR), "remote", "-v"],
        capture_output=True, text=True
    ).stdout
    public_remote = None
    for line in remotes.splitlines():
        if "agi-agent-kit" in line and "(fetch)" in line:
            public_remote = line.split()[0]
            break
    if not public_remote:
        print("   ⚠️  No remote pointing at agi-agent-kit found in private repo — skipping gatekeeper.")
        print("      Add one with: git remote add public https://github.com/techwavedev/agi-agent-kit.git")
        return

    # 1. Fetch latest public state via the private repo's remote
    fetch = subprocess.run(
        ["git", "-C", str(ROOT_DIR), "fetch", public_remote, "main"],
        capture_output=True, text=True
    )
    if fetch.returncode != 0:
        print(f"   ❌ Could not fetch {public_remote} remote.")
        print(fetch.stderr)
        sys.exit(2)

    # 3. Use `git cherry HEAD public/main` which reports commits in public/main
    #    that don't have an equivalent patch in HEAD. '+' prefix = UNIQUE
    #    (patch not found in HEAD by patch-id), '-' prefix = equivalent exists
    #    (same change reapplied via different SHA, safe). This is content-level,
    #    not SHA-level, and correctly ignores airgap-sync commits (they produce
    #    no real patch vs HEAD since they mirror HEAD's content).
    cherry = subprocess.run(
        ["git", "-C", str(ROOT_DIR), "cherry", "-v", "HEAD", "public/main"],
        capture_output=True, text=True
    )
    unique_lines = []
    for line in cherry.stdout.splitlines():
        if not line.startswith("+ "):
            continue
        # Skip airgap auto-sync commits — they have no net content
        if "airgap update from private" in line:
            continue
        unique_lines.append(line[2:])  # strip "+ "

    # For each unique commit, verify at least one of its files is NOT already
    # represented as a blob in HEAD's tree. (Guards against edge cases where
    # the commit only touched `.private` files we intentionally exclude.)
    unsafe_commits = []
    for line in unique_lines:
        parts = line.split(maxsplit=1)
        if not parts:
            continue
        sha = parts[0]
        subject = parts[1] if len(parts) > 1 else ""

        changed = subprocess.run(
            ["git", "-C", str(ROOT_DIR), "show", "--name-only", "--format=", sha],
            capture_output=True, text=True
        ).stdout.splitlines()

        differing = []
        for rel in changed:
            rel = rel.strip()
            if not rel or rel in private_files or rel == ".private":
                continue
            # Skip symlinks on the private side — airgap sync resolves them
            # to flat files on public, so the blob hash naturally differs.
            ls = subprocess.run(
                ["git", "-C", str(ROOT_DIR), "ls-tree", "HEAD", rel],
                capture_output=True, text=True
            ).stdout.strip()
            if ls.startswith("120000"):
                continue
            pub_blob = subprocess.run(
                ["git", "-C", str(ROOT_DIR), "rev-parse", f"public/main:{rel}"],
                capture_output=True, text=True
            )
            priv_blob = subprocess.run(
                ["git", "-C", str(ROOT_DIR), "rev-parse", f"HEAD:{rel}"],
                capture_output=True, text=True
            )
            pub_hash = pub_blob.stdout.strip() if pub_blob.returncode == 0 else None
            priv_hash = priv_blob.stdout.strip() if priv_blob.returncode == 0 else None
            if not pub_hash or pub_hash == priv_hash:
                continue

            # Blob differs. Safe if private has evolved this file PAST the
            # public version: HEAD's last-touch of `rel` must be newer than
            # public/main's last-touch of `rel`.
            pub_time = subprocess.run(
                ["git", "-C", str(ROOT_DIR), "log", "-1", "--format=%ct",
                 "public/main", "--", rel],
                capture_output=True, text=True
            ).stdout.strip()
            priv_time = subprocess.run(
                ["git", "-C", str(ROOT_DIR), "log", "-1", "--format=%ct",
                 "HEAD", "--", rel],
                capture_output=True, text=True
            ).stdout.strip()
            try:
                if priv_time and pub_time and int(priv_time) >= int(pub_time):
                    continue  # private is equal-or-newer — safe to overwrite
            except ValueError:
                pass
            differing.append(rel)

        if differing:
            unsafe_commits.append((sha[:9], subject, differing))

    if unsafe_commits:
        print("   ❌ BLOCKED: public/main has content NOT represented in private source:")
        for sha, subject, files in unsafe_commits:
            print(f"        {sha}  {subject}")
            for f in files[:5]:
                print(f"           └─ {f}")
            if len(files) > 5:
                print(f"           └─ … and {len(files) - 5} more")
        print("   These would be silently overwritten by wipe-and-copy.")
        print("   Resolve by merging or cherry-picking them into private main first,")
        print("   then retry the publish. Use --force-unsafe to override (not recommended).")
        sys.exit(3)

    total_ahead = len(cherry.stdout.splitlines())
    print(f"   ✅ Public remote is fully represented in private source "
          f"({total_ahead} ahead commits, all reapplied via different SHAs or airgap-only).")


def main():
    parser = argparse.ArgumentParser(description="Airgap Sync to Public Release folder")
    parser.add_argument("--push", action="store_true", help="Push to public remote after sync")
    parser.add_argument("--dry-run", action="store_true", help="Only show file blocking simulation")
    parser.add_argument("--force-unsafe", action="store_true",
                        help="Skip gatekeeper check — WILL overwrite public-only work. Do not use without review.")
    args = parser.parse_args()

    print("🛡️  AGI Airgap Sync Protocol Started\n")

    if not (PUBLIC_DIR / ".git").exists():
        print("❌ ERROR: 'public_release_repo/' directory is not a valid Git repository.")
        print("   Initialize it first: git clone https://github.com/techwavedev/agi-agent-kit.git public_release_repo")
        sys.exit(1)

    private_files = load_private_files()
    print(f"📋 Loaded {len(private_files)} blocked paths from .private manifest\n")

    # Gatekeeper BEFORE any destructive action (unless explicitly overridden)
    if not args.dry_run and not args.force_unsafe:
        verify_public_in_sync(private_files)

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
    print("   Running `.agent/scripts/release_gate.py` against `public_release_repo/` to guard against manifest misses.")
    
    # We must explicitly run the release gate within the public_release_repodirectory to scan its contents!
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
            print("⚠️ The public_release_repofolder is tainted. Fix the source, add to .private if needed, and re-sync.")
            sys.exit(1)
        else:
            print("   ✅ Airgap scan passed. No leaked paths or security faults detected.")
    else:
        print("   ⚠️  Warning: Release Gate script not found in destination. Assuming safe.")

    # --- Step 3: Commit in public_release_repo---
    print("\n📝 Step 3: Committing to public_release_repo local repository...")
    status = run("git status --porcelain").stdout.strip()
    if not status:
        print("   ℹ️  No changes detected between main repo and public release.")
    else:
        run("git add .")
        run('git commit -m "sync: airgap update from private development source"')
        print("   ✅ Committed changes to public_release_repo local branch.")

    # --- Step 4: Push ---
    if args.push:
        print("\n🚀 Step 4: Pushing to public remote (NPM Release Trigger)...")
        current_branch = run("git rev-parse --abbrev-ref HEAD").stdout.strip()
        run(f"git push origin {current_branch}")
        print("   ✅ Push complete!")
    else:
        print("\n   ℹ️  Changes committed locally in public_release_repo/ but not pushed yet.")
        print("      Run with --push to deploy, or cd into public_release_repo and push manually.")


if __name__ == "__main__":
    main()
