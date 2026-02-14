---
name: plan-writing
description: Structured task planning with clear breakdowns, dependencies, and verification criteria. Use when implementing features, refactoring, or any multi-step work.
allowed-tools: Read, Glob, Grep
---

# Plan Writing

> Source: obra/superpowers

## Overview

This skill provides a framework for breaking down work into clear, actionable tasks with verification criteria.

## Task Breakdown Principles

### 1. Small, Focused Tasks

- Each task should take 2-5 minutes
- One clear outcome per task
- Independently verifiable

### 2. Clear Verification

- How do you know it's done?
- What can you check/test?
- What's the expected output?

### 3. Logical Ordering

- Dependencies identified
- Parallel work where possible
- Critical path highlighted
- **Phase X: Verification is always LAST**

### 4. Dynamic Naming in Project Root

- Plan files are saved as `{task-slug}.md` in the PROJECT ROOT
- Name derived from task (e.g., "add auth" → `auth-feature.md`)
- **NEVER** inside `.claude/`, `docs/`, or temp folders

## Planning Principles (NOT Templates!)

> 🔴 **NO fixed templates. Each plan is UNIQUE to the task.**

### Principle 1: Keep It SHORT

| ❌ Wrong                    | ✅ Right              |
| --------------------------- | --------------------- |
| 50 tasks with sub-sub-tasks | 5-10 clear tasks max  |
| Every micro-step listed     | Only actionable items |
| Verbose descriptions        | One-line per task     |

> **Rule:** If plan is longer than 1 page, it's too long. Simplify.

---

### Principle 2: Be SPECIFIC, Not Generic

| ❌ Wrong             | ✅ Right                                                 |
| -------------------- | -------------------------------------------------------- |
| "Set up project"     | "Run `npx create-next-app`"                              |
| "Add authentication" | "Install next-auth, create `/api/auth/[...nextauth].ts`" |
| "Style the UI"       | "Add Tailwind classes to `Header.tsx`"                   |

> **Rule:** Each task should have a clear, verifiable outcome.

---

### Principle 3: Dynamic Content Based on Project Type

**For NEW PROJECT:**

- What tech stack? (decide first)
- What's the MVP? (minimal features)
- What's the file structure?

**For FEATURE ADDITION:**

- Which files are affected?
- What dependencies needed?
- How to verify it works?

**For BUG FIX:**

- What's the root cause?
- What file/line to change?
- How to test the fix?

---

### Principle 4: Scripts Are Project-Specific

> 🔴 **DO NOT copy-paste script commands. Choose based on project type.**

| Project Type   | Relevant Scripts                          |
| -------------- | ----------------------------------------- |
| Frontend/React | `ux_audit.py`, `accessibility_checker.py` |
| Backend/API    | `api_validator.py`, `security_scan.py`    |
| Mobile         | `mobile_audit.py`                         |
| Database       | `schema_validator.py`                     |
| Full-stack     | Mix of above based on what you touched    |

**Wrong:** Adding all scripts to every plan
**Right:** Only scripts relevant to THIS task

---

### Principle 5: Verification is Simple

| ❌ Wrong                               | ✅ Right                                      |
| -------------------------------------- | --------------------------------------------- |
| "Verify the component works correctly" | "Run `npm run dev`, click button, see toast"  |
| "Test the API"                         | "curl localhost:3000/api/users returns 200"   |
| "Check styles"                         | "Open browser, verify dark mode toggle works" |

---

## Plan Structure (Flexible, Not Fixed!)

```
# [Task Name]

## Goal
One sentence: What are we building/fixing?

## Tasks
- [ ] Task 1: [Specific action] → Verify: [How to check]
- [ ] Task 2: [Specific action] → Verify: [How to check]
- [ ] Task 3: [Specific action] → Verify: [How to check]

## Done When
- [ ] [Main success criteria]
```

> **That's it.** No phases, no sub-sections unless truly needed.
> Keep it minimal. Add complexity only when required.

## Notes

[Any important considerations]

````

---

## Bite-Sized Task Granularity (TDD Steps)

> Adapted from obra/superpowers — each step is one action (2-5 minutes).

When the project has testable code, structure each task with TDD steps:

```markdown
### Task N: [Component Name]

**Files:**
- Create: `exact/path/to/file.ext`
- Modify: `exact/path/to/existing.ext`
- Test: `tests/exact/path/to/test.ext`

**Step 1: Write the failing test**
[Complete test code]

**Step 2: Run test to verify it fails**
Run: [exact command]
Expected: FAIL with "[reason]"

**Step 3: Write minimal implementation**
[Complete implementation code]

**Step 4: Run test to verify it passes**
Run: [exact command]
Expected: PASS

**Step 5: Commit**
git add [files] && git commit -m "feat: [description]"
````

> 🔴 **Not every task needs TDD steps.** Config changes, setup tasks, and non-code tasks can use simpler step structure.

---

## Execution Handoff

After saving the plan, offer execution choice:

**"Plan complete. Two execution options:**

**1. Subagent-Driven** — Fresh agent per task, two-stage review (spec compliance + code quality), fast iteration

**2. Batch Execution** — Execute 3 tasks at a time, report for human review between batches

**Which approach?"**

Both options use the `executing-plans` skill for structured execution.

---

## Best Practices (Quick Reference)

1. **Start with goal** - What are we building/fixing?
2. **Max 10 tasks** - If more, break into multiple plans
3. **Each task verifiable** - Clear "done" criteria
4. **Project-specific** - No copy-paste templates
5. **Update as you go** - Mark `[x]` when complete
6. **TDD when testable** - Use red-green-refactor step structure
7. **Complete code in plan** - Not "add validation" but the actual code

---

## When to Use

- New project from scratch
- Adding a feature
- Fixing a bug (if complex)
- Refactoring multiple files

---

## Integration

| Skill                            | Relationship                         |
| -------------------------------- | ------------------------------------ |
| `brainstorming`                  | Design phase before plan creation    |
| `executing-plans`                | Executes the plan this skill creates |
| `test-driven-development`        | TDD cycle referenced in task steps   |
| `verification-before-completion` | Gate before marking plan complete    |
