#!/usr/bin/env python3
"""
Script: agent_runtime.py
Purpose: Native Python multi-agent execution runtime. Replaces external CLIs by
         routing tasks directly to strictly local Ollama micro-agents OR delegating
         complex tasks to the current active orchestrator session (Claude, Antigravity, Copilot, etc.) via in-context prompts.

Architecture:
    - simple/security tasks → local_micro_agent.py (runs in background on Ollama)
    - complex reasoning tasks → generates `.tmp/active_subagent.md` and halts,
      instructing the active session to step into the persona and solve it natively in the IDE.

Usage:
    # Spawn a single agent task
    python3 execution/agent_runtime.py spawn --agent code- reviewer --task "Review src/auth/"

    # Spawn from a dispatch manifest
    python3 execution/agent_runtime.py dispatch --manifest .tmp/team-runs/xyz/manifest.json

Exit Codes:
    0 - Completed (or delegated successfully to the active session)
    1 - Invalid arguments
    2 - Local micro-agent execution failed
    3 - Cloud delegation failed
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from datetime import datetime, timezone

# Add execution dir to sys.path
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

try:
    from task_router import classify_task
except ImportError:
    print(json.dumps({"status": "error", "message": "task_router.py not found!"}), file=sys.stderr)
    sys.exit(1)


def ensure_tmp_dir(project_root: Path):
    tmp_dir = project_root / ".tmp" / "delegations"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    return tmp_dir


def execute_local_agent(agent_id: str, task: str, context: str = "", worktree: str = ".") -> dict:
    """Invokes local_micro_agent.py to handle a task strictly locally on Ollama."""
    print(f"[{agent_id}] Routing to local_micro_agent (Ollama)...", file=sys.stderr)
    
    micro_agent_script = SCRIPT_DIR / "local_micro_agent.py"
    if not micro_agent_script.exists():
        return {"status": "error", "error": "local_micro_agent.py not found."}

    cmd = [
        sys.executable, str(micro_agent_script),
        "--task", task,
    ]
    if context:
        # Pass context via a temporary file if needed, but local_micro_agent 
        # usually takes --input-file or similar. For simplicity if it accepts --context:
        pass # Depending on local_micro_agent args, adjust this. Assuming standard task string here.
    
    start_time = datetime.now(timezone.utc)
    try:
        Path(worktree).mkdir(parents=True, exist_ok=True)
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=worktree,
            timeout=120,
        )
        duration_ms = int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000)
        
        if result.returncode == 0:
            return {
                "agent_id": agent_id,
                "status": "completed",
                "result": result.stdout.strip(),
                "duration_ms": duration_ms,
                "execution": "local"
            }
        else:
            return {
                "agent_id": agent_id,
                "status": "error",
                "error": result.stderr.strip(),
                "execution": "local"
            }
    except subprocess.TimeoutExpired:
        duration_ms = int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000)
        return {
            "agent_id": agent_id,
            "status": "error",
            "error": "Local model execution timed out after 120s. Unable to complete operation.",
            "duration_ms": duration_ms,
            "execution": "local"
        }
    except Exception as e:
        return {
            "agent_id": agent_id,
            "status": "error",
            "error": str(e),
            "execution": "local"
        }


def format_active_session_delegation(agent_id: str, task: str, payload_str: str, 
                                  directive_content: str, worktree: str, project_root: Path) -> dict:
    """
    Formats a markdown file acting as an explicit prompt for the active session agent
    to consume in the current context, effectively becoming the sub-agent.
    """
    tmp_dir = ensure_tmp_dir(project_root)
    run_id = datetime.now().strftime("%Y%md_%H%M%S")
    delegation_file = tmp_dir / f"subagent_{agent_id}_{run_id}.md"

    prompt = f"""# 🤖 Sub-Agent Context For Active Session

You (the active orchestrator session) have been assigned the role of sub-agent: `{agent_id}`.
Due to hardware limitations or API constraints, you are executing this task natively
in your current session rather than spawning an external worker.

## Working Directory Isolation
If a worktree was assigned, you MUST perform your actions relative to this path:
**Path:** `{worktree}`

## Task Payload
```json
{payload_str}
```

## Specific Task Fragment
{task}

## Your Persona / Directive
{directive_content if directive_content else "No explicit directive found. Execute the task natively using your standard tools."}

