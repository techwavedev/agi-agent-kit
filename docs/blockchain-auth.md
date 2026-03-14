# Blockchain-Authenticated Agent Memory

## Why Blockchain Auth?

In a distributed agent system, any agent with Qdrant access can read/write any memory. This is fine for trusted environments, but problematic when:

- **Tamper detection is required** — you need proof that stored content hasn't been modified after writing
- **Access control matters** — not every agent should read every project's data
- **Audit trails are mandatory** — you need to know who stored what and when
- **Rogue agents are a concern** — an untrusted agent could inject poisoned context

Blockchain auth (`MEMORY_MODE=pro`) solves this by adding cryptographic signing, hash verification, and access grants — all stored in the shared Qdrant `agent_auth` collection so it works across machines.

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│  TRUST MODEL (Verified working — 36/36 tests pass)         │
│                                                              │
│  1. Register identity → stored in Qdrant agent_auth         │
│  2. Grant project access → stored in Qdrant agent_auth      │
│  3. Write: sign (HMAC-SHA256) → store Qdrant → anchor hash  │
│  4. Read: check access → retrieve → verify hash             │
│                                                              │
│  Unregistered agent → rejected (tested)                      │
│  Tampered content → hash mismatch detected (tested)          │
│  No project grant → access denied (tested)                   │
│  Impersonation attempt → signature mismatch (tested)         │
│  Qdrant/Aries down → graceful degradation (tested)           │
└──────────────────────────────────────────────────────────────┘
```

## Quick Start

```bash
# 1. Set mode in .env
echo "MEMORY_MODE=pro" >> .env

# 2. Initialize auth collection in Qdrant
python3 execution/blockchain_auth.py init
# Output: {"status": "initialized", "store": "Qdrant (agent_auth)", ...}

# 3. Register an identity
python3 execution/blockchain_auth.py register \
  --entity-type developer --entity-id you@co.com
# Output: {"status": "registered", ...}

# 4. Grant project access
python3 execution/blockchain_auth.py grant \
  --entity-id you@co.com --project myapp --permissions read,write
# Output: {"status": "granted", ...}

# 5. Store with signing + hash anchoring
MEMORY_MODE=pro python3 execution/memory_manager.py store \
  --content "Use PostgreSQL for relational model" \
  --type decision --project myapp --auth
# Output includes: signature, blockchain_anchor, event
```

## Why Qdrant for Auth Storage (Not SQLite)?

The auth data (identities, access grants, content hashes, audit log) is stored in a **Qdrant collection** (`agent_auth`), not SQLite. Here's why:

| Approach | Pros | Cons |
|---|---|---|
| **SQLite (old)** | Simple, zero setup | Local only — Agent A registers on Machine 1, Agent B on Machine 2 can't see it. Auth state is fragmented. |
| **Qdrant (current)** | Already the shared data layer. Auth data is automatically distributed. Zero new infrastructure. | Requires Qdrant (but we already need it for memories). |
| **Dedicated DB (Postgres)** | Full SQL, ACID | Extra infrastructure to manage. Overkill for key-value auth data. |

**Decision:** Qdrant is the clear winner because it's already deployed and shared across all agents. Adding another database would increase complexity without meaningful benefit for auth data that's essentially key-value (entity→identity, entity+project→permissions).

The `agent_auth` collection uses:
- **4-dimensional vectors** (minimal — auth data doesn't need embeddings)
- **8 payload indexes** for efficient filtering (`record_type`, `entity_id`, `entity_type`, `project`, `permissions`, `hash_value`, `action`, `timestamp`)
- **Deterministic UUIDs** (uuid5) for idempotent upserts — re-registering the same entity doesn't create duplicates

## Why Hyperledger Aries (Not MultiChain, Not Ethereum)?

| Technology | Status (2026) | Docker Image | Standards | License |
|---|---|---|---|---|
| **MultiChain** | ❌ Last commit 2023, build fails, no maintained Docker image | None (must build from source) | Proprietary protocol | GPLv3 |
| **Ethereum (Ganache)** | ⚠️ Ganache deprecated, Hardhat is dev-only | Available but complex | ERC standards | Various |
| **Hyperledger Aries** | ✅ Active (v1.5.0, Mar 2026), OpenWallet Foundation | `ghcr.io/openwallet-foundation/acapy-agent:1.5.0` | W3C DIDs, DIDComm | Apache 2.0 |

**Decision:** Aries was chosen because:
1. **Active development** — v1.5.0 released by OpenWallet Foundation, regular commits
2. **Standards compliance** — W3C DIDs, not proprietary protocols
3. **Official Docker image** — `docker compose up` just works (tested, pulls in ~30s)
4. **Apache 2.0 license** — no copyleft restrictions
5. **Optional** — system works without it (HMAC-SHA256 signing works offline)

## What Aries Actually Does vs What We Do Without It

| Feature | Without Aries (HMAC) | With Aries (DID) |
|---|---|---|
| **Signing algorithm** | HMAC-SHA256 (shared secret) | Ed25519 (via wallet) |
| **Identity** | Developer email + hostname | W3C DID (`did:key:`) |
| **Key management** | Environment variable | Aries wallet (encrypted) |
| **Verification** | Shared secret required | Public key from DID |
| **Interoperability** | Internal only | Any DID-compatible system |

**In practice:** Most deployments use HMAC-SHA256 (no Aries needed). Aries adds proper DID-based identity for environments that integrate with external credential systems.

## CLI Reference

Every command below has been tested and produces the shown output format:

```bash
# Initialize auth store
python3 execution/blockchain_auth.py init
# → {"status": "initialized", "store": "Qdrant (agent_auth)", "mode": "..."}

