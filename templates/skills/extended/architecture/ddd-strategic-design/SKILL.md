---
name: ddd-strategic-design
description: Design DDD strategic artifacts including subdomains, bounded contexts, and ubiquitous language for complex business domains.
risk: safe
source: self
tags: [ddd, strategic-design, bounded-context, ubiquitous-language]
---

# DDD Strategic Design

## Use this skill when

- Defining core, supporting, and generic subdomains.
- Splitting a monolith or service landscape by domain boundaries.
- Aligning teams and ownership with bounded contexts.
- Building a shared ubiquitous language with domain experts.

## Do not use this skill when

- The domain model is stable and already well bounded.
- You need tactical code patterns only.
- The task is purely infrastructure or UI oriented.

## Instructions

1. Extract domain capabilities and classify subdomains.
2. Define bounded contexts around consistency and ownership.
3. Establish a ubiquitous language glossary and anti-terms.
4. Capture context boundaries in ADRs before implementation.

If detailed templates are needed, open `references/strategic-design-template.md`.

## Required artifacts

- Subdomain classification table
- Bounded context catalog
- Glossary with canonical terms
- Boundary decisions with rationale

## Examples

```text
Use @ddd-strategic-design to map our commerce domain into bounded contexts,
classify subdomains, and propose team ownership.
```

## Limitations

- This skill does not produce executable code.
- It cannot infer business truth without stakeholder input.
- It should be followed by tactical design before implementation.
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
  --tags ddd-strategic-design <relevant-tags>
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