## Instructions
1. Review the task and your directive.
2. Execute the necessary actions (e.g., viewing files, running bash commands, editing code).
3. Ensure you report your findings or completions in your final chat message.
4. When finished, explicitly state: **"SUB-AGENT {agent_id} COMPLETED"** so the session flow can continue.
"""
    delegation_file.write_text(prompt, encoding="utf-8")

    return {
        "agent_id": agent_id,
        "status": "delegated_to_active_session",
        "action_required": True,
        "delegation_file": str(delegation_file.resolve()),
        "message": f"Task requires cloud-level reasoning. The active orchestrator session must read {delegation_file} and execute the task.",
        "execution": "active_session_context"
    }


def process_agent_task(agent_id: str, task: str, payload_str: str = "{}", 
                       directive_path: str = "", worktree: str = ".", project_root: Path = None):
    """Classifies a task and executes it either locally or via Antigravity delegation."""
    if not project_root:
        project_root = SCRIPT_DIR.parent

    # 1. Load directive context if available
    directive_content = ""
    if directive_path and Path(directive_path).is_file():
        directive_content = Path(directive_path).read_text(encoding="utf-8")

    # 2. Classify task routing (local vs cloud)
    cls = classify_task(task, context=directive_content)
    route = cls.get("route", "cloud")

    # 3. Handle Local Execution
    if route in ("local", "local_required"):
        # Combine task + payload context for local execution
        local_task = f"As {agent_id}:\nTask: {task}\nPayload: {payload_str}"
        return execute_local_agent(agent_id, local_task, worktree=worktree)
    
    # 4. Handle Active Session Delegation
    else:
        return format_active_session_delegation(agent_id, task, payload_str, directive_content, worktree, project_root)


def cmd_spawn():
    parser = argparse.ArgumentParser(description="Spawn a single native sub-agent")
    parser.add_argument("--agent", required=True, help="Agent Persona ID")
    parser.add_argument("--task", required=True, help="Task description")
    parser.add_argument("--payload", default="{}", help="Task payload JSON string")
    parser.add_argument("--directive", default="", help="Path to persona directive markdown file")
    parser.add_argument("--worktree", default=".", help="Working directory to bind the agent to")
    
    args = parser.parse_args(sys.argv[2:])
    project_root = SCRIPT_DIR.parent

    result = process_agent_task(
        agent_id=args.agent,
        task=args.task,
        payload_str=args.payload,
        directive_path=args.directive,
        worktree=args.worktree,
        project_root=project_root
    )

    print(json.dumps(result, indent=2))
    if result["status"] == "error":
        sys.exit(2)
    sys.exit(0)


def cmd_dispatch():
    parser = argparse.ArgumentParser(description="Dispatch a full multi-agent manifest natively")
    parser.add_argument("--manifest", required=True, help="Path to dispatch JSON manifest")
    
    args = parser.parse_args(sys.argv[2:])
    project_root = SCRIPT_DIR.parent

    manifest_path = Path(args.manifest)
    if not manifest_path.exists():
        print(json.dumps({"status": "error", "message": "Manifest not found"}), file=sys.stderr)
        sys.exit(1)

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(json.dumps({"status": "error", "message": f"Malformed manifest JSON: {str(e)}"}), file=sys.stderr)
        sys.exit(3)
        
    team = manifest.get("team", "unknown")
    sub_agents = manifest.get("sub_agents", [])
    payload = manifest.get("payload", {})
    payload_str = json.dumps(payload, indent=2)

    # Simplified execution: Loop over sub_agents.
    # Parallel execution implies background local tasks combined with ONE active session task piece, 
    # since the active session evaluates in a single conversation thread sequentially.
    
    results = []
    active_session_delegations = []

    for sa in sub_agents:
        agent_id = sa.get("id", "unknown")
        task = payload.get("task", f"Execute {agent_id} tasks for {team}")
        directive_path = project_root / sa.get("directive_path", "")
        worktree = sa.get("worktree_path", ".")

        res = process_agent_task(
            agent_id=agent_id,
            task=task,
            payload_str=payload_str,
            directive_path=str(directive_path) if directive_path.is_file() else "",
            worktree=worktree,
            project_root=project_root
        )
        results.append(res)
        
        if res.get("status") == "delegated_to_active_session":
            active_session_delegations.append(res)

    summary = {
        "team": team,
        "run_id": manifest.get("run_id", "unknown"),
        "total_agents": len(sub_agents),
        "results": results,
    }

    print(json.dumps(summary, indent=2))
    
    # If any task was delegated to the active session, exit 0 but the IDE prompt picks up the JSON
    # and processes the files.
    sys.exit(0)


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 agent_runtime.py [spawn|dispatch] ...", file=sys.stderr)
        sys.exit(1)

    command = sys.argv[1]
    if command == "spawn":
        cmd_spawn()
    elif command == "dispatch":
        cmd_dispatch()
    else:
        print(f"Unknown command: {command}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
