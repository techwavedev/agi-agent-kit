#!/usr/bin/env python3
"""
Gem Factory

A factory script that scaffolds specialized "Gems" (Portable AI instances)
and allows the user to export them as raw JSON payloads OR native Framework Skills.
"""

import os
import sys
import json
import argparse
import subprocess
from pathlib import Path

def run_command(cmd_args):
    try:
        result = subprocess.run(cmd_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error executing {' '.join(cmd_args)}: {e.stderr.strip()}")
        sys.exit(1)

def export_as_skill(gem_data):
    """Packages the Gem as a native AGI Framework Skill."""
    skill_name = gem_data['name'].lower().replace(" ", "-")
    skill_dir = Path(f"skills/{skill_name}")
    skill_dir.mkdir(parents=True, exist_ok=True)
    
    skill_md_path = skill_dir / "SKILL.md"
    
    # YAML Frontmatter + Markdown Instruction
    content = f"""---
name: {skill_name}
description: {gem_data['description']}
type: gem
gem_prompt: |
{gem_data['core_prompt']}
---

# {gem_data['name']} (Gem)

This is an auto-generated Gem Skill. When using this skill, the agent must adhere to the core prompt.

## Core Prompt
{gem_data['core_prompt']}

## Activated Context (Qdrant)
This Gem inherently relies on the following Qdrant Project context namespace: `{gem_data['collection']}`
"""
    with open(skill_md_path, "w") as f:
        f.write(content)
        
    print(f"✅ Gem natively built as a Skill at: {skill_md_path}")
    return str(skill_md_path)

def build_gem(name, description, prompt, context_files, collection, as_skill):
    gem_data = {
        "id": f"gem-{os.urandom(4).hex()}",
        "name": name,
        "description": description,
        "core_prompt": prompt,
        "collection": collection,
        "context_files": context_files,
        "version": "1.0.0"
    }

    # 1. Scrape Context Files and upload to Qdrant if provided
    if context_files:
        print(f"🧠 Encoding {len(context_files)} context files into Qdrant namespace '{collection}'...")
        for fpath in context_files:
            if os.path.exists(fpath):
                with open(fpath, "r") as f:
                    content = f.read()
                print(f"   -> Storing {fpath}...")
                run_command([
                    "python3", "execution/memory_manager.py", "store",
                    "--content", f"System Context from {fpath}: {content[:1500]}...", # Truncated for demo script
                    "--type", "knowledge",
                    "--project", collection,
                    "--tags", "gem-context", "gem-factory"
                ])
            else:
                print(f"   ⚠️ File not found: {fpath}")

    # 2. Export Raw JSON
    out_dir = Path(".tmp/gems")
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / f"{name.lower().replace(' ', '_')}.gem.json"
    
    with open(json_path, "w") as f:
        json.dump(gem_data, f, indent=2)
        
    print(f"💎 Portable Gem JSON generated at: {json_path}")

    # 3. Export as Skill if requested
    if as_skill:
        export_as_skill(gem_data)
        
    return json_path

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Gem Factory: Pack portable AI instances.")
    parser.add_argument("--name", type=str, required=True, help="Display Name of the Gem")
    parser.add_argument("--desc", type=str, required=True, help="Brief description")
    parser.add_argument("--prompt", type=str, required=True, help="The specialized system instruction")
    parser.add_argument("--context", type=str, nargs="+", help="File paths to inject into Qdrant context")
    parser.add_argument("--project", type=str, default="openminions-gems", help="Qdrant Project/Collection ID")
    parser.add_argument("--as-skill", action="store_true", help="Also generate a native skills/ folder for it")
    
    args = parser.parse_args()
    build_gem(args.name, args.desc, args.prompt, args.context, args.project, args.as_skill)
