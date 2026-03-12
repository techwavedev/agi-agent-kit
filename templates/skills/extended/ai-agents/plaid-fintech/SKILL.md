---
name: plaid-fintech
description: "Expert patterns for Plaid API integration including Link token flows, transactions sync, identity verification, Auth for ACH, balance checks, webhook handling, and fintech compliance best practices..."
risk: unknown
source: "vibeship-spawner-skills (Apache 2.0)"
date_added: "2026-02-27"
---

# Plaid Fintech

## Patterns

### Link Token Creation and Exchange

Create a link_token for Plaid Link, exchange public_token for access_token.
Link tokens are short-lived, one-time use. Access tokens don't expire but
may need updating when users change passwords.


### Transactions Sync

Use /transactions/sync for incremental transaction updates. More efficient
than /transactions/get. Handle webhooks for real-time updates instead of
polling.


### Item Error Handling and Update Mode

Handle ITEM_LOGIN_REQUIRED errors by putting users through Link update mode.
Listen for PENDING_DISCONNECT webhook to proactively prompt users.


## Anti-Patterns

### ❌ Storing Access Tokens in Plain Text

### ❌ Polling Instead of Webhooks

### ❌ Ignoring Item Errors

## ⚠️ Sharp Edges

| Issue | Severity | Solution |
|-------|----------|----------|
| Issue | critical | See docs |
| Issue | high | See docs |
| Issue | high | See docs |
| Issue | high | See docs |
| Issue | medium | See docs |
| Issue | medium | See docs |
| Issue | medium | See docs |
| Issue | medium | See docs |

## When to Use
This skill is applicable to execute the workflow or actions described in the overview.

---

<!-- AGI-INTEGRATION-START -->

## AGI Framework Integration

> **Adapted for [@techwavedev/agi-agent-kit](https://www.npmjs.com/package/@techwavedev/agi-agent-kit)**
> Original source: [antigravity-awesome-skills](https://github.com/sickn33/antigravity-awesome-skills)

### Memory-First Protocol

Retrieve prior agent configurations, team compositions, and orchestration patterns. Critical for multi-agent system consistency.

```bash
# Check for prior AI agent orchestration context before starting
python3 execution/memory_manager.py auto --query "agent patterns and orchestration strategies for Plaid Fintech"
```

### Storing Results

After completing work, store AI agent orchestration decisions for future sessions:

```bash
python3 execution/memory_manager.py store \
  --content "Agent pattern: hierarchical orchestration with Control Tower dispatcher, 3 specialist sub-agents" \
  --type decision --project <project> \
  --tags plaid-fintech ai-agents
```

### Multi-Agent Collaboration

This skill is inherently multi-agent. Use cross-agent context to coordinate task distribution and avoid duplicate work.

```bash
python3 execution/cross_agent_context.py store \
  --agent "<your-agent>" \
  --action "Agent architecture designed — Control Tower + specialist agents with shared Qdrant memory" \
  --project <project>
```

### Control Tower Integration

Register agents and tasks with the Control Tower (`execution/control_tower.py`) for centralized orchestration across machines and LLM providers.

### Blockchain Identity

Each agent has a cryptographic Ed25519 identity. All memory writes are signed — enabling trust verification in multi-agent systems.

<!-- AGI-INTEGRATION-END -->
