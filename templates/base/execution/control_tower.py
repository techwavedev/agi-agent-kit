#!/usr/bin/env python3
"""
Script: control_tower.py
Purpose: Central orchestrator that tracks all active agents, sub-agents, teams,
         and LLMs. Enables task distribution, redistribution, and global visibility.

Usage:
    python3 execution/control_tower.py register --agent claude --llm anthropic --project agi
    python3 execution/control_tower.py heartbeat --agent claude --task "Working on X" --project agi
    python3 execution/control_tower.py status --project agi
    python3 execution/control_tower.py assign --agent antigravity --task "Do Y" --project agi
    python3 execution/control_tower.py reassign --from claude --to antigravity --task "Do Y" --project agi
    python3 execution/control_tower.py dashboard --project agi

Exit Codes:
    0 - Success
    1 - No results / not found
    2 - Connection error
    3 - Operation error
"""

import argparse
import json
import os
import platform
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

QDRANT_URL = os.environ.get("QDRANT_URL", "http://localhost:6333")
COLLECTION = os.environ.get("MEMORY_COLLECTION", "agent_memory")

KNOWN_AGENTS = ["claude", "antigravity", "gemini", "cursor", "copilot", "opencode", "openclaw"]

LLM_PROVIDERS = {
    "claude": "anthropic",
    "antigravity": "google",
    "gemini": "google",
    "cursor": "anthropic",
    "copilot": "github",
    "opencode": "openai",
    "openclaw": "local",
}


def _qdrant_upsert(point_id: str, payload: dict, vector: list = None):
    """Upsert a point to Qdrant. Uses a zero vector if none provided (metadata-only)."""
    if vector is None:
        # Get vector dimension from collection info
        try:
            req = Request(f"{QDRANT_URL}/collections/{COLLECTION}", method="GET")
            with urlopen(req, timeout=5) as resp:
                col_info = json.loads(resp.read().decode())
                dim = col_info.get("result", {}).get("config", {}).get("params", {}).get("vectors", {}).get("size", 768)
        except Exception:
            dim = 768
        vector = [0.0] * dim

    upsert = {
        "points": [{
            "id": point_id,
            "vector": vector,
            "payload": payload,
        }]
    }
    req = Request(
        f"{QDRANT_URL}/collections/{COLLECTION}/points?wait=true",
        data=json.dumps(upsert).encode(),
        headers={"Content-Type": "application/json"},
        method="PUT",
    )
    with urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())


def _qdrant_scroll(filters: dict, limit: int = 50) -> list:
    """Scroll points from Qdrant with filters."""
    payload = {
        "filter": filters,
        "limit": limit,
        "with_payload": True,
        "with_vector": False,
    }
    req = Request(
        f"{QDRANT_URL}/collections/{COLLECTION}/points/scroll",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(req, timeout=30) as resp:
        result = json.loads(resp.read().decode())
    return result.get("result", {}).get("points", [])


def _get_agent_identity() -> str:
    """Try to load crypto agent_id, fallback to None."""
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from agent_identity import load_identity
        identity = load_identity()
        return identity["agent_id"] if identity else None
    except Exception:
        return None


def _control_tower_filter(project: str = None, subtype: str = None, agent: str = None):
    """Build Qdrant filter for control_tower entries."""
    must = [{"key": "type", "match": {"value": "control_tower"}}]
    if project:
        must.append({"key": "project", "match": {"value": project}})
    if subtype:
        must.append({"key": "subtype", "match": {"value": subtype}})
    if agent:
        must.append({"key": "agent_id", "match": {"value": agent.lower()}})
    return {"must": must}


def register_agent(agent: str, llm: str = None, project: str = None) -> dict:
    """Register an agent as available."""
    agent = agent.lower()
    llm_provider = llm or LLM_PROVIDERS.get(agent, "unknown")
    crypto_id = _get_agent_identity()

    payload = {
        "type": "control_tower",
        "subtype": "registration",
        "content": f"[CONTROL TOWER] Agent {agent} registered on {platform.node()}",
        "agent_id": agent,
        "agent_identity": crypto_id,
        "llm_provider": llm_provider,
        "status": "active",
        "current_task": None,
        "machine": platform.node(),
        "last_heartbeat": datetime.now(timezone.utc).isoformat(),
        "project": project,
        "tags": ["control-tower", "registration", f"agent:{agent}"],
    }

    # Use deterministic ID so re-registration updates the same point
    point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"ct-reg-{agent}-{project or 'global'}"))
    _qdrant_upsert(point_id, payload)

    return {
        "status": "registered",
        "agent_id": agent,
        "agent_identity": crypto_id,
        "llm_provider": llm_provider,
        "machine": platform.node(),
        "project": project,
    }


def heartbeat(agent: str, task: str = None, project: str = None) -> dict:
    """Report agent is alive with optional task update."""
    agent = agent.lower()
    now = datetime.now(timezone.utc).isoformat()

    payload = {
        "type": "control_tower",
        "subtype": "heartbeat",
        "content": f"[HEARTBEAT] {agent}: {task or 'idle'} @ {now}",
        "agent_id": agent,
        "status": "busy" if task else "idle",
        "current_task": task,
        "machine": platform.node(),
        "last_heartbeat": now,
        "project": project,
        "tags": ["control-tower", "heartbeat", f"agent:{agent}"],
    }

    point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"ct-hb-{agent}-{project or 'global'}"))
    _qdrant_upsert(point_id, payload)

    return {"status": "ok", "agent_id": agent, "task": task, "timestamp": now}


