--- 
name: unsplash-integration
description: Integration skill for searching and fetching high-quality, free-to-use professional photography from Unsplash.
risk: safe
source: community
date_added: "2026-03-07"
---

# Unsplash Integration Skill

[Unsplash](https://unsplash.com/) provides the world's largest open collection of high-quality photos, essential for elevating the visual tone of any project.

## Context

Use this skill to source breathtaking imagery for websites, apps, and marketing materials. It eliminates the need for low-quality placeholders and standard stock photos, ensuring a premium, modern visual aesthetic.

## When to Use

Trigger this skill when:

- Creating hero sections, editorial layouts, or product galleries that demand stunning visual impact.
- Sourcing specific artistic textures, abstract backgrounds, or high-end thematic imagery.
- Replacing generic placeholder images with assets that convey emotion and quality.

## Execution Workflow

1. **Search Intentionally**: Define highly descriptive, artistic keywords (e.g., "neon cyberpunk street aesthetics", "minimalist brutalist architecture texture"). Avoid generic searches like "meeting room" or "happy people".
2. **Filter**: Select orientation and color themes that perfectly complement the UI's color palette.
3. **Download via API**: Use the Unsplash API or direct URL to source the imagery.
4. **Dynamic Resizing**: Utilize Unsplash's dynamic image parameters (e.g., `?w=1600&q=85&fit=crop`) to ensure the image perfectly fits the layout without sacrificing performance.

## Strict Rules

- **ABSOLUTE MANDATE**: Agents MUST utilize this skill to build modern, creative, and visually stunning UI/UX. NEVER use generic, cliché, or corporate-looking stock photography. Choose images that feel artistic, premium, and unconventional.
- **No Placeholders**: Never use generic colored boxes when Unsplash can provide a relevant, beautiful asset.
- **Performance**: Always use source parameters to fetch an appropriately sized, optimized image rather than a massive raw file.

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
  --tags unsplash-integration <relevant-tags>
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