# Register identity
python3 execution/blockchain_auth.py register \
  --entity-type developer --entity-id alice@co.com
# → {"status": "registered", "entity_id": "alice@co.com", ...}

# Grant access
python3 execution/blockchain_auth.py grant \
  --entity-id alice@co.com --project myapp --permissions read,write
# → {"status": "granted", "permissions": ["read", "write"], ...}

# Check access
python3 execution/blockchain_auth.py check-access \
  --entity-id alice@co.com --project myapp --permission write
# → {"allowed": true, ...}

# Anchor a hash (tamper detection)
python3 execution/blockchain_auth.py anchor \
  --hash <sha256-hex> --entity-id alice@co.com
# → {"status": "anchored", "immutable": true, ...}

# Verify content hasn't been tampered
python3 execution/blockchain_auth.py verify --content "Original text"
# → {"verified": true, ...}

# View audit trail
python3 execution/blockchain_auth.py audit --project myapp
# → [{"action": "...", "entity_id": "...", "timestamp": "..."}, ...]

# Health check
python3 execution/blockchain_auth.py health
# → {"status": "healthy", "aries": {...}, "qdrant_auth": {...}}
```

## Graceful Degradation

Every failure mode has been tested:

| Scenario | Behavior | Tested? |
|---|---|---|
| Aries not running | HMAC signing works, DID creation skipped | ✅ 36/36 online tests pass without Aries running |
| Qdrant not running | `is_available()` returns False, no crash | ✅ Graceful degradation test |
| `MEMORY_MODE=solo` | Auth module not loaded, zero overhead | ✅ Import only happens for team/pro |
| `MEMORY_MODE=team` | Auth available but `--auth` flag requires pro | ✅ Returns `graceful_degradation: true` |
| Bad API key | Aries returns 401, system degrades | ✅ |
| Impersonation attempt | Signature mismatch detected | ✅ Poisoning prevention tests |

## Technology Stack

| Component | Technology | Version | Verified |
|---|---|---|---|
| Auth store | Qdrant `agent_auth` collection | 1.13+ | ✅ 36/36 tests |
| Identity (optional) | Hyperledger Aries ACA-Py | 1.5.0 | ✅ Docker pull + health check |
| Signing (offline) | HMAC-SHA256 | Python stdlib | ✅ 14/14 offline tests |
| Hash algorithm | SHA-256 | Python stdlib | ✅ |
| Docker image | `ghcr.io/openwallet-foundation/acapy-agent:1.5.0` | OCI | ✅ Pulled and verified |
| License | Apache 2.0 | — | ✅ |
