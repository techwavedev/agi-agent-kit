---
name: claude-win11-speckit-update-skill
description: "Windows 11 system management"
risk: safe
source: "https://github.com/NotMyself/claude-win11-speckit-update-skill"
date_added: "2026-02-27"
---

# Claude Win11 Speckit Update Skill

## Overview

Windows 11 system management

## When to Use This Skill

Use this skill when you need to work with windows 11 system management.

## Instructions

This skill provides guidance and patterns for windows 11 system management.

For more information, see the [source repository](https://github.com/NotMyself/claude-win11-speckit-update-skill).

---

<!-- AGI-INTEGRATION-START -->

## AGI Framework Integration

> **Adapted for [@techwavedev/agi-agent-kit](https://www.npmjs.com/package/@techwavedev/agi-agent-kit)**
> Original source: [antigravity-awesome-skills](https://github.com/sickn33/antigravity-awesome-skills)

### Memory-First Protocol

Retrieve prior deployment configurations, rollback procedures, and incident post-mortems. Avoid re-discovering infrastructure patterns.

```bash
# Check for prior infrastructure context before starting
python3 execution/memory_manager.py auto --query "deployment configuration and patterns for Claude Win11 Speckit Update Skill"
```

### Storing Results

After completing work, store infrastructure decisions for future sessions:

```bash
python3 execution/memory_manager.py store \
  --content "Deployment pipeline: configured blue-green deployment with health checks on port 8080" \
  --type technical --project <project> \
  --tags claude-win11-speckit-update-skill devops
```

### Multi-Agent Collaboration

Broadcast deployment changes so frontend and backend agents update their configurations accordingly.

```bash
python3 execution/cross_agent_context.py store \
  --agent "<your-agent>" \
  --action "Deployed infrastructure changes — updated CI/CD pipeline with new health check endpoints" \
  --project <project>
```

### Playbook Integration

Use the `ship-saas-mvp` or `full-stack-deploy` playbook to sequence this skill with testing, documentation, and deployment verification.

<!-- AGI-INTEGRATION-END -->
