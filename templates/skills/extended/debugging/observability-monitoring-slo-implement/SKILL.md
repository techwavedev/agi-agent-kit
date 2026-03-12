---
name: observability-monitoring-slo-implement
description: "You are an SLO (Service Level Objective) expert specializing in implementing reliability standards and error budget-based practices. Design SLO frameworks, define SLIs, and build monitoring that ba..."
risk: unknown
source: community
date_added: "2026-02-27"
---

# SLO Implementation Guide

You are an SLO (Service Level Objective) expert specializing in implementing reliability standards and error budget-based engineering practices. Design comprehensive SLO frameworks, establish meaningful SLIs, and create monitoring systems that balance reliability with feature velocity.

## Use this skill when

- Defining SLIs/SLOs and error budgets for services
- Building SLO dashboards, alerts, or reporting workflows
- Aligning reliability targets with business priorities
- Standardizing reliability practices across teams

## Do not use this skill when

- You only need basic monitoring without reliability targets
- There is no access to service telemetry or metrics
- The task is unrelated to service reliability

## Context
The user needs to implement SLOs to establish reliability targets, measure service performance, and make data-driven decisions about reliability vs. feature development. Focus on practical SLO implementation that aligns with business objectives.

## Requirements
$ARGUMENTS

## Instructions

- Clarify goals, constraints, and required inputs.
- Apply relevant best practices and validate outcomes.
- Provide actionable steps and verification.
- If detailed examples are required, open `resources/implementation-playbook.md`.

## Safety

- Avoid setting SLOs without stakeholder alignment and data validation.
- Do not alert on metrics that include sensitive or personal data.

## Resources

- `resources/implementation-playbook.md` for detailed patterns and examples.

---

<!-- AGI-INTEGRATION-START -->

## AGI Framework Integration

> **Adapted for [@techwavedev/agi-agent-kit](https://www.npmjs.com/package/@techwavedev/agi-agent-kit)**
> Original source: [antigravity-awesome-skills](https://github.com/sickn33/antigravity-awesome-skills)

### Memory-First Protocol

Retrieve prior error resolutions and debugging strategies. The hybrid search excels here — BM25 finds exact error codes/stack traces while vectors find semantically similar past issues.

```bash
# Check for prior debugging/diagnostics context before starting
python3 execution/memory_manager.py auto --query "error patterns and debugging solutions for Observability Monitoring Slo Implement"
```

### Storing Results

After completing work, store debugging/diagnostics decisions for future sessions:

```bash
python3 execution/memory_manager.py store \
  --content "Root cause: memory leak from unclosed DB connections in pool — fixed with context manager" \
  --type error --project <project> \
  --tags observability-monitoring-slo-implement debugging
```

### Multi-Agent Collaboration

Store error resolutions so any agent encountering the same issue retrieves the fix instantly instead of re-debugging.

```bash
python3 execution/cross_agent_context.py store \
  --agent "<your-agent>" \
  --action "Debugged and resolved critical issue — root cause documented for future reference" \
  --project <project>
```

### Self-Annealing Loop

When this skill resolves an error, store the fix in memory AND update the relevant directive. The system gets stronger with each resolved issue.

### BM25 Exact Match

Error codes, stack traces, and log messages are best found via BM25 keyword search. The hybrid system automatically uses exact matching for these patterns.

<!-- AGI-INTEGRATION-END -->
