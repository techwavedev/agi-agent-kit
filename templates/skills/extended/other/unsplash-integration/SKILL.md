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

## AGI Framework Integration

> **Adapted for [@techwavedev/agi-agent-kit](https://www.npmjs.com/package/@techwavedev/agi-agent-kit)**
> Original source: [antigravity-awesome-skills](https://github.com/sickn33/antigravity-awesome-skills)

### Memory-First Protocol

Retrieve prior decisions and patterns to avoid re-discovering solutions. Cache results for instant retrieval in future sessions.

```bash
# Check for prior development context before starting
python3 execution/memory_manager.py auto --query "prior work and patterns related to Unsplash Integration"
```

### Storing Results

After completing work, store development decisions for future sessions:

```bash
python3 execution/memory_manager.py store \
  --content "Completed task with key insights documented for future reference" \
  --type decision --project <project> \
  --tags unsplash-integration default
```

### Multi-Agent Collaboration

Share outcomes with other agents so the team stays aligned and avoids duplicate work.

```bash
python3 execution/cross_agent_context.py store \
  --agent "<your-agent>" \
  --action "Task completed — results documented and shared with team" \
  --project <project>
```

<!-- AGI-INTEGRATION-END -->
