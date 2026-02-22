# Team Directive: QA Team

## Team Identity

| Field       | Value       |
|-------------|-------------|
| Team ID     | `qa_team`   |
| Role        | Generate tests for new code, then run and verify them |
| Trigger     | After both code_review_team passes |
| Mode        | Sequential |

---

## Goal

Ensure every code change has test coverage verified by an independent sub-agent.

---

## Sub-Agents (in order)

### 1. `test-generator`
- **Directive:** `directives/subagents/test_generator.md`
- **Role:** Analyses changed files and generates or updates unit/integration tests
- **Output:** Test files written to appropriate test directory
- **Convention:** Follow existing test naming patterns in the project

### 2. `test-verifier`
- **Directive:** `directives/subagents/test_verifier.md`
- **Role:** Runs the generated tests and reports results
- **Output:** Structured JSON with pass/fail counts and any failure details

---

## Inputs

```json
{
  "changed_files": ["<list of changed file paths>"],
  "task_spec": "<original task spec>",
  "test_runner": "pytest|jest|node"
}
```

---

## Execution Protocol

```
qa_team
  │
  ├── [1] test-generator
  │     └── writes test files
  │
  └── [2] test-verifier
        ├── ✅ all pass → QA done
        └── ❌ failures → test-generator fixes tests or flags spec ambiguity
```

---

## Outputs

```json
{
  "team": "qa_team",
  "run_id": "<uuid>",
  "sub_agents": {
    "test_generator": { "status": "pass", "test_files": [] },
    "test_verifier": { "status": "pass", "passed": 0, "failed": 0, "skipped": 0 }
  },
  "overall_status": "pass|fail"
}
```

---

## Edge Cases

- **No test framework detected:** `test-generator` defaults to Python `unittest`
- **Tests fail due to missing dependency:** `test-verifier` escalates, does not loop
- **Changed file is documentation only:** QA team is skipped

---

## Memory Integration

```bash
python3 execution/memory_manager.py store \
  --content "qa_team: <changed_files> tested. Passed: <n>, Failed: <n>" \
  --type decision \
  --tags qa-team testing coverage
```
