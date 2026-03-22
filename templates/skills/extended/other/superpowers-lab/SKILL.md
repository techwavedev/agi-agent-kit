---
name: superpowers-lab
description: "Lab environment for Claude superpowers"
risk: safe
source: "https://github.com/obra/superpowers-lab"
date_added: "2026-02-27"
---

# Superpowers Lab

## Overview

Lab environment for Claude superpowers

## When to Use This Skill

Use this skill when you need to work with lab environment for claude superpowers.

## Instructions

This skill provides guidance and patterns for lab environment for claude superpowers.

For more information, see the [source repository](https://github.com/obra/superpowers-lab).

---

<!-- AGI-INTEGRATION-START -->

## AGI Framework Integration

> **Adapted for [@techwavedev/agi-agent-kit](https://www.npmjs.com/package/@techwavedev/agi-agent-kit)**
> Original source: [superpowers](https://github.com/obra/superpowers)

### Memory-First Protocol

Retrieve prior decisions and patterns to avoid re-discovering solutions. Cache results for instant retrieval in future sessions.

```bash
# Check for prior development context before starting
python3 execution/memory_manager.py auto --query "prior work and patterns related to Superpowers Lab"
```

### Storing Results

After completing work, store development decisions for future sessions:

```bash
python3 execution/memory_manager.py store \
  --content "Completed task with key insights documented for future reference" \
  --type decision --project <project> \
  --tags superpowers-lab default
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
