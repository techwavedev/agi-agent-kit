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

## AGI Framework Integration

> **Adapted for [@techwavedev/agi-agent-kit](https://www.npmjs.com/package/@techwavedev/agi-agent-kit)**
> Original source: [antigravity-awesome-skills](https://github.com/sickn33/antigravity-awesome-skills)

### Memory-First Protocol

Retrieve prior API design decisions, database schema choices, and error handling patterns. Cache API response templates for consistent error formatting.

```bash
# Check for prior backend/API context before starting
python3 execution/memory_manager.py auto --query "API design patterns and architecture decisions for Database Migrations Sql Migrations"
```

### Storing Results

After completing work, store backend/API decisions for future sessions:

```bash
python3 execution/memory_manager.py store \
  --content "API architecture: REST with HATEOAS, JWT auth, rate limiting at 100 req/min per tenant" \
  --type decision --project <project> \
  --tags database-migrations-sql-migrations backend
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
