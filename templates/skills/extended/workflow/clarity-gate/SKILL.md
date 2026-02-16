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

### Qdrant Memory Integration

Before executing complex tasks with this skill:
```bash
python3 execution/memory_manager.py auto --query "<task summary>"
```
- **Cache hit?** Use cached response directly — no need to re-process.
- **Memory match?** Inject `context_chunks` into your reasoning.
- **No match?** Proceed normally, then store results:
```bash
python3 execution/memory_manager.py store \
  --content "Description of what was decided/solved" \
  --type decision \
  --tags clarity-gate <relevant-tags>
```

### Agent Team Collaboration

- This skill can be invoked by the `orchestrator` agent via intelligent routing.
- In **Agent Teams mode**, results are shared via Qdrant shared memory for cross-agent context.
- In **Subagent mode**, this skill runs in isolation with its own memory namespace.

### Local LLM Support

When available, use local Ollama models for embedding and lightweight inference:
- Embeddings: `nomic-embed-text` via Qdrant memory system
- Lightweight analysis: Local models reduce API costs for repetitive patterns
