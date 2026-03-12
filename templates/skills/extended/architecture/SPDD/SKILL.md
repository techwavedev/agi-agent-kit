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

### Hybrid Memory Integration (Qdrant + BM25)

Before executing this skill, check memory for prior context:
```bash
python3 execution/memory_manager.py auto --query "<skill-related query>"
```

After completing work, store the results:
```bash
python3 execution/memory_manager.py store --content "<summary>" --type decision --project <project>
```

### Agent Team Collaboration

Share outcomes with other agents:
```bash
python3 execution/cross_agent_context.py store --agent "<name>" --action "<what was done>" --project <project>
```

### Local LLM Support

This skill works with any LLM provider. For local inference, ensure Ollama is running with the required model.

<!-- AGI-INTEGRATION-END -->