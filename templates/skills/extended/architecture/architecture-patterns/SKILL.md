---
name: architecture-patterns
description: "Implement proven backend architecture patterns including Clean Architecture, Hexagonal Architecture, and Domain-Driven Design. Use when architecting complex backend systems or refactoring existing ..."
risk: unknown
source: community
date_added: "2026-02-27"
---

# Architecture Patterns

Master proven backend architecture patterns including Clean Architecture, Hexagonal Architecture, and Domain-Driven Design to build maintainable, testable, and scalable systems.

## Use this skill when

- Designing new backend systems from scratch
- Refactoring monolithic applications for better maintainability
- Establishing architecture standards for your team
- Migrating from tightly coupled to loosely coupled architectures
- Implementing domain-driven design principles
- Creating testable and mockable codebases
- Planning microservices decomposition

## Do not use this skill when

- You only need small, localized refactors
- The system is primarily frontend with no backend architecture changes
- You need implementation details without architectural design

## Instructions

1. Clarify domain boundaries, constraints, and scalability targets.
2. Select an architecture pattern that fits the domain complexity.
3. Define module boundaries, interfaces, and dependency rules.
4. Provide migration steps and validation checks.
5. For workflows that must survive failures (payments, order fulfillment, multi-step processes), use durable execution at the infrastructure layer — frameworks like DBOS persist workflow state, providing crash recovery without adding architectural complexity.

Refer to `resources/implementation-playbook.md` for detailed patterns, checklists, and templates.

## Related Skills

Works well with: `event-sourcing-architect`, `saga-orchestration`, `workflow-automation`, `dbos-*`

## Resources

- `resources/implementation-playbook.md` for detailed patterns, checklists, and templates.

---

<!-- AGI-INTEGRATION-START -->

## AGI Framework Integration

> **Adapted for [@techwavedev/agi-agent-kit](https://www.npmjs.com/package/@techwavedev/agi-agent-kit)**
> Original source: [antigravity-awesome-skills](https://github.com/sickn33/antigravity-awesome-skills)

### Memory-First Protocol

Retrieve prior Architecture Decision Records (ADRs), trade-off analyses, and system design rationale. Critical for maintaining consistency across long-running projects.

```bash
# Check for prior architecture/design context before starting
python3 execution/memory_manager.py auto --query "architecture decisions and trade-off analysis for Architecture Patterns"
```

### Storing Results

After completing work, store architecture/design decisions for future sessions:

```bash
python3 execution/memory_manager.py store \
  --content "Architecture: event-driven microservices with CQRS, Pulsar for messaging, Qdrant for semantic search" \
  --type decision --project <project> \
  --tags architecture-patterns architecture
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
