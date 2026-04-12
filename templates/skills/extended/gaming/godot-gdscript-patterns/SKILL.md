---
name: godot-gdscript-patterns
description: "Master Godot 4 GDScript patterns including signals, scenes, state machines, and optimization. Use when building Godot games, implementing game systems, or learning GDScript best practices."
risk: safe
source: community
date_added: "2026-02-27"
---

# Godot GDScript Patterns

Production patterns for Godot 4.x game development with GDScript, covering architecture, signals, scenes, and optimization.

## Use this skill when

- Building games with Godot 4
- Implementing game systems in GDScript
- Designing scene architecture
- Managing game state
- Optimizing GDScript performance
- Learning Godot best practices

## Do not use this skill when

- The task is unrelated to godot gdscript patterns
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
python3 execution/memory_manager.py auto --query "game architecture and engine patterns for Godot Gdscript Patterns"
```

### Storing Results

After completing work, store game development decisions for future sessions:

```bash
python3 execution/memory_manager.py store \
  --content "Game: ECS architecture with 60fps target, spatial partitioning for collision, asset pipeline with LOD" \
  --type technical --project <project> \
  --tags godot-gdscript-patterns gaming
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
