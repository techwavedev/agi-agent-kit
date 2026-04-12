#!/usr/bin/env python3
"""
Script: cross_agent_context.py
Purpose: Enables multiple AI agents (Claude, Gemini/Antigravity, Cursor, etc.)
         to share context and coordinate via the shared Qdrant memory system.

         Each agent stores its work with agent identification metadata,
         so other agents can retrieve what was done, decisions made,
         and current task status.

Usage:
    # Store context for other agents to pick up
    python3 execution/cross_agent_context.py store \
        --agent "antigravity" \
        --action "Completed security audit of release pipeline" \
        --project agi-agent-kit \
        --tags security release

    # Retrieve what other agents have done recently
    python3 execution/cross_agent_context.py sync \
        --agent "claude" \
        --project agi-agent-kit

    # Get full team status (all agents, recent activity)
    python3 execution/cross_agent_context.py status \
        --project agi-agent-kit

    # Hand off a task to another agent
    python3 execution/cross_agent_context.py handoff \
        --from "antigravity" \
        --to "claude" \
        --task "Review the pre-push hook security implementation" \
        --context "Hook is at .git/hooks/pre-push, runs release_gate.py" \
        --project agi-agent-kit

Exit Codes:
    0 - Success
    1 - No results
    2 - Connection error
    3 - Operation error
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone, timedelta
from urllib.request import Request, urlopen
from urllib.error import URLError

# Resolve path to qdrant-memory scripts
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
_candidates = [
    os.path.join(project_root, "skills", "qdrant-memory", "scripts"),
    os.path.join(project_root, "skills", "core", "qdrant-memory", "scripts"),
]
SKILL_SCRIPTS_DIR = next((p for p in _candidates if os.path.exists(p)), _candidates[0])
sys.path.insert(0, SKILL_SCRIPTS_DIR)

from embedding_utils import check_embedding_service
from memory_retrieval import retrieve_context, store_memory, build_filter

QDRANT_URL = os.environ.get("QDRANT_URL", "http://localhost:6333")
KNOWN_AGENTS = ["antigravity", "claude", "gemini", "cursor", "copilot", "opencode", "openclaw"]


def store_agent_context(agent: str, action: str, project: str = None, tags: list = None) -> dict:
    """Store an agent's action/decision with agent identification."""
    metadata = {
        "agent_id": agent.lower(),
        "cross_agent": True,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    if project:
        metadata["project"] = project
    if tags:
        metadata["tags"] = ["cross-agent", f"agent:{agent.lower()}"] + tags
    else:
        metadata["tags"] = ["cross-agent", f"agent:{agent.lower()}"]

    content = f"[{agent.upper()}] {action}"
    result = store_memory(content, "decision", metadata)
    return {"status": "stored", "agent": agent, "action": action, "result": result}


def sync_from_agents(requesting_agent: str, project: str = None, hours: int = 24) -> dict:
    """Retrieve recent actions from OTHER agents (not the requesting one)."""
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()

    # Query for cross-agent tagged memories
    query = f"cross-agent team coordination recent work {project or ''}"
    filters_must = [
        {"key": "tags", "match": {"value": "cross-agent"}},
        {"key": "timestamp", "range": {"gte": cutoff}},
    ]
    if project:
        filters_must.append({"key": "project", "match": {"value": project}})

    try:
        context = retrieve_context(
            query,
            filters={"must": filters_must},
            top_k=20,
            score_threshold=0.3,
        )
    except Exception as e:
        return {"status": "error", "message": str(e)}

    # Filter to show only OTHER agents' work
    chunks = context.get("chunks", [])
    other_agent_chunks = []
    for chunk in chunks:
        agent_tag = None
        for tag in chunk.get("tags", []):
            if tag.startswith("agent:"):
                agent_tag = tag.split(":")[1]
                break
        if agent_tag and agent_tag != requesting_agent.lower():
            chunk["from_agent"] = agent_tag
            other_agent_chunks.append(chunk)

    return {
        "status": "ok",
        "requesting_agent": requesting_agent,
        "other_agents_activity": other_agent_chunks,
        "total_found": len(other_agent_chunks),
    }


def get_team_status(project: str = None) -> dict:
    """Get overview of all agent activity."""
    query = f"cross-agent team coordination work decisions {project or ''}"
    filters_must = [{"key": "tags", "match": {"value": "cross-agent"}}]
    if project:
        filters_must.append({"key": "project", "match": {"value": project}})

    try:
        context = retrieve_context(
            query,
            filters={"must": filters_must},
            top_k=50,
            score_threshold=0.2,
        )
    except Exception as e:
        return {"status": "error", "message": str(e)}

    # Group by agent
    by_agent = {}
    for chunk in context.get("chunks", []):
        agent_tag = "unknown"
        for tag in chunk.get("tags", []):
            if tag.startswith("agent:"):
                agent_tag = tag.split(":")[1]
                break
        if agent_tag not in by_agent:
            by_agent[agent_tag] = []
        by_agent[agent_tag].append({
            "content": chunk.get("content", "")[:200],
            "timestamp": chunk.get("timestamp", ""),
            "score": chunk.get("score", 0),
        })

    return {
        "status": "ok",
        "project": project,
        "agents_active": list(by_agent.keys()),
        "activity_by_agent": by_agent,
        "total_entries": sum(len(v) for v in by_agent.values()),
    }


def handoff_task(from_agent: str, to_agent: str, task: str, context: str = "", project: str = None) -> dict:
    """Create a task handoff between agents."""
    handoff_content = (
        f"[HANDOFF: {from_agent.upper()} → {to_agent.upper()}] "
        f"Task: {task}"
    )
    if context:
        handoff_content += f" | Context: {context}"

    metadata = {
        "agent_id": from_agent.lower(),
        "target_agent": to_agent.lower(),
        "cross_agent": True,
        "handoff": True,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    if project:
        metadata["project"] = project
    metadata["tags"] = [
        "cross-agent",
        "handoff",
        f"agent:{from_agent.lower()}",
        f"for:{to_agent.lower()}",
    ]

    result = store_memory(handoff_content, "decision", metadata)
    return {
        "status": "handoff_created",
        "from": from_agent,
        "to": to_agent,
        "task": task,
        "result": result,
    }


def broadcast_context(from_agent: str, message: str, project: str = None, tags: list = None) -> dict:
    """Broadcast a message to ALL agents via Qdrant (shared context for the whole team)."""
    metadata = {
        "agent_id": from_agent.lower(),
        "cross_agent": True,
        "broadcast": True,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    if project:
        metadata["project"] = project
    broadcast_tags = ["cross-agent", "broadcast", f"agent:{from_agent.lower()}"]
    # Tag for every known agent so they all pick it up
    for agent in KNOWN_AGENTS:
        if agent != from_agent.lower():
            broadcast_tags.append(f"for:{agent}")
    if tags:
        broadcast_tags.extend(tags)
    metadata["tags"] = broadcast_tags

    content = f"[BROADCAST from {from_agent.upper()}] {message}"
    result = store_memory(content, "decision", metadata)
    return {
        "status": "broadcast_sent",
        "from": from_agent,
        "message": message,
        "recipients": [a for a in KNOWN_AGENTS if a != from_agent.lower()],
        "result": result,
    }


def get_pending_tasks(agent: str, project: str = None) -> dict:
    """Get tasks handed off TO this agent (pending work from other agents)."""
    query = f"handoff task for {agent}"
    filters_must = [
        {"key": "tags", "match": {"value": "handoff"}},
        {"key": "tags", "match": {"value": f"for:{agent.lower()}"}},
    ]
    if project:
        filters_must.append({"key": "project", "match": {"value": project}})

    try:
        context = retrieve_context(
            query,
            filters={"must": filters_must},
            top_k=20,
            score_threshold=0.2,
        )
    except Exception as e:
        return {"status": "error", "message": str(e)}

    # Also check broadcasts
    broadcast_query = f"broadcast team update for {agent}"
    broadcast_filters = [
        {"key": "tags", "match": {"value": "broadcast"}},
    ]
    if project:
        broadcast_filters.append({"key": "project", "match": {"value": project}})

    try:
        broadcasts = retrieve_context(
            broadcast_query,
            filters={"must": broadcast_filters},
            top_k=10,
            score_threshold=0.2,
        )
    except Exception:
        broadcasts = {"chunks": []}

    handoffs = context.get("chunks", [])
    broadcast_chunks = broadcasts.get("chunks", [])

    return {
        "status": "ok",
        "agent": agent,
        "pending_handoffs": len(handoffs),
        "handoffs": [
            {
                "content": h.get("content", "")[:300],
                "timestamp": h.get("timestamp", ""),
                "from_agent": next(
                    (t.split(":")[1] for t in h.get("tags", []) if t.startswith("agent:")),
                    "unknown"
                ),
            }
            for h in handoffs
        ],
        "broadcasts": len(broadcast_chunks),
        "broadcast_messages": [
            {
                "content": b.get("content", "")[:300],
                "timestamp": b.get("timestamp", ""),
            }
            for b in broadcast_chunks
        ],
    }


def main():
    parser = argparse.ArgumentParser(
        description="Cross-agent context sharing via Qdrant",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Store command
    store_p = subparsers.add_parser("store", help="Store context for other agents")
    store_p.add_argument("--agent", required=True, help="Your agent name (antigravity, claude, etc.)")
    store_p.add_argument("--action", required=True, help="What you did/decided")
    store_p.add_argument("--project", help="Project name")
    store_p.add_argument("--tags", nargs="+", help="Additional tags")

    # Sync command
    sync_p = subparsers.add_parser("sync", help="Get other agents' recent activity")
    sync_p.add_argument("--agent", required=True, help="Your agent name (to exclude your own entries)")
    sync_p.add_argument("--project", help="Filter by project")
    sync_p.add_argument("--hours", type=int, default=24, help="Look back N hours (default: 24)")

    # Status command
    status_p = subparsers.add_parser("status", help="Team status overview")
    status_p.add_argument("--project", help="Filter by project")

    # Handoff command
    handoff_p = subparsers.add_parser("handoff", help="Hand off a task to another agent")
    handoff_p.add_argument("--from", dest="from_agent", required=True, help="Source agent")
    handoff_p.add_argument("--to", required=True, help="Target agent")
    handoff_p.add_argument("--task", required=True, help="Task description")
    handoff_p.add_argument("--context", default="", help="Additional context")
    handoff_p.add_argument("--project", help="Project name")

    # Broadcast command
    broadcast_p = subparsers.add_parser("broadcast", help="Broadcast context to all agents")
    broadcast_p.add_argument("--agent", required=True, help="Your agent name")
    broadcast_p.add_argument("--message", required=True, help="Message to broadcast")
    broadcast_p.add_argument("--project", help="Project name")
    broadcast_p.add_argument("--tags", nargs="+", help="Additional tags")

    # Pending command
    pending_p = subparsers.add_parser("pending", help="Check tasks handed off to you")
    pending_p.add_argument("--agent", required=True, help="Your agent name")
    pending_p.add_argument("--project", help="Filter by project")

    args = parser.parse_args()

    try:
        if args.command == "store":
            result = store_agent_context(args.agent, args.action, args.project, args.tags)
            print(json.dumps(result, indent=2))
            sys.exit(0)

        elif args.command == "sync":
            result = sync_from_agents(args.agent, args.project, args.hours)
            print(json.dumps(result, indent=2))
            sys.exit(0 if result.get("total_found", 0) > 0 else 1)

        elif args.command == "status":
            result = get_team_status(args.project)
            print(json.dumps(result, indent=2))
            sys.exit(0)

        elif args.command == "handoff":
            result = handoff_task(
                args.from_agent, args.to, args.task, args.context, args.project
            )
            print(json.dumps(result, indent=2))
            sys.exit(0)

        elif args.command == "broadcast":
            result = broadcast_context(args.agent, args.message, args.project, args.tags)
            print(json.dumps(result, indent=2))
            sys.exit(0)

        elif args.command == "pending":
            result = get_pending_tasks(args.agent, args.project)
            print(json.dumps(result, indent=2))
            sys.exit(0 if result.get("pending_handoffs", 0) > 0 or result.get("broadcasts", 0) > 0 else 1)

    except URLError as e:
        print(json.dumps({
            "status": "error",
            "type": "connection_error",
            "message": str(e),
            "hint": "Is Qdrant running? Try: docker run -p 6333:6333 qdrant/qdrant",
        }), file=sys.stderr)
        sys.exit(2)
    except Exception as e:
        print(json.dumps({
            "status": "error",
            "type": type(e).__name__,
            "message": str(e),
        }), file=sys.stderr)
        sys.exit(3)


if __name__ == "__main__":
    main()
