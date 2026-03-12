--- 
name: iconsax-library
description: Extensive icon library and AI-driven icon generation skill for premium UI/UX design.
risk: safe
source: community
date_added: "2026-03-07"
---

# Iconsax Library Skill

[Iconsax](https://iconsax.io/) is an intuitive and comprehensive icon library designed for modern digital products, offering styles far superior to generic default sets.

## Context

Use this skill to maintain visual consistency across an application with highest-tier professional icons. The library is optimized for both designers and developers to create a distinctly premium feel.

## When to Use

Trigger this skill when:

- Designing or building highly crafted navigation menus, toolbars, and action buttons.
- You need an icon that is part of a cohesive, modern design system, moving away from stale, ubiquitous icons.
- Generating a custom, perfectly styled icon using **Iconsax AI** when a unique concept is required.

## Execution Workflow

1. **Identify Need**: Determine the concept the icon needs to represent.
2. **Choose Premium Style**: Select the style that matches the creative direction:
   - `Linear`: For ultra-minimalism and clarity.
   - `Bold`/`Bulk`: For solid weight and emphasis in premium dark modes.
   - `Two-tone`: For highly branded, colorful, and distinct aesthetics.
3. **Search or Generate**: Find the existing icon, or if it doesn't exist, use [Iconsax AI](https://app.iconsax.io/ai) to generate a custom variation that perfectly matches the chosen style.
4. **Integration**: Implementation using SVGs or web components, ensuring precise alignment and sizing.

## Strict Rules

- **ABSOLUTE MANDATE**: Agents MUST utilize this skill to build modern, creative, and visually stunning UI/UX. DO NOT use common, generic, or default browser/framework icons. Every icon must feel intentional and premium.
- **Strict Consistency**: Stick to ONE style (e.g., only "Two-tone") throughout a single project to maintain high-end polish.
- **Sizing & Alignment**: Follow strict, standard grid sizes (24x24) to ensure absolute crispness on high-DPI displays.

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
  --tags iconsax-library <relevant-tags>
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
