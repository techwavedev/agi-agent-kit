---
name: godot-4-migration
description: "Specialized guide for migrating Godot 3.x projects to Godot 4 (GDScript 2.0), covering syntax changes, Tweens, and exports."
risk: safe
source: community
date_added: "2026-02-27"
---

# Godot 4 Migration Guide

## Overview

A critical guide for developers transitioning from Godot 3.x to Godot 4. This skill focuses on the major syntax changes in GDScript 2.0, the new `Tween` system, and `export` annotation updates.

## When to Use This Skill

- Use when porting a Godot 3 project to Godot 4.
- Use when encountering syntax errors after upgrading.
- Use when replacing deprecated nodes (like `Tween` node vs `create_tween`).
- Use when updating `export` variables to `@export` annotations.

## Key Changes

### 1. Annotations (`@`)

Godot 4 uses `@` for keywords that modify behavior.
- `export var x` -> `@export var x`
- `onready var y` -> `@onready var y`
- `tool` -> `@tool` (at top of file)

### 2. Setters and Getters

Properties now define setters/getters inline.

**Godot 3:**
```gdscript
var health setget set_health, get_health

func set_health(value):
    health = value
```

**Godot 4:**
```gdscript
var health: int:
    set(value):
        health = value
        emit_signal("health_changed", health)
    get:
        return health
```

### 3. Tween System

The `Tween` node is deprecated. Use `create_tween()` in code.

**Godot 3:**
```gdscript
$Tween.interpolate_property(...)
$Tween.start()
```

**Godot 4:**
```gdscript
var tween = create_tween()
tween.tween_property($Sprite, "position", Vector2(100, 100), 1.0)
tween.parallel().tween_property($Sprite, "modulate:a", 0.0, 1.0)
```

### 4. Signal Connections

String-based connections are discouraged. Use callables.

**Godot 3:**
```gdscript
connect("pressed", self, "_on_pressed")
```

**Godot 4:**
```gdscript
pressed.connect(_on_pressed)
```

## Examples

### Example 1: Typed Arrays

GDScript 2.0 supports typed arrays for better performance and type safety.

```gdscript
# Godot 3
var enemies = []

# Godot 4
var enemies: Array[Node] = []

func _ready():
    for child in get_children():
        if child is Enemy:
            enemies.append(child)
```

### Example 2: Awaiting Signals (Coroutines)

`yield` is replaced by `await`.

**Godot 3:**
```gdscript
yield(get_tree().create_timer(1.0), "timeout")
```

**Godot 4:**
```gdscript
await get_tree().create_timer(1.0).timeout
```

## Best Practices

- ✅ **Do:** Use `@export_range`, `@export_file`, etc., for better inspector UI.
- ✅ **Do:** Type all variables (`var x: int`) for performance gains in GDScript 2.0.
- ✅ **Do:** Use `super()` to call parent methods instead of `.function_name()`.
- ❌ **Don't:** Use string names for signals (`emit_signal("name")`) if you can use the signal object (`name.emit()`).

## Troubleshooting

**Problem:** "Identifier 'Tween' is not a valid type."
**Solution:** `Tween` is now `SceneTreeTween` or just an object returned by `create_tween()`. You rarely type it explicitly, just use `var tween = create_tween()`.

---

<!-- AGI-INTEGRATION-START -->

## 🧠 AGI Framework Integration

> **Adapted for [@techwavedev/agi-agent-kit](https://www.npmjs.com/package/@techwavedev/agi-agent-kit)**
> Original source: [antigravity-awesome-skills](https://github.com/sickn33/antigravity-awesome-skills)

### Qdrant Memory Integration

Before executing complex tasks with this skill:
```bash
python3 execution/memory_manager.py auto --query "<task summary>"
```
- **Cache hit?** Use cached response directly — no need to re-process.
- **Memory match?** Inject `context_chunks` into your reasoning.
- **No match?** Proceed normally, then store results:
```bash
python3 execution/memory_manager.py store \\
  --content "Description of what was decided/solved" \\
  --type decision \\
  --tags godot-4-migration <relevant-tags>
```

### Agent Team Collaboration

- This skill can be invoked by the `orchestrator` agent via intelligent routing.
- In **Agent Teams mode**, results are shared via Qdrant shared memory for cross-agent context.
- In **Subagent mode**, this skill runs in isolation with its own memory namespace.

### Local LLM Support

When available, use local Ollama models for embedding and lightweight inference:
- Embeddings: `nomic-embed-text` via Qdrant memory system
- Lightweight analysis: Local models reduce API costs for repetitive patterns

<!-- AGI-INTEGRATION-END -->