def get_status(project: str = None) -> dict:
    """Show all active agents and their current tasks."""
    filters = _control_tower_filter(project=project)
    points = _qdrant_scroll(filters, limit=100)

    # Group by agent, keep latest entry per agent
    agents = {}
    for p in points:
        pl = p["payload"]
        aid = pl.get("agent_id", "unknown")
        ts = pl.get("last_heartbeat", "")
        if aid not in agents or ts > agents[aid].get("last_heartbeat", ""):
            agents[aid] = {
                "agent_id": aid,
                "status": pl.get("status", "unknown"),
                "current_task": pl.get("current_task"),
                "llm_provider": pl.get("llm_provider"),
                "machine": pl.get("machine"),
                "last_heartbeat": ts,
                "subtype": pl.get("subtype"),
            }

    return {
        "status": "ok",
        "project": project,
        "agents": list(agents.values()),
        "total_agents": len(agents),
    }


def assign_task(agent: str, task: str, project: str = None, assigner: str = "orchestrator") -> dict:
    """Assign a task to a specific agent."""
    agent = agent.lower()
    now = datetime.now(timezone.utc).isoformat()

    payload = {
        "type": "control_tower",
        "subtype": "assignment",
        "content": f"[TASK ASSIGNED] {assigner} → {agent}: {task}",
        "agent_id": agent,
        "assigned_by": assigner,
        "status": "assigned",
        "current_task": task,
        "timestamp": now,
        "project": project,
        "tags": ["control-tower", "assignment", f"agent:{agent}", f"for:{agent}"],
    }

    point_id = str(uuid.uuid4())
    _qdrant_upsert(point_id, payload)

    # Also create a cross-agent handoff so the target agent picks it up
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from cross_agent_context import handoff_task
        handoff_task(assigner, agent, task, project=project)
    except Exception:
        pass  # Handoff is best-effort

    return {
        "status": "assigned",
        "agent_id": agent,
        "task": task,
        "assigned_by": assigner,
        "project": project,
    }


def reassign_task(from_agent: str, to_agent: str, task: str, project: str = None) -> dict:
    """Reassign a task from one agent to another."""
    from_agent = from_agent.lower()
    to_agent = to_agent.lower()

    # Assign to new agent
    result = assign_task(to_agent, task, project=project, assigner=from_agent)
    result["reassigned_from"] = from_agent
    result["status"] = "reassigned"

    return result


def dashboard(project: str = None) -> dict:
    """Full overview: agents, tasks, assignments, recent activity."""
    status = get_status(project)

    # Get recent assignments
    assignment_filter = _control_tower_filter(project=project, subtype="assignment")
    assignments = _qdrant_scroll(assignment_filter, limit=20)

    recent_tasks = []
    for p in assignments:
        pl = p["payload"]
        recent_tasks.append({
            "task": pl.get("current_task"),
            "agent_id": pl.get("agent_id"),
            "assigned_by": pl.get("assigned_by"),
            "status": pl.get("status"),
            "timestamp": pl.get("timestamp"),
        })

    # Sort by timestamp descending
    recent_tasks.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

    return {
        "status": "ok",
        "project": project,
        "agents": status["agents"],
        "total_agents": status["total_agents"],
        "recent_assignments": recent_tasks[:10],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def main():
    parser = argparse.ArgumentParser(description="Control Tower — agent orchestrator")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # register
    reg_p = subparsers.add_parser("register", help="Register agent as available")
    reg_p.add_argument("--agent", required=True)
    reg_p.add_argument("--llm", help="LLM provider override")
    reg_p.add_argument("--project")

    # heartbeat
    hb_p = subparsers.add_parser("heartbeat", help="Report alive + progress")
    hb_p.add_argument("--agent", required=True)
    hb_p.add_argument("--task", help="Current task description")
    hb_p.add_argument("--project")

    # status
    st_p = subparsers.add_parser("status", help="Show all active agents")
    st_p.add_argument("--project")

    # assign
    as_p = subparsers.add_parser("assign", help="Assign task to agent")
    as_p.add_argument("--agent", required=True)
    as_p.add_argument("--task", required=True)
    as_p.add_argument("--project")
    as_p.add_argument("--assigner", default="orchestrator")

    # reassign
    ra_p = subparsers.add_parser("reassign", help="Reassign task between agents")
    ra_p.add_argument("--from", required=True, dest="from_agent")
    ra_p.add_argument("--to", required=True, dest="to_agent")
    ra_p.add_argument("--task", required=True)
    ra_p.add_argument("--project")

    # dashboard
    db_p = subparsers.add_parser("dashboard", help="Full overview")
    db_p.add_argument("--project")

    args = parser.parse_args()

    try:
        if args.command == "register":
            result = register_agent(args.agent, llm=args.llm, project=args.project)
        elif args.command == "heartbeat":
            result = heartbeat(args.agent, task=args.task, project=args.project)
        elif args.command == "status":
            result = get_status(project=args.project)
        elif args.command == "assign":
            result = assign_task(args.agent, args.task, project=args.project, assigner=args.assigner)
        elif args.command == "reassign":
            result = reassign_task(args.from_agent, args.to_agent, args.task, project=args.project)
        elif args.command == "dashboard":
            result = dashboard(project=args.project)
        else:
            print(json.dumps({"status": "error", "message": f"Unknown command: {args.command}"}))
            sys.exit(1)

        print(json.dumps(result, indent=2))
        sys.exit(0)

    except (URLError, HTTPError) as e:
        print(json.dumps({"status": "error", "type": "connection_error", "message": str(e)}), file=sys.stderr)
        sys.exit(2)
    except Exception as e:
        print(json.dumps({"status": "error", "type": type(e).__name__, "message": str(e)}), file=sys.stderr)
        sys.exit(3)


if __name__ == "__main__":
    main()
