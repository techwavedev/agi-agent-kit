#!/usr/bin/env python3
"""
Script: sync_to_template.py
Purpose: Sync root development files to templates/base/ (the public NPM scaffold).
         Root is always the source of truth. Template never flows back to root.

Usage:
    python3 execution/sync_to_template.py --check          # Preview drift
    python3 execution/sync_to_template.py --sync           # Apply all syncs
    python3 execution/sync_to_template.py --files FILE...  # Sync specific files
    python3 execution/sync_to_template.py --json           # JSON output

Exit Codes:
    0 - No drift / sync successful
    1 - Drift detected (with --check)
    2 - Sync error
"""

import argparse
import filecmp
import json
import os
import shutil
import sys
from pathlib import Path

PROJECT_DIR = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TEMPLATE_DIR = PROJECT_DIR / "templates" / "base"

# ──────────────────────────────────────────────
# Sync Map: root path → template path
# ──────────────────────────────────────────────

FILE_SYNC_MAP = {
    # Core instruction file
    "AGENTS.md": "AGENTS.md",
    # Changelog
    "CHANGELOG.md": "CHANGELOG.md",
    # Requirements
    "requirements.txt": "requirements.txt",
}

DIR_SYNC_MAP = {
    # Execution scripts (all)
    "execution": "execution",
    # Skill creator toolkit
    "skill-creator": "skill-creator",
    # Data (workflows.json etc.)
    "data": "data",
    # Directives (public-facing only)
    "directives/memory_integration.md": "directives/memory_integration.md",
    "directives/release_process.md": "directives/release_process.md",
    "directives/subagents": "directives/subagents",
    "directives/teams": "directives/teams",
    # Agent rules (public-facing only)
    ".agent/rules/core_rules.md": ".agent/rules/core_rules.md",
    ".agent/rules/agent_team_rules.md": ".agent/rules/agent_team_rules.md",
    # Agent workflows (public-facing only)
    ".agent/workflows/memory-usage.md": ".agent/workflows/memory-usage.md",
    ".agent/workflows/run-agent-team-tests.md": ".agent/workflows/run-agent-team-tests.md",
}

# Files that must NEVER be synced to template
PRIVATE_FILES = {
    "execution/sync_to_template.py",
    "execution/validate_template.py",
    "directives/framework_development.md",
    "directives/template_sync.md",
    "directives/skill_development.md",
    ".agent/rules/framework_dev_rules.md",
    ".agent/rules/versioning_rules.md",
    ".agent/scripts/release_gate.py",
    ".agent/workflows/release-protocol.md",
    ".agent/workflows/sync-templates.md",
    ".agent/workflows/add-skill.md",
    ".agent/workflows/update-execution-script.md",
    ".agent/workflows/upstream-sync.md",
    ".agent/workflows/publish-npm.md",
}

# Core skills that sync to templates/skills/core/
CORE_SKILLS = ["qdrant-memory", "documentation", "pdf-reader", "webcrawler"]


def is_private(rel_path: str) -> bool:
    """Check if a file is private-only and should never be synced."""
    return rel_path in PRIVATE_FILES


def compare_file(src: Path, dst: Path) -> dict:
    """Compare two files, return drift info."""
    if not dst.exists():
        return {"status": "missing_in_template", "src": str(src), "dst": str(dst)}
    if not src.exists():
        return {"status": "missing_in_root", "src": str(src), "dst": str(dst)}
    if filecmp.cmp(src, dst, shallow=False):
        return {"status": "in_sync", "src": str(src), "dst": str(dst)}
    return {"status": "drifted", "src": str(src), "dst": str(dst)}


