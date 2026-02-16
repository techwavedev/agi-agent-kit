---
name: beautiful-prose
description: "Hard-edged writing style contract for timeless, forceful English prose without AI tics"
source: "https://github.com/SHADOWPR0/beautiful_prose"
risk: safe
---

# Beautiful Prose

## Overview

Hard-edged writing style contract for timeless, forceful English prose without AI tics

## When to Use This Skill

Use this skill when you need to work with hard-edged writing style contract for timeless, forceful english prose without ai tics.

## Instructions

This skill provides guidance and patterns for hard-edged writing style contract for timeless, forceful english prose without ai tics.

For more information, see the [source repository](https://github.com/SHADOWPR0/beautiful_prose).


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
  --tags beautiful-prose <relevant-tags>
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