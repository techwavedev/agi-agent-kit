#!/usr/bin/env python3
"""
Change Detection Engine for Documentation Skill

Scans the repository or specific directories to detect code changes
since the last documentation update. Uses git for accurate change tracking.

Usage:
    python detect_changes.py --scope <path> [options]

Arguments:
    --scope         Directory to scan (required)
    --since         Compare since commit/date (default: HEAD~10)
    --output        Output report file (default: stdout)
    --format        Output format: md, json (default: md)
    --include-git   Use git diff for precise changes (default: true)

Exit Codes:
    0 - Success
    1 - Invalid arguments
    2 - Directory not found
    3 - Git error
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


# File patterns to track for documentation updates
TRACKED_PATTERNS = {
    'skill_definition': ['*/SKILL.md', 'SKILL_*.md'],
    'skill_scripts': ['skills/*/scripts/*.py'],
    'skill_references': ['skills/*/references/*.md'],
    'execution_scripts': ['execution/*.py'],
    'directives': ['directives/*.md'],
    'core_docs': ['AGENTS.md', 'README.md', 'SKILLS_CATALOG.md'],
    'python_modules': ['**/*.py'],
}

# Patterns to ignore
IGNORE_PATTERNS = [
    '.tmp/',
    '.git/',
    '__pycache__/',
    '*.pyc',
    '.DS_Store',
    'node_modules/',
    '.env',
    '*.egg-info/',
]


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
    except subprocess.TimeoutExpired:
        return False, "Git command timed out"
    except Exception as e:
        return False, str(e)


def get_git_root(path: Path) -> Optional[Path]:
    """Find the git repository root."""
    success, output = run_git_command(['rev-parse', '--show-toplevel'], path)
    if success:
        return Path(output)
    return None


def get_changed_files(scope: Path, since: str) -> Dict[str, List[str]]:
    """
    Get files changed since a specific commit or date.
    
    Returns:
        Dict with keys: 'added', 'modified', 'deleted'
    """
    git_root = get_git_root(scope)
    if not git_root:
        print("⚠️  Not a git repository, using file scan fallback", file=sys.stderr)
        return get_files_by_scan(scope)
    
    changes = {
        'added': [],
        'modified': [],
        'deleted': [],
    }
    
    # Get diff with names and status
    success, output = run_git_command(
        ['diff', '--name-status', since, '--', str(scope.relative_to(git_root))],
        git_root
    )
    
    if not success:
        # Try with HEAD if since ref doesn't exist
        success, output = run_git_command(
            ['diff', '--name-status', 'HEAD~5', '--', str(scope.relative_to(git_root))],
            git_root
        )
    
    if not success:
        print(f"⚠️  Git diff failed, using file scan fallback", file=sys.stderr)
        return get_files_by_scan(scope)
    
    # Parse git diff output
    for line in output.split('\n'):
        if not line.strip():
            continue
        
        parts = line.split('\t')
        if len(parts) < 2:
            continue
        
        status, filepath = parts[0], parts[1]
        
        # Filter by ignore patterns
        if should_ignore(filepath):
            continue
        
        if status.startswith('A'):
            changes['added'].append(filepath)
        elif status.startswith('M'):
            changes['modified'].append(filepath)
        elif status.startswith('D'):
            changes['deleted'].append(filepath)
        elif status.startswith('R'):
            # Renamed: treat as delete + add
            if len(parts) >= 3:
                changes['deleted'].append(filepath)
                changes['added'].append(parts[2])
    
    # Also check for untracked files in scope
    success, untracked = run_git_command(
        ['ls-files', '--others', '--exclude-standard', str(scope.relative_to(git_root))],
        git_root
    )
    
    if success and untracked:
        for filepath in untracked.split('\n'):
            if filepath and not should_ignore(filepath):
                changes['added'].append(filepath)
    
    return changes


def get_files_by_scan(scope: Path) -> Dict[str, List[str]]:
    """Fallback: scan directory for all files (no change detection)."""
    files = []
    for pattern in ['**/*.py', '**/*.md']:
        for f in scope.glob(pattern):
            if not should_ignore(str(f)):
                files.append(str(f.relative_to(scope)))
    
    return {
        'added': [],
        'modified': files,  # Treat all as modified when we can't detect
        'deleted': [],
    }


def should_ignore(filepath: str) -> bool:
    """Check if a file should be ignored."""
    for pattern in IGNORE_PATTERNS:
        if pattern.endswith('/'):
            if pattern[:-1] in filepath:
                return True
        elif pattern.startswith('*'):
            if filepath.endswith(pattern[1:]):
                return True
        elif pattern in filepath:
            return True
    return False


def categorize_file(filepath: str) -> Tuple[str, str]:
    """
    Categorize a file and determine its documentation impact.
    
    Returns:
        (category, doc_impact)
    """
    path = Path(filepath)
    
    if 'SKILL.md' in filepath or filepath.startswith('SKILL_'):
        return 'skill_definition', 'Update SKILLS_CATALOG.md'
    
    if '/scripts/' in filepath and filepath.endswith('.py'):
        skill_match = filepath.split('/scripts/')[0]
        skill_name = Path(skill_match).name
        return 'skill_scripts', f'Update {skill_name} SKILL.md scripts section'
    
    if '/references/' in filepath and filepath.endswith('.md'):
        skill_match = filepath.split('/references/')[0]
        skill_name = Path(skill_match).name
        return 'skill_references', f'Update {skill_name} SKILL.md references section'
    
    if filepath.startswith('execution/') and filepath.endswith('.py'):
        return 'execution_scripts', 'Update execution documentation'
    
    if filepath.startswith('directives/') and filepath.endswith('.md'):
        return 'directives', 'Update directives catalog if exists'
    
    if path.name in ['AGENTS.md', 'README.md', 'SKILLS_CATALOG.md']:
        return 'core_docs', 'Core documentation changed - review manually'
    
    if filepath.endswith('.py'):
        return 'python_modules', 'Potential module documentation update'
    
    if filepath.endswith('.md'):
        return 'markdown', 'Documentation file changed'
    
    return 'other', 'No documentation action required'


def analyze_impact(changes: Dict[str, List[str]]) -> Dict[str, List[Dict]]:
    """
    Analyze the documentation impact of detected changes.
    
    Returns:
        Dict with documentation update recommendations
    """
    impact = {
        'skills_catalog_update': False,
        'skill_updates': {},
        'other_updates': [],
        'files': []
    }
    
    all_files = []
    for status, files in changes.items():
        for filepath in files:
            category, doc_impact = categorize_file(filepath)
            
            file_info = {
                'path': filepath,
                'status': status,
                'category': category,
                'impact': doc_impact
            }
            all_files.append(file_info)
            
            # Track specific impacts
            if category == 'skill_definition':
                impact['skills_catalog_update'] = True
            
            if category in ['skill_scripts', 'skill_references']:
                # Extract skill name
                if '/scripts/' in filepath:
                    skill = filepath.split('/scripts/')[0].split('/')[-1]
                elif '/references/' in filepath:
                    skill = filepath.split('/references/')[0].split('/')[-1]
                else:
                    skill = 'unknown'
                
                if skill not in impact['skill_updates']:
                    impact['skill_updates'][skill] = []
                impact['skill_updates'][skill].append(file_info)
    
    impact['files'] = all_files
    return impact


def format_markdown_report(changes: Dict, impact: Dict, scope: str, since: str) -> str:
    """Generate a markdown report of changes and their documentation impact."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    added_count = len(changes['added'])
    modified_count = len(changes['modified'])
    deleted_count = len(changes['deleted'])
    total = added_count + modified_count + deleted_count
    
    lines = [
        "# Documentation Change Report",
        "",
        f"> **Generated:** {now}",
        f"> **Scope:** `{scope}`",
        f"> **Since:** `{since}`",
        "",
        "---",
        "",
        "## Summary",
        "",
        f"- **Added:** {added_count} files",
        f"- **Modified:** {modified_count} files", 
        f"- **Deleted:** {deleted_count} files",
        f"- **Total Changes:** {total}",
        "",
    ]
    
    if total == 0:
        lines.append("✅ No changes detected requiring documentation updates.")
        return '\n'.join(lines)
    
    # Documentation Impact Section
    lines.extend([
        "---",
        "",
        "## Documentation Impact",
        "",
    ])
    
    if impact['skills_catalog_update']:
        lines.append("- [x] **SKILLS_CATALOG.md** — Skill definitions changed, catalog update required")
    
    for skill, files in impact['skill_updates'].items():
        lines.append(f"- [ ] **skills/{skill}/SKILL.md** — {len(files)} file(s) changed")
    
    lines.extend(["", "---", ""])
    
    # Detailed Changes
    lines.append("## Detailed Changes")
    lines.append("")
    
    if changes['added']:
        lines.extend([
            "### Added Files",
            "",
            "| File | Category | Documentation Impact |",
            "|------|----------|---------------------|",
        ])
        for filepath in sorted(changes['added']):
            category, doc_impact = categorize_file(filepath)
            lines.append(f"| `{filepath}` | {category} | {doc_impact} |")
        lines.append("")
    
    if changes['modified']:
        lines.extend([
            "### Modified Files",
            "",
            "| File | Category | Documentation Impact |",
            "|------|----------|---------------------|",
        ])
        for filepath in sorted(changes['modified']):
            category, doc_impact = categorize_file(filepath)
            lines.append(f"| `{filepath}` | {category} | {doc_impact} |")
        lines.append("")
    
    if changes['deleted']:
        lines.extend([
            "### Deleted Files",
            "",
            "| File | Category | Documentation Impact |",
            "|------|----------|---------------------|",
        ])
        for filepath in sorted(changes['deleted']):
            category, doc_impact = categorize_file(filepath)
            lines.append(f"| `{filepath}` | {category} | {doc_impact} |")
        lines.append("")
    
    # Recommended Actions
    lines.extend([
        "---",
        "",
        "## Recommended Actions",
        "",
    ])
    
    if impact['skills_catalog_update']:
        lines.append("```bash")
        lines.append("# Update the skills catalog")
        lines.append("python skill-creator/scripts/update_catalog.py --skills-dir skills/")
        lines.append("```")
        lines.append("")
    
    for skill in impact['skill_updates'].keys():
        lines.append("```bash")
        lines.append(f"# Update documentation for {skill} skill")
        lines.append(f"python skills/documentation/scripts/update_skill_docs.py --skill {skill}")
        lines.append("```")
        lines.append("")
    
    return '\n'.join(lines)


