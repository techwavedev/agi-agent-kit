---
name: acceptance-orchestrator
description: Use when a coding task should be driven end-to-end from issue intake through implementation, review, deployment, and acceptance verification with minimal human re-intervention.
risk: safe
source: community
date_added: "2026-03-12"
---

# Acceptance Orchestrator

## Overview

Orchestrate coding work as a state machine that ends only when acceptance criteria are verified with evidence or the task is explicitly escalated.

Core rule: **do not optimize for "code changed"; optimize for "DoD proven".**

## Required Sub-Skills

- `create-issue-gate`
- `closed-loop-delivery`
- `verification-before-completion`

Optional supporting skills:
- `deploy-dev`
- `pr-watch`
- `pr-review-autopilot`
- `git-ship`

## Inputs

Require these inputs:
- issue id or issue body
- issue status
- acceptance criteria (DoD)
- target environment (`dev` default)

Fixed defaults:
- max iteration rounds = `2`
- PR review polling = `3m -> 6m -> 10m`

## State Machine

- `intake`
- `issue-gated`
- `executing`
- `review-loop`
- `deploy-verify`
- `accepted`
- `escalated`

## Workflow

1. **Intake**
   - Read issue and extract task goal + DoD.

2. **Issue gate**
   - Use `create-issue-gate` logic.
   - If issue is not `ready` or execution gate is not `allowed`, stop immediately.
   - Do not implement anything while issue remains `draft`.

3. **Execute**
   - Hand off to `closed-loop-delivery` for implementation and local verification.

4. **Review loop**
   - If PR feedback is relevant, batch polling windows as:
     - wait `3m`
     - then `6m`
     - then `10m`
   - After the `10m` round, stop waiting and process all visible comments together.

5. **Deploy and runtime verification**
   - If DoD depends on runtime behavior, deploy only to `dev` by default.
   - Verify with real logs/API/Lambda behavior, not assumptions.

6. **Completion gate**
   - Before any claim of completion, require `verification-before-completion`.
   - No success claim without fresh evidence.

## Stop Conditions

Move to `accepted` only when every acceptance criterion has matching evidence.

Move to `escalated` when any of these happen:
- DoD still fails after `2` full rounds
- missing secrets/permissions/external dependency blocks progress
- task needs production action or destructive operation approval
- review instructions conflict and cannot both be satisfied

## Human Gates

Always stop for human confirmation on:
- prod/stage deploys beyond agreed scope
- destructive git/data operations
- billing or security posture changes
- missing user-provided acceptance criteria

## Output Contract

When reporting status, always include:
- `Status`: intake / executing / accepted / escalated
- `Acceptance Criteria`: pass/fail checklist
- `Evidence`: commands, logs, API results, or runtime proof
- `Open Risks`: anything still uncertain
- `Need Human Input`: smallest next decision, if blocked

Do not report "done" unless status is `accepted`.

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
  --tags acceptance-orchestrator <relevant-tags>
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
