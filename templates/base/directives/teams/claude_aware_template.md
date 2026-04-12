# Team Directive Template: Claude Code-Aware

> Copy this template when creating teams that leverage Claude Code-native features.

## Team Identity

| Field       | Value                |
|-------------|----------------------|
| Team ID     | `<team_id>`          |
| Role        | <one-line purpose>   |
| Trigger     | <when to dispatch>   |
| Mode        | Sequential or Parallel |
| Claude-Aware | Yes                 |

---

## Goal

<1-2 sentences describing the team's objective.>

---

## Sub-Agents (in order)

### 1. `<agent-id>`
- **Directive:** `directives/subagents/<agent_id>.md`
- **Role:** <what this agent does>
- **Isolation:** `worktree` (parallel) or `none` (sequential)
- **Output:** <expected deliverable>

### 2. `<agent-id>`
- **Directive:** `directives/subagents/<agent_id>.md`
- **Role:** <what this agent does>
- **Depends on:** Agent 1 output (sequential only)
- **Output:** <expected deliverable>

---

## Inputs

```json
{
  "key": "<description>"
}
```

---

## Claude Code Native Dispatch

Use the adapter for Claude Code-native Agent tool calls:

```bash
# Native mode (default when Claude Code detected)
python3 execution/claude_dispatch.py --team <team_id> \
  --payload '<json>'

# Or via dispatch_agent_team.py with --claude flag
python3 execution/dispatch_agent_team.py --team <team_id> \
  --payload '<json>' --claude

# Cloud scheduling
python3 execution/claude_dispatch.py --team <team_id> \
  --payload '<json>' --mode schedule
```

### Parallel Sub-Agents (Claude Code)

For parallel teams, each agent call uses `isolation: "worktree"`:

```
Orchestrator (Claude Code)
  ├─ Agent tool call: agent-1 (isolation: worktree)
  ├─ Agent tool call: agent-2 (isolation: worktree)  ← parallel
  └─ Merge results after all complete
```

### Sequential Sub-Agents (Claude Code)

For sequential teams, pass `handoff_state` between Agent tool calls:

```
Orchestrator (Claude Code)
  ├─ Agent tool call: agent-1 → captures handoff_state
  └─ Agent tool call: agent-2 → receives handoff_state in prompt
```

---

## Cross-Agent Visibility

Sub-agents store work to Qdrant so non-Claude agents (Gemma 4, Gemini) can see results:

```bash
python3 execution/cross_agent_context.py store \
  --agent "claude" \
  --action "[<team_id>/<agent-id>] <summary>" \
  --project <project> \
  --tags claude-dispatch <team_id> <agent-id>
```

Other agents retrieve with:

```bash
python3 execution/cross_agent_context.py sync \
  --agent "gemma" --project <project>
```

---

## Outputs

```json
{
  "team": "<team_id>",
  "run_id": "<uuid>",
  "status": "pass|fail",
  "sub_agents": {}
}
```

---

## Memory Integration

```bash
# Query before
python3 execution/memory_manager.py auto --query "<team_id> <context>"

# Store after
python3 execution/memory_manager.py store \
  --content "<team_id> run completed: <summary>" \
  --type decision --tags <team_id> claude-dispatch
```
