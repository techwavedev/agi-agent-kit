#!/usr/bin/env python3
"""
Automated Extended Skills Adaptation Script

Syncs skills from the antigravity-awesome-skills fork into templates/skills/extended/,
applying AGI framework adaptations to each SKILL.md.

Features:
- Diff detection: finds new/modified skills vs current extended/
- Section-marker preservation: protects AGI additions during upstream updates
- AGI integration injection: Qdrant memory, Agent Teams, Local LLM
- Dry-run mode: preview changes without modifying files
- JSON report output for CI/CD integration

Usage:
    python3 scripts/adapt_extended_skills.py [--dry-run] [--report]
    python3 scripts/adapt_extended_skills.py --source /path/to/awesome-skills/skills

Exit codes:
    0 - Success
    1 - Source directory not found
    2 - Processing error
"""

import argparse
import json
import os
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

# Defaults
DEFAULT_SOURCE = Path(".tmp/antigravity-awesome-skills/skills")
EXTENDED_DIR = Path("templates/skills/extended")
CORE_DIR = Path("templates/skills/core")
KNOWLEDGE_DIR = Path("templates/skills/knowledge")
CATEGORY_MAP = Path("templates/skills/category_map.json")
DEFAULT_CATEGORY = "other"

# Markers to protect AGI-specific additions during upstream merges
AGI_START_MARKER = "<!-- AGI-INTEGRATION-START -->"
AGI_END_MARKER = "<!-- AGI-INTEGRATION-END -->"

AGI_INTEGRATION_BLOCK = f"""
---

{AGI_START_MARKER}

## 🧠 AGI Framework Integration

> **Adapted for [@techwavedev/agi-agent-kit](https://www.npmjs.com/package/@techwavedev/agi-agent-kit)**
> Original source: [antigravity-awesome-skills](https://github.com/sickn33/antigravity-awesome-skills)

### Qdrant Memory Integration

Before executing complex tasks with this skill:
```bash
python3 execution/memory_manager.py auto --query "<task summary>"
```
- **Cache hit?** Use cached response directly — no need to re-process.
- **Memory match?** Inject `context_chunks` into your reasoning.
- **No match?** Proceed normally, then store results:
```bash
python3 execution/memory_manager.py store \\\\
  --content "Description of what was decided/solved" \\\\
  --type decision \\\\
  --tags <skill-name> <relevant-tags>
```

### Agent Team Collaboration

- This skill can be invoked by the `orchestrator` agent via intelligent routing.
- In **Agent Teams mode**, results are shared via Qdrant shared memory for cross-agent context.
- In **Subagent mode**, this skill runs in isolation with its own memory namespace.

### Local LLM Support

When available, use local Ollama models for embedding and lightweight inference:
- Embeddings: `nomic-embed-text` via Qdrant memory system
- Lightweight analysis: Local models reduce API costs for repetitive patterns

{AGI_END_MARKER}
"""


def get_dirs(path: Path) -> set:
    """Get set of directory names in a path, walking into category subdirectories."""
    if not path.exists():
        return set()
    result = set()
    for entry in path.iterdir():
        if not entry.is_dir():
            continue
        if (entry / "SKILL.md").exists():
            # Direct skill directory (flat layout, e.g., core/)
            result.add(entry.name)
        else:
            # Category directory — look inside for skills
            for sub in entry.iterdir():
                if sub.is_dir() and (sub / "SKILL.md").exists():
                    result.add(sub.name)
    return result


def find_skill_path(base_dir: Path, skill_name: str) -> Path | None:
    """Find actual path of a skill within categorized or flat layout."""
    # Check flat first
    direct = base_dir / skill_name
    if direct.exists():
        return direct
    # Check category subdirectories
    for cat_dir in base_dir.iterdir():
        if cat_dir.is_dir() and not (cat_dir / "SKILL.md").exists():
            candidate = cat_dir / skill_name
            if candidate.exists():
                return candidate
    return None


def load_category_map() -> dict:
    """Load skill→category mapping."""
    if CATEGORY_MAP.exists():
        return json.loads(CATEGORY_MAP.read_text())
    return {}


def get_skill_category(skill_name: str, category_map: dict) -> str:
    """Determine category for a skill. Falls back to DEFAULT_CATEGORY."""
    return category_map.get(skill_name, DEFAULT_CATEGORY)


