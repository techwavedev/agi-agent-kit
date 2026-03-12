---
name: competitive-landscape
description: This skill should be used when the user asks to \\\"analyze competitors", "assess competitive landscape", "identify differentiation", "evaluate market positioning", "apply Porter's Five Forces",...
risk: unknown
source: community
date_added: '2026-02-27'
---

# Competitive Landscape Analysis

Comprehensive frameworks for analyzing competition, identifying differentiation opportunities, and developing winning market positioning strategies.

## Use this skill when

- Working on competitive landscape analysis tasks or workflows
- Needing guidance, best practices, or checklists for competitive landscape analysis

## Do not use this skill when

- The task is unrelated to competitive landscape analysis
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
python3 execution/memory_manager.py auto --query "mobile architecture and platform-specific patterns for Competitive Landscape"
```

### Storing Results

After completing work, store mobile development decisions for future sessions:

```bash
python3 execution/memory_manager.py store \
  --content "Mobile: React Native with Expo, offline-first with SQLite sync, push notifications via FCM" \
  --type decision --project <project> \
  --tags competitive-landscape mobile
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
