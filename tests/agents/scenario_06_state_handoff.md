# Scenario 06: Dynamic State Handoff via Qdrant

**Pattern:** `state-handoff`
**Team used:** `build_deploy_team`
**Sub-agents:** `asset-compiler` → `cloud-deployer`

---

## Goal

Validate that the framework's `build_deploy_team` dispatch produces a manifest that
explicitly instructs the orchestrator to store and retrieve `handoff_state` via Qdrant
memory — enabling `asset-compiler` to pass its output to `cloud-deployer`.

---

## What This Tests

| Test Point | Description |
|---|---|
| Team dispatch | `dispatch_agent_team.py` correctly reads `build_deploy_team` directive |
| Sub-agent ordering | `asset-compiler` precedes `cloud-deployer` |
| Handoff instructions | Manifest `instructions` field references `handoff_state` and `Qdrant memory` |
| Directive resolution | Both sub-agent directive files are found and linked |

---

## Run

```bash
python3 execution/run_test_scenario.py --scenario 6
```

---

## Expected Output

```json
{
  "scenario": "scenario_06_state_handoff",
  "pattern": "state-handoff",
  "status": "pass",
  "steps": [
    { "step": "dispatch build_deploy_team", "exit_code": 0 },
    { "step": "validate team has compiler and deployer", "pass": true },
    { "step": "validate Qdrant handoff instructions present", "pass": true }
  ]
}
```
