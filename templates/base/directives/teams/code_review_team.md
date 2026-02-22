# Team Directive: Code Review Team

## Team Identity

| Field       | Value               |
|-------------|---------------------|
| Team ID     | `code_review_team`  |
| Role        | Two-stage code review: spec compliance → quality |
| Trigger     | After implementer sub-agent completes a task |
| Mode        | Sequential |

---

## Goal

Enforce two quality gates after every implementation:
1. **Spec compliance** — does the code match the specification exactly?
2. **Code quality** — is the code well-structured and maintainable?

No implementation is accepted until both reviewers give `✅`.

---

## Sub-Agents (in order)

### 1. `spec-reviewer`
- **Directive:** `directives/subagents/spec_reviewer.md`
- **Role:** Compares implementation against the task specification
- **Checks:** All requirements present? Nothing extra added? Contracts respected?
- **Output:** `✅ compliant` or `❌ gaps: [list]`
- **On failure:** Implementer fixes, spec-reviewer re-checks (max 3 loops)

### 2. `quality-reviewer`
- **Directive:** `directives/subagents/quality_reviewer.md`
- **Role:** Reviews code quality — naming, structure, error handling, tests
- **Runs after:** `spec-reviewer` gives `✅`
- **Output:** `✅ approved` or `❌ issues: [list]` (critical/important/minor)
- **On failure:** Implementer fixes critical/important issues, re-check (minor issues may be noted only)

---

## Inputs

```json
{
  "task_spec": "<full specification text>",
  "changed_files": ["<list of changed file paths>"],
  "git_shas": ["<sha>"],
  "task_id": "<task identifier>"
}
```

---

## Execution Protocol

```
code_review_team
  │
  ├── [1] spec-reviewer
  │     ├── ✅ → proceed to quality-reviewer
  │     └── ❌ → implementer fixes → spec-reviewer re-checks (max 3x)
  │
  └── [2] quality-reviewer
        ├── ✅ → task accepted
        └── ❌ critical/important → implementer fixes → quality-reviewer re-checks
```

---

## Outputs

```json
{
  "team": "code_review_team",
  "run_id": "<uuid>",
  "sub_agents": {
    "spec_reviewer": { "status": "pass", "loops": 1, "notes": "" },
    "quality_reviewer": { "status": "pass", "loops": 1, "issues_noted": [] }
  },
  "overall_status": "pass|fail"
}
```

---

## Edge Cases

- **Spec not provided:** `spec-reviewer` exits with `"status": "blocked"` — escalate to primary agent
- **Max loops reached:** Team fails — escalate to primary agent with full review history
- **Minor quality issues only:** May pass with notes rather than blocking

---

## Memory Integration

```bash
python3 execution/memory_manager.py store \
  --content "code_review_team: task <task_id> reviewed. Result: <status>" \
  --type decision \
  --tags code-review spec-compliance quality-gate
```
