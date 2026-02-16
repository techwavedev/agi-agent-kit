---
name: clarity-gate
description: "Pre-ingestion verification for epistemic quality in RAG systems with 9-point verification and Two-Round HITL workflow"
source: "https://github.com/frmoretto/clarity-gate"
risk: safe
---

# Clarity Gate

## Overview

Pre-ingestion verification for epistemic quality in RAG systems with 9-point verification and Two-Round HITL workflow

## When to Use This Skill

Use this skill when you need to work with pre-ingestion verification for epistemic quality in rag systems with 9-point verification and two-round hitl workflow.

## Instructions

This skill provides guidance and patterns for pre-ingestion verification for epistemic quality in rag systems with 9-point verification and two-round hitl workflow.

For more information, see the [source repository](https://github.com/frmoretto/clarity-gate).


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
  --tags clarity-gate <relevant-tags>
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