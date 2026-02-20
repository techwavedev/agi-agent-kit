---
name: react-patterns
description: Modern React patterns and principles. Hooks, composition, performance, TypeScript best practices.
allowed-tools: Read, Write, Edit, Glob, Grep
---

# React Patterns

> Principles for building production-ready React applications.

---

## 1. Component Design Principles

### Component Types

| Type | Use | State |
|------|-----|-------|
| **Server** | Data fetching, static | None |
| **Client** | Interactivity | useState, effects |
| **Presentational** | UI display | Props only |
| **Container** | Logic/state | Heavy state |

### Design Rules

- One responsibility per component
- Props down, events up
- Composition over inheritance
- Prefer small, focused components

---

## 2. Hook Patterns

### When to Extract Hooks

| Pattern | Extract When |
|---------|-------------|
| **useLocalStorage** | Same storage logic needed |
| **useDebounce** | Multiple debounced values |
| **useFetch** | Repeated fetch patterns |
| **useForm** | Complex form state |

### Hook Rules

- Hooks at top level only
- Same order every render
- Custom hooks start with "use"
- Clean up effects on unmount

---

## 3. State Management Selection

| Complexity | Solution |
|------------|----------|
| Simple | useState, useReducer |
| Shared local | Context |
| Server state | React Query, SWR |
| Complex global | Zustand, Redux Toolkit |

### State Placement

| Scope | Where |
|-------|-------|
| Single component | useState |
| Parent-child | Lift state up |
| Subtree | Context |
| App-wide | Global store |

---

## 4. React 19 Patterns

### New Hooks

| Hook | Purpose |
|------|---------|
| **useActionState** | Form submission state |
| **useOptimistic** | Optimistic UI updates |
| **use** | Read resources in render |

### Compiler Benefits

- Automatic memoization
- Less manual useMemo/useCallback
- Focus on pure components

---

## 5. Composition Patterns

### Compound Components

- Parent provides context
- Children consume context
- Flexible slot-based composition
- Example: Tabs, Accordion, Dropdown

### Render Props vs Hooks

| Use Case | Prefer |
|----------|--------|
| Reusable logic | Custom hook |
| Render flexibility | Render props |
| Cross-cutting | Higher-order component |

---

## 6. Performance Principles

### When to Optimize

| Signal | Action |
|--------|--------|
| Slow renders | Profile first |
| Large lists | Virtualize |
| Expensive calc | useMemo |
| Stable callbacks | useCallback |

### Optimization Order

1. Check if actually slow
2. Profile with DevTools
3. Identify bottleneck
4. Apply targeted fix

---

## 7. Error Handling

### Error Boundary Usage

| Scope | Placement |
|-------|-----------|
| App-wide | Root level |
| Feature | Route/feature level |
| Component | Around risky component |

### Error Recovery

- Show fallback UI
- Log error
- Offer retry option
- Preserve user data

---

## 8. TypeScript Patterns

### Props Typing

| Pattern | Use |
|---------|-----|
| Interface | Component props |
| Type | Unions, complex |
| Generic | Reusable components |

### Common Types

| Need | Type |
|------|------|
| Children | ReactNode |
| Event handler | MouseEventHandler |
| Ref | RefObject<Element> |

---

## 9. Testing Principles

| Level | Focus |
|-------|-------|
| Unit | Pure functions, hooks |
| Integration | Component behavior |
| E2E | User flows |

### Test Priorities

- User-visible behavior
- Edge cases
- Error states
- Accessibility

---

## 10. Anti-Patterns

| ❌ Don't | ✅ Do |
|----------|-------|
| Prop drilling deep | Use context |
| Giant components | Split smaller |
| useEffect for everything | Server components |
| Premature optimization | Profile first |
| Index as key | Stable unique ID |

---

> **Remember:** React is about composition. Build small, combine thoughtfully.

## AGI Framework Integration

### Qdrant Memory Integration

Before executing complex tasks with this skill:
```bash
python3 execution/memory_manager.py auto --query "<task summary>"
```

**Decision Tree:**
- **Cache hit?** Use cached response directly — no need to re-process.
- **Memory match?** Inject `context_chunks` into your reasoning.
- **No match?** Proceed normally, then store results:

```bash
python3 execution/memory_manager.py store \
  --content "Description of what was decided/solved" \
  --type decision \
  --tags react-patterns <relevant-tags>
```

> **Note:** Storing automatically updates both Vector (Qdrant) and Keyword (BM25) indices.

### Agent Team Collaboration

- **Strategy**: This skill communicates via the shared memory system.
- **Orchestration**: Invoked by `orchestrator` via intelligent routing.
- **Context Sharing**: Always read previous agent outputs from memory before starting.

### Local LLM Support

When available, use local Ollama models for embedding and lightweight inference:
- Embeddings: `nomic-embed-text` via Qdrant memory system
- Lightweight analysis: Local models reduce API costs for repetitive patterns
