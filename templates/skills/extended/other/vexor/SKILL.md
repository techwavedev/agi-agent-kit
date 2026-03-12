---
name: vexor
description: "Vector-powered CLI for semantic file search with a Claude/Codex skill"
risk: safe
source: "https://github.com/scarletkc/vexor"
date_added: "2026-02-27"
---

# Vexor

## Overview

Vector-powered CLI for semantic file search with a Claude/Codex skill

## When to Use This Skill

Use this skill when you need to work with vector-powered cli for semantic file search with a claude/codex skill.

## Instructions

This skill provides guidance and patterns for vector-powered cli for semantic file search with a claude/codex skill.

For more information, see the [source repository](https://github.com/scarletkc/vexor).

---

<!-- AGI-INTEGRATION-START -->

## AGI Framework Integration

> **Adapted for [@techwavedev/agi-agent-kit](https://www.npmjs.com/package/@techwavedev/agi-agent-kit)**
> Original source: [antigravity-awesome-skills](https://github.com/sickn33/antigravity-awesome-skills)

### Memory-First Protocol

Retrieve prior decisions and patterns to avoid re-discovering solutions. Cache results for instant retrieval in future sessions.

```bash
# Check for prior development context before starting
python3 execution/memory_manager.py auto --query "prior work and patterns related to Vexor"
```

### Storing Results

After completing work, store development decisions for future sessions:

```bash
python3 execution/memory_manager.py store \
  --content "Completed task with key insights documented for future reference" \
  --type decision --project <project> \
  --tags vexor default
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