def compare_dir(src: Path, dst: Path, rel_prefix: str = "") -> list:
    """Recursively compare directory contents."""
    results = []
    if not src.exists():
        return [{"status": "missing_in_root", "path": rel_prefix or str(src)}]

    for item in sorted(src.rglob("*")):
        if item.is_dir():
            continue
        if "__pycache__" in str(item) or ".pyc" in str(item):
            continue
        rel = item.relative_to(src)
        full_rel = f"{rel_prefix}/{rel}" if rel_prefix else str(rel)

        # Skip private files
        root_rel = f"{rel_prefix}/{rel}" if rel_prefix else str(rel)
        if is_private(root_rel):
            continue

        dst_file = dst / rel
        results.append(compare_file(item, dst_file))

    # Check for template-only files (not in root)
    if dst.exists():
        for item in sorted(dst.rglob("*")):
            if item.is_dir() or "__pycache__" in str(item):
                continue
            rel = item.relative_to(dst)
            src_file = src / rel
            if not src_file.exists():
                results.append({
                    "status": "template_only",
                    "src": str(src_file),
                    "dst": str(item)
                })

    return results


def check_all() -> dict:
    """Check all sync mappings for drift."""
    report = {"files": [], "dirs": [], "skills": [], "summary": {}}

    # Check individual files
    for root_path, tmpl_path in FILE_SYNC_MAP.items():
        if is_private(root_path):
            continue
        result = compare_file(PROJECT_DIR / root_path, TEMPLATE_DIR / tmpl_path)
        result["mapping"] = f"{root_path} → {tmpl_path}"
        report["files"].append(result)

    # Check directories and file mappings
    for root_path, tmpl_path in DIR_SYNC_MAP.items():
        if is_private(root_path):
            continue
        src = PROJECT_DIR / root_path
        dst = TEMPLATE_DIR / tmpl_path
        if src.is_file():
            result = compare_file(src, dst)
            result["mapping"] = f"{root_path} → {tmpl_path}"
            report["files"].append(result)
        else:
            results = compare_dir(src, dst, root_path)
            for r in results:
                r["mapping"] = f"{root_path}/ → {tmpl_path}/"
            report["dirs"].extend(results)

    # Check core skills
    for skill_name in CORE_SKILLS:
        src = PROJECT_DIR / "skills" / skill_name
        dst = PROJECT_DIR / "templates" / "skills" / "core" / skill_name
        results = compare_dir(src, dst, f"skills/{skill_name}")
        for r in results:
            r["mapping"] = f"skills/{skill_name}/ → templates/skills/core/{skill_name}/"
        report["skills"].extend(results)

    # Summarize
    all_results = report["files"] + report["dirs"] + report["skills"]
    report["summary"] = {
        "total": len(all_results),
        "in_sync": sum(1 for r in all_results if r["status"] == "in_sync"),
        "drifted": sum(1 for r in all_results if r["status"] == "drifted"),
        "missing_in_template": sum(1 for r in all_results if r["status"] == "missing_in_template"),
        "template_only": sum(1 for r in all_results if r["status"] == "template_only"),
    }

    return report


def sync_file(src: Path, dst: Path) -> dict:
    """Copy src to dst, creating parent dirs as needed."""
    try:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        return {"status": "synced", "src": str(src), "dst": str(dst)}
    except Exception as e:
        return {"status": "error", "src": str(src), "dst": str(dst), "error": str(e)}


def sync_dir(src: Path, dst: Path, rel_prefix: str = "") -> list:
    """Sync directory from root to template."""
    results = []
    if not src.exists():
        return [{"status": "error", "path": str(src), "error": "Source not found"}]

    for item in sorted(src.rglob("*")):
        if item.is_dir() or "__pycache__" in str(item) or ".pyc" in str(item):
            continue
        rel = item.relative_to(src)
        root_rel = f"{rel_prefix}/{rel}" if rel_prefix else str(rel)
        if is_private(root_rel):
            continue
        dst_file = dst / rel
        result = compare_file(item, dst_file)
        if result["status"] != "in_sync":
            results.append(sync_file(item, dst_file))
        else:
            results.append({"status": "skipped_in_sync", "src": str(item), "dst": str(dst_file)})

    return results


