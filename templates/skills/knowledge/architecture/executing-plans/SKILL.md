---
name: executing-plans
description: Structured plan execution with batch checkpoints or subagent-per-task with two-stage review. Use when you have a written implementation plan to execute methodically.
version: 1.0.0
---

# Executing Plans

> Adapted from obra/superpowers — fitted to the agi multi-platform architecture.

## Overview

Load a plan, review it critically, then execute tasks using one of two strategies. Report for review between batches.

**Core principle:** Batch execution with quality gates. Never skip verification.

---

## When to Use

| Scenario                                  | Strategy                                                |
| ----------------------------------------- | ------------------------------------------------------- |
| Have a plan, tasks are mostly independent | **Subagent-Driven** (two-stage review per task)         |
| Have a plan, prefer human checkpoints     | **Batch Execution** (3 tasks at a time, review between) |
| No plan exists                            | STOP → Use `plan-writing` skill first                   |

---

## The Process

### Step 1: Load and Review Plan

1. Read the plan file
2. Review critically — identify questions or concerns
3. If concerns: **Raise them with the user before starting**
4. If clear: Create task tracker and proceed

> 🔴 **VIOLATION:** Starting execution with unresolved questions = failed execution.

### Step 2: Choose Execution Mode

**Option A — Batch Execution (human checkpoints):**

- Execute first 3 tasks
- Report what was done + verification output
- Wait for feedback → apply changes → next batch
- Best for: high-risk changes, unfamiliar codebases

**Option B — Subagent-Driven (two-stage review):**

- Fresh context per task (no context pollution)
- Implementer → Spec Reviewer → Code Quality Reviewer chain
- Faster iteration, review is automated
- Best for: independent tasks, well-defined plan

### Step 3: Execute Tasks

**For each task:**

1. Mark as `[/]` in-progress
2. Follow each step exactly (plan has granular steps)
3. Run verifications as specified in the plan
4. Mark as `[x]` completed

### Step 4: Report (Batch Mode)

After each batch of 3 tasks:

```markdown
## Batch N Complete

### Implemented

- Task X: [what was done]
- Task Y: [what was done]
- Task Z: [what was done]

### Verification Output

[Paste actual command output]

### Status

Ready for feedback.
```

### Step 5: Complete Development

After all tasks complete and verified:

- Run full verification suite (`verify_all.py` or project test suite)
- Use `verification-before-completion` skill before claiming done
- Present summary and next steps

---

## Two-Stage Review Protocol (Subagent-Driven Mode)

For each task, three roles execute in sequence:

### 1. Implementer

- Reads the task from the plan (full task text provided, never the plan file)
- Asks clarifying questions if anything is unclear
- Implements following TDD: write test → verify fail → implement → verify pass → commit
- Self-reviews before handoff

### 2. Spec Compliance Reviewer

Reviews against the plan requirements:

| Check                         | Pass | Fail                          |
| ----------------------------- | ---- | ----------------------------- |
| All requirements implemented? | ✅   | ❌ List missing items         |
| Nothing extra added?          | ✅   | ❌ List additions not in spec |
| Tests cover the requirement?  | ✅   | ❌ List gaps                  |

**If issues found:** Implementer fixes → re-review until ✅

### 3. Code Quality Reviewer

Reviews implementation quality:

| Check                                  | Pass | Fail                  |
| -------------------------------------- | ---- | --------------------- |
| Clean, readable code?                  | ✅   | ❌ List issues        |
| No magic numbers, good naming?         | ✅   | ❌ List specifics     |
| Edge cases handled?                    | ✅   | ❌ List missing cases |
| Tests are meaningful (not mock-heavy)? | ✅   | ❌ List concerns      |

**If issues found:** Implementer fixes → re-review until ✅

> 🔴 **Order matters:** Spec compliance FIRST, then code quality. Never reverse.

---

## Red Flags — STOP Immediately

- Starting implementation on main/master without user consent
- Skipping either review stage (spec OR quality)
- Proceeding with unfixed issues
- Guessing when blocked instead of asking
- Making the implementer read the full plan file (provide task text directly)
- Accepting "close enough" on spec compliance
- Moving to next task with open review issues

---

## When to Stop and Ask

**STOP executing when:**

- Hit a blocker mid-batch (missing dependency, test fails, instruction unclear)
- Plan has critical gaps preventing progress
- You don't understand an instruction
- Verification fails repeatedly (3+ times → question architecture)

**Ask for clarification rather than guessing.**

---

## Platform Adaptation

| Platform                      | Subagent-Driven                       | Batch Execution                   |
| ----------------------------- | ------------------------------------- | --------------------------------- |
| **Claude Code** (Agent Teams) | Teammates as implementer/reviewers    | Lead executes batches             |
| **Claude Code** (Subagents)   | `Task()` tool for each role           | Direct execution with checkpoints |
| **Gemini / Antigravity**      | Sequential persona switching per role | Direct execution with checkpoints |
| **Kiro IDE**                  | Autonomous agent tasks                | Direct execution with PR reviews  |

---

## Integration

| Skill                            | Relationship                         |
| -------------------------------- | ------------------------------------ |
| `plan-writing`                   | Creates the plan this skill executes |
| `test-driven-development`        | TDD cycle used by implementers       |
| `verification-before-completion` | Gate before claiming tasks complete  |
| `parallel-agents`                | Platform detection for subagent mode |
| `brainstorming`                  | Design phase before plan creation    |

## AGI Framework Integration

### Qdrant Memory Integration

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
  --tags executing-plans <relevant-tags>
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
