---
name: dbt-transformation-patterns
description: Master dbt (data build tool) for analytics engineering with model organization, testing, documentation, and incremental strategies. Use when building data transformations, creating data models, or implementing analytics engineering best practices.
---

# dbt Transformation Patterns

Production-ready patterns for dbt (data build tool) including model organization, testing strategies, documentation, and incremental processing.

## Use this skill when

- Building data transformation pipelines with dbt
- Organizing models into staging, intermediate, and marts layers
- Implementing data quality tests and documentation
- Creating incremental models for large datasets
- Setting up dbt project structure and conventions

## Do not use this skill when

- The project is not using dbt or a warehouse-backed workflow
- You only need ad-hoc SQL queries
- There is no access to source data or schemas

## Instructions

- Define model layers, naming, and ownership.
- Implement tests, documentation, and freshness checks.
- Choose materializations and incremental strategies.
- Optimize runs with selectors and CI workflows.
- If detailed patterns are required, open `resources/implementation-playbook.md`.

## Resources

- `resources/implementation-playbook.md` for detailed dbt patterns and examples.


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
  --tags dbt-transformation-patterns <relevant-tags>
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