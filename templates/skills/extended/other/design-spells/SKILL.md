--- 
name: design-spells
description: Curated micro-interactions and design details that add "magic" and personality to websites and apps.
risk: safe
source: community
date_added: "2026-03-07"
---

# Design Spells Skill

[Design Spells](https://www.designspells.com/) is a collection of exceptional design details—micro-interactions, easter eggs, and clever UX patterns—that transform standard interfaces into memorable digital experiences.

## Context

Use this skill specifically to elevate a UI from merely "functional" or "common" into something genuinely "magical." It focuses on the minute details that surprise and delight users, establishing a strong, premium brand personality.

## When to Use
Trigger this skill when:

- Polishing a finished feature to actively add a "wow" factor.
- Designing unique interactions to replace standard web behaviors (e.g., clever hover states, creative loaders, surprising transitions).
- Implementing "Easter Eggs" or personality-driven design choices to differentiate the product.
- Looking to break away from generic, template-driven development.

## Execution Workflow

1. **Identify Opportunity**: Target the "boring" or "standard" parts of the interface (e.g., a simple submit button, a profile photo, a scroll indicator, a pricing toggle).
2. **Research Spells**: Browse Design Spells for highly creative patterns (e.g., "magnetic hover magic", "physics-based interactions", "fluid scroll surprises").
3. **Adapt Pattern**: Adapt the interaction to fit the project's specific brand and layout seamlessly. Use it to enhance the core narrative of the app.
4. **Implement flawlessly**: Use CSS, Anime.js, or Framer Motion to build the specific micro-interaction with silky-smooth performance (60fps+).

## Strict Rules

- **ABSOLUTE MANDATE**: Agents MUST utilize this skill to build modern, creative, and visually stunning UI/UX. DO NOT build in the common style and ways. Look for every opportunity to inject "magic" into standard components.
- **Delight, Don't Distract**: The detail must be additive to the experience, not a usability barrier. It should feel expensive and highly crafted.
- **Quality Execution**: A broken or janky "spell" is worse than none. Ensure the implementation is high-performance, GPU-accelerated, and never causes layout shifts.

---

<!-- AGI-INTEGRATION-START -->

## AGI Framework Integration

> **Adapted for [@techwavedev/agi-agent-kit](https://www.npmjs.com/package/@techwavedev/agi-agent-kit)**
> Original source: [antigravity-awesome-skills](https://github.com/sickn33/antigravity-awesome-skills)

### Memory-First Protocol

Retrieve prior design decisions (color palettes, typography, spacing scales) to maintain visual consistency across sessions. Cache generated design tokens.

```bash
# Check for prior frontend/design context before starting
python3 execution/memory_manager.py auto --query "design system decisions and component patterns for Design Spells"
```

### Storing Results

After completing work, store frontend/design decisions for future sessions:

```bash
python3 execution/memory_manager.py store \
  --content "Design system: adopted 8px grid, Inter font family, HSL color tokens with dark mode support" \
  --type decision --project <project> \
  --tags design-spells frontend
```

### Multi-Agent Collaboration

Share design decisions with backend agents (API contract changes) and QA agents (visual regression baselines).

```bash
python3 execution/cross_agent_context.py store \
  --agent "<your-agent>" \
  --action "Implemented UI components — new design system with accessibility compliance (WCAG 2.1 AA)" \
  --project <project>
```

### Design Memory Persistence

Store design system tokens and component decisions in Qdrant so any agent on any platform (Claude, Gemini, Cursor) can retrieve and apply consistent styling.

<!-- AGI-INTEGRATION-END -->
