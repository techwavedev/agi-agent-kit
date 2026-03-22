---
name: claude-speed-reader
description: "-Speed read Claude's responses at 600+ WPM using RSVP with Spritz-style ORP highlighting"
risk: safe
source: "https://github.com/SeanZoR/claude-speed-reader"
date_added: "2026-02-27"
---

# Claude Speed Reader

## Overview

-Speed read Claude's responses at 600+ WPM using RSVP with Spritz-style ORP highlighting

## When to Use This Skill

Use this skill when you need to work with -speed read claude's responses at 600+ wpm using rsvp with spritz-style orp highlighting.

## Instructions

This skill provides guidance and patterns for -speed read claude's responses at 600+ wpm using rsvp with spritz-style orp highlighting.

For more information, see the [source repository](https://github.com/SeanZoR/claude-speed-reader).

---

<!-- AGI-INTEGRATION-START -->

## AGI Framework Integration

> **Adapted for [@techwavedev/agi-agent-kit](https://www.npmjs.com/package/@techwavedev/agi-agent-kit)**
> Original source: [antigravity-awesome-skills](https://github.com/sickn33/antigravity-awesome-skills)

### Memory-First Protocol

Cache workflow configurations and automation patterns. Retrieve prior pipeline designs to avoid re-building similar flows from scratch.

```bash
# Check for prior workflow/automation context before starting
python3 execution/memory_manager.py auto --query "automation patterns and workflow configurations for Claude Speed Reader"
```

### Storing Results

After completing work, store workflow/automation decisions for future sessions:

```bash
python3 execution/memory_manager.py store \
  --content "Workflow: automated data pipeline with retry logic, dead-letter queue, and Slack alerts on failure" \
  --type technical --project <project> \
  --tags claude-speed-reader workflow
```

### Multi-Agent Collaboration

Share workflow state with other agents so they can trigger, monitor, or extend the automation.

```bash
python3 execution/cross_agent_context.py store \
  --agent "<your-agent>" \
  --action "Workflow automation deployed — pipeline processing 1000+ events/day with 99.9% success rate" \
  --project <project>
```

### Playbook Engine

Combine this skill with others using the Playbook Engine (`execution/workflow_engine.py`) for guided multi-step automation with progress tracking.

<!-- AGI-INTEGRATION-END -->
