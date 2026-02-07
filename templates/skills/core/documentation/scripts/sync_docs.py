#!/usr/bin/env python3
"""
Full Documentation Synchronization

Orchestrates a complete documentation update across the entire repository.
Combines change detection, skill updates, and catalog synchronization.

Usage:
    python sync_docs.py --skills-dir <path> [options]

Arguments:
    --skills-dir       Skills directory (required)
    --update-catalog   Update SKILLS_CATALOG.md (default: true)
    --update-readme    Update README.md if exists (optional)
    --dry-run          Preview changes without writing (optional)
    --report           Save sync report to file (optional)

Exit Codes:
    0 - Success
    1 - Invalid arguments
    2 - Directory not found
    3 - Sync error
"""

import argparse
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Tuple


def find_repo_root(start_path: Path) -> Path:
    """Find repository root by looking for AGENTS.md or .git."""
    current = start_path.resolve()
    
    while current != current.parent:
        if (current / 'AGENTS.md').exists() or (current / '.git').exists():
            return current
        current = current.parent
    
    return start_path.resolve()


def scan_all_skills(skills_dir: Path) -> List[Dict]:
    """Scan all skills and gather their metadata."""
    skills = []
    
    for item in sorted(skills_dir.iterdir()):
        if not item.is_dir():
            continue
        
        skill_md = item / 'SKILL.md'
        if not skill_md.exists():
            continue
        
        skill_info = {
            'name': item.name,
            'path': item,
            'scripts': list((item / 'scripts').glob('*.py')) if (item / 'scripts').exists() else [],
            'references': list((item / 'references').glob('*.md')) if (item / 'references').exists() else [],
            'has_assets': (item / 'assets').exists() and any((item / 'assets').iterdir()),
        }
        
        # Filter out example files
        skill_info['scripts'] = [s for s in skill_info['scripts'] 
                                  if not s.name.startswith('example') and not s.name.startswith('__')]
        skill_info['references'] = [r for r in skill_info['references'] 
                                     if not r.name.startswith('example')]
        
        skills.append(skill_info)
    
    return skills


def update_skill_timestamps(skills: List[Dict], dry_run: bool = False) -> List[Tuple[str, bool]]:
    """Update the 'Last Updated' timestamp in all SKILL.md files."""
    results = []
    today = datetime.now().strftime('%Y-%m-%d')
    
    for skill in skills:
        skill_md = skill['path'] / 'SKILL.md'
        
        try:
            content = skill_md.read_text()
            
            # Check if timestamp exists and update it
            import re
            pattern = r'>\s*\*\*Last Updated:\*\*\s*\d{4}-\d{2}-\d{2}'
            replacement = f'> **Last Updated:** {today}'
            
            if re.search(pattern, content):
                new_content = re.sub(pattern, replacement, content)
                
                if new_content != content and not dry_run:
                    skill_md.write_text(new_content)
                    results.append((skill['name'], True))
                else:
                    results.append((skill['name'], False))  # No change needed or dry run
            else:
                results.append((skill['name'], False))  # No timestamp found
                
        except Exception as e:
            print(f"  ⚠️  Error updating {skill['name']}: {e}", file=sys.stderr)
            results.append((skill['name'], False))
    
    return results


