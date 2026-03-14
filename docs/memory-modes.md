# Memory System Modes

Set `MEMORY_MODE` in `.env`:

```bash
export MEMORY_MODE=solo   # or team, or pro
```

## Why Three Modes?

Different teams have different needs. A solo developer prototyping on a laptop shouldn't need Docker containers for authentication. A team of 10 agents across 3 machines needs shared context and identity. An enterprise deployment needs signed writes and access control. The three modes let you start simple and add capability as needed — no data migration, no breaking changes.

## Feature Comparison

| Feature | Solo | Team | Pro |
|---|:---:|:---:|:---:|
| **Infrastructure** | Ollama + Qdrant | Same | + Aries Docker |
| **Optional Add-ons** | — | Pulsar (events) | Pulsar (events) |
| Vector + hybrid search | ✅ | ✅ | ✅ |
| Semantic cache | ✅ | ✅ | ✅ |
| BM25 keyword search | ✅ | ✅ | ✅ |
| Developer identity tagging | — | ✅ | ✅ |
| Agent identity tagging | — | ✅ | ✅ |
| Shared team memory (`--shared`) | — | ✅ | ✅ |
| Developer isolation (private by default) | — | ✅ | ✅ |
| Real-time events (Pulsar) | — | ✅ | ✅ |
| W3C DID identity (Aries) | — | — | ✅ |
| Signed writes (HMAC-SHA256) | — | — | ✅ |
| Hash anchoring (tamper detection) | — | — | ✅ |
| Project access control | — | — | ✅ |
| Audit trail | — | — | ✅ |

> **Tested:** All features in this table have passing tests. Solo/Team: 15/15 multi-tenancy tests. Pro: 36/36 blockchain auth tests. Events: 19/19 agent events tests.

## When to Use Each Mode

### 🟢 Solo — Single Developer, One Machine

**Choose this when:** You're the only user, there's one agent, and you don't need access control.

**What you get:** Full vector + hybrid search, semantic caching, BM25 keyword matching. No identity overhead — every memory is yours.

**What you skip:** No developer/agent tagging, no shared memory, no signing, no events.

```bash
MEMORY_MODE=solo
python3 execution/session_boot.py --auto-fix
# Output: ✅ Memory system ready — N memories, N cached responses
#         Mode: Solo (single user)
```

### 🔵 Team — Multiple Agents/Developers Sharing Context (Default)

**Choose this when:** Multiple agents or developers share a Qdrant instance. Each agent writes private memories by default but can share specific ones with `--shared`.

**What you get:** Everything in Solo, plus identity-based isolation (your private memories are invisible to others) and team-visible shared context.

**Why not just use Solo?** Without identity tagging, Agent A's debugging notes about PostgreSQL would pollute Agent B's retrieval results for a completely different project. Team mode ensures each agent gets relevant context.

```bash
MEMORY_MODE=team
# Identity auto-detected from git config (email + hostname)
python3 execution/memory_manager.py store \
  --content "Use Redis for session cache" --type decision \
  --project myapp --shared
# Other agents on the same Qdrant see this shared memory
```

**Optional add-on:** Start Pulsar for real-time event push between agents (see [agent-events.md](agent-events.md)).

### 🟣 Pro — Blockchain Auth + Access Control

**Choose this when:** You need tamper detection, signed writes, project-level access control, or an audit trail. Typical for enterprise or high-trust environments.

**What you get:** Everything in Team, plus HMAC-SHA256 signing, hash anchoring in the `agent_auth` Qdrant collection, project access grants, and audit logging. Optionally: W3C DID identity via Hyperledger Aries.

**Why not just use Team?** Team mode has no mechanism to prevent a rogue agent from reading any project's memories or to detect if stored content has been modified. Pro mode adds cryptographic verification.

```bash
MEMORY_MODE=pro
docker compose -f docker-compose.aries.yml up -d  # Optional: DID identity
python3 execution/blockchain_auth.py init
python3 execution/blockchain_auth.py register --entity-type developer --entity-id you@co.com
python3 execution/blockchain_auth.py grant --entity-id you@co.com --project myapp --permissions read,write
python3 execution/memory_manager.py store --content "Decision" --type decision --project myapp --auth
```

See [blockchain-auth.md](blockchain-auth.md) for full setup and trust model.

## Setup Comparison

| Mode | Required Infrastructure | Optional Infrastructure | Setup Time |
|---|---|---|---|
| Solo | Ollama, Qdrant | — | 2 min |
| Team | Ollama, Qdrant | Pulsar | 2 min |
| Pro | Ollama, Qdrant | Pulsar, Aries | 5 min |

## Upgrading Between Modes

All modes are backward-compatible. Existing memories are preserved. No data migration needed.

| Upgrade Path | Action | Risk |
|---|---|---|
| Solo → Team | Change `MEMORY_MODE=team` | None — memories get identity tags on next store |
| Team → Pro | Change `MEMORY_MODE=pro` + start Aries | None — existing Qdrant data preserved |
| Pro → Team | Change `MEMORY_MODE=team` | Signing/access control disabled but data stays |
| Team → Solo | Change `MEMORY_MODE=solo` | Identity filtering disabled — all memories visible |

## Data Storage Summary

| Component | Storage | Shared Across Machines? |
|---|---|---|
| Memories (content, embeddings) | Qdrant `agent_memory` (768d) | ✅ Via shared Qdrant |
| Response cache | Qdrant `semantic_cache` (768d) | ✅ Via shared Qdrant |
| Auth data (identities, access, audit) | Qdrant `agent_auth` (4d) | ✅ Via shared Qdrant |
| BM25 keyword index | Local SQLite (auto-synced from Qdrant on boot) | ✅ Data sourced from shared Qdrant |
| Pulsar events | Pulsar broker (ephemeral) | ✅ Via shared Pulsar |
