---
name: makepad-skills
description: "Makepad UI development skills for Rust apps: setup, patterns, shaders, packaging, and troubleshooting."
risk: safe
source: "https://github.com/ZhangHanDong/makepad-skills"
date_added: "2026-02-27"
---

# Makepad Skills

## Overview

Makepad UI development skills for Rust apps: setup, patterns, shaders, packaging, and troubleshooting.

## When to Use This Skill

Use this skill when you need to work with makepad ui development skills for rust apps: setup, patterns, shaders, packaging, and troubleshooting..

## Instructions

This skill provides guidance and patterns for makepad ui development skills for rust apps: setup, patterns, shaders, packaging, and troubleshooting..

For more information, see the [source repository](https://github.com/ZhangHanDong/makepad-skills).

---

<!-- AGI-INTEGRATION-START -->

## AGI Framework Integration

> **Adapted for [@techwavedev/agi-agent-kit](https://www.npmjs.com/package/@techwavedev/agi-agent-kit)**
> Original source: [antigravity-awesome-skills](https://github.com/sickn33/antigravity-awesome-skills)

### Memory-First Protocol

Retrieve prior design decisions (color palettes, typography, spacing scales) to maintain visual consistency across sessions. Cache generated design tokens.

```bash
# Check for prior frontend/design context before starting
python3 execution/memory_manager.py auto --query "design system decisions and component patterns for Makepad Skills"
```

### Storing Results

After completing work, store frontend/design decisions for future sessions:

```bash
python3 execution/memory_manager.py store \
  --content "Design system: adopted 8px grid, Inter font family, HSL color tokens with dark mode support" \
  --type decision --project <project> \
  --tags makepad-skills frontend
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
