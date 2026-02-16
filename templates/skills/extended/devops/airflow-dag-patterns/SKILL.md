---
name: airflow-dag-patterns
description: Build production Apache Airflow DAGs with best practices for operators, sensors, testing, and deployment. Use when creating data pipelines, orchestrating workflows, or scheduling batch jobs.
---

# Apache Airflow DAG Patterns

Production-ready patterns for Apache Airflow including DAG design, operators, sensors, testing, and deployment strategies.

## Use this skill when

- Creating data pipeline orchestration with Airflow
- Designing DAG structures and dependencies
- Implementing custom operators and sensors
- Testing Airflow DAGs locally
- Setting up Airflow in production
- Debugging failed DAG runs

## Do not use this skill when

- You only need a simple cron job or shell script
- Airflow is not part of the tooling stack
- The task is unrelated to workflow orchestration

## Instructions

1. Identify data sources, schedules, and dependencies.
2. Design idempotent tasks with clear ownership and retries.
3. Implement DAGs with observability and alerting hooks.
4. Validate in staging and document operational runbooks.

Refer to `resources/implementation-playbook.md` for detailed patterns, checklists, and templates.

## Safety

- Avoid changing production DAG schedules without approval.
- Test backfills and retries carefully to prevent data duplication.

## Resources

- `resources/implementation-playbook.md` for detailed patterns, checklists, and templates.


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
  --tags airflow-dag-patterns <relevant-tags>
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