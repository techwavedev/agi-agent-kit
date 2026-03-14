---
name: modern-javascript-patterns
description: "Master ES6+ features including async/await, destructuring, spread operators, arrow functions, promises, modules, iterators, generators, and functional programming patterns for writing clean, effici..."
risk: unknown
source: community
date_added: "2026-02-27"
---

# Modern JavaScript Patterns

Comprehensive guide for mastering modern JavaScript (ES6+) features, functional programming patterns, and best practices for writing clean, maintainable, and performant code.

## Use this skill when

- Refactoring legacy JavaScript to modern syntax
- Implementing functional programming patterns
- Optimizing JavaScript performance
- Writing maintainable and readable code
- Working with asynchronous operations
- Building modern web applications
- Migrating from callbacks to Promises/async-await
- Implementing data transformation pipelines

## Do not use this skill when

- The task is unrelated to modern javascript patterns
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
python3 execution/memory_manager.py auto --query "architecture decisions and trade-off analysis for Modern Javascript Patterns"
```

### Storing Results

After completing work, store architecture/design decisions for future sessions:

```bash
python3 execution/memory_manager.py store \
  --content "Architecture: event-driven microservices with CQRS, Pulsar for messaging, Qdrant for semantic search" \
  --type decision --project <project> \
  --tags modern-javascript-patterns architecture
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
