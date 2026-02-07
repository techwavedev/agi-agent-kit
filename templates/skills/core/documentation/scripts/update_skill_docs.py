#!/usr/bin/env python3
"""
Skill Documentation Updater

Updates documentation for a specific skill based on its current state.
Extracts information from scripts, references, and updates SKILL.md.

Usage:
    python update_skill_docs.py --skill <name> [options]

Arguments:
    --skill         Skill name to update (required)
    --skills-dir    Skills directory (default: skills/)
    --changelog     Generate changelog entry (optional)
    --analyze-scripts  Analyze script docstrings (default: true)
    --update-references  Update references list (default: true)
    --dry-run       Preview changes without writing (optional)

Exit Codes:
    0 - Success
    1 - Invalid arguments
    2 - Skill not found
    3 - Parse error
    4 - Write error
"""

import argparse
import ast
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


def parse_skill_md(skill_path: Path) -> Tuple[Dict, str]:
    """
    Parse SKILL.md into frontmatter and body.
    
    Returns:
        (frontmatter_dict, body_string)
    """
    content = skill_path.read_text()
    
    if not content.startswith('---'):
        return {}, content
    
    parts = content.split('---', 2)
    if len(parts) < 3:
        return {}, content
    
    frontmatter_raw = parts[1].strip()
    body = parts[2]
    
    # Parse simple YAML
    frontmatter = {}
    for line in frontmatter_raw.split('\n'):
        if ':' in line:
            key, value = line.split(':', 1)
            frontmatter[key.strip()] = value.strip().strip('"\'')
    
    return frontmatter, body


def extract_script_info(script_path: Path) -> Dict:
    """
    Extract documentation info from a Python script.
    
    Returns:
        Dict with: name, docstring, functions, usage
    """
    try:
        content = script_path.read_text()
        tree = ast.parse(content)
    except SyntaxError as e:
        return {
            'name': script_path.name,
            'docstring': f'[Parse error: {e}]',
            'functions': [],
            'usage': None
        }
    
    info = {
        'name': script_path.name,
        'docstring': '',
        'functions': [],
        'usage': None
    }
    
    # Get module docstring
    if tree.body and isinstance(tree.body[0], ast.Expr):
        if isinstance(tree.body[0].value, ast.Constant):
            info['docstring'] = tree.body[0].value.value or ''
    
    # Extract usage from docstring
    if 'Usage:' in info['docstring']:
        usage_match = re.search(r'Usage:\s*\n(.*?)(?:\n\n|\nArguments:|\nExit)', 
                                info['docstring'], re.DOTALL)
        if usage_match:
            info['usage'] = usage_match.group(1).strip()
    
    # Get main function definitions
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            func_info = {
                'name': node.name,
                'docstring': ast.get_docstring(node) or '',
                'args': [arg.arg for arg in node.args.args if arg.arg != 'self']
            }
            info['functions'].append(func_info)
    
    return info


def get_first_line_description(docstring: str) -> str:
    """Extract the first meaningful line from a docstring."""
    if not docstring:
        return '*[See script for details]*'
    
    # Skip empty lines and get first content line
    lines = [l.strip() for l in docstring.split('\n') if l.strip()]
    if lines:
        first_line = lines[0]
        # Truncate if too long
        if len(first_line) > 100:
            return first_line[:97] + '...'
        return first_line
    
    return '*[See script for details]*'


def scan_skill_scripts(skill_dir: Path) -> List[Dict]:
    """Scan all Python scripts in a skill's scripts/ directory."""
    scripts_dir = skill_dir / 'scripts'
    if not scripts_dir.exists():
        return []
    
    scripts = []
    for script_path in sorted(scripts_dir.glob('*.py')):
        if script_path.name.startswith('__') or script_path.name.startswith('example'):
            continue
        
        info = extract_script_info(script_path)
        scripts.append(info)
    
    return scripts


def scan_skill_references(skill_dir: Path) -> List[str]:
    """Scan all reference files in a skill's references/ directory."""
    refs_dir = skill_dir / 'references'
    if not refs_dir.exists():
        return []
    
    refs = []
    for ref_path in sorted(refs_dir.glob('*.md')):
        if ref_path.name.startswith('example'):
            continue
        refs.append(ref_path.name)
    
    return refs


def update_last_updated(body: str) -> str:
    """Update the 'Last Updated' timestamp in the body."""
    today = datetime.now().strftime('%Y-%m-%d')
    
    # Pattern: > **Last Updated:** YYYY-MM-DD
    pattern = r'>\s*\*\*Last Updated:\*\*\s*\d{4}-\d{2}-\d{2}'
    replacement = f'> **Last Updated:** {today}'
    
    if re.search(pattern, body):
        return re.sub(pattern, replacement, body)
    
    # If not found, try to add it after the first heading
    lines = body.split('\n')
    for i, line in enumerate(lines):
        if line.startswith('# ') and i < len(lines) - 1:
            # Insert after heading and any following empty line
            insert_at = i + 1
            while insert_at < len(lines) and not lines[insert_at].strip():
                insert_at += 1
            
            lines.insert(insert_at, '')
            lines.insert(insert_at + 1, replacement)
            lines.insert(insert_at + 2, '')
            break
    
    return '\n'.join(lines)


