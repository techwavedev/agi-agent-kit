#!/usr/bin/env python3
"""
Skills Catalog Updater

Scans the skills directory and updates SKILLS_CATALOG.md with current skill information.
Run this script after creating, modifying, or deleting any skill.

Usage:
    update_catalog.py --skills-dir <path>

Examples:
    update_catalog.py --skills-dir skills/
    update_catalog.py --skills-dir /path/to/skills

Exit Codes:
    0 - Success
    1 - Invalid arguments
    2 - Skills directory not found
    3 - Catalog file error
"""

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path


def parse_skill_frontmatter(skill_md_path: Path) -> dict:
    """
    Parse YAML frontmatter from a SKILL.md file.
    
    Returns:
        dict with 'name' and 'description' keys, or None if parsing fails.
    """
    try:
        content = skill_md_path.read_text()
    except Exception as e:
        print(f"  ⚠️  Could not read {skill_md_path}: {e}")
        return None
    
    # Check for YAML frontmatter
    if not content.startswith('---'):
        print(f"  ⚠️  No YAML frontmatter in {skill_md_path}")
        return None
    
    # Extract frontmatter
    parts = content.split('---', 2)
    if len(parts) < 3:
        print(f"  ⚠️  Invalid YAML frontmatter in {skill_md_path}")
        return None
    
    frontmatter = parts[1].strip()
    
    # Parse simple YAML (name and description only)
    result = {}
    for line in frontmatter.split('\n'):
        if ':' in line:
            key, value = line.split(':', 1)
            key = key.strip()
            value = value.strip()
            if key in ('name', 'description'):
                result[key] = value
    
    return result if 'name' in result else None


def scan_skills(skills_dir: Path) -> list:
    """
    Scan the skills directory for all skills.
    
    Returns:
        List of skill info dicts with name, description, location, scripts, references.
    """
    skills = []
    
    for item in sorted(skills_dir.iterdir()):
        if not item.is_dir():
            continue
        
        skill_md = item / 'SKILL.md'
        if not skill_md.exists():
            print(f"  ⚠️  Skipping {item.name}: no SKILL.md found")
            continue
        
        frontmatter = parse_skill_frontmatter(skill_md)
        if not frontmatter:
            print(f"  ⚠️  Skipping {item.name}: could not parse frontmatter")
            continue
        
        # Gather skill info
        skill_info = {
            'name': frontmatter.get('name', item.name),
            'description': frontmatter.get('description', ''),
            'dir_name': item.name,
            'location': f"skills/{item.name}/",
            'scripts': [],
            'references': [],
            'has_assets': False,
            'parent': None,
        }
        
        # Check for scripts
        scripts_dir = item / 'scripts'
        if scripts_dir.exists() and scripts_dir.is_dir():
            for script in sorted(scripts_dir.glob('*.py')):
                if script.name != '__init__.py' and not script.name.startswith('example'):
                    skill_info['scripts'].append(script.name)
        
        # Check for references
        refs_dir = item / 'references'
        if refs_dir.exists() and refs_dir.is_dir():
            for ref in sorted(refs_dir.glob('*.md')):
                if not ref.name.startswith('example'):
                    skill_info['references'].append(ref.name)
        
        # Check for assets
        assets_dir = item / 'assets'
        if assets_dir.exists() and assets_dir.is_dir():
            skill_info['has_assets'] = any(assets_dir.iterdir())
        
        # Detect parent skill from SKILL.md content
        try:
            content = skill_md.read_text()
            if 'Part of the' in content and 'skill family' in content:
                # Extract parent reference
                match = re.search(r'\[([Aa]ws)\s*(skill family|skill)\]', content)
                if match:
                    skill_info['parent'] = 'aws'
            elif '../aws/SKILL.md' in content:
                skill_info['parent'] = 'aws'
        except Exception:
            pass
        
        skills.append(skill_info)
        print(f"  ✅ Found skill: {skill_info['name']}")
    
    return skills


def generate_skill_entry(skill: dict) -> str:
    """Generate a markdown section for a single skill."""
    lines = []
    
    # Title
    title = skill['name'].replace('-', ' ').title()
    if skill['name'] == 'aws':
        title = 'AWS (Hub)'
    lines.append(f"### {title}")
    lines.append("")
    
    # Property table
    lines.append("| Property | Value |")
    lines.append("| -------- | ----- |")
    lines.append(f"| **Name** | `{skill['name']}` |")
    lines.append(f"| **Location** | `{skill['location']}` |")
    
    if skill['parent']:
        parent_title = skill['parent'].replace('-', ' ').title()
        parent_anchor = skill['parent'].replace('-', '')
        lines.append(f"| **Parent** | [{parent_title}](#{parent_anchor}) |")
    elif skill['name'] == 'aws':
        lines.append("| **Type** | Router / Hub |")
    else:
        lines.append("| **Type** | Standalone |")
    
    lines.append("")
    
    # Description
    desc = skill['description']
    if desc.startswith('[TODO'):
        desc = '*[Description not yet provided]*'
    lines.append(f"**Description:** {desc}")
    lines.append("")
    
    # Scripts
    if skill['scripts']:
        lines.append("**Scripts:**")
        lines.append("")
        lines.append("| Script | Purpose |")
        lines.append("| ------ | ------- |")
        for script in skill['scripts']:
            lines.append(f"| `scripts/{script}` | *[See script for details]* |")
        lines.append("")
    
    # References
    if skill['references']:
        lines.append("**References:**")
        for ref in skill['references']:
            lines.append(f"- `references/{ref}`")
        lines.append("")
    
    lines.append("---")
    lines.append("")
    
    return '\n'.join(lines)


