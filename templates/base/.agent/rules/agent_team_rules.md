---
description: Rules for when and how to trigger agent teams — mandatory for all coding work
---

# 🤖 Agent Team Rules (MANDATORY)

These rules extend the core operating principles in `AGENTS.md`. They apply to **every coding task**.

---

## Rule 1: Documentation Team is Triggered After Every Code Change

**Trigger condition:** Any file write or commit that modifies files in:
- `execution/`
- `skills/`
- `templates/`
- `directives/`
- Any script, module, or configuration that affects agent behaviour

**Required action BEFORE marking the task complete:**

```bash
python3 execution/dispatch_agent_team.py \
  --team documentation_team \
  --payload '{
    "changed_files": ["<list of changed paths>"],
    "commit_msg": "<description of the change>",
    "change_type": "feat|fix|refactor|docs|chore"
  }'
```

Then invoke each sub-agent in the printed manifest in order:
1. `doc-writer` — reads `directives/subagents/doc_writer.md`, updates docs
2. `doc-reviewer` — reads `directives/subagents/doc_reviewer.md`, validates accuracy
3. `changelog-updater` — reads `directives/subagents/changelog_updater.md`, appends to CHANGELOG.md

**A task is NOT complete until the documentation team has run and passed.**

---

## Rule 2: Code Review Team is Used for Implementation Tasks

When a sub-agent (or the primary agent) implements a non-trivial change, the `code_review_team` must be dispatched:

```bash
python3 execution/dispatch_agent_team.py \
  --team code_review_team \
  --payload '{
    "task_spec": "<the original specification>",
    "changed_files": ["<list>"],
    "git_shas": ["<sha>"],
    "task_id": "<identifier>"
  }'
```

Order matters: `spec-reviewer` must pass BEFORE `quality-reviewer` is invoked.

---

## Rule 3: Use Teams for Complex, Multi-Domain Work

| Situation | Pattern | Team |
|---|---|---|
| Sequential coding task | subagent-driven-development | `code_review_team` |
| Multiple independent problems | dispatching-parallel-agents | Multiple dispatches in parallel |
| Any code change | **Always** | `documentation_team` |
| Full release cycle | Full pipeline | `code_review_team` → `documentation_team` → `qa_team` |

---

## Rule 4: Never Skip Team Dispatch Due to Time Pressure

> **"I'll update the docs manually later"** leads to documentation drift.

The documentation team is fast (3 sub-agents, structured flow). There is no valid reason to skip it.

**Only exception:** Change type is `chore` with no functional impact (e.g., renaming a variable in a private function). In this case, only `changelog-updater` is required (skip `doc-writer` + `doc-reviewer`).

---

## Rule 5: Store Team Results to Memory

After each team run, store the result:

```bash
python3 execution/memory_manager.py store \
  --content "<team_id> completed: <commit_msg>. Status: pass/fail. Files updated: <list>" \
  --type decision \
  --tags <team_id> agent-team
```

---

## Verification

To verify team agent rules are being followed in the current session:

```bash
# Check memory for team dispatch records
python3 execution/memory_manager.py auto --query "documentation_team dispatched"

# Check memory usage audit
python3 execution/memory_usage_proof.py --check --since 60
```
