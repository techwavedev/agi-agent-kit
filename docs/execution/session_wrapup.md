# session_wrapup.py

Session Close Protocol script. Counterpart to `session_boot.py`.

## Purpose

Reviews session activity, verifies memory stores were made, optionally broadcasts accomplishments to other agents, and flags stale `.tmp/` files. This is the **last** script an agent runs before ending a session.

## Usage

```bash
python3 execution/session_wrapup.py
python3 execution/session_wrapup.py --json
python3 execution/session_wrapup.py --agent gemini --project myapp --since 90
python3 execution/session_wrapup.py --auto-broadcast
```

## Arguments

| Flag | Default | Description |
|------|---------|-------------|
| `--agent` | `claude` | Agent name |
| `--project` | None | Project name for Qdrant filter |
| `--since` | `60` | Look back N minutes for session activity |
| `--json` | off | JSON-only output |
| `--auto-broadcast` | off | Broadcast accomplishments to all agents via `cross_agent_context.py` |

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Session wrapped up successfully (memories were stored) |
| 1 | Warnings: zero stores detected this session |
| 2 | Memory system (Qdrant) unreachable |

## What It Does

1. **Queries Qdrant** for memories stored in the last N minutes (default 60)
2. **Verifies** at least one memory was stored (warns if zero)
3. **Broadcasts** session accomplishments via `cross_agent_context.py store` (if `--auto-broadcast`)
4. **Scans `.tmp/`** for files older than 24 hours and reports them as stale
5. **Deregisters** from Control Tower heartbeat (best-effort)

## Dependencies

- Qdrant running at `QDRANT_URL` (default `http://localhost:6333`)
- `execution/cross_agent_context.py` (for broadcast)
- `execution/control_tower.py` (optional, for heartbeat deregister)

## JSON Output Shape

```json
{
  "session_wrapup": true,
  "agent": "claude",
  "memories_stored_count": 3,
  "memory_types": {"decision": 2, "code": 1},
  "accomplishments": ["..."],
  "stale_tmp_files": [],
  "broadcast_status": "stored",
  "warnings": []
}
```
