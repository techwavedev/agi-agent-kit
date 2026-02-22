# Scenario 01: Single Sub-Agent with Two-Stage Review

**Pattern:** `subagent-driven-development`  
**Team used:** `code_review_team`  
**Sub-agents:** `spec-reviewer` → `quality-reviewer`

---

## Goal

Validate that the framework correctly dispatches a single implementation cycle:
- Implementer sub-agent completes a task
- Spec-reviewer validates compliance
- Quality-reviewer validates code quality
- Both must pass before proceeding

---

## What This Tests

| Test Point | Description |
|---|---|
| Team dispatch | `dispatch_agent_team.py` correctly reads `code_review_team` directive |
| Sub-agent extraction | Both `spec-reviewer` and `quality-reviewer` appear in the manifest |
| Sequential ordering | Spec review appears before quality review |
| Directive resolution | Both sub-agent directive files are found and linked |
| Manifest structure | `run_id`, `team`, `sub_agents`, `payload` all present |

---

## Run

```bash
python3 execution/run_test_scenario.py --scenario 1
```

---

## Expected Output

```json
{
  "scenario": "scenario_01_single_subagent",
  "pattern": "subagent-driven-development",
  "status": "pass",
  "steps": [
    { "step": "dispatch code_review_team", "exit_code": 0 },
    { "step": "validate manifest", "pass": true, "sub_agents_found": 2 }
  ]
}
```

---

## Manual Walkthrough (for human-in-the-loop testing)

1. Read `directives/teams/code_review_team.md`
2. Understand the two sub-agents and their order
3. Simulate implementing a feature (e.g., adding a flag to a script)
4. Dispatch: `python3 execution/dispatch_agent_team.py --team code_review_team --payload '{"task_spec": "Add --dry-run flag","changed_files":["execution/dispatch_agent_team.py"],"git_shas":["abc1234"],"task_id":"manual-01"}'`
5. Read the manifest — confirm `spec-reviewer` and `quality-reviewer` are listed in that order
6. Invoke each sub-agent using their directives in `directives/subagents/`
7. Verify the sequence: spec reviewer must pass before quality reviewer runs
