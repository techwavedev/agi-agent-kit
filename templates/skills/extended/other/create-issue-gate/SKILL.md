---
name: create-issue-gate
description: Use when starting a new implementation task and an issue must be created with strict acceptance criteria gating before execution.
risk: safe
source: community
date_added: "2026-03-12"
---

# Create Issue Gate

## Overview

Create GitHub issues as the single tracking entrypoint for tasks, with a hard gate on acceptance criteria.

Core rule: **no explicit, testable acceptance criteria from user => issue stays `draft` and execution is blocked.**

## Required Fields

Every issue must include these sections:
- Problem
- Goal
- Scope
- Non-Goals
- Acceptance Criteria
- Dependencies/Blockers
- Status (`draft` | `ready` | `blocked` | `done`)

## Acceptance Criteria Gate

Acceptance criteria are valid only when they are testable and pass/fail checkable.

Examples:
- valid: "CreateCheckoutLambda-dev returns an openable third-party payment checkout URL"
- invalid: "fix checkout" / "improve UX" / "make it better"

If criteria are missing or non-testable:
- still create the issue
- set `Status: draft`
- add `Execution Gate: blocked (missing valid acceptance criteria)`
- do not move task to execution

## Issue Creation Mode

Default mode is direct GitHub creation using `gh issue create`.

Use a body template like:

```md
## Problem
<what is broken or missing>

## Goal
<what outcome is expected>

## Scope
- <in scope item>

## Non-Goals
- <out of scope item>

## Acceptance Criteria
- <explicit, testable criterion 1>

## Dependencies/Blockers
- <dependency or none>

## Status
draft|ready|blocked|done

## Execution Gate
allowed|blocked (<reason>)
```

## Status Rules

- `draft`: missing/weak acceptance criteria or incomplete task definition
- `ready`: acceptance criteria are explicit and testable
- `blocked`: external dependency prevents progress
- `done`: acceptance criteria verified with evidence

Never mark an issue `ready` without valid acceptance criteria.

## Handoff to Execution

Execution workflows (for example `closed-loop-delivery`) may start only when:
- issue status is `ready`
- execution gate is `allowed`

If issue is `draft`, stop and request user-provided acceptance criteria.

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
  --tags create-issue-gate <relevant-tags>
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