def sync_all() -> dict:
    """Sync all mapped files from root to template."""
    report = {"synced": [], "skipped": [], "errors": []}

    # Sync individual files
    for root_path, tmpl_path in FILE_SYNC_MAP.items():
        if is_private(root_path):
            continue
        src = PROJECT_DIR / root_path
        dst = TEMPLATE_DIR / tmpl_path
        if not src.exists():
            report["errors"].append({"file": root_path, "error": "Source not found"})
            continue
        result = compare_file(src, dst)
        if result["status"] != "in_sync":
            r = sync_file(src, dst)
            if r["status"] == "synced":
                report["synced"].append(root_path)
            else:
                report["errors"].append(r)
        else:
            report["skipped"].append(root_path)

    # Sync directories
    for root_path, tmpl_path in DIR_SYNC_MAP.items():
        if is_private(root_path):
            continue
        src = PROJECT_DIR / root_path
        dst = TEMPLATE_DIR / tmpl_path
        if src.is_file():
            if not src.exists():
                report["errors"].append({"file": root_path, "error": "Source not found"})
                continue
            result = compare_file(src, dst)
            if result["status"] != "in_sync":
                r = sync_file(src, dst)
                if r["status"] == "synced":
                    report["synced"].append(root_path)
                else:
                    report["errors"].append(r)
            else:
                report["skipped"].append(root_path)
        else:
            results = sync_dir(src, dst, root_path)
            for r in results:
                if r["status"] == "synced":
                    report["synced"].append(r.get("src", root_path))
                elif r["status"] == "error":
                    report["errors"].append(r)
                else:
                    report["skipped"].append(r.get("src", root_path))

    # Sync core skills
    for skill_name in CORE_SKILLS:
        src = PROJECT_DIR / "skills" / skill_name
        dst = PROJECT_DIR / "templates" / "skills" / "core" / skill_name
        if not src.exists():
            report["errors"].append({"file": f"skills/{skill_name}", "error": "Source not found"})
            continue
        results = sync_dir(src, dst, f"skills/{skill_name}")
        for r in results:
            if r["status"] == "synced":
                report["synced"].append(r.get("src", f"skills/{skill_name}"))
            elif r["status"] == "error":
                report["errors"].append(r)

    report["summary"] = {
        "synced": len(report["synced"]),
        "skipped": len(report["skipped"]),
        "errors": len(report["errors"]),
    }

    return report


def sync_specific_files(file_paths: list) -> dict:
    """Sync specific files from root to their template destinations."""
    report = {"synced": [], "errors": []}

    all_mappings = {}
    # Build full mapping from all sources
    for root_path, tmpl_path in FILE_SYNC_MAP.items():
        all_mappings[root_path] = TEMPLATE_DIR / tmpl_path
    for root_path, tmpl_path in DIR_SYNC_MAP.items():
        all_mappings[root_path] = TEMPLATE_DIR / tmpl_path
    for skill_name in CORE_SKILLS:
        all_mappings[f"skills/{skill_name}"] = PROJECT_DIR / "templates" / "skills" / "core" / skill_name

    for file_path in file_paths:
        # Normalize
        fp = file_path.lstrip("./")

        if is_private(fp):
            report["errors"].append({"file": fp, "error": "Private file — cannot sync to template"})
            continue

        # Try direct mapping
        if fp in all_mappings:
            src = PROJECT_DIR / fp
            dst = all_mappings[fp]
            if src.is_dir():
                results = sync_dir(src, dst, fp)
                for r in results:
                    if r["status"] == "synced":
                        report["synced"].append(r.get("src", fp))
                    elif r["status"] == "error":
                        report["errors"].append(r)
            else:
                r = sync_file(src, dst)
                if r["status"] == "synced":
                    report["synced"].append(fp)
                else:
                    report["errors"].append(r)
            continue

        # Try to find parent mapping
        matched = False
        for root_path, tmpl_path in {**DIR_SYNC_MAP, **FILE_SYNC_MAP}.items():
            if fp.startswith(root_path + "/") or fp == root_path:
                rel = fp[len(root_path):].lstrip("/")
                src = PROJECT_DIR / fp
                dst = TEMPLATE_DIR / tmpl_path / rel if rel else TEMPLATE_DIR / tmpl_path
                if src.exists():
                    r = sync_file(src, dst)
                    if r["status"] == "synced":
                        report["synced"].append(fp)
                    else:
                        report["errors"].append(r)
                else:
                    report["errors"].append({"file": fp, "error": "Source not found"})
                matched = True
                break

        # Try core skills
        if not matched:
            for skill_name in CORE_SKILLS:
                prefix = f"skills/{skill_name}"
                if fp.startswith(prefix):
                    rel = fp[len(prefix):].lstrip("/")
                    src = PROJECT_DIR / fp
                    dst = PROJECT_DIR / "templates" / "skills" / "core" / skill_name / rel
                    if src.exists():
                        r = sync_file(src, dst)
                        if r["status"] == "synced":
                            report["synced"].append(fp)
                        else:
                            report["errors"].append(r)
                    else:
                        report["errors"].append({"file": fp, "error": "Source not found"})
                    matched = True
                    break

        if not matched:
            report["errors"].append({"file": fp, "error": "No sync mapping found for this file"})

    return report


