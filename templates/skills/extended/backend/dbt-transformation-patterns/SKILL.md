---
name: dbt-transformation-patterns
description: "Master dbt (data build tool) for analytics engineering with model organization, testing, documentation, and incremental strategies. Use when building data transformations, creating data models, or ..."
risk: unknown
source: community
date_added: "2026-02-27"
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

<!-- AGI-INTEGRATION-START -->

## AGI Framework Integration

> **Adapted for [@techwavedev/agi-agent-kit](https://www.npmjs.com/package/@techwavedev/agi-agent-kit)**
> Original source: [antigravity-awesome-skills](https://github.com/sickn33/antigravity-awesome-skills)

### Memory-First Protocol

Retrieve prior API design decisions, database schema choices, and error handling patterns. Cache API response templates for consistent error formatting.

```bash
# Check for prior backend/API context before starting
python3 execution/memory_manager.py auto --query "API design patterns and architecture decisions for Dbt Transformation Patterns"
```

### Storing Results

After completing work, store backend/API decisions for future sessions:

```bash
python3 execution/memory_manager.py store \
  --content "API architecture: REST with HATEOAS, JWT auth, rate limiting at 100 req/min per tenant" \
  --type decision --project <project> \
  --tags dbt-transformation-patterns backend
```

### Multi-Agent Collaboration

Share API contract changes with frontend agents so they update their client code, and with QA agents for test coverage.

```bash
python3 execution/cross_agent_context.py store \
  --agent "<your-agent>" \
  --action "Implemented API endpoints — 5 new routes with OpenAPI spec and integration tests" \
  --project <project>
```

### Agent Team: Code Review

After implementation, dispatch `code_review_team` for two-stage review (spec compliance + code quality) before merging.

<!-- AGI-INTEGRATION-END -->
