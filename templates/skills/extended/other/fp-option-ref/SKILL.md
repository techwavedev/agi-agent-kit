---
name: fp-option-ref
description: Quick reference for Option type. Use when user needs to handle nullable values, optional data, or wants to avoid null checks.
version: 1.0.0
tags: [fp-ts, option, nullable, maybe, quick-reference]
---

# Option Quick Reference

Option = value that might not exist. `Some(value)` or `None`.

## Create

```typescript
import * as O from 'fp-ts/Option'

O.some(5)              // Some(5)
O.none                 // None
O.fromNullable(x)      // null/undefined → None, else Some(x)
O.fromPredicate(x > 0)(x) // false → None, true → Some(x)
```

## Transform

```typescript
O.map(fn)              // Transform inner value
O.flatMap(fn)          // Chain Options (fn returns Option)
O.filter(predicate)    // None if predicate false
```

## Extract

```typescript
O.getOrElse(() => default)  // Get value or default
O.toNullable(opt)           // Back to T | null
O.toUndefined(opt)          // Back to T | undefined
O.match(onNone, onSome)     // Pattern match
```

## Common Patterns

```typescript
import { pipe } from 'fp-ts/function'
import * as O from 'fp-ts/Option'

// Safe property access
pipe(
  O.fromNullable(user),
  O.map(u => u.profile),
  O.flatMap(p => O.fromNullable(p.avatar)),
  O.getOrElse(() => '/default-avatar.png')
)

// Array first element
import * as A from 'fp-ts/Array'
pipe(
  users,
  A.head,  // Option<User>
  O.map(u => u.name),
  O.getOrElse(() => 'No users')
)
```

## vs Nullable

```typescript
// ❌ Nullable - easy to forget checks
const name = user?.profile?.name ?? 'Guest'

// ✅ Option - explicit, composable
pipe(
  O.fromNullable(user),
  O.flatMap(u => O.fromNullable(u.profile)),
  O.map(p => p.name),
  O.getOrElse(() => 'Guest')
)
```

Use Option when you need to **chain** operations on optional values.

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
  --tags fp-option-ref <relevant-tags>
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
