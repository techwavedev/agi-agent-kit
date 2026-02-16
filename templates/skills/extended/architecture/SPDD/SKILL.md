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

## 🧠 AGI Framework Integration

> **Adapted for [@techwavedev/agi-agent-kit](https://www.npmjs.com/package/@techwavedev/agi-agent-kit)**
> Original source: [antigravity-awesome-skills](https://github.com/sickn33/antigravity-awesome-skills)

### Hybrid Memory Integration (Qdrant + BM25)

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
  --tags spdd <relevant-tags>
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