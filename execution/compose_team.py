#!/usr/bin/env python3
"""
Script: compose_team.py
Purpose: Auto-composes an ad-hoc agent team when a user request doesn't match
         any pre-defined team with high confidence. Uses the capability catalog
         from list_capabilities.py to match keywords to sub-agents and skills.
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from list_capabilities import get_sub_agents, get_skills

# Simple heuristics mapping task intents to required sub-agents
INTENT_MAP = {
    "research": ["researcher", "analyst", "investigator"],
    "fix": ["code-fixer", "debugger", "developer"],
    "test": ["test-generator", "qa-engineer", "diagnostician"],
    "review": ["quality-reviewer", "code-reviewer", "doc-reviewer"],
    "doc": ["doc-writer", "changelog-updater"],
    "deploy": ["release-manager", "devops"]
}

def analyze_request(request: str) -> list[str]:
    """Extract intents from the request string."""
    req_lower = request.lower()
    intents = []
    
    if any(k in req_lower for k in ["research", "investigate", "find out", "analyze"]):
        intents.append("research")
    if any(k in req_lower for k in ["fix", "solve", "bug", "implement", "build"]):
        intents.append("fix")
    if any(k in req_lower for k in ["test", "ci", "failing"]):
        intents.append("test")
    if any(k in req_lower for k in ["review", "check", "verify"]):
        intents.append("review")
    if any(k in req_lower for k in ["doc", "readme", "changelog", "write"]):
        intents.append("doc")
    if any(k in req_lower for k in ["deploy", "release", "ship"]):
        intents.append("deploy")
        
    return intents

def match_sub_agents(intents: list[str], available_agents: list) -> list[dict]:
    """Map required intents to available sub-agents."""
    selected = []
    selected_ids = set()
    
    agent_id_map = {a["id"]: a for a in available_agents}
    
    # Process sequentially (research -> fix -> review -> doc -> test -> deploy)
    order = ["research", "fix", "review", "doc", "test", "deploy"]
    
    for layer in order:
        if layer in intents:
            candidates = INTENT_MAP[layer]
            # Try to find a matching agent in the catalog
            matched = False
            for cand in candidates:
                # Check exact or partial match against available agent IDs
                for aid, a_obj in agent_id_map.items():
                    if cand in aid and aid not in selected_ids:
                        selected.append({"id": aid, "role": layer, "skills": []})
                        selected_ids.add(aid)
                        matched = True
                        break
                if matched:
                    break
    return selected

def compose_team(request: str) -> dict:
    sub_agents = get_sub_agents()
    skills = get_skills()
    
    intents = analyze_request(request)
    if not intents:
        # Default fallback
        intents = ["fix", "review"]
        
    team_members = match_sub_agents(intents, sub_agents)
    
    req_hash = hashlib.md5(request.encode()).hexdigest()[:8]
    
    # Attach memory skill to the first agent if requested
    if "past" in request.lower() or "memory" in request.lower():
        if team_members:
            for s in skills:
                if "memory" in s["id"] or "qdrant" in s["id"]:
                    team_members[0]["skills"].append(s["id"])
                    break
                    
    manifest = {
        "synthesized": True,
        "team_id": f"ad-hoc-{req_hash}",
        "rationale": f"Request mapped to intents: {', '.join(intents)}",
        "sub_agents": team_members,
        "execution_mode": "sequential"
    }
    
    return manifest

def main():
    parser = argparse.ArgumentParser(description="Auto-compose an agent team")
    parser.add_argument("--request", required=True, help="User request string")
    args = parser.parse_args()
    
    manifest = compose_team(args.request)
    print(json.dumps(manifest, indent=2))

if __name__ == "__main__":
    main()
