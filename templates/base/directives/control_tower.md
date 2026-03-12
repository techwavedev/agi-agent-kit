# Control Tower Orchestrator

## Goal

Central dispatcher that tracks all active agents, sub-agents, teams, and LLMs across machines. Enables task distribution, redistribution, and global visibility into who is doing what.

## Commands

| Command | Purpose |
|---------|---------|
| `register` | Agent registers itself as available (auto-called from session_boot) |
| `heartbeat` | Agent reports alive + progress update |
| `status` | Show all active agents and their current tasks |
| `assign` | Assign a task to a specific agent/team/LLM |
| `reassign` | Move a task from one agent to another |
| `dashboard` | Full overview: agents, tasks, teams, queues |

## Data Model

Stored in Qdrant `agent_memory` collection with `type: "control_tower"`:

```json
{
  "type": "control_tower",
  "subtype": "registration|assignment|heartbeat",
  "agent_id": "claude",
  "agent_identity": "<crypto fingerprint>",
  "llm_provider": "anthropic|google|openai|local",
  "status": "active|idle|busy|offline",
  "current_task": "description",
  "machine": "hostname",
  "last_heartbeat": "ISO timestamp",
  "project": "project-name"
}
```

## Integration

- `session_boot.py` auto-calls `register` on boot
- Agents call `heartbeat` after key actions
- Primary agent calls `dashboard` for global view
- `assign`/`reassign` creates handoff entries picked up via `cross_agent_context.py pending`

## Usage

```bash
# Register this agent
python3 execution/control_tower.py register --agent claude --llm anthropic --project agi-agent-kit

# Heartbeat with progress
python3 execution/control_tower.py heartbeat --agent claude --task "Implementing Phase 1" --project agi-agent-kit

# View all agents
python3 execution/control_tower.py dashboard --project agi-agent-kit

# Assign task
python3 execution/control_tower.py assign --agent antigravity --task "Review blockchain code" --project agi-agent-kit

# Reassign task
python3 execution/control_tower.py reassign --from claude --to antigravity --task "Template sync" --project agi-agent-kit
```
