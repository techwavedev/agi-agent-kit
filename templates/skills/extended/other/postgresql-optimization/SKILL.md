---
name: postgresql-optimization
description: "PostgreSQL database optimization workflow for query tuning, indexing strategies, performance analysis, and production database management."
category: granular-workflow-bundle
risk: safe
source: personal
date_added: "2026-02-27"
---

# PostgreSQL Optimization Workflow

## Overview

Specialized workflow for PostgreSQL database optimization including query tuning, indexing strategies, performance analysis, vacuum management, and production database administration.

## When to Use This Workflow

Use this workflow when:
- Optimizing slow PostgreSQL queries
- Designing indexing strategies
- Analyzing database performance
- Tuning PostgreSQL configuration
- Managing production databases

## Workflow Phases

### Phase 1: Performance Assessment

#### Skills to Invoke
- `database-optimizer` - Database optimization
- `postgres-best-practices` - PostgreSQL best practices

#### Actions
1. Check database version
2. Review configuration
3. Analyze slow queries
4. Check resource usage
5. Identify bottlenecks

#### Copy-Paste Prompts
```
Use @database-optimizer to assess PostgreSQL performance
```

### Phase 2: Query Analysis

#### Skills to Invoke
- `sql-optimization-patterns` - SQL optimization
- `postgres-best-practices` - PostgreSQL patterns

#### Actions
1. Run EXPLAIN ANALYZE
2. Identify scan types
3. Check join strategies
4. Analyze execution time
5. Find optimization opportunities

#### Copy-Paste Prompts
```
Use @sql-optimization-patterns to analyze and optimize queries
```

### Phase 3: Indexing Strategy

#### Skills to Invoke
- `database-design` - Index design
- `postgresql` - PostgreSQL indexing

#### Actions
1. Identify missing indexes
2. Create B-tree indexes
3. Add composite indexes
4. Consider partial indexes
5. Review index usage

#### Copy-Paste Prompts
```
Use @database-design to design PostgreSQL indexing strategy
```

### Phase 4: Query Optimization

#### Skills to Invoke
- `sql-optimization-patterns` - Query tuning
- `sql-pro` - SQL expertise

#### Actions
1. Rewrite inefficient queries
2. Optimize joins
3. Add CTEs where helpful
4. Implement pagination
5. Test improvements

#### Copy-Paste Prompts
```
Use @sql-optimization-patterns to optimize SQL queries
```

### Phase 5: Configuration Tuning

#### Skills to Invoke
- `postgres-best-practices` - Configuration
- `database-admin` - Database administration

#### Actions
1. Tune shared_buffers
2. Configure work_mem
3. Set effective_cache_size
4. Adjust checkpoint settings
5. Configure autovacuum

#### Copy-Paste Prompts
```
Use @postgres-best-practices to tune PostgreSQL configuration
```

### Phase 6: Maintenance

#### Skills to Invoke
- `database-admin` - Database maintenance
- `postgresql` - PostgreSQL maintenance

#### Actions
1. Schedule VACUUM
2. Run ANALYZE
3. Check table bloat
4. Monitor autovacuum
5. Review statistics

#### Copy-Paste Prompts
```
Use @database-admin to schedule PostgreSQL maintenance
```

### Phase 7: Monitoring

#### Skills to Invoke
- `grafana-dashboards` - Monitoring dashboards
- `prometheus-configuration` - Metrics collection

#### Actions
1. Set up monitoring
2. Create dashboards
3. Configure alerts
4. Track key metrics
5. Review trends

#### Copy-Paste Prompts
```
Use @grafana-dashboards to create PostgreSQL monitoring
```

## Optimization Checklist

- [ ] Slow queries identified
- [ ] Indexes optimized
- [ ] Configuration tuned
- [ ] Maintenance scheduled
- [ ] Monitoring active
- [ ] Performance improved

## Quality Gates

- [ ] Query performance improved
- [ ] Indexes effective
- [ ] Configuration optimized
- [ ] Maintenance automated
- [ ] Monitoring in place

## Related Workflow Bundles

- `database` - Database operations
- `cloud-devops` - Infrastructure
- `performance-optimization` - Performance

---

<!-- AGI-INTEGRATION-START -->

## AGI Framework Integration

> **Adapted for [@techwavedev/agi-agent-kit](https://www.npmjs.com/package/@techwavedev/agi-agent-kit)**
> Original source: [antigravity-awesome-skills](https://github.com/sickn33/antigravity-awesome-skills)

### Memory-First Protocol

Cache workflow configurations and automation patterns. Retrieve prior pipeline designs to avoid re-building similar flows from scratch.

```bash
# Check for prior workflow/automation context before starting
python3 execution/memory_manager.py auto --query "automation patterns and workflow configurations for Postgresql Optimization"
```

### Storing Results

After completing work, store workflow/automation decisions for future sessions:

```bash
python3 execution/memory_manager.py store \
  --content "Workflow: automated data pipeline with retry logic, dead-letter queue, and Slack alerts on failure" \
  --type technical --project <project> \
  --tags postgresql-optimization workflow
```

### Multi-Agent Collaboration

Share workflow state with other agents so they can trigger, monitor, or extend the automation.

```bash
python3 execution/cross_agent_context.py store \
  --agent "<your-agent>" \
  --action "Workflow automation deployed — pipeline processing 1000+ events/day with 99.9% success rate" \
  --project <project>
```

### Playbook Engine

Combine this skill with others using the Playbook Engine (`execution/workflow_engine.py`) for guided multi-step automation with progress tracking.

<!-- AGI-INTEGRATION-END -->