def extract_agi_block(content: str) -> str | None:
    """Extract existing AGI integration block from content."""
    pattern = re.compile(
        rf"{re.escape(AGI_START_MARKER)}.*?{re.escape(AGI_END_MARKER)}",
        re.DOTALL
    )
    match = pattern.search(content)
    return match.group(0) if match else None


def strip_agi_block(content: str) -> str:
    """Remove AGI integration block from content for comparison."""
    # Remove marker-based block
    pattern = re.compile(
        rf"\n*---\n*\n*{re.escape(AGI_START_MARKER)}.*?{re.escape(AGI_END_MARKER)}\n*",
        re.DOTALL
    )
    content = pattern.sub("", content)
    
    # Also remove legacy block without markers
    pattern2 = re.compile(
        r"\n*---\n*\n*## 🧠 AGI Framework Integration.*$",
        re.DOTALL
    )
    content = pattern2.sub("", content)
    
    return content.rstrip()


def has_upstream_changes(upstream_content: str, local_content: str) -> bool:
    """Check if upstream has meaningful changes (ignoring our AGI additions)."""
    upstream_clean = strip_agi_block(upstream_content).strip()
    local_clean = strip_agi_block(local_content).strip()
    return upstream_clean != local_clean


def adapt_skill_md(skill_dir: Path, skill_name: str, dry_run: bool = False) -> str:
    """
    Add or preserve AGI integration block in SKILL.md.
    Returns: 'adapted', 'preserved', 'no_skill_md'
    """
    skill_md = skill_dir / "SKILL.md"
    
    if not skill_md.exists():
        return "no_skill_md"
    
    content = skill_md.read_text(encoding="utf-8")
    
    # Check for existing marker-based block
    existing_block = extract_agi_block(content)
    
    if existing_block:
        return "preserved"  # Already has markers, don't touch
    
    # Check for legacy block (without markers)
    if "AGI Framework Integration" in content:
        # Upgrade: replace legacy block with marker-based one
        content = strip_agi_block(content)
    
    # Customize and append
    customized = AGI_INTEGRATION_BLOCK.replace("<skill-name>", skill_name)
    content = content.rstrip() + "\n" + customized
    
    if not dry_run:
        skill_md.write_text(content, encoding="utf-8")
    
    return "adapted"


def process_skills(source_dir: Path, dry_run: bool = False) -> dict:
    """Main processing logic. Places skills into categorized subdirectories."""
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source": str(source_dir),
        "dry_run": dry_run,
        "new_skills": [],
        "updated_skills": [],
        "unchanged_skills": [],
        "skipped_duplicates": [],
        "adapted": [],
        "preserved": [],
        "no_skill_md": [],
        "errors": [],
    }

    # Build exclusion set (core + knowledge = already in medium tier)
    exclude_skills = get_dirs(CORE_DIR) | get_dirs(KNOWLEDGE_DIR)
    
    # Get existing extended skills (walks category subdirs)
    existing_extended = get_dirs(EXTENDED_DIR)
    
    # Load category mapping
    category_map = load_category_map()
    
    # Get all source skills (upstream is always flat)
    if not source_dir.exists():
        print(f"✖ Source directory not found: {source_dir}", file=sys.stderr)
        sys.exit(1)
    
    source_skills = sorted(d.name for d in source_dir.iterdir() if d.is_dir())
    print(f"Source: {len(source_skills)} skills")
    print(f"Excluded (core+knowledge): {len(exclude_skills)}")
    print(f"Existing extended: {len(existing_extended)}")
    print(f"Category map: {len(category_map)} entries")
    print(f"Dry run: {dry_run}\n")
    
    EXTENDED_DIR.mkdir(parents=True, exist_ok=True)
    
    for skill_name in source_skills:
        src = source_dir / skill_name
        
        # Skip if in core or knowledge
        if skill_name in exclude_skills:
            report["skipped_duplicates"].append(skill_name)
            continue
        
        # Determine category for this skill
        category = get_skill_category(skill_name, category_map)
        category_dir = EXTENDED_DIR / category
        dest = category_dir / skill_name
        
        # New skill
        if skill_name not in existing_extended:
            if not dry_run:
                category_dir.mkdir(parents=True, exist_ok=True)
                shutil.copytree(src, dest)
                # Update category map with new skills
                category_map[skill_name] = category
            report["new_skills"].append(skill_name)
            
            # Adapt the new skill
            result = adapt_skill_md(dest, skill_name, dry_run)
            report[result].append(skill_name) if result != "adapted" else report["adapted"].append(skill_name)
            continue
        
        # Existing skill — find it in its current category directory
        existing_path = find_skill_path(EXTENDED_DIR, skill_name)
        if not existing_path:
            report["errors"].append(f"{skill_name}: exists in set but not found on disk")
            continue
        
        # Check for upstream changes
        src_skill_md = src / "SKILL.md"
        dest_skill_md = existing_path / "SKILL.md"
        
        if src_skill_md.exists() and dest_skill_md.exists():
            upstream = src_skill_md.read_text(encoding="utf-8")
            local = dest_skill_md.read_text(encoding="utf-8")
            
            if has_upstream_changes(upstream, local):
                # Upstream changed — update core content, preserve AGI block
                existing_agi = extract_agi_block(local)
                new_content = strip_agi_block(upstream).rstrip()
                
                if existing_agi:
                    new_content += f"\n\n---\n\n{existing_agi}\n"
                else:
                    customized = AGI_INTEGRATION_BLOCK.replace("<skill-name>", skill_name)
                    new_content += "\n" + customized
                
                if not dry_run:
                    dest_skill_md.write_text(new_content, encoding="utf-8")
                
                report["updated_skills"].append(skill_name)
            else:
                report["unchanged_skills"].append(skill_name)
        else:
            report["unchanged_skills"].append(skill_name)
    
    # Save updated category map (with any new skills added)
    if not dry_run:
        CATEGORY_MAP.write_text(json.dumps(category_map, indent=2, sort_keys=True))
    
    return report


