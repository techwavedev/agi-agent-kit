#!/usr/bin/env python3
"""
Script: sync_upstream.py
Purpose: Sync upstream fork repositories with the agi-agent-kit codebase.
         Clones upstream sources, detects changes, creates feature branches,
         and applies framework adaptations.

Usage:
    python3 skills/upstream-sync/scripts/sync_upstream.py --all
    python3 skills/upstream-sync/scripts/sync_upstream.py --id superpowers
    python3 skills/upstream-sync/scripts/sync_upstream.py --all --dry-run --report .tmp/sync_report.json

Exit Codes:
    0 - Success (no changes or changes applied)
    1 - Invalid arguments
    2 - Clone/network error
    3 - Merge conflict requiring manual review
    4 - Processing error
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent.parent  # skills/upstream-sync/
REGISTRY_FILE = SCRIPT_DIR / "upstream_registry.json"
PROJECT_ROOT = SCRIPT_DIR.parent.parent  # skills/upstream-sync -> skills -> root
TMP_DIR = PROJECT_ROOT / ".tmp" / "upstream-sync"

AGI_START_MARKER = "<!-- AGI-INTEGRATION-START -->"
AGI_END_MARKER = "<!-- AGI-INTEGRATION-END -->"


def load_registry() -> dict:
    """Load the upstream registry."""
    if not REGISTRY_FILE.exists():
        print(f"❌ Registry not found: {REGISTRY_FILE}", file=sys.stderr)
        sys.exit(1)
    return json.loads(REGISTRY_FILE.read_text())


def clone_repo(org_repo: str, dest: Path, label: str = "upstream") -> bool:
    """Shallow-clone a GitHub repo."""
    url = f"https://github.com/{org_repo}.git"
    if dest.exists():
        shutil.rmtree(dest)
    print(f"  📥 Cloning {label}: {org_repo}...")
    result = subprocess.run(
        ["git", "clone", "--depth", "1", url, str(dest)],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"  ⚠️  Clone failed for {org_repo}: {result.stderr.strip()}")
        return False
    return True


def extract_agi_block(content: str) -> str | None:
    """Extract existing AGI integration block."""
    pattern = re.compile(
        rf"{re.escape(AGI_START_MARKER)}.*?{re.escape(AGI_END_MARKER)}",
        re.DOTALL
    )
    match = pattern.search(content)
    return match.group(0) if match else None


def strip_agi_block(content: str) -> str:
    """Remove AGI integration block for comparison."""
    pattern = re.compile(
        rf"\n*---\n*\n*{re.escape(AGI_START_MARKER)}.*?{re.escape(AGI_END_MARKER)}\n*",
        re.DOTALL
    )
    content = pattern.sub("", content)
    # Also remove legacy block without markers
    pattern2 = re.compile(r"\n*---\n*\n*## 🧠 AGI Framework Integration.*$", re.DOTALL)
    content = pattern2.sub("", content)
    return content.rstrip()


def get_upstream_commit_info(repo_dir: Path) -> dict:
    """Get latest commit info from cloned repo."""
    try:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%H|%s|%ai"],
            capture_output=True, text=True, cwd=str(repo_dir)
        )
        if result.returncode == 0:
            parts = result.stdout.strip().split("|", 2)
            return {"hash": parts[0][:8], "message": parts[1], "date": parts[2]}
    except Exception:
        pass
    return {"hash": "unknown", "message": "", "date": ""}


def create_feat_branch(upstream_id: str, dry_run: bool) -> str:
    """Create a feature branch for this sync."""
    branch = f"feat/upstream-sync-{upstream_id}"
    if dry_run:
        return branch
    # Check if branch already exists
    result = subprocess.run(
        ["git", "branch", "--list", branch],
        capture_output=True, text=True, cwd=str(PROJECT_ROOT)
    )
    if result.stdout.strip():
        print(f"  ⚠️  Branch {branch} already exists — reusing")
    else:
        subprocess.run(
            ["git", "checkout", "-b", branch],
            capture_output=True, text=True, cwd=str(PROJECT_ROOT)
        )
        print(f"  🌿 Created branch: {branch}")
    return branch


def sync_skill_adapt(config: dict, dry_run: bool) -> dict:
    """Strategy: skill-adapt — use the existing adapt_extended_skills.py."""
    report = {"strategy": "skill-adapt", "status": "skipped"}
    clone_dir = TMP_DIR / config["id"]

    if not clone_repo(config["fork"], clone_dir, "fork"):
        report["status"] = "clone_failed"
        return report

    source = clone_dir / config.get("clone_subdir", "skills")
    if not source.exists():
        report["status"] = "source_dir_missing"
        report["error"] = f"Expected {source} not found"
        return report

    adapt_script = PROJECT_ROOT / config.get("adapt_script", "scripts/adapt_extended_skills.py")
    if not adapt_script.exists():
        report["status"] = "adapt_script_missing"
        report["error"] = f"Script {adapt_script} not found"
        return report

    cmd = [sys.executable, str(adapt_script), "--source", str(source)]
    if dry_run:
        cmd.append("--dry-run")

    report_file = TMP_DIR / f"{config['id']}_adapt_report.json"
    cmd.extend(["--report", str(report_file)])

    print(f"  🔧 Running adaptation script...")
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(PROJECT_ROOT))
    print(result.stdout[-500:] if len(result.stdout) > 500 else result.stdout)

    if report_file.exists():
        adapt_report = json.loads(report_file.read_text())
        report["new_skills"] = adapt_report.get("new_skills", [])
        report["updated_skills"] = adapt_report.get("updated_skills", [])
        report["unchanged"] = len(adapt_report.get("unchanged_skills", []))
        report["status"] = "changes_found" if (report["new_skills"] or report["updated_skills"]) else "up_to_date"
    else:
        report["status"] = "completed"
        report["stdout"] = result.stdout[-200:]

    return report


def sync_skill_diff(config: dict, dry_run: bool) -> dict:
    """Strategy: skill-diff — diff individual skills against local copies."""
    report = {"strategy": "skill-diff", "new_skills": [], "updated_skills": [],
              "unchanged": 0, "status": "up_to_date"}
    clone_dir = TMP_DIR / config["id"]

    if not clone_repo(config["fork"], clone_dir, "fork"):
        report["status"] = "clone_failed"
        return report

    source = clone_dir / config.get("clone_subdir", ".")
    if not source.exists():
        report["status"] = "source_dir_missing"
        return report

    # Find all skills in the upstream (directories with SKILL.md or .md files)
    upstream_skills = {}
    for item in source.iterdir():
        if item.is_dir() and (item / "SKILL.md").exists():
            upstream_skills[item.name] = item / "SKILL.md"
        elif item.is_file() and item.suffix == ".md" and item.name != "README.md":
            upstream_skills[item.stem] = item

    # Compare against local paths
    for skill_name, upstream_file in sorted(upstream_skills.items()):
        # Find local equivalent
        local_file = None
        for local_path in config.get("local_paths", []):
            candidate = PROJECT_ROOT / local_path
            if candidate.is_file() and candidate.suffix == ".md":
                if candidate.stem == skill_name:
                    local_file = candidate
                    break
            elif candidate.is_dir():
                for check in [
                    candidate / "SKILL.md",
                    candidate / f"{skill_name}.md",
                ]:
                    if check.exists():
                        local_file = check
                        break
                # Also check if skill_name matches the directory name
                if local_file is None and candidate.name == skill_name:
                    check = candidate / "SKILL.md"
                    if check.exists():
                        local_file = check

        if local_file is None:
            # Search all local_paths for this skill name
            for local_path in config.get("local_paths", []):
                search_base = PROJECT_ROOT / local_path
                if search_base.is_dir():
                    for p in search_base.rglob("SKILL.md"):
                        if p.parent.name == skill_name:
                            local_file = p
                            break

        upstream_content = upstream_file.read_text(encoding="utf-8", errors="ignore")

        if local_file is None or not local_file.exists():
            report["new_skills"].append(skill_name)
            continue

        local_content = local_file.read_text(encoding="utf-8", errors="ignore")

        # Compare without AGI blocks
        upstream_clean = strip_agi_block(upstream_content).strip()
        local_clean = strip_agi_block(local_content).strip()

        if upstream_clean != local_clean:
            report["updated_skills"].append(skill_name)
            if not dry_run:
                # Preserve our AGI block, take upstream core content
                agi_block = extract_agi_block(local_content)
                new_content = upstream_clean
                if agi_block:
                    new_content += f"\n\n---\n\n{agi_block}\n"
                local_file.write_text(new_content, encoding="utf-8")
        else:
            report["unchanged"] += 1

    if report["new_skills"] or report["updated_skills"]:
        report["status"] = "changes_found"

    return report


def sync_full_replace(config: dict, dry_run: bool) -> dict:
    """Strategy: full-replace — replace content preserving AGI markers."""
    report = {"strategy": "full-replace", "files_updated": [], "status": "up_to_date"}
    clone_dir = TMP_DIR / config["id"]

    if not clone_repo(config["fork"], clone_dir, "fork"):
        report["status"] = "clone_failed"
        return report

    source = clone_dir / config.get("clone_subdir", ".")

    for local_path_str in config.get("local_paths", []):
        local_path = PROJECT_ROOT / local_path_str
        if not local_path.exists():
            report["files_updated"].append({"path": local_path_str, "action": "new_dir"})
            if not dry_run:
                shutil.copytree(source, local_path, dirs_exist_ok=True)
            continue

        # Compare files
        for src_file in source.rglob("*"):
            if not src_file.is_file():
                continue
            if src_file.name.startswith(".") or "__pycache__" in str(src_file):
                continue

            relative = src_file.relative_to(source)
            dst_file = local_path / relative

            src_content = src_file.read_text(encoding="utf-8", errors="ignore")

            if not dst_file.exists():
                report["files_updated"].append({"path": str(relative), "action": "new"})
                if not dry_run:
                    dst_file.parent.mkdir(parents=True, exist_ok=True)
                    dst_file.write_text(src_content, encoding="utf-8")
                continue

            dst_content = dst_file.read_text(encoding="utf-8", errors="ignore")

            # For .md files, compare without AGI blocks
            if dst_file.suffix == ".md":
                if strip_agi_block(src_content).strip() != strip_agi_block(dst_content).strip():
                    report["files_updated"].append({"path": str(relative), "action": "updated"})
                    if not dry_run:
                        agi_block = extract_agi_block(dst_content)
                        new_content = strip_agi_block(src_content).rstrip()
                        if agi_block:
                            new_content += f"\n\n---\n\n{agi_block}\n"
                        dst_file.write_text(new_content, encoding="utf-8")
            else:
                # Non-markdown: simple content comparison
                if src_content != dst_content:
                    report["files_updated"].append({"path": str(relative), "action": "updated"})
                    if not dry_run:
                        dst_file.write_text(src_content, encoding="utf-8")

    if report["files_updated"]:
        report["status"] = "changes_found"

    return report


def sync_inspect_merge(config: dict, dry_run: bool) -> dict:
    """Strategy: inspect-merge — compare fork vs upstream, produce divergence report."""
    report = {"strategy": "inspect-merge", "status": "needs_review",
              "fork_info": {}, "upstream_info": {}, "divergence": {}}

    fork_dir = TMP_DIR / f"{config['id']}_fork"
    upstream_dir = TMP_DIR / f"{config['id']}_upstream"

    # Clone both
    fork_ok = clone_repo(config["fork"], fork_dir, "our fork")
    upstream_ok = clone_repo(config["upstream"], upstream_dir, "upstream")

    if not fork_ok or not upstream_ok:
        report["status"] = "clone_failed"
        return report

    report["fork_info"] = get_upstream_commit_info(fork_dir)
    report["upstream_info"] = get_upstream_commit_info(upstream_dir)

    # Compare file trees
    fork_files = set()
    for f in fork_dir.rglob("*"):
        if f.is_file() and ".git" not in f.parts:
            fork_files.add(str(f.relative_to(fork_dir)))

    upstream_files = set()
    for f in upstream_dir.rglob("*"):
        if f.is_file() and ".git" not in f.parts:
            upstream_files.add(str(f.relative_to(upstream_dir)))

    only_in_fork = sorted(fork_files - upstream_files)
    only_in_upstream = sorted(upstream_files - fork_files)
    in_both = sorted(fork_files & upstream_files)

    changed_files = []
    for rel in in_both:
        try:
            fork_content = (fork_dir / rel).read_text(encoding="utf-8", errors="ignore")
            upstream_content = (upstream_dir / rel).read_text(encoding="utf-8", errors="ignore")
            if fork_content != upstream_content:
                changed_files.append(rel)
        except Exception:
            pass

    report["divergence"] = {
        "only_in_fork": only_in_fork[:50],
        "only_in_upstream": only_in_upstream[:50],
        "changed_in_both": changed_files[:50],
        "total_only_fork": len(only_in_fork),
        "total_only_upstream": len(only_in_upstream),
        "total_changed": len(changed_files),
    }

    print(f"  📊 Divergence: {len(only_in_fork)} fork-only, "
          f"{len(only_in_upstream)} upstream-only, {len(changed_files)} modified")

    return report


def sync_reference_only(config: dict, dry_run: bool) -> dict:
    """Strategy: reference-only — just summarize what's new."""
    report = {"strategy": "reference-only", "status": "inspected"}
    clone_dir = TMP_DIR / config["id"]

    if not clone_repo(config["upstream"], clone_dir, "upstream"):
        report["status"] = "clone_failed"
        return report

    report["upstream_info"] = get_upstream_commit_info(clone_dir)

    # Count files by type
    file_counts = {}
    for f in clone_dir.rglob("*"):
        if f.is_file() and ".git" not in f.parts:
            ext = f.suffix or "no_ext"
            file_counts[ext] = file_counts.get(ext, 0) + 1

    report["file_summary"] = file_counts
    report["total_files"] = sum(file_counts.values())

    # Check for README
    readme = clone_dir / "README.md"
    if readme.exists():
        content = readme.read_text(encoding="utf-8", errors="ignore")
        report["readme_preview"] = content[:500]

    return report