def format_json_report(changes: Dict, impact: Dict, scope: str, since: str) -> str:
    """Generate a JSON report of changes."""
    report = {
        'generated': datetime.now().isoformat(),
        'scope': str(scope),
        'since': since,
        'summary': {
            'added': len(changes['added']),
            'modified': len(changes['modified']),
            'deleted': len(changes['deleted']),
        },
        'changes': changes,
        'impact': {
            'skills_catalog_update_required': impact['skills_catalog_update'],
            'skill_updates_required': list(impact['skill_updates'].keys()),
            'files': impact['files'],
        }
    }
    return json.dumps(report, indent=2)


def main():
    parser = argparse.ArgumentParser(
        description='Detect code changes for documentation updates',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument('--scope', required=True, help='Directory to scan')
    parser.add_argument('--since', default='HEAD~10', help='Compare since commit/date')
    parser.add_argument('--output', help='Output file (default: stdout)')
    parser.add_argument('--format', choices=['md', 'json'], default='md', help='Output format')
    parser.add_argument('--include-git', type=bool, default=True, help='Use git for detection')
    args = parser.parse_args()
    
    scope = Path(args.scope).resolve()
    
    if not scope.exists():
        print(f"❌ Error: Directory not found: {scope}", file=sys.stderr)
        sys.exit(2)
    
    print(f"🔍 Scanning for changes in: {scope}", file=sys.stderr)
    print(f"   Since: {args.since}", file=sys.stderr)
    
    # Detect changes
    changes = get_changed_files(scope, args.since)
    
    total = sum(len(v) for v in changes.values())
    print(f"   Found: {total} changed file(s)", file=sys.stderr)
    
    # Analyze impact
    impact = analyze_impact(changes)
    
    # Generate report
    if args.format == 'json':
        report = format_json_report(changes, impact, str(scope), args.since)
    else:
        report = format_markdown_report(changes, impact, str(scope), args.since)
    
    # Output
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(report)
        print(f"✅ Report saved to: {args.output}", file=sys.stderr)
    else:
        print(report)
    
    sys.exit(0)


if __name__ == '__main__':
    main()
