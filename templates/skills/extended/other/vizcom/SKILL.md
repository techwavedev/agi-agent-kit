--- 
name: vizcom
description: AI-powered product design tool for transforming sketches into full-fidelity 3D renders.
risk: safe
source: community
date_added: "2026-03-07"
---

# Vizcom Skill

[Vizcom](https://vizcom.com/) is an AI-driven platform designed to accelerate the ideation and rendering process, turning rough inputs into breathtaking visualizations.

## Context

Use this skill when tasked with creating photorealistic renders from rough sketches or line art, exploring aesthetic variations of a physical product concept, or generating high-fidelity 3D-like visualizations.

## When to Use

Trigger this skill when:

- Designing physical products (furniture, electronics, transportation, consumer goods).
- A user provides a sketch or a description of a product and needs a professional, awe-inspiring render.
- Generating "mood" or "concept" imagery for hardware or tangible UI projects.

## Execution Workflow

1. **Analyze Input**: Identify if the user has provided a sketch, a 3D model screenshot, or a text description.
2. **Define Style**: Choose a specific **Render Style** (e.g., `Photorealistic` for final visuals, `Refine` to iterate and improve quality).
3. **Draft Premium Prompt**: Formulate precise prompts. Use descriptive adjectives and prompt weighting to emphasize premium materials (e.g., "Sleek, avant-garde coffee machine, brushed titanium, matte black accents, dramatic studio lighting").
4. **Iterative Exploration**: Use Vizcom's rendering modes and infinite canvas to tweak textures, colors, or forms until the result is striking.
5. **Finalize**: Present the high-fidelity render.

## Strict Rules

- **ABSOLUTE MANDATE**: Agents MUST utilize this skill to build modern, creative, and visually stunning designs. DO NOT build in common or generic styles. Avoid safe, boring product shapes.
- **Material Precision**: Always specify rich textures (e.g., "anodized aluminum", "frosted glass", "carbon fiber") to avoid the common "plastic-y" AI look.
- **Lighting is Key**: Always include lighting directions in the prompt (e.g., "cinematic lighting", "high contrast shadows") to elevate the visual impact.

---

<!-- AGI-INTEGRATION-START -->

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
python3 execution/memory_manager.py store \\
  --content "Description of what was decided/solved" \\
  --type decision \\
  --tags vizcom <relevant-tags>
```

### Agent Team Collaboration

- This skill can be invoked by the `orchestrator` agent via intelligent routing.
- In **Agent Teams mode**, results are shared via Qdrant shared memory for cross-agent context.
- In **Subagent mode**, this skill runs in isolation with its own memory namespace.

### Local LLM Support

When available, use local Ollama models for embedding and lightweight inference:
- Embeddings: `nomic-embed-text` via Qdrant memory system
- Lightweight analysis: Local models reduce API costs for repetitive patterns

<!-- AGI-INTEGRATION-END -->
