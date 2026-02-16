---
name: Infinite Gratitude
description: Multi-agent research skill for parallel research execution (10 agents, battle-tested with real case studies).
risk: safe
source: https://github.com/sstklen/infinite-gratitude
---

# Infinite Gratitude

> **Source**: [sstklen/infinite-gratitude](https://github.com/sstklen/infinite-gratitude)

## Description

A multi-agent research skill designed for parallel research execution. It orchestrates 10 agents to conduct deep research, battle-tested with real case studies.

## When to Use

Use this skill when you need to perform extensive, parallelized research on a topic, leveraging multiple agents to gather and synthesize information more efficiently than a single linear process.

## How to Use

This is an external skill. Please refer to the [official repository](https://github.com/sstklen/infinite-gratitude) for installation and usage instructions.

```bash
git clone https://github.com/sstklen/infinite-gratitude
```


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
  --tags Infinite Gratitude <relevant-tags>
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