def generate_catalog(skills: list) -> str:
    """Generate the complete SKILLS_CATALOG.md content."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # Header
    header = f"""# Skills Catalog

> **Auto-generated Documentation** — Last updated: {now}
>
> This catalog is automatically maintained. Update it by running:
> ```bash
> python skill-creator/scripts/update_catalog.py --skills-dir skills/
> ```

This document provides comprehensive documentation on available skills, how to use them, and when each skill should be triggered.

---

## Table of Contents

- [What Are Skills?](#what-are-skills)
- [Available Skills](#available-skills)
"""
    
    # Add skill links to TOC
    toc_lines = []
    for skill in skills:
        title = skill['name'].replace('-', ' ').title()
        if skill['name'] == 'aws':
            title = 'AWS (Hub)'
        anchor = title.lower().replace(' ', '-').replace('(', '').replace(')', '')
        toc_lines.append(f"  - [{title}](#{anchor})")
    
    header += '\n'.join(toc_lines)
    header += """
- [Using Skills](#using-skills)
- [Creating New Skills](#creating-new-skills)
- [Maintenance](#maintenance)

---

## What Are Skills?

**Skills** are modular, self-contained packages that extend the AI agent's capabilities with specialized knowledge, workflows, and tools.

### Skill Structure

```
skill-name/
├── SKILL.md           # (required) Main instruction file
├── scripts/           # (optional) Executable scripts
├── references/        # (optional) Documentation
└── assets/            # (optional) Templates, images, etc.
```

---

## Available Skills

"""
    
    # Generate skill entries
    skill_entries = []
    
    # Sort: hub skills first, then by name
    def sort_key(s):
        if s['name'] == 'aws':
            return ('0', s['name'])
        elif s['parent']:
            return ('1', s['name'])
        else:
            return ('2', s['name'])
    
    for skill in sorted(skills, key=sort_key):
        skill_entries.append(generate_skill_entry(skill))
    
    # Footer
    footer = """## Using Skills

Skills are automatically triggered based on the user's request matching the skill description. You can also explicitly invoke a skill:

```
"Use the <skill-name> skill to <task>"
```

---

## Creating New Skills

```bash
# Initialize a new skill
python skill-creator/scripts/init_skill.py my-new-skill --path skills/

# Package the skill
python skill-creator/scripts/package_skill.py skills/my-new-skill
```

For detailed guidance, see: `skill-creator/SKILL_skillcreator.md`

---

## Maintenance

### Updating This Catalog

**IMPORTANT:** This catalog must be updated whenever skills are created, modified, or deleted.

```bash
python skill-creator/scripts/update_catalog.py --skills-dir skills/
```

---

*This catalog is part of the [3-Layer Architecture](../AGENTS.md) for reliable AI agent operations.*
"""
    
    return header + '\n'.join(skill_entries) + footer


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--skills-dir', required=True, help='Path to skills directory')
    parser.add_argument('--output', help='Output path (default: <skills-dir>/SKILLS_CATALOG.md)')
    parser.add_argument('--json', action='store_true', help='Also output JSON summary')
    args = parser.parse_args()
    
    skills_dir = Path(args.skills_dir).resolve()
    
    if not skills_dir.exists() or not skills_dir.is_dir():
        print(f"❌ Error: Skills directory not found: {skills_dir}")
        sys.exit(2)
    
    print(f"🔍 Scanning skills in: {skills_dir}")
    print()
    
    # Scan for skills
    skills = scan_skills(skills_dir)
    
    if not skills:
        print("\n⚠️  No valid skills found.")
        sys.exit(0)
    
    print(f"\n📚 Found {len(skills)} skill(s)")
    
    # Generate catalog
    catalog_content = generate_catalog(skills)
    
    # Determine output path
    output_path = Path(args.output) if args.output else skills_dir / 'SKILLS_CATALOG.md'
    
    try:
        output_path.write_text(catalog_content)
        print(f"✅ Catalog updated: {output_path}")
    except Exception as e:
        print(f"❌ Error writing catalog: {e}")
        sys.exit(3)
    
    # Optional JSON output
    if args.json:
        json_path = output_path.with_suffix('.json')
        try:
            json_path.write_text(json.dumps(skills, indent=2))
            print(f"✅ JSON summary: {json_path}")
        except Exception as e:
            print(f"⚠️  Could not write JSON: {e}")
    
    print("\n✅ Catalog update complete!")
    sys.exit(0)


if __name__ == '__main__':
    main()