def main():
    parser = argparse.ArgumentParser(description="Sync root files to templates/base/")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", action="store_true", help="Preview drift without changing anything")
    group.add_argument("--sync", action="store_true", help="Sync all mapped files")
    group.add_argument("--files", nargs="+", help="Sync specific files")
    parser.add_argument("--json", action="store_true", help="JSON-only output")
    args = parser.parse_args()

    if args.check:
        report = check_all()
        if args.json:
            print(json.dumps(report, indent=2))
        else:
            s = report["summary"]
            print(f"\n📋 Template Sync Check")
            print(f"   Total files:  {s['total']}")
            print(f"   In sync:      {s['in_sync']}")
            print(f"   Drifted:      {s['drifted']}")
            print(f"   Missing:      {s['missing_in_template']}")
            print(f"   Template-only: {s['template_only']}")
            if s["drifted"] > 0 or s["missing_in_template"] > 0:
                print(f"\n⚠️  Drift detected. Run --sync to fix.")
                for r in report["files"] + report["dirs"] + report["skills"]:
                    if r["status"] in ("drifted", "missing_in_template"):
                        print(f"   {r['status']:25s} {r.get('mapping', r.get('src', ''))}")
                sys.exit(1)
            else:
                print(f"\n✅ All files in sync.")
        sys.exit(0 if report["summary"]["drifted"] == 0 and report["summary"]["missing_in_template"] == 0 else 1)

    elif args.sync:
        report = sync_all()
        if args.json:
            print(json.dumps(report, indent=2))
        else:
            s = report["summary"]
            print(f"\n🔄 Template Sync Complete")
            print(f"   Synced:   {s['synced']}")
            print(f"   Skipped:  {s['skipped']} (already in sync)")
            print(f"   Errors:   {s['errors']}")
            if s["errors"] > 0:
                for e in report["errors"]:
                    print(f"   ❌ {e}")
                sys.exit(2)
            else:
                print(f"\n✅ Sync successful.")
        sys.exit(2 if report["summary"]["errors"] > 0 else 0)

    elif args.files:
        report = sync_specific_files(args.files)
        if args.json:
            print(json.dumps(report, indent=2))
        else:
            print(f"\n🔄 Selective Sync")
            print(f"   Synced: {len(report['synced'])}")
            print(f"   Errors: {len(report['errors'])}")
            for e in report["errors"]:
                print(f"   ❌ {e.get('file', '')}: {e.get('error', '')}")
        sys.exit(2 if report["errors"] else 0)


if __name__ == "__main__":
    main()
