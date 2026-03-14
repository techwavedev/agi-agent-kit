---
name: fp-types-ref
description: Quick reference for fp-ts types. Use when user asks which type to use, needs Option/Either/Task decision help, or wants fp-ts imports.
version: 1.0.0
tags: [fp-ts, typescript, quick-reference, option, either, task]
---

# fp-ts Quick Reference

## Which Type Should I Use?

```
Is the operation async?
├─ NO: Does it involve errors?
│   ├─ YES → Either<Error, Value>
│   └─ NO: Might value be missing?
│       ├─ YES → Option<Value>
│       └─ NO → Just use the value
└─ YES: Does it involve errors?
    ├─ YES → TaskEither<Error, Value>
    └─ NO: Might value be missing?
        ├─ YES → TaskOption<Value>
        └─ NO → Task<Value>
```

## Common Imports

```typescript
// Core
import { pipe, flow } from 'fp-ts/function'

// Types
import * as O from 'fp-ts/Option'      // Maybe exists
import * as E from 'fp-ts/Either'      // Success or failure
import * as TE from 'fp-ts/TaskEither' // Async + failure
import * as T from 'fp-ts/Task'        // Async (no failure)
import * as A from 'fp-ts/Array'       // Array utilities
```

## One-Line Patterns

| Need | Code |
|------|------|
| Wrap nullable | `O.fromNullable(value)` |
| Default value | `O.getOrElse(() => default)` |
| Transform if exists | `O.map(fn)` |
| Chain optionals | `O.flatMap(fn)` |
| Wrap try/catch | `E.tryCatch(() => risky(), toError)` |
| Wrap async | `TE.tryCatch(() => fetch(url), toError)` |
| Run pipe | `pipe(value, fn1, fn2, fn3)` |

## Pattern Match

```typescript
// Option
pipe(maybe, O.match(
  () => 'nothing',
  (val) => `got ${val}`
))

// Either
pipe(result, E.match(
  (err) => `error: ${err}`,
  (val) => `success: ${val}`
))
```

---

<!-- AGI-INTEGRATION-START -->

## AGI Framework Integration

> **Adapted for [@techwavedev/agi-agent-kit](https://www.npmjs.com/package/@techwavedev/agi-agent-kit)**
> Original source: [antigravity-awesome-skills](https://github.com/sickn33/antigravity-awesome-skills)

### Memory-First Protocol

Retrieve prior design decisions (color palettes, typography, spacing scales) to maintain visual consistency across sessions. Cache generated design tokens.

```bash
# Check for prior frontend/design context before starting
python3 execution/memory_manager.py auto --query "design system decisions and component patterns for Fp Types Ref"
```

### Storing Results

After completing work, store frontend/design decisions for future sessions:

```bash
python3 execution/memory_manager.py store \
  --content "Design system: adopted 8px grid, Inter font family, HSL color tokens with dark mode support" \
  --type decision --project <project> \
  --tags fp-types-ref frontend
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
