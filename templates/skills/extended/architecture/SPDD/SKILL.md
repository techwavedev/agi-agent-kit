---
name: spdd
description: Spec-Driven Product Development - A 3-phase methodology (Research, Spec, Implementation) for building software from structured specifications.
---

# SPDD - Spec-Driven Product Development

A structured methodology for building software through three sequential phases:

1. **Research** (`1-research.md`) — Codebase analysis and technical cartography
2. **Spec** (`2-spec.md`) — Product specification and architecture design
3. **Implementation** (`3-implementation.md`) — Code generation following the spec

## When to Use

- Starting greenfield projects that need structured planning
- Refactoring or rebuilding existing codebases
- Complex features requiring research → spec → build flow

## References

- `1-research.md` — Codebase Research Agent instructions
- `2-spec.md` — Specification writing methodology
- `3-implementation.md` — Implementation execution guidelines

---

<!-- AGI-INTEGRATION-START -->

## AGI Framework Integration

> **Adapted for [@techwavedev/agi-agent-kit](https://www.npmjs.com/package/@techwavedev/agi-agent-kit)**
> Original source: [antigravity-awesome-skills](https://github.com/sickn33/antigravity-awesome-skills)

### Memory-First Protocol

Retrieve prior Architecture Decision Records (ADRs), trade-off analyses, and system design rationale. Critical for maintaining consistency across long-running projects.

```bash
# Check for prior architecture/design context before starting
python3 execution/memory_manager.py auto --query "architecture decisions and trade-off analysis for Spdd"
```

### Storing Results

After completing work, store architecture/design decisions for future sessions:

```bash
python3 execution/memory_manager.py store \
  --content "Architecture: event-driven microservices with CQRS, Pulsar for messaging, Qdrant for semantic search" \
  --type decision --project <project> \
  --tags spdd architecture
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