# Blockchain Agent Trust & Multi-Tenant Memory

## Goal

Provide agent identity, trust verification, and tenant-scoped memory isolation using a local, free blockchain — without degrading read performance.

## Architecture

### Three-Tier Memory Model

```
┌─────────────────────────────────────────────┐
│  GLOBAL (shared)                            │
│  Common patterns, best practices, token     │
│  savings cache — all agents read/write      │
├─────────────────────────────────────────────┤
│  TENANT (team/project-scoped)               │
│  Project decisions, architecture, secrets   │
│  context — only team members access         │
├─────────────────────────────────────────────┤
│  PRIVATE (single agent)                     │
│  Agent-specific cache, session state        │
│  — only the owning agent                    │
└─────────────────────────────────────────────┘
```

### How It Works

1. **Agent Identity**: Each agent gets a blockchain keypair on first boot. The public key becomes its verifiable identity.
2. **Write Signing**: Every Qdrant write is signed with the agent's private key. The signature + content hash are anchored on-chain.
3. **Read Verification** (optional, async): Consumers can verify authorship and integrity of any memory chunk by checking the chain. This is **never blocking** — reads hit Qdrant directly.
4. **Tenant Gating**: Qdrant collections are namespaced per tenant. The blockchain stores ACLs (which agent identities can access which tenants). Agents present signed tokens to access tenant-scoped collections.

### Tenant Scoping in Qdrant

| Tier | Qdrant Collection Pattern | Access Control |
|------|---------------------------|----------------|
| Global | `global_*` | All registered agents |
| Tenant | `tenant_{project}_{team}_*` | Agents with on-chain ACL grant |
| Private | `private_{agent_id}_*` | Owner agent only |

### Performance Contract

- **Reads**: Always direct to Qdrant. Zero blockchain overhead.
- **Writes**: Sign locally (< 1ms), anchor hash on-chain async (background). No write latency added to the agent's critical path.
- **ACL checks**: Cached locally with TTL. Chain is only consulted on cache miss or explicit refresh.

## Blockchain Selection

| Option | Pros | Cons |
|--------|------|------|
| **Hyperledger Fabric** | Enterprise-grade, permissioned, no crypto fees, rich ACL | Complex setup (orderers, peers, CAs) |
| **MultiChain** | Simple setup, built-in permissions, streams for data anchoring | Smaller ecosystem |
| **Hyperledger Besu** (private mode) | EVM-compatible, good tooling | Heavier than needed |

**Recommendation**: Start with **MultiChain** for simplicity (single-node local chain, streams for hash anchoring, built-in permissions). Migrate to Fabric if enterprise multi-org tenancy is needed later.

## Implementation Phases

### Phase 1: Agent Identity + Write Signing
- Generate keypair per agent on first `session_boot.py` run
- Store keys in `~/.agi-agent-kit/identity/`
- Sign all `memory_manager.py store` calls
- Anchor hashes to local MultiChain stream

### Phase 2: Tenant Isolation
- Namespace Qdrant collections by tenant
- Register tenant ACLs on-chain
- Update `cross_agent_context.py` to enforce tenant boundaries
- Add `--tenant` flag to memory commands

### Phase 3: Verification & Audit
- Optional read-time verification (check signature against chain)
- Audit trail: who wrote what, when, with cryptographic proof
- Tamper detection: alert if Qdrant content doesn't match on-chain hash

## Integration Points

| Existing Script | Change |
|-----------------|--------|
| `execution/session_boot.py` | Generate/load agent identity keypair |
| `execution/memory_manager.py` | Sign writes, add tenant scoping |
| `execution/cross_agent_context.py` | Enforce tenant ACLs on store/sync/handoff |

## Edge Cases

- **First agent on new machine**: Auto-generates identity, registers with local chain
- **Chain unavailable**: Writes proceed unsigned (degraded mode), queued for anchoring when chain returns
- **Tenant conflict**: Agent tries to access a tenant it's not authorized for → clear error, suggest requesting access
