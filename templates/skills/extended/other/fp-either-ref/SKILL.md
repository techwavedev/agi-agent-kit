---
name: fp-either-ref
description: Quick reference for Either type. Use when user needs error handling, validation, or operations that can fail with typed errors.
version: 1.0.0
tags: [fp-ts, either, error-handling, validation, quick-reference]
---

# Either Quick Reference

Either = success or failure. `Right(value)` or `Left(error)`.

## Create

```typescript
import * as E from 'fp-ts/Either'

E.right(value)           // Success
E.left(error)            // Failure
E.fromNullable(err)(x)   // null → Left(err), else Right(x)
E.tryCatch(fn, toError)  // try/catch → Either
```

## Transform

```typescript
E.map(fn)                // Transform Right value
E.mapLeft(fn)            // Transform Left error
E.flatMap(fn)            // Chain (fn returns Either)
E.filterOrElse(pred, toErr) // Right → Left if pred fails
```

## Extract

```typescript
E.getOrElse(err => default)  // Get Right or default
E.match(onLeft, onRight)     // Pattern match
E.toUnion(either)            // E | A (loses type info)
```

## Common Patterns

```typescript
import { pipe } from 'fp-ts/function'
import * as E from 'fp-ts/Either'

// Validation
const validateEmail = (s: string): E.Either<string, string> =>
  s.includes('@') ? E.right(s) : E.left('Invalid email')

// Chain validations (stops at first error)
pipe(
  E.right({ email: 'test@example.com', age: 25 }),
  E.flatMap(d => pipe(validateEmail(d.email), E.map(() => d))),
  E.flatMap(d => d.age >= 18 ? E.right(d) : E.left('Must be 18+'))
)

// Convert throwing code
const parseJson = (s: string) => E.tryCatch(
  () => JSON.parse(s),
  (e) => `Parse error: ${e}`
)
```

## vs try/catch

```typescript
// ❌ try/catch - errors not in types
try {
  const data = JSON.parse(input)
  process(data)
} catch (e) {
  handleError(e)
}

// ✅ Either - errors explicit in types
pipe(
  E.tryCatch(() => JSON.parse(input), String),
  E.map(process),
  E.match(handleError, identity)
)
```

Use Either when **error type matters** and you want to chain operations.

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
  --tags fp-either-ref <relevant-tags>
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
