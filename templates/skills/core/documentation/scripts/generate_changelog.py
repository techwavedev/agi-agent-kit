#!/usr/bin/env python3
"""
Changelog Generator

Creates structured changelog entries from detected code changes.
Follows the Keep a Changelog format (https://keepachangelog.com/).

Usage:
    python generate_changelog.py --scope <path> --since <commit|date> [options]

Arguments:
    --scope         Directory to analyze (required)
    --since         Changes since commit/date (required)
    --output        Output file (default: stdout)
    --format        Changelog format (default: keep-a-changelog)
    --prepend       Prepend to existing changelog (optional)

Exit Codes:
    0 - Success
    1 - Invalid arguments
    2 - Directory not found
    3 - Output error
"""

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


def run_git_command(args: List[str], cwd: Path) -> Tuple[bool, str]:
    """Execute a git command and return (success, output)."""
    try:
        result = subprocess.run(
            ['git'] + args,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.returncode == 0, result.stdout.strip()
    except Exception as e:
        return False, str(e)


def get_git_log(scope: Path, since: str) -> List[Dict]:
    """Get git log entries since a specific commit or date."""
    # Format: hash|author|date|subject
    success, output = run_git_command(
        ['log', '--format=%H|%an|%ai|%s', since + '..HEAD', '--', str(scope)],
        scope
    )
    
    if not success:
        # Try alternative format
        success, output = run_git_command(
            ['log', '--format=%H|%an|%ai|%s', '-20', '--', str(scope)],
            scope
        )
    
    if not success or not output:
        return []
    
    commits = []
    for line in output.split('\n'):
        if not line.strip():
            continue
        
        parts = line.split('|', 3)
        if len(parts) >= 4:
            commits.append({
                'hash': parts[0][:7],
                'author': parts[1],
                'date': parts[2].split()[0],
                'subject': parts[3]
            })
    
    return commits


def get_changed_files(scope: Path, since: str) -> Dict[str, List[str]]:
    """Get files changed with their status."""
    success, output = run_git_command(
        ['diff', '--name-status', since, '--', str(scope)],
        scope
    )
    
    if not success:
        success, output = run_git_command(
            ['diff', '--name-status', 'HEAD~10', '--', str(scope)],
            scope
        )
    
    changes = {'added': [], 'modified': [], 'deleted': []}
    
    if not success or not output:
        return changes
    
    for line in output.split('\n'):
        if not line.strip():
            continue
        
        parts = line.split('\t')
        if len(parts) < 2:
            continue
        
        status, filepath = parts[0], parts[1]
        
        if status.startswith('A'):
            changes['added'].append(filepath)
        elif status.startswith('M'):
            changes['modified'].append(filepath)
        elif status.startswith('D'):
            changes['deleted'].append(filepath)
    
    return changes


def categorize_change(filepath: str) -> str:
    """Categorize a file change for changelog purposes."""
    if 'SKILL.md' in filepath:
        return 'skill'
    if '/scripts/' in filepath:
        return 'script'
    if '/references/' in filepath:
        return 'documentation'
    if filepath.endswith('.py'):
        return 'code'
    if filepath.endswith('.md'):
        return 'documentation'
    return 'other'


def generate_changelog_entry(changes: Dict, commits: List[Dict], 
                              scope: str, version: str = 'Unreleased') -> str:
    """Generate a changelog entry in Keep a Changelog format."""
    today = datetime.now().strftime('%Y-%m-%d')
    
    lines = [
        f"## [{version}] - {today}",
        ""
    ]
    
    # Group changes
    added = []
    changed = []
    removed = []
    
    for filepath in changes['added']:
        category = categorize_change(filepath)
        filename = Path(filepath).name
        
        if category == 'skill':
            added.append(f"New skill definition: `{Path(filepath).parent.name}`")
        elif category == 'script':
            skill = filepath.split('/scripts/')[0].split('/')[-1] if '/scripts/' in filepath else 'unknown'
            added.append(f"New script `{filename}` for `{skill}` skill")
        elif category == 'documentation':
            added.append(f"New documentation: `{filename}`")
        else:
            added.append(f"Added `{filepath}`")
    
    for filepath in changes['modified']:
        category = categorize_change(filepath)
        filename = Path(filepath).name
        
        if category == 'skill':
            skill = Path(filepath).parent.name
            changed.append(f"Updated `{skill}` skill definition")
        elif category == 'script':
            skill = filepath.split('/scripts/')[0].split('/')[-1] if '/scripts/' in filepath else 'unknown'
            changed.append(f"Modified `{filename}` in `{skill}` skill")
        elif category == 'documentation':
            changed.append(f"Updated documentation: `{filename}`")
        else:
            changed.append(f"Modified `{filepath}`")
    
    for filepath in changes['deleted']:
        category = categorize_change(filepath)
        filename = Path(filepath).name
        
        if category == 'skill':
            removed.append(f"Removed skill: `{Path(filepath).parent.name}`")
        else:
            removed.append(f"Removed `{filepath}`")
    
    # Deduplicate
    added = list(dict.fromkeys(added))
    changed = list(dict.fromkeys(changed))
    removed = list(dict.fromkeys(removed))
    
    # Write sections
    if added:
        lines.append("### Added")
        for item in added:
            lines.append(f"- {item}")
        lines.append("")
    
    if changed:
        lines.append("### Changed")
        for item in changed:
            lines.append(f"- {item}")
        lines.append("")
    
    if removed:
        lines.append("### Removed")
        for item in removed:
            lines.append(f"- {item}")
        lines.append("")
    
    # Add commit references if available
    if commits:
        lines.append("### Commits")
        for commit in commits[:10]:  # Limit to 10 commits
            lines.append(f"- `{commit['hash']}` {commit['subject']}")
        lines.append("")
    
    return '\n'.join(lines)


def prepend_to_changelog(new_entry: str, changelog_path: Path) -> bool:
    """Prepend a new entry to an existing changelog."""
    if not changelog_path.exists():
        # Create new changelog
        header = """# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

"""
        changelog_path.write_text(header + new_entry)
        return True
    
    content = changelog_path.read_text()
    
    # Find where to insert (after header, before first version)
    insert_pattern = r'(# Changelog.*?\n\n)'
    match = re.search(insert_pattern, content, re.DOTALL)
    
    if match:
        insert_pos = match.end()
        new_content = content[:insert_pos] + new_entry + '\n' + content[insert_pos:]
        changelog_path.write_text(new_content)
        return True
    else:
        # Just prepend
        changelog_path.write_text(new_entry + '\n' + content)
        return True


def main():
    parser = argparse.ArgumentParser(
        description='Generate changelog entries from code changes',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument('--scope', required=True, help='Directory to analyze')
    parser.add_argument('--since', required=True, help='Changes since commit/date')
    parser.add_argument('--output', help='Output file (default: stdout)')
    parser.add_argument('--format', default='keep-a-changelog', help='Changelog format')
    parser.add_argument('--prepend', action='store_true', help='Prepend to existing changelog')
    parser.add_argument('--version', default='Unreleased', help='Version label')
    args = parser.parse_args()
    
    scope = Path(args.scope).resolve()
    
    if not scope.exists():
        print(f"❌ Error: Directory not found: {scope}", file=sys.stderr)
        sys.exit(2)
    
    print(f"📋 Generating changelog...", file=sys.stderr)
    print(f"   Scope: {scope}", file=sys.stderr)
    print(f"   Since: {args.since}", file=sys.stderr)
    
    # Get changes and commits
    changes = get_changed_files(scope, args.since)
    commits = get_git_log(scope, args.since)
    
    total_changes = sum(len(v) for v in changes.values())
    print(f"   Found {total_changes} changed file(s), {len(commits)} commit(s)", file=sys.stderr)
    
    if total_changes == 0 and len(commits) == 0:
        print("   No changes to document", file=sys.stderr)
        sys.exit(0)
    
    # Generate entry
    entry = generate_changelog_entry(changes, commits, str(scope), args.version)
    
    # Output
    if args.output:
        output_path = Path(args.output)
        
        if args.prepend:
            prepend_to_changelog(entry, output_path)
            print(f"✅ Prepended to: {args.output}", file=sys.stderr)
        else:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(entry)
            print(f"✅ Saved to: {args.output}", file=sys.stderr)
    else:
        print(entry)
    
    sys.exit(0)


if __name__ == '__main__':
    main()