def run_catalog_update(skills_dir: Path, repo_root: Path, dry_run: bool = False) -> bool:
    """Run the skills catalog updater."""
    update_script = repo_root / 'skill-creator' / 'scripts' / 'update_catalog.py'
    
    if not update_script.exists():
        print(f"  ⚠️  Catalog update script not found: {update_script}", file=sys.stderr)
        return False
    
    if dry_run:
        print("  🔍 [Dry Run] Would update SKILLS_CATALOG.md")
        return True
    
    try:
        result = subprocess.run(
            [sys.executable, str(update_script), '--skills-dir', str(skills_dir)],
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            return True
        else:
            print(f"  ⚠️  Catalog update failed: {result.stderr}", file=sys.stderr)
            return False
            
    except Exception as e:
        print(f"  ⚠️  Error running catalog update: {e}", file=sys.stderr)
        return False


def generate_sync_report(skills: List[Dict], catalog_updated: bool, 
                         timestamp_results: List[Tuple[str, bool]]) -> str:
    """Generate a synchronization report."""
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    
    lines = [
        "# Documentation Synchronization Report",
        "",
        f"> **Generated:** {now}",
        "",
        "---",
        "",
        "## Summary",
        "",
        f"- **Skills Scanned:** {len(skills)}",
        f"- **Catalog Updated:** {'✅ Yes' if catalog_updated else '❌ No'}",
        f"- **Timestamps Updated:** {sum(1 for _, updated in timestamp_results if updated)}",
        "",
        "---",
        "",
        "## Skills Overview",
        "",
        "| Skill | Scripts | References | Timestamp Updated |",
        "|-------|---------|------------|-------------------|",
    ]
    
    for skill in skills:
        name = skill['name']
        scripts_count = len(skill['scripts'])
        refs_count = len(skill['references'])
        
        # Find timestamp result
        ts_updated = '—'
        for ts_name, updated in timestamp_results:
            if ts_name == name:
                ts_updated = '✅' if updated else '—'
                break
        
        lines.append(f"| `{name}` | {scripts_count} | {refs_count} | {ts_updated} |")
    
    lines.extend([
        "",
        "---",
        "",
        "## Next Steps",
        "",
    ])
    
    if not catalog_updated:
        lines.append("- [ ] Manually run catalog update if it failed")
    
    lines.extend([
        "- [ ] Review any skills with warnings",
        "- [ ] Commit documentation changes",
        "",
    ])
    
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(
        description='Synchronize all documentation',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument('--skills-dir', required=True, help='Skills directory')
    parser.add_argument('--update-catalog', type=bool, default=True, help='Update catalog')
    parser.add_argument('--update-readme', action='store_true', help='Update README.md')
    parser.add_argument('--dry-run', action='store_true', help='Preview without writing')
    parser.add_argument('--report', help='Save report to file')
    args = parser.parse_args()
    
    skills_dir = Path(args.skills_dir).resolve()
    
    if not skills_dir.exists():
        print(f"❌ Error: Skills directory not found: {skills_dir}", file=sys.stderr)
        sys.exit(2)
    
    repo_root = find_repo_root(skills_dir)
    
    print(f"🔄 Documentation Synchronization")
    print(f"   Skills directory: {skills_dir}")
    print(f"   Repository root: {repo_root}")
    if args.dry_run:
        print(f"   Mode: DRY RUN (no changes will be written)")
    print()
    
    # Scan all skills
    print("📂 Scanning skills...")
    skills = scan_all_skills(skills_dir)
    print(f"   Found {len(skills)} skill(s)")
    
    # Update timestamps
    print("\n📅 Updating timestamps...")
    timestamp_results = update_skill_timestamps(skills, args.dry_run)
    updated_count = sum(1 for _, updated in timestamp_results if updated)
    print(f"   Updated {updated_count} timestamp(s)")
    
    # Update catalog
    catalog_updated = False
    if args.update_catalog:
        print("\n📚 Updating skills catalog...")
        catalog_updated = run_catalog_update(skills_dir, repo_root, args.dry_run)
        if catalog_updated:
            print("   ✅ Catalog updated successfully")
        else:
            print("   ⚠️  Catalog update had issues")
    
    # Generate report
    report = generate_sync_report(skills, catalog_updated, timestamp_results)
    
    if args.report:
        report_path = Path(args.report)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        
        if not args.dry_run:
            report_path.write_text(report)
            print(f"\n📋 Report saved to: {args.report}")
        else:
            print(f"\n📋 [Dry Run] Would save report to: {args.report}")
    
    print("\n" + "=" * 50)
    print("✅ Documentation synchronization complete!")
    print("=" * 50)
    
    sys.exit(0)


if __name__ == '__main__':
    main()
