---
name: fal-upscale
description: "Upscale and enhance image and video resolution using AI"
source: "https://github.com/fal-ai-community/skills/blob/main/skills/claude.ai/fal-upscale/SKILL.md"
risk: safe
---

# Fal Upscale

## Overview

Upscale and enhance image and video resolution using AI

## When to Use This Skill

Use this skill when you need to work with upscale and enhance image and video resolution using ai.

## Instructions

This skill provides guidance and patterns for upscale and enhance image and video resolution using ai.

For more information, see the [source repository](https://github.com/fal-ai-community/skills/blob/main/skills/claude.ai/fal-upscale/SKILL.md).


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
  --tags fal-upscale <relevant-tags>
```

### Agent Team Collaboration

- This skill can be invoked by the `orchestrator` agent via intelligent routing.
- In **Agent Teams mode**, results are shared via Qdrant shared memory for cross-agent context.
- In **Subagent mode**, this skill runs in isolation with its own memory namespace.

### Local LLM Support

When available, use local Ollama models for embedding and lightweight inference:
- Embeddings: `nomic-embed-text` via Qdrant memory system
- Lightweight analysis: Local models reduce API costs for repetitive patterns
