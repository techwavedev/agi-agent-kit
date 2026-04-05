#!/usr/bin/env python3
"""
Script: list_capabilities.py
Purpose: Rapidly scans both project-local and global environments to enumerate
         all available skills, teams, and sub-agents. Merges them and produces
         a JSON catalog for the /agi router to use. Project overrides global.
"""

import json
import sys
from pathlib import Path

# Add the script's directory to sys.path so we can import local modules
sys.path.insert(0, str(Path(__file__).resolve().parent))
from resolve_paths import gather_from_both


def parse_markdown_metadata(content: str) -> dict:
    """Extract YAML frontmatter between --- blocks."""
    meta = {}
    lines = content.splitlines()
    if not lines or lines[0].strip() != "---":
        return meta
        
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if ":" in line:
            parts = line.split(":", 1)
            meta[parts[0].strip()] = parts[1].strip().strip('"\'')
    return meta


def get_skills() -> list:
    """Find all SKILL.md files and parse their metadata."""
    skills = []
    # SKILL.md files can be in templates/skills/extended/... or just skills/...
    # Walk both trees
    for path in gather_from_both("templates/skills"):
        if path.name == "SKILL.md":
            meta = parse_markdown_metadata(path.read_text(errors="replace"))
            if meta.get("name"):
                skills.append({
                    "id": meta["name"],
                    "description": meta.get("description", "No description"),
                    "type": "skill"
                })
    return skills


def get_teams() -> list:
    """Find all team directives."""
    teams = []
    for path in gather_from_both("directives/teams"):
        if path.suffix == ".md":
            team_id = path.stem
            # Very basic extraction: first paragraph
            content = path.read_text(errors="replace").splitlines()
            desc = ""
            for line in content:
                if line.strip() and not line.startswith("#") and not line.startswith("|") and not line.startswith("-"):
                    desc = line.strip()
                    break
                    
            teams.append({
                "id": team_id,
                "description": desc or f"Team directive for {team_id}",
                "type": "team"
            })
    return teams


def get_sub_agents() -> list:
    """Find all sub-agent directives."""
    agents = []
    for path in gather_from_both("directives/subagents"):
        if path.suffix == ".md":
            agent_id = path.stem
            agents.append({
                "id": agent_id,
                "description": f"Sub-agent specialized in {agent_id.replace('_', ' ')}",
                "type": "sub_agent"
            })
    return agents


def main():
    catalog = {
        "teams": get_teams(),
        "sub_agents": get_sub_agents(),
        "skills": get_skills()
    }
    
    # Simple JSON dump to stdout
    print(json.dumps(catalog, indent=2))
    sys.exit(0)


if __name__ == "__main__":
    main()