STRATEGY_MAP = {
    "skill-adapt": sync_skill_adapt,
    "skill-diff": sync_skill_diff,
    "full-replace": sync_full_replace,
    "inspect-merge": sync_inspect_merge,
    "reference-only": sync_reference_only,
}


def sync_one(config: dict, dry_run: bool, create_branch: bool) -> dict:
    """Sync a single upstream."""
    upstream_id = config["id"]
    strategy = config.get("sync_strategy", "reference-only")

    print(f"\n{'='*60}")
    print(f"📦 Syncing: {upstream_id}")
    print(f"   Fork: {config['fork']}")
    print(f"   Upstream: {config['upstream']}")
    print(f"   Strategy: {strategy}")
    print(f"   {'(DRY RUN)' if dry_run else ''}")
    print(f"{'='*60}")

    handler = STRATEGY_MAP.get(strategy)
    if not handler:
        return {"id": upstream_id, "status": "unknown_strategy", "strategy": strategy}

    branch = None
    if create_branch and not dry_run and strategy not in ("reference-only",):
        branch = create_feat_branch(upstream_id, dry_run)

    report = handler(config, dry_run)
    report["id"] = upstream_id
    report["fork"] = config["fork"]
    report["upstream"] = config["upstream"]
    report["timestamp"] = datetime.now(timezone.utc).isoformat()
    report["dry_run"] = dry_run
    if branch:
        report["branch"] = branch

    # Summary
    status_icon = {"changes_found": "🔄", "up_to_date": "✅",
                   "needs_review": "👀", "inspected": "📋",
                   "clone_failed": "❌"}.get(report["status"], "❓")
    print(f"\n  {status_icon} Status: {report['status']}")

    return report


