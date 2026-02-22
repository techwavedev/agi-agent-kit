# Scenario 05: Failure Recovery

**Pattern:** `failure-recovery`  
**Tests:** Invalid team ID, malformed payload, then successful re-dispatch

---

## Goal

Validate that the framework handles errors gracefully and recovers — it never crashes silently, always returns structured errors, and allows a re-dispatch after failure without leaving the system in a broken state.

---

## What This Tests

| Test Point | Exit Code | Description |
|---|---|---|
| Invalid team ID | 2 | `dispatch_agent_team.py` returns structured error, exits 2 |
| Malformed JSON payload | 3 | Script returns structured error, exits 3 |
| Recovery re-dispatch | 0 | Valid dispatch after failures succeeds normally |

---

## Run

```bash
python3 execution/run_test_scenario.py --scenario 5
```

---

## Expected Output

```json
{
  "scenario": "scenario_05_failure_recovery",
  "pattern": "failure-recovery",
  "status": "pass",
  "steps": [
    {
      "step": "dispatch invalid team (expect fail)",
      "expected_exit_code": 2,
      "actual_exit_code": 2,
      "pass": true
    },
    {
      "step": "dispatch invalid payload JSON (expect exit 3)",
      "expected_exit_code": 3,
      "actual_exit_code": 3,
      "pass": true
    },
    {
      "step": "recovery: re-dispatch valid request (expect pass)",
      "expected_exit_code": 0,
      "actual_exit_code": 0,
      "pass": true
    }
  ]
}
```

---

## Manual Walkthrough

```bash
# Simulate failure: bad team name
python3 execution/dispatch_agent_team.py \
  --team not_a_real_team \
  --payload '{"changed_files": []}'
# Expected: exit 2, stderr shows structured JSON error with hint

# Simulate failure: broken JSON
python3 execution/dispatch_agent_team.py \
  --team documentation_team \
  --payload '{this is not valid json'
# Expected: exit 3, stderr shows JSON parse error with hint

# Recovery: valid dispatch after failures
python3 execution/dispatch_agent_team.py \
  --team documentation_team \
  --payload '{"changed_files": ["README.md"], "commit_msg": "docs: fix typo", "change_type": "docs"}'
# Expected: exit 0, manifest printed to stdout

# Confirm no state corruption from previous failures
python3 execution/agent_team_result.py --team documentation_team
# Expected: result for the successful (recovery) dispatch only
```

---

## Self-Annealing Principle

This scenario validates the **self-annealing pattern** from `AGENTS.md`:

> Errors are learning opportunities, not failures. When something breaks:
> 1. Read error message and stack trace
> 2. Diagnose root cause
> 3. Fix and retry
> 4. Update directive with what was learned

A well-designed sub-agent or team script should:
- **Never panic** on bad input
- **Always** return structured JSON errors (not raw Python tracebacks)
- **Always** use semantic exit codes so the orchestrator can respond appropriately
