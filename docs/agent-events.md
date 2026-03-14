# Real-Time Agent Events

> **Optional add-on** — works with team/pro modes. Agents fall back to polling Qdrant when Pulsar is not running.

## Quick Start

```bash
# Start Pulsar (one-time)
docker compose -f docker-compose.pulsar.yml up -d

# Verify
python3 execution/agent_events.py health
```

## What It Does

When an agent stores a memory via `memory_manager.py store`, an event is **automatically published** to a project-specific Pulsar topic. Other agents subscribed to that project receive the event in real-time.

```
Agent A (Machine 1)              Agent B (Machine 2)
  │ store decision                  │
  │ → Qdrant (always)               │
  │ → Pulsar event ──────────────→  │ receives event
  │                                 │ → knows to re-query Qdrant
```

Without Pulsar, agents poll Qdrant on each `auto` query. With Pulsar, agents get **push notifications** when new context is available.

## Architecture

Topics follow project scoping:

```
persistent://agi/memory/<project-name>
```

Event types:
- `memory_stored` — new memory added
- `decision_made` — architecture/tech decision
- `code_written` — code change stored
- `error_resolved` — bug fix documented
- `task_completed` — task finished
- `access_granted` / `identity_registered` — auth events
- `context_request` / `context_response` — peer-to-peer context sharing

## CLI Reference

```bash
# Health check
python3 execution/agent_events.py health

# Publish manually
python3 execution/agent_events.py publish \
  --project myapp --event-type decision_made \
  --content "Chose PostgreSQL for relational model"

# Subscribe (listen for 30s)
python3 execution/agent_events.py subscribe \
  --project myapp --timeout 30

# List active topics
python3 execution/agent_events.py list-topics
```

## Auto-Publish (via memory_manager.py)

Events are auto-published when **all conditions** are met:
1. `MEMORY_MODE` is `team` or `pro`
2. `--project` flag is provided on `store`
3. Pulsar is reachable

```bash
# This auto-publishes a "decision_made" event to project topic
MEMORY_MODE=team python3 execution/memory_manager.py store \
  --content "Use event sourcing for audit" \
  --type decision --project myapp
```

Event type mapping from memory type:
| Memory Type | Event Type |
|---|---|
| `decision` | `decision_made` |
| `code` | `code_written` |
| `error` | `error_resolved` |
| `technical`, `conversation` | `memory_stored` |

## Graceful Degradation

| Scenario | Behavior |
|---|---|
| Pulsar not running | Events silently dropped, Qdrant still works |
| `pulsar-client` not installed | HTTP fallback (admin API only) |
| Solo mode | Events disabled (no need for push) |
| Network partition | Events dropped, agents poll Qdrant |

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `PULSAR_URL` | `pulsar://localhost:6650` | Binary protocol endpoint |
| `PULSAR_HTTP_URL` | `http://localhost:8080` | Admin API endpoint |
| `PULSAR_TENANT` | `agi` | Pulsar tenant name |
| `PULSAR_NAMESPACE` | `memory` | Pulsar namespace |

## Dependencies

- **Required**: Apache Pulsar broker (Docker)
- **Recommended**: `pip install pulsar-client` (native binary protocol, faster)
- **Fallback**: HTTP admin API only (no pub/sub)
