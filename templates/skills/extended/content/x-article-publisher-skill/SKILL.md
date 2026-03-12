---
name: x-article-publisher-skill
description: "Publish articles to X/Twitter"
risk: safe
source: "https://github.com/wshuyi/x-article-publisher-skill"
date_added: "2026-02-27"
---

# X Article Publisher Skill

## Overview

Publish articles to X/Twitter

## When to Use This Skill

Use this skill when you need to work with publish articles to x/twitter.

## Instructions

This skill provides guidance and patterns for publish articles to x/twitter.

For more information, see the [source repository](https://github.com/wshuyi/x-article-publisher-skill).

---

<!-- AGI-INTEGRATION-START -->

## AGI Framework Integration

> **Adapted for [@techwavedev/agi-agent-kit](https://www.npmjs.com/package/@techwavedev/agi-agent-kit)**
> Original source: [antigravity-awesome-skills](https://github.com/sickn33/antigravity-awesome-skills)

### Memory-First Protocol

Retrieve brand voice guidelines, content templates, and prior successful content patterns. Cache editorial decisions for consistency across sessions.

```bash
# Check for prior content creation context before starting
python3 execution/memory_manager.py auto --query "content patterns and brand voice guidelines for X Article Publisher Skill"
```

### Storing Results

After completing work, store content creation decisions for future sessions:

```bash
python3 execution/memory_manager.py store \
  --content "Content: brand voice established — professional but approachable, 8th-grade reading level, active voice" \
  --type decision --project <project> \
  --tags x-article-publisher-skill content
```

### Multi-Agent Collaboration

Share content guidelines with design agents (visual alignment) and development agents (copy integration).

```bash
python3 execution/cross_agent_context.py store \
  --agent "<your-agent>" \
  --action "Content created and reviewed — matches brand guidelines, SEO-optimized, A/B test variant prepared" \
  --project <project>
```

<!-- AGI-INTEGRATION-END -->