def main():
    parser = argparse.ArgumentParser(
        description="Sync upstream fork repositories with agi-agent-kit",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--all", action="store_true", help="Sync all registered upstreams")
    parser.add_argument("--id", help="Sync specific upstream by ID")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes only")
    parser.add_argument("--branch", action="store_true", help="Create feat branch per sync")
    parser.add_argument("--priority", type=int, default=99, help="Only sync priority <= N")
    parser.add_argument("--report", type=Path, help="Save JSON report to file")
    args = parser.parse_args()

    if not args.all and not args.id:
        parser.error("Specify --all or --id <upstream_id>")

    registry = load_registry()
    upstreams = registry.get("upstreams", [])

    TMP_DIR.mkdir(parents=True, exist_ok=True)

    if args.id:
        targets = [u for u in upstreams if u["id"] == args.id]
        if not targets:
            ids = [u["id"] for u in upstreams]
            print(f"❌ Unknown upstream ID: {args.id}", file=sys.stderr)
            print(f"   Available: {', '.join(ids)}", file=sys.stderr)
            sys.exit(1)
    else:
        targets = [u for u in upstreams if u.get("priority", 99) <= args.priority]

    # Sort by priority
    targets.sort(key=lambda u: u.get("priority", 99))

    print(f"🚀 Upstream Sync — {len(targets)} target(s)")
    print(f"   Dry run: {args.dry_run}")

    reports = []
    for config in targets:
        report = sync_one(config, args.dry_run, args.branch)
        reports.append(report)

    # Final summary
    print(f"\n{'='*60}")
    print("📊 SYNC SUMMARY")
    print(f"{'='*60}")
    for r in reports:
        status_icon = {"changes_found": "🔄", "up_to_date": "✅",
                       "needs_review": "👀", "inspected": "📋",
                       "clone_failed": "❌"}.get(r.get("status", ""), "❓")
        extras = []
        if r.get("new_skills"):
            extras.append(f"+{len(r['new_skills'])} new")
        if r.get("updated_skills"):
            extras.append(f"~{len(r['updated_skills'])} updated")
        if r.get("files_updated"):
            extras.append(f"{len(r['files_updated'])} files")
        if r.get("divergence"):
            d = r["divergence"]
            extras.append(f"{d.get('total_changed', 0)} diverged")
        extra_str = f" ({', '.join(extras)})" if extras else ""
        print(f"  {status_icon} {r['id']:25s} {r.get('status', ''):20s}{extra_str}")

    # Save report
    full_report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "dry_run": args.dry_run,
        "results": reports,
    }

    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(full_report, indent=2))
        print(f"\n📄 Report saved: {args.report}")

    # Print JSON to stdout
    print(f"\n{json.dumps(full_report, indent=2)}")

    # Exit code
    has_changes = any(r.get("status") in ("changes_found", "needs_review") for r in reports)
    has_errors = any(r.get("status") == "clone_failed" for r in reports)
    if has_errors:
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()
