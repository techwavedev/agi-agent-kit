#!/usr/bin/env python3
"""
Script: route_request.py
Purpose: Route a user's free-text request to the appropriate agent team, 
         sub-agent, or skill by searching the capabilities catalog. 
         Matches requests to execution units.
"""

import argparse
import json
import sys
import subprocess
from pathlib import Path

# Add the script's directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from list_capabilities import get_teams, get_skills, get_sub_agents

def rank_capabilities(request: str, teams: list, skills: list) -> list:
    """
    Very fast heuristic keyword ranker. 
    In production with high token budgets, this might fallback to an LLM, 
    but keyword + heuristic matching is fastest and cheapest.
    """
    req_lower = request.lower()
    ranked = []
    
    # 1. Check Teams (highest priority execution unit)
    for t in teams:
        score = 0
        tid = t["id"].lower()
        if tid in req_lower or req_lower in tid:
            score += 10
        
        # Keyword matching from team ID
        keywords = tid.replace("_", " ").split()
        for kw in keywords:
            if len(kw) > 3 and kw in req_lower:
                score += 5
                
        if score > 0:
            t["score"] = score
            ranked.append(t)
            
    # 2. Check Skills
    for s in skills:
        score = 0
        sid = s["id"].lower()
        if sid in req_lower or req_lower in sid:
            score += 8
            
        keywords = sid.replace("-", " ").split()
        for kw in keywords:
            if len(kw) > 3 and kw in req_lower:
                score += 3
                
        if score > 0:
            s["score"] = score
            ranked.append(s)
            
    # Sort by score descending
    ranked.sort(key=lambda x: x.get("score", 0), reverse=True)
    return ranked[:3] # Return top 3


def main():
    parser = argparse.ArgumentParser(description="Unified free-text request router")
    parser.add_argument("--request", required=True, help="User's prompt or request string")
    parser.add_argument("--json", action="store_true", help="Format output as JSON")
    args = parser.parse_args()

    teams = get_teams()
    skills = get_skills()
    
    top_candidates = rank_capabilities(args.request, teams, skills)
    
    if args.json:
        print(json.dumps({"request": args.request, "plan": top_candidates}, indent=2))
    else:
        if not top_candidates:
            print(f"No strong matches found for '{args.request}'. Requesting general skill-fallback.")
        else:
            print(f"Routing Plan for '{args.request}':")
            for i, cand in enumerate(top_candidates):
                print(f" {i+1}. [{cand['type'].upper()}] {cand['id']} (confidence: {cand['score']})")


if __name__ == "__main__":
    main()
