---
name: unity-ecs-patterns
description: "Master Unity ECS (Entity Component System) with DOTS, Jobs, and Burst for high-performance game development. Use when building data-oriented games, optimizing performance, or working with large ent..."
risk: unknown
source: community
date_added: "2026-02-27"
---

# Unity ECS Patterns

Production patterns for Unity's Data-Oriented Technology Stack (DOTS) including Entity Component System, Job System, and Burst Compiler.

## Use this skill when

- Building high-performance Unity games
- Managing thousands of entities efficiently
- Implementing data-oriented game systems
- Optimizing CPU-bound game logic
- Converting OOP game code to ECS
- Using Jobs and Burst for parallelization

## Do not use this skill when

- The task is unrelated to unity ecs patterns
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

Retrieve game design decisions, performance benchmarks, and engine configuration. Cache asset pipeline settings and build configurations.

```bash
# Check for prior game development context before starting
python3 execution/memory_manager.py auto --query "game architecture and engine patterns for Unity Ecs Patterns"
```

### Storing Results

After completing work, store game development decisions for future sessions:

```bash
python3 execution/memory_manager.py store \
  --content "Game: ECS architecture with 60fps target, spatial partitioning for collision, asset pipeline with LOD" \
  --type technical --project <project> \
  --tags unity-ecs-patterns gaming
```

### Multi-Agent Collaboration

Share engine decisions and performance budgets with art/design agents and QA agents.

```bash
python3 execution/cross_agent_context.py store \
  --agent "<your-agent>" \
  --action "Game feature implemented — performance profiled, asset pipeline updated, QA test plan created" \
  --project <project>
```

<!-- AGI-INTEGRATION-END -->
