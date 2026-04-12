#!/usr/bin/env python3
"""
Script: tool_discovery.py
Purpose: Dynamic Tool Discovery Bridge for AGI Agent Kit.
         Scans all SKILL.md files, parses definitions and multi-shot examples, 
         and indexes them into Qdrant to allow deferred, context-saving tool loading.

Usage:
    # Index all available skills
    python3 execution/tool_discovery.py index

    # Search for exactly the tools needed for a task
    python3 execution/tool_discovery.py search --query "I need to parse a PDF file"

Arguments:
    index    - Re-indexes all SKILL.md files into the Qdrant memory collection
    search   - Queries Qdrant and returns the JSON schemas + examples for matching skills

Exit Codes:
    0 - Success
    1 - Invalid arguments
    3 - API/Processing error
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

# Add the project root to sys.path to easily import memory_manager components
script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent
sys.path.insert(0, str(script_dir))

try:
    from memory_manager import store_memory, retrieve_context, build_filter
except ImportError:
    print("Error: Could not import memory_manager. Ensure you are running this from the project root.", file=sys.stderr)
    sys.exit(3)

def parse_skill_file(filepath: Path) -> dict:
    """Parses a SKILL.md file to extract name, description, and examples."""
    content = filepath.read_text(encoding='utf-8')
    
    # Extract YAML frontmatter
    frontmatter_match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
    name = "unknown_skill"
    description = ""
    
    if frontmatter_match:
        yaml_content = frontmatter_match.group(1)
        for line in yaml_content.split('\n'):
            if line.startswith('name:'):
                name = line.split(':', 1)[1].strip().strip('"\'')
            elif line.startswith('description:'):
                description = line.split(':', 1)[1].strip().strip('"\'')
    
    # Extract multi-shot examples (look for bash or python code blocks)
    examples = []
    code_blocks = re.findall(r'```(bash|python|sh)\n(.*?)```', content, re.DOTALL)
    for lang, code in code_blocks:
        if len(examples) < 3: # Keep max 3 examples
            clean_code = code.strip()
            if clean_code and not clean_code.startswith('pip install'):
                examples.append({"language": lang, "code": clean_code})

    # Prepare schema document for embedding
    # We want Qdrant to embed a concise representation of what the tooling does
    search_document = f"Tool Name: {name}\nDescription: {description}\n"
    
    return {
        "name": name,
        "description": description,
        "examples": examples,
        "search_document": search_document,
        "path": str(filepath.relative_to(project_root))
    }

def index_skills():
    print("Scanning for SKILL.md files...")
    # Support both templates and base skills dirs
    search_dirs = [
        project_root / "skills",
        project_root / "templates" / "skills"
    ]
    
    skill_files = []
    for d in search_dirs:
        if d.exists():
            skill_files.extend(list(d.rglob("SKILL.md")))

    print(f"Found {len(skill_files)} skill files. Submitting to Qdrant Tool Discovery Bridge...")
    
    indexed = 0
    for sf in skill_files:
        try:
            skill_data = parse_skill_file(sf)
            if skill_data["name"] == "unknown_skill":
                continue
            
            # Storing memory via the execution manager wrapper 
            # We use type 'skill_schema' to differentiate from normal memories
            store_memory(
                content=skill_data["search_document"],
                memory_type="skill_schema",
                metadata={
                    "project": "agi-agent-kit",
                    "skill_name": skill_data["name"],
                    "skill_path": skill_data["path"],
                    "examples": json.dumps(skill_data["examples"])
                }
            )
            indexed += 1
            print(f" ✓ Indexed: {skill_data['name']}")
        except Exception as e:
            print(f" ⚠ Failed to index {sf}: {e}", file=sys.stderr)

    print(f"\nSuccessfully indexed {indexed} skills.")

def search_skills(query: str, top_k: int = 3):
    """Searches Qdrant for the best N tools for a given prompt."""
    filters = build_filter(type_filter="skill_schema", project="agi-agent-kit")
    
    result = retrieve_context(
        query=query,
        filters={"must": filters["must"]} if filters else None,
        top_k=top_k,
        score_threshold=0.5
    )
    
    if result.get("total_chunks", 0) == 0:
        return {"status": "no_results", "tools": []}
    
    tools = []
    for chunk in result["chunks"]:
        # Reconstruct the tool payload from memory metadata
        examples = []
        try:
            if chunk.get("tags") and isinstance(chunk["tags"], dict): 
                # Depending on how qdrant payload stores it
                pass 
                
            # If stored as flat metadata
            raw_examples = chunk.get("examples") or "[]"
            if isinstance(raw_examples, str):
                examples = json.loads(raw_examples)
            else:
                examples = raw_examples
        except json.JSONDecodeError:
            pass

        tool_def = {
            "skill_name": chunk.get("skill_name", "Unknown"),
            "description": chunk.get("content", "").replace("Tool Name:", "").split("Description: ")[-1].strip(),
            "file_path": chunk.get("skill_path", ""),
            "similarity_score": chunk.get("score"),
            "multi_shot_examples": examples
        }
        tools.append(tool_def)
        
    return {"status": "success", "tools": tools, "tokens_saved": result.get("total_tokens_estimate")}

def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    subparsers = parser.add_subparsers(dest="action", required=True)
    
    subparsers.add_parser("index", help="Index all skills into Qdrant")
    
    search_p = subparsers.add_parser("search", help="Find best skills for a task")
    search_p.add_argument("--query", required=True, help="Task description")
    search_p.add_argument("--top-k", type=int, default=3, help="Max tools to return")
    
    args = parser.parse_args()
    
    if args.action == "index":
        index_skills()
        sys.exit(0)
    elif args.action == "search":
        res = search_skills(args.query, args.top_k)
        print(json.dumps(res, indent=2))
        sys.exit(0 if res["status"] == "success" else 1)

if __name__ == "__main__":
    main()
