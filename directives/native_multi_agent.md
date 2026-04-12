# Native Multi-Agent Protocol

This framework strictly manages multi-agent team coordination natively *within* the Python architecture, avoiding expensive and redundant cloud API calls via external CLIs whenever possible. 

The primary interface for spawning and managing team tasks is:
`python3 execution/agent_runtime.py spawn` or `python3 execution/agent_runtime.py dispatch`

## 1. Local vs. Cloud Execution

When a sub-agent task is requested, the framework (`execution/task_router.py`) determines execution environment based on complexity:

### A. Local Micro-Agents (Hardware-Efficient)
- **Role:** Handles extremely simple, deterministic, or computationally cheap tasks (e.g., extracting fields from JSON, checking simple git states, basic linting checks, reviewing environment variables).
- **Execution:** Runs silently in the background using `local_micro_agent.py` backed by local Ollama models (e.g. `gemma4:e4b`).
- **Result:** Completes and returns the JSON payload `{"status": "completed", "result": "..." }` instantly. You read this JSON and continue.

### B. Antigravity Coordinator (In-Context Delegation)
- **Role:** Handles complex, high-reasoning tasks (refactoring, architecture design, holistic code reviews) that require state-of-the-art capability. 
- **Wait, why not spawn an external API?** To conserve cloud API keys and token quotas, the framework leverages *you* — the currently actively running cloud session. 
- **Execution:** `agent_runtime.py` identifies the heavy workload and writes a structured persona prompt to `.tmp/delegations/subagent_<id>_<run>.md`. The script then exits returning:
  `{"status": "delegated_to_antigravity", "action_required": true, "delegation_file": "..."}`
- **Your Response:** When you see a task is `delegated_to_antigravity`, you MUST immediately:
  1. Open and read the `delegation_file`.
  2. Adopt the persona specified in the file. No need to inform the user, just do the work.
  3. Execute the work in the optionally defined `worktree_path`.
  4. Yield an explicit message ending with **"SUB-AGENT <ID> COMPLETED"**.

## 2. Team Dispatch (Parallel and Sequential)

The `dispatch_agent_team.py` script automatically utilizes the new `agent_runtime.py` when passed the `--execute-native` flag.

**Workflow example:**
```bash
# 1. Dispatch team and tell it to use native runtime logic
python3 execution/dispatch_agent_team.py --team qa-team --payload '{"task": "Evaluate auth flow"}' --execute-native
```

The output will be an array of JSON results for each sub-agent. If any return `delegated_to_antigravity`, you read their corresponding delegation files and execute them one-by-one.

## 3. Worktree Isolation

A key feature for parallel team operation is `worktree_isolator.py`. When an agent task specifies a `worktree`, you (or the local-micro-agent) MUST `cd` into that explicit path before executing shell operations, file writes, or tests.
This guarantees multiple reasoning agents don't overwrite each other's code.

## Summary Checklist
- Never use external tools like Node's `openclaude` for bridging.
- When you use `dispatch_agent_team.py`, always append `--execute-native`.
- Let `task_router.py` automatically route simple prompts to the local micro-agent.
- Step up and execute `delegated_to_antigravity` assignments by acting as the sub-agent yourself.
