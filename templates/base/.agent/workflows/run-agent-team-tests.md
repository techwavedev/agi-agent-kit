---
description: Run all sub-agent and team agent test scenarios to validate full framework support
---

# Workflow: Run Agent Team Tests

Use this workflow to run all 5 test scenarios that validate sub-agent and team agent functionality.

## Prerequisites

Ensure the session is booted and memory is ready:
```bash
python3 execution/session_boot.py --auto-fix
```

## Steps

1. **Validate setup** — check all directives and scripts are in place
```bash
python3 execution/run_test_scenario.py --scenario 1 --dry-run
```

// turbo
2. **Scenario 1** — Single sub-agent with two-stage review
```bash
python3 execution/run_test_scenario.py --scenario 1
```

// turbo
3. **Scenario 2** — Parallel sub-agents on independent domains
```bash
python3 execution/run_test_scenario.py --scenario 2
```

// turbo
4. **Scenario 3** — Documentation team triggered on code change *(primary pattern)*
```bash
python3 execution/run_test_scenario.py --scenario 3
```

// turbo
5. **Scenario 4** — Full team pipeline (review → docs → QA)
```bash
python3 execution/run_test_scenario.py --scenario 4
```

// turbo
6. **Scenario 5** — Failure recovery
```bash
python3 execution/run_test_scenario.py --scenario 5
```

// turbo
7. **Run all scenarios at once** *(shortcut for steps 2–6)*
```bash
python3 execution/run_test_scenario.py --all
```

8. **Check memory usage was recorded**
```bash
python3 execution/memory_usage_proof.py --check --since 60
```

## Interpreting Results

| Status | Meaning |
|--------|---------|
| `"overall_status": "pass"` | All scenarios passed ✅ |
| `"overall_status": "fail"` | One or more scenarios failed ❌ |
| Exit code `0` | All pass |
| Exit code `3` | One or more scenarios failed |

## After Running Tests

If all pass — the framework **fully supports sub-agents and team agents**. 

If a scenario fails:
1. Read the `steps` array in the JSON output to find the failing step
2. Check the referenced directive or script
3. Fix the issue
4. Re-run the failing scenario
5. Store the fix to memory:
```bash
python3 execution/memory_manager.py store \
  --content "Fixed scenario <N>: <what was wrong and how it was fixed>" \
  --type error \
  --tags agent-team-tests sub-agents
```
