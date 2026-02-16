---
name: skill-seekers
description: "-Automatically convert documentation websites, GitHub repositories, and PDFs into Claude AI skills in minutes."
source: "https://github.com/yusufkaraaslan/Skill_Seekers"
risk: safe
---

# Skill Seekers

## Overview

-Automatically convert documentation websites, GitHub repositories, and PDFs into Claude AI skills in minutes.

## When to Use This Skill

Use this skill when you need to work with -automatically convert documentation websites, github repositories, and pdfs into claude ai skills in minutes..

## Instructions

This skill provides guidance and patterns for -automatically convert documentation websites, github repositories, and pdfs into claude ai skills in minutes..

For more information, see the [source repository](https://github.com/yusufkaraaslan/Skill_Seekers).


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
  --tags skill-seekers <relevant-tags>
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