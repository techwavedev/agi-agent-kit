# Real-Time Agent Events (Apache Pulsar)

> **Optional add-on** — works with team/pro modes. Without Pulsar, agents poll Qdrant on each query (which always works). Pulsar adds real-time push notifications.

## Why Pulsar?

Without Pulsar, agent coordination works like this: Agent A stores a decision in Qdrant. Agent B doesn't know about it until it runs `memory_manager.py auto`, which queries Qdrant. This is fine for most workflows — Qdrant queries take <10ms.

But in real-time collaboration (e.g., Agent A is writing code while Agent B reviews architecture), the polling delay means Agent B might not see Agent A's latest decisions until its next query. Pulsar fixes this by pushing events to subscribed agents immediately.

### Why Pulsar Over Alternatives?

| Technology | Pros | Cons | Why Not |
|---|---|---|---|
| **Redis Pub/Sub** | Simple, low latency | No persistence, messages lost if subscriber offline | Lost events = lost coordination |
| **RabbitMQ** | Mature, well-supported | Not designed for multi-tenant topics | Topic-per-project pattern is awkward |
| **Kafka** | Excellent persistence | Heavy (ZooKeeper required), overkill for events | 4+ containers for a message bus |
| **Apache Pulsar** | ✅ Topic-per-project, persistent, single container, lightweight standalone mode | Newer ecosystem | — |

**Decision:** Pulsar in standalone mode runs as a single Docker container (256-512MB heap) and natively supports our topic pattern (`persistent://agi/memory/<project>`). Messages persist until consumed. No ZooKeeper, no cluster overhead.

## Architecture

```
Agent A (Machine 1)              Agent B (Machine 2)
  │                                │
  │ store --project myapp          │
  │ → Qdrant (always)             │
  │ → Pulsar event ─────────────→ │ real-time notification
  │                                │ → re-queries Qdrant
  │                                │
  └─── Topic: persistent://agi/memory/myapp ───┘
```

Events are **fire-and-forget** — if Pulsar is down, the Qdrant store still succeeds. The event is simply dropped. No data loss, no crash, no retry.

## Verified Capabilities

Every feature below is tested (19/19 tests pass):

| Feature | Status | Test Coverage |
|---|---|---|
| Health check | ✅ | `test_pulsar_health` |
| Publish events (native client) | ✅ | `test_publish_event` — verified `method: native` |
| Subscribe to events | ✅ | Tested via native pulsar-client |
| Topic listing | ✅ | `test_list_topics` — found topics after publish |
| Auto-publish on `memory_manager.py store` | ✅ | `test_memory_manager_integration` — `event status: published` |
| Graceful degradation (Pulsar down) | ✅ | `test_graceful_degradation` — returns `unavailable`, no crash |
| Event type validation | ✅ | `test_event_types` — 9 types verified |
| Topic name sanitization | ✅ | `test_topic_naming` — special chars handled |

## Quick Start

```bash
# 1. Start Pulsar
docker compose -f docker-compose.pulsar.yml up -d
# Pulls apachepulsar/pulsar:4.1.3 (~1.2GB), starts in ~30-60s

# 2. Install native client (required for publish/subscribe)
pip install pulsar-client

# 3. Verify
python3 execution/agent_events.py health
# → {"agent": "Apache Pulsar", "status": "healthy", "topics": 0, "native_client": true}
```

> **Important:** `pulsar-client` Python library is **required** for publish and subscribe. The HTTP admin API is used only for health checks, tenant/namespace management, and topic listing. Pulsar's REST produce API is not available in standalone mode (v4.x).

## Auto-Publish (via memory_manager.py)

Events are auto-published when **all conditions** are met:
1. `MEMORY_MODE` is `team` or `pro`
2. `--project` flag is provided on `store`
3. Pulsar is reachable
4. `pulsar-client` library is installed

```bash
# This auto-publishes a "decision_made" event to the project topic
MEMORY_MODE=team python3 execution/memory_manager.py store \
  --content "Use event sourcing for audit" \
  --type decision --project myapp
# Output includes: "event": {"status": "published", "topic": "...", "method": "native"}
```

If any condition isn't met, the event is silently skipped:
```json
"event": {"status": "unavailable", "reason": "Pulsar not running (events silently dropped)"}
```

### Event Type Mapping

| Memory Type | Event Type |
|---|---|
| `decision` | `decision_made` |
| `code` | `code_written` |
| `error` | `error_resolved` |
| `technical`, `conversation` | `memory_stored` |

## CLI Reference

All commands verified working:

```bash
# Health check
python3 execution/agent_events.py health
# → {"agent": "Apache Pulsar", "status": "healthy", "topics": N, ...}

# Publish manually
python3 execution/agent_events.py publish \
  --project myapp --event-type decision_made \
  --content "Chose PostgreSQL for relational model"
# → {"status": "published", "topic": "persistent://agi/memory/myapp", "method": "native"}

# Subscribe (listen for 30s)
python3 execution/agent_events.py subscribe \
  --project myapp --timeout 30
# Prints received events as JSON

# List active topics
python3 execution/agent_events.py list-topics
# → {"topics": ["persistent://agi/memory/myapp", ...], "count": N}
```

## Graceful Degradation

| Scenario | Behavior | Tested? |
|---|---|---|
| Pulsar not running | Events silently dropped, Qdrant store still succeeds | ✅ |
| `pulsar-client` not installed | `_EVENTS_AVAILABLE` stays True (module loads), but publish fails gracefully | ✅ |
| Solo mode | Events module not activated (no `_TEAM_FEATURES`) | ✅ |
| Network partition mid-publish | Event dropped, no crash | ✅ |
| `session_boot.py` | Reports `ℹ️ Pulsar: not running (optional)` | ✅ |

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `PULSAR_URL` | `pulsar://localhost:6650` | Binary protocol (native client) |
| `PULSAR_HTTP_URL` | `http://localhost:8080` | Admin API (health, topics) |
| `PULSAR_TENANT` | `agi` | Auto-created on first publish |
| `PULSAR_NAMESPACE` | `memory` | Auto-created on first publish |

## Dependencies

| Dependency | Required? | Purpose |
|---|---|---|
| Apache Pulsar broker | Yes (for events) | Message routing and persistence |
| `pulsar-client` pip package | Yes (for publish/subscribe) | Native binary protocol (v3.10.0 tested) |
| Docker | Yes (for broker) | Runs `apachepulsar/pulsar:4.1.3` |
