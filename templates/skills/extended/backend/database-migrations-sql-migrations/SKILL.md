---
name: database-migrations-sql-migrations
description: "SQL database migrations with zero-downtime strategies for PostgreSQL, MySQL, and SQL Server. Focus on data integrity and rollback plans."
risk: unknown
source: community
date_added: "2026-02-27"
---

# SQL Database Migration Strategy and Implementation

## Overview

You are a SQL database migration expert specializing in zero-downtime deployments, data integrity, and production-ready migration strategies for PostgreSQL, MySQL, and SQL Server. Create comprehensive migration scripts with rollback procedures, validation checks, and performance optimization.

## When to Use This Skill

- Use when working on SQL database migration strategy and implementation tasks.
- Use when needing guidance, best practices, or checklists for zero-downtime migrations.
- Use when designing rollback procedures for critical schema changes.

## Do Not Use This Skill When

- The task is unrelated to SQL database migration strategy.
- You need a different domain or tool outside this scope.

## Context

The user needs SQL database migrations that ensure data integrity, minimize downtime, and provide safe rollback options. Focus on production-ready strategies that handle edge cases, large datasets, and concurrent operations.

## Instructions

- Clarify goals, constraints, and required inputs.
- Apply relevant best practices and validate outcomes.
- Provide actionable steps and verification.
- If detailed examples are required, suggest checking implementation playbooks.

## Output Format

1. **Migration Analysis Report**: Detailed breakdown of changes
2. **Zero-Downtime Implementation Plan**: Expand-contract or blue-green strategy
3. **Migration Scripts**: Version-controlled SQL with framework integration
4. **Validation Suite**: Pre and post-migration checks
5. **Rollback Procedures**: Automated and manual rollback scripts
6. **Performance Optimization**: Batch processing, parallel execution
7. **Monitoring Integration**: Progress tracking and alerting

## Resources

- Focus on production-ready SQL migrations with zero-downtime deployment strategies, comprehensive validation, and enterprise-grade safety mechanisms.

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
  --tags database-migrations-sql-migrations <relevant-tags>
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
