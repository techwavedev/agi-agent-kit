---
name: workflow-patterns
description: Use this skill when implementing tasks according to Conductor's TDD workflow, handling phase checkpoints, managing git commits for tasks, or understanding the verification protocol.
risk: unknown
source: community
date_added: '2026-02-27'
---

# Workflow Patterns

Guide for implementing tasks using Conductor's TDD workflow, managing phase checkpoints, handling git commits, and executing the verification protocol that ensures quality throughout implementation.

## Use this skill when

- Implementing tasks from a track's plan.md
- Following TDD red-green-refactor cycle
- Completing phase checkpoints
- Managing git commits and notes
- Understanding quality assurance gates
- Handling verification protocols
- Recording progress in plan files

## Do not use this skill when

- The task is unrelated to workflow patterns
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

Retrieve prior Architecture Decision Records (ADRs), trade-off analyses, and system design rationale. Critical for maintaining consistency across long-running projects.

```bash
# Check for prior architecture/design context before starting
python3 execution/memory_manager.py auto --query "architecture decisions and trade-off analysis for Workflow Patterns"
```

### Storing Results

After completing work, store architecture/design decisions for future sessions:

```bash
python3 execution/memory_manager.py store \
  --content "Architecture: event-driven microservices with CQRS, Pulsar for messaging, Qdrant for semantic search" \
  --type decision --project <project> \
  --tags workflow-patterns architecture
```

### Multi-Agent Collaboration

Broadcast architecture decisions to ALL agents so implementation stays aligned with the chosen patterns.

```bash
python3 execution/cross_agent_context.py store \
  --agent "<your-agent>" \
  --action "Completed architecture review — ADR documented, trade-offs analyzed, team aligned" \
  --project <project>
```

### Control Tower Coordination

Register architecture tasks in the Control Tower so all agents across machines know the current system design and constraints.

<!-- AGI-INTEGRATION-END -->
