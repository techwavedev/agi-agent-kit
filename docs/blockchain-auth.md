# Blockchain-Authenticated Agent Memory

## Overview

Agents, developers, and teams are authenticated via an on-chain identity registry.
Every memory write is signed, content hashes are anchored immutably, and project
access is token-gated. **Qdrant remains the data layer; the blockchain adds trust.**

## Trust Model

```
┌─────────────────────────────────────────────────────────────┐
│  HOW AGENTS TRUST EACH OTHER                                │
│                                                             │
│  1. Register identity on blockchain (one-time)              │
│     → Creates immutable on-chain record                     │
│                                                             │
│  2. Admin grants project access (per-project)               │
│     → Permissions: read, write, admin                       │
│                                                             │
│  3. Every write: sign content → store Qdrant → anchor hash  │
│     → Content hash is immutable on-chain                    │
│                                                             │
│  4. Every read: check access → retrieve → verify hash       │
│     → Tampered content detected via hash mismatch           │
│                                                             │
│  RESULT: Unregistered agents rejected. Poisoned content     │
│  detected. Project context protected per-team.              │
└─────────────────────────────────────────────────────────────┘
```

## Quick Start

```bash
# 1. Start MultiChain (first time builds the image)
cd templates/base
docker compose -f docker-compose.multichain.yml up -d

# 2. Initialize blockchain streams
python3 execution/blockchain_auth.py init

# 3. Register your identity
python3 execution/blockchain_auth.py register \
  --entity-type developer --entity-id "your@email.com"

# 4. Grant project access
python3 execution/blockchain_auth.py grant \
  --entity-id "your@email.com" --project myapp --permissions read,write

# 5. Store with blockchain auth
python3 execution/memory_manager.py store \
  --content "My decision" --type decision --project myapp --auth

# 6. Check audit trail
python3 execution/blockchain_auth.py audit --project myapp
```

## Graceful Degradation

If MultiChain is not running, the system **continues to work** using Qdrant only.
The `--auth` flag will report `blockchain_anchor: unavailable` but the memory
is still stored. No crash, no data loss.

## Data Streams

| Stream | Purpose | Key Format |
|---|---|---|
| `identities` | Agent/dev/team registration | `entity_id` |
| `access-control` | Project-scoped permissions | `entity_id:project` |
| `content-hashes` | Anchored SHA-256 hashes | `content_hash` |
| `audit-log` | Timestamped operation log | `project` |

## Poisoning Prevention

**Scenario:** A malicious agent tries to inject false context.

1. **Unregistered agent** → Not in `identities` stream → Rejected
2. **No project access** → `check_access()` returns denied → Blocked
3. **Forged signature** → HMAC doesn't match → Detected
4. **Tampered content** → Hash mismatch vs on-chain anchor → Detected

## CLI Reference

| Command | Description |
|---|---|
| `blockchain_auth.py health` | Check MultiChain connectivity |
| `blockchain_auth.py init` | Create data streams |
| `blockchain_auth.py register` | Register entity on-chain |
| `blockchain_auth.py sign --content "..."` | Sign content |
| `blockchain_auth.py verify --content "..."` | Verify against on-chain hash |
| `blockchain_auth.py anchor` | Anchor hash on-chain |
| `blockchain_auth.py grant` | Grant project permissions |
| `blockchain_auth.py check-access` | Check entity permission |
| `blockchain_auth.py audit --project X` | Full audit trail |

## Environment Variables

| Variable | Default | Purpose |
|---|---|---|
| `MULTICHAIN_RPC_URL` | `http://localhost:4730` | MultiChain RPC endpoint |
| `MULTICHAIN_RPC_USER` | `agiadmin` | RPC username |
| `MULTICHAIN_RPC_PASS` | `agipass123` | RPC password |
| `MULTICHAIN_CHAIN_NAME` | `agi-memory-chain` | Blockchain name |
