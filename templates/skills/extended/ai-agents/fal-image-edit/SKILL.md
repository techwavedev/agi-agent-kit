---
name: fal-image-edit
description: "AI-powered image editing with style transfer and object removal"
risk: safe
source: "https://github.com/fal-ai-community/skills/blob/main/skills/claude.ai/fal-image-edit/SKILL.md"
date_added: "2026-02-27"
---

# Fal Image Edit

## Overview

AI-powered image editing with style transfer and object removal

## When to Use This Skill

Use this skill when you need to work with ai-powered image editing with style transfer and object removal.

## Instructions

This skill provides guidance and patterns for ai-powered image editing with style transfer and object removal.

For more information, see the [source repository](https://github.com/fal-ai-community/skills/blob/main/skills/claude.ai/fal-image-edit/SKILL.md).

---

<!-- AGI-INTEGRATION-START -->

## AGI Framework Integration

> **Adapted for [@techwavedev/agi-agent-kit](https://www.npmjs.com/package/@techwavedev/agi-agent-kit)**
> Original source: [antigravity-awesome-skills](https://github.com/sickn33/antigravity-awesome-skills)

### Memory-First Protocol

Retrieve prior agent configurations, team compositions, and orchestration patterns. Critical for multi-agent system consistency.

```bash
# Check for prior AI agent orchestration context before starting
python3 execution/memory_manager.py auto --query "agent patterns and orchestration strategies for Fal Image Edit"
```

### Storing Results

After completing work, store AI agent orchestration decisions for future sessions:

```bash
python3 execution/memory_manager.py store \
  --content "Agent pattern: hierarchical orchestration with Control Tower dispatcher, 3 specialist sub-agents" \
  --type decision --project <project> \
  --tags fal-image-edit ai-agents
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