def print_report(report: dict):
    """Pretty-print the report."""
    print("\n" + "=" * 60)
    print("ADAPTATION REPORT")
    print("=" * 60)
    print(f"  Timestamp:         {report['timestamp']}")
    print(f"  Source:             {report['source']}")
    print(f"  Dry run:           {report['dry_run']}")
    print(f"  New skills:        {len(report['new_skills'])}")
    print(f"  Updated skills:    {len(report['updated_skills'])}")
    print(f"  Unchanged:         {len(report['unchanged_skills'])}")
    print(f"  Skipped (dupes):   {len(report['skipped_duplicates'])}")
    print(f"  Adapted (AGI):     {len(report['adapted'])}")
    print(f"  Preserved (AGI):   {len(report['preserved'])}")
    print(f"  Missing SKILL.md:  {len(report['no_skill_md'])}")
    print(f"  Errors:            {len(report['errors'])}")
    
    # Final counts
    print(f"\n  FINAL TIER COUNTS (walking category subdirs):")
    print(f"    Core:      {len(get_dirs(CORE_DIR))}")
    print(f"    Knowledge: {len(get_dirs(KNOWLEDGE_DIR))}")
    print(f"    Extended:  {len(get_dirs(EXTENDED_DIR))}")

    if report["new_skills"]:
        print(f"\n  NEW SKILLS ({len(report['new_skills'])}):")
        for s in report["new_skills"][:20]:
            print(f"    + {s}")
        if len(report["new_skills"]) > 20:
            print(f"    ... and {len(report['new_skills']) - 20} more")

    if report["updated_skills"]:
        print(f"\n  UPDATED SKILLS ({len(report['updated_skills'])}):")
        for s in report["updated_skills"][:20]:
            print(f"    ~ {s}")
        if len(report["updated_skills"]) > 20:
            print(f"    ... and {len(report['updated_skills']) - 20} more")


def main():
    parser = argparse.ArgumentParser(
        description="Adapt extended skills from antigravity-awesome-skills for AGI Agent Kit"
    )
    parser.add_argument(
        "--source", type=Path, default=DEFAULT_SOURCE,
        help=f"Source skills directory (default: {DEFAULT_SOURCE})"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Preview changes without modifying files"
    )
    parser.add_argument(
        "--report", type=Path, default=None,
        help="Save JSON report to file (default: stdout only)"
    )
    args = parser.parse_args()

    report = process_skills(args.source, dry_run=args.dry_run)
    print_report(report)

    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2))
        print(f"\nJSON report saved to: {args.report}")

    # Exit code
    if report["errors"]:
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()