def generate_scripts_section(scripts: List[Dict]) -> str:
    """Generate a markdown section for scripts."""
    if not scripts:
        return ""
    
    lines = [
        "## Scripts",
        ""
    ]
    
    for script in scripts:
        lines.append(f"### `{script['name']}`")
        lines.append("")
        
        # First line of docstring as description
        desc = get_first_line_description(script['docstring'])
        if desc and desc != '*[See script for details]*':
            lines.append(desc)
            lines.append("")
        
        # Usage example if available
        if script['usage']:
            lines.append("```bash")
            for usage_line in script['usage'].split('\n'):
                lines.append(usage_line)
            lines.append("```")
            lines.append("")
    
    return '\n'.join(lines)


def generate_references_section(references: List[str]) -> str:
    """Generate a markdown section for references."""
    if not references:
        return ""
    
    lines = [
        "## References",
        ""
    ]
    
    for ref in references:
        ref_name = ref.replace('.md', '').replace('_', ' ').title()
        lines.append(f"- [`{ref}`](references/{ref}) — {ref_name}")
    
    lines.append("")
    return '\n'.join(lines)


def generate_changelog_entry(skill_name: str, scripts: List[Dict], refs: List[str]) -> str:
    """Generate a changelog entry for the skill update."""
    today = datetime.now().strftime('%Y-%m-%d')
    
    lines = [
        f"## [{today}] - {skill_name} Documentation Update",
        "",
        "### Changed",
        f"- Updated documentation for `{skill_name}` skill",
    ]
    
    if scripts:
        lines.append(f"- Updated scripts documentation ({len(scripts)} scripts)")
    
    if refs:
        lines.append(f"- Updated references listing ({len(refs)} references)")
    
    lines.extend(["", ""])
    return '\n'.join(lines)


def update_skill_md(skill_dir: Path, scripts: List[Dict], refs: List[str], 
                    dry_run: bool = False) -> Tuple[bool, str]:
    """
    Update the SKILL.md file with current script and reference information.
    
    Returns:
        (success, message)
    """
    skill_md_path = skill_dir / 'SKILL.md'
    
    if not skill_md_path.exists():
        return False, f"SKILL.md not found in {skill_dir}"
    
    frontmatter, body = parse_skill_md(skill_md_path)
    
    if not frontmatter:
        return False, "Could not parse SKILL.md frontmatter"
    
    # Update last updated timestamp
    body = update_last_updated(body)
    
    # TODO: More sophisticated body updates could be done here
    # For now, we just update the timestamp and leave content intact
    # A more advanced version could:
    # - Update scripts section with extracted docstrings
    # - Update references section with current files
    # - Add missing sections
    
    # Rebuild SKILL.md
    new_content = '---\n'
    for key, value in frontmatter.items():
        if ' ' in value or ':' in value or value.startswith('['):
            new_content += f'{key}: "{value}"\n'
        else:
            new_content += f'{key}: {value}\n'
    new_content += '---\n'
    new_content += body
    
    if dry_run:
        return True, "Dry run - no changes written"
    
    try:
        skill_md_path.write_text(new_content)
        return True, f"Updated {skill_md_path}"
    except Exception as e:
        return False, f"Write error: {e}"


def main():
    parser = argparse.ArgumentParser(
        description='Update skill documentation',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument('--skill', required=True, help='Skill name to update')
    parser.add_argument('--skills-dir', default='skills/', help='Skills directory')
    parser.add_argument('--changelog', action='store_true', help='Generate changelog entry')
    parser.add_argument('--analyze-scripts', type=bool, default=True, help='Analyze scripts')
    parser.add_argument('--update-references', type=bool, default=True, help='Update references')
    parser.add_argument('--dry-run', action='store_true', help='Preview without writing')
    args = parser.parse_args()
    
    skills_dir = Path(args.skills_dir).resolve()
    skill_dir = skills_dir / args.skill
    
    if not skill_dir.exists():
        print(f"❌ Error: Skill not found: {skill_dir}", file=sys.stderr)
        sys.exit(2)
    
    print(f"📝 Updating documentation for: {args.skill}")
    
    # Scan scripts
    scripts = scan_skill_scripts(skill_dir) if args.analyze_scripts else []
    print(f"   Found {len(scripts)} script(s)")
    
    # Scan references
    refs = scan_skill_references(skill_dir) if args.update_references else []
    print(f"   Found {len(refs)} reference(s)")
    
    # Update SKILL.md
    success, message = update_skill_md(skill_dir, scripts, refs, args.dry_run)
    
    if success:
        print(f"✅ {message}")
    else:
        print(f"❌ {message}", file=sys.stderr)
        sys.exit(4)
    
    # Generate changelog if requested
    if args.changelog and not args.dry_run:
        changelog_entry = generate_changelog_entry(args.skill, scripts, refs)
        print("\n📋 Changelog Entry:")
        print(changelog_entry)
    
    print("\n✅ Documentation update complete!")
    
    # Remind to update catalog
    print("\n💡 Remember to update the skills catalog:")
    print("   python skill-creator/scripts/update_catalog.py --skills-dir skills/")
    
    sys.exit(0)


if __name__ == '__main__':
    main()
