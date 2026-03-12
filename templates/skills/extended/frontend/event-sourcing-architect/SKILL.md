---
name: event-sourcing-architect
description: "Expert in event sourcing, CQRS, and event-driven architecture patterns. Masters event store design, projection building, saga orchestration, and eventual consistency patterns. Use PROACTIVELY for e..."
risk: unknown
source: community
date_added: "2026-02-27"
---

# Event Sourcing Architect

Expert in event sourcing, CQRS, and event-driven architecture patterns. Masters event store design, projection building, saga orchestration, and eventual consistency patterns. Use PROACTIVELY for event-sourced systems, audit trail requirements, or complex domain modeling with temporal queries.

## Capabilities

- Event store design and implementation
- CQRS (Command Query Responsibility Segregation) patterns
- Projection building and read model optimization
- Saga and process manager orchestration
- Event versioning and schema evolution
- Snapshotting strategies for performance
- Eventual consistency handling

## Use this skill when

- Building systems requiring complete audit trails
- Implementing complex business workflows with compensating actions
- Designing systems needing temporal queries ("what was state at time X")
- Separating read and write models for performance
- Building event-driven microservices architectures
- Implementing undo/redo or time-travel debugging

## Do not use this skill when

- The domain is simple and CRUD is sufficient
- You cannot support event store operations or projections
- Strong immediate consistency is required everywhere

## Instructions

1. Identify aggregate boundaries and event streams
2. Design events as immutable facts
3. Implement command handlers and event application
4. Build projections for query requirements
5. Design saga/process managers for cross-aggregate workflows
6. Implement snapshotting for long-lived aggregates
7. Set up event versioning strategy

## Safety

- Never mutate or delete committed events in production.
- Rebuild projections in staging before running in production.

## Best Practices

- Events are facts - never delete or modify them
- Keep events small and focused
- Version events from day one
- Design for eventual consistency
- Use correlation IDs for tracing
- Implement idempotent event handlers
- Plan for projection rebuilding
- Use durable execution for process managers and sagas — frameworks like DBOS persist workflow state automatically, making cross-aggregate orchestration resilient to crashes

## Related Skills

Works well with: `saga-orchestration`, `architecture-patterns`, `dbos-*`

---

<!-- AGI-INTEGRATION-START -->

## AGI Framework Integration

> **Adapted for [@techwavedev/agi-agent-kit](https://www.npmjs.com/package/@techwavedev/agi-agent-kit)**
> Original source: [antigravity-awesome-skills](https://github.com/sickn33/antigravity-awesome-skills)

### Memory-First Protocol

Retrieve prior design decisions (color palettes, typography, spacing scales) to maintain visual consistency across sessions. Cache generated design tokens.

```bash
# Check for prior frontend/design context before starting
python3 execution/memory_manager.py auto --query "design system decisions and component patterns for Event Sourcing Architect"
```

### Storing Results

After completing work, store frontend/design decisions for future sessions:

```bash
python3 execution/memory_manager.py store \
  --content "Design system: adopted 8px grid, Inter font family, HSL color tokens with dark mode support" \
  --type decision --project <project> \
  --tags event-sourcing-architect frontend
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
