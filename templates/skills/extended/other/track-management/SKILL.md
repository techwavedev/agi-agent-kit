---
name: track-management
description: Use this skill when creating, managing, or working with Conductor tracks - the logical work units for features, bugs, and refactors. Applies to spec.md, plan.md, and track lifecycle operations.
risk: unknown
source: community
date_added: '2026-02-27'
---

# Track Management

Guide for creating, managing, and completing Conductor tracks - the logical work units that organize features, bugs, and refactors through specification, planning, and implementation phases.

## Use this skill when

- Creating new feature, bug, or refactor tracks
- Writing or reviewing spec.md files
- Creating or updating plan.md files
- Managing track lifecycle from creation to completion
- Understanding track status markers and conventions
- Working with the tracks.md registry
- Interpreting or updating track metadata

## Do not use this skill when

- The task is unrelated to track management
- You need a different domain or tool outside this scope

## Instructions

- Clarify goals, constraints, and required inputs.
- Apply relevant best practices and validate outcomes.
- Provide actionable steps and verification.
- If detailed examples are required, open `resources/implementation-playbook.md`.

## Resources

- `resources/implementation-playbook.md` for detailed patterns and examples.

---

<!-- AGI-INTEGRATION-START -->

## AGI Framework Integration

> **Adapted for [@techwavedev/agi-agent-kit](https://www.npmjs.com/package/@techwavedev/agi-agent-kit)**
> Original source: [antigravity-awesome-skills](https://github.com/sickn33/antigravity-awesome-skills)

### Memory-First Protocol

Retrieve platform-specific patterns (iOS/Android), build configurations, and device compatibility notes from prior sessions.

```bash
# Check for prior mobile development context before starting
python3 execution/memory_manager.py auto --query "mobile architecture and platform-specific patterns for Track Management"
```

### Storing Results

After completing work, store mobile development decisions for future sessions:

```bash
python3 execution/memory_manager.py store \
  --content "Mobile: React Native with Expo, offline-first with SQLite sync, push notifications via FCM" \
  --type decision --project <project> \
  --tags track-management mobile
```

### Multi-Agent Collaboration

Share API contract changes with backend agents and coordinate release timing with QA agents.

```bash
python3 execution/cross_agent_context.py store \
  --agent "<your-agent>" \
  --action "Mobile feature implemented — cross-platform component with native performance optimizations" \
  --project <project>
```

<!-- AGI-INTEGRATION-END -->
