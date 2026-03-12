---
name: infinite-gratitude
description: "Multi-agent research skill for parallel research execution (10 agents, battle-tested with real case studies)."
risk: safe
source: "https://github.com/sstklen/infinite-gratitude"
date_added: "2026-02-27"
---

# Infinite Gratitude

> **Source**: [sstklen/infinite-gratitude](https://github.com/sstklen/infinite-gratitude)

## Description

A multi-agent research skill designed for parallel research execution. It orchestrates 10 agents to conduct deep research, battle-tested with real case studies.

## When to Use

Use this skill when you need to perform extensive, parallelized research on a topic, leveraging multiple agents to gather and synthesize information more efficiently than a single linear process.

## How to Use

This is an external skill. Please refer to the [official repository](https://github.com/sstklen/infinite-gratitude) for installation and usage instructions.

```bash
git clone https://github.com/sstklen/infinite-gratitude
```

---

<!-- AGI-INTEGRATION-START -->

## AGI Framework Integration

> **Adapted for [@techwavedev/agi-agent-kit](https://www.npmjs.com/package/@techwavedev/agi-agent-kit)**
> Original source: [antigravity-awesome-skills](https://github.com/sickn33/antigravity-awesome-skills)

### Memory-First Protocol

Retrieve prior test strategies, known flaky tests, and coverage gaps. Cache test infrastructure setup to avoid re-configuring test environments.

```bash
# Check for prior testing/QA context before starting
python3 execution/memory_manager.py auto --query "test patterns and coverage strategies for Infinite Gratitude"
```

### Storing Results

After completing work, store testing/QA decisions for future sessions:

```bash
python3 execution/memory_manager.py store \
  --content "Testing strategy: integration tests hit real DB (no mocks), 85% line coverage, mutation testing on critical paths" \
  --type technical --project <project> \
  --tags infinite-gratitude testing
```

### Multi-Agent Collaboration

Share test results and coverage reports with code review agents so they can verify adequate coverage on changed code.

```bash
python3 execution/cross_agent_context.py store \
  --agent "<your-agent>" \
  --action "QA complete — test suite expanded with 12 new integration tests, all passing" \
  --project <project>
```

### TDD Enforcement

This skill integrates with the framework's iron-law RED-GREEN-REFACTOR cycle. No production code without a failing test first.

### Agent Team: QA

Dispatch `qa_team` to generate tests and verify they pass before marking implementation complete.

<!-- AGI-INTEGRATION-END -->
