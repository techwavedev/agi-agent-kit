---
name: ddd-tactical-patterns
description: "Apply DDD tactical patterns in code using entities, value objects, aggregates, repositories, and domain events with explicit invariants."
risk: safe
source: self
tags: "[ddd, tactical, aggregates, value-objects, domain-events]"
date_added: "2026-02-27"
---

# DDD Tactical Patterns

## Use this skill when

- Translating domain rules into code structures.
- Designing aggregate boundaries and invariants.
- Refactoring an anemic model into behavior-rich domain objects.
- Defining repository contracts and domain event boundaries.

## Do not use this skill when

- You are still defining strategic boundaries.
- The task is only API documentation or UI layout.
- Full DDD complexity is not justified.

## Instructions

1. Identify invariants first and design aggregates around them.
2. Model immutable value objects for validated concepts.
3. Keep domain behavior in domain objects, not controllers.
4. Emit domain events for meaningful state transitions.
5. Keep repositories at aggregate root boundaries.

If detailed checklists are needed, open `references/tactical-checklist.md`.

## Example

```typescript
class Order {
  private status: "draft" | "submitted" = "draft";

  submit(itemsCount: number): void {
    if (itemsCount === 0) throw new Error("Order cannot be submitted empty");
    if (this.status !== "draft") throw new Error("Order already submitted");
    this.status = "submitted";
  }
}
```

## Limitations

- This skill does not define deployment architecture.
- It does not choose databases or transport protocols.
- It should be paired with testing patterns for invariant coverage.

---

<!-- AGI-INTEGRATION-START -->

## AGI Framework Integration

> **Adapted for [@techwavedev/agi-agent-kit](https://www.npmjs.com/package/@techwavedev/agi-agent-kit)**
> Original source: [antigravity-awesome-skills](https://github.com/sickn33/antigravity-awesome-skills)

### Memory-First Protocol

Retrieve prior Architecture Decision Records (ADRs), trade-off analyses, and system design rationale. Critical for maintaining consistency across long-running projects.

```bash
# Check for prior architecture/design context before starting
python3 execution/memory_manager.py auto --query "architecture decisions and trade-off analysis for Ddd Tactical Patterns"
```

### Storing Results

After completing work, store architecture/design decisions for future sessions:

```bash
python3 execution/memory_manager.py store \
  --content "Architecture: event-driven microservices with CQRS, Pulsar for messaging, Qdrant for semantic search" \
  --type decision --project <project> \
  --tags ddd-tactical-patterns architecture
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
