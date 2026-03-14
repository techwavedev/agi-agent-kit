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

## AGI Framework Integration

> **Adapted for [@techwavedev/agi-agent-kit](https://www.npmjs.com/package/@techwavedev/agi-agent-kit)**
> Original source: [antigravity-awesome-skills](https://github.com/sickn33/antigravity-awesome-skills)

### Memory-First Protocol

Retrieve prior design decisions (color palettes, typography, spacing scales) to maintain visual consistency across sessions. Cache generated design tokens.

```bash
# Check for prior frontend/design context before starting
python3 execution/memory_manager.py auto --query "design system decisions and component patterns for Iconsax Library"
```

### Storing Results

After completing work, store frontend/design decisions for future sessions:

```bash
python3 execution/memory_manager.py store \
  --content "Design system: adopted 8px grid, Inter font family, HSL color tokens with dark mode support" \
  --type decision --project <project> \
  --tags iconsax-library frontend
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
