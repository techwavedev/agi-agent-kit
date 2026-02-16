---
name: hubspot-integration
description: "Expert patterns for HubSpot CRM integration including OAuth authentication, CRM objects, associations, batch operations, webhooks, and custom objects. Covers Node.js and Python SDKs. Use when: hubspot, hubspot api, hubspot crm, hubspot integration, contacts api."
source: vibeship-spawner-skills (Apache 2.0)
---

# HubSpot Integration

## Patterns

### OAuth 2.0 Authentication

Secure authentication for public apps

### Private App Token

Authentication for single-account integrations

### CRM Object CRUD Operations

Create, read, update, delete CRM records

## Anti-Patterns

### ❌ Using Deprecated API Keys

### ❌ Individual Requests Instead of Batch

### ❌ Polling Instead of Webhooks

## ⚠️ Sharp Edges

| Issue | Severity | Solution |
|-------|----------|----------|
| Issue | high | See docs |
| Issue | high | See docs |
| Issue | critical | See docs |
| Issue | high | See docs |
| Issue | critical | See docs |
| Issue | medium | See docs |
| Issue | high | See docs |
| Issue | medium | See docs |


---

## 🧠 AGI Framework Integration

> **Adapted for [@techwavedev/agi-agent-kit](https://www.npmjs.com/package/@techwavedev/agi-agent-kit)**
> Original source: [antigravity-awesome-skills](https://github.com/sickn33/antigravity-awesome-skills)

### Hybrid Memory Integration (Qdrant + BM25)

Before executing complex tasks with this skill:
```bash
python3 execution/memory_manager.py auto --query "<task summary>"
```

**Decision Tree:**
- **Cache hit?** Use cached response directly — no need to re-process.
- **Memory match?** Inject `context_chunks` into your reasoning.
- **No match?** Proceed normally, then store results:

```bash
python3 execution/memory_manager.py store \
  --content "Description of what was decided/solved" \
  --type decision \
  --tags hubspot-integration <relevant-tags>
```

> **Note:** Storing automatically updates both Vector (Qdrant) and Keyword (BM25) indices.

### Agent Team Collaboration

- **Strategy**: This skill communicates via the shared memory system.
- **Orchestration**: Invoked by `orchestrator` via intelligent routing.
- **Context Sharing**: Always read previous agent outputs from memory before starting.

### Local LLM Support

When available, use local Ollama models for embedding and lightweight inference:
- Embeddings: `nomic-embed-text` via Qdrant memory system
- Lightweight analysis: Local models reduce API costs for repetitive patterns