# Scenario 12: state.json Emission

**Pattern:** `state-observability`
**Tests:** Every `dispatch_agent_team.py` invocation writes a `state.json` file at a predictable
path (`.tmp/team-runs/<run_id>/state.json`) and `team_state.py` provides helper subcommands for
reading and updating it.

---

## Goal

Validate that:

1. `dispatch_agent_team.py` creates `.tmp/team-runs/<run_id>/state.json` at dispatch time
2. The state file has the correct schema (`run_id`, `team`, `status`, `sub_agents`, `started_at`, `updated_at`, `total_steps`, …)
3. `python3 execution/team_state.py read --run-id <id>` returns valid JSON matching the file
4. `python3 execution/team_state.py list-active` includes the newly-dispatched run
5. `python3 execution/team_state.py update --run-id <id> --status running --step 0 --agent-id <id> --agent-status running` transitions state correctly
6. The manifest's `state_file` key points to the written path

---

## What This Tests

| Test Point | Expected |
|---|---|
| State file created on dispatch | `.tmp/team-runs/<run_id>/state.json` exists |
| Schema — required keys | `run_id`, `team`, `status`, `sub_agents`, `started_at`, `updated_at`, `total_steps` |
| Initial status | `"pending"` |
| Sub-agent entries | Each has `id`, `status: "pending"`, `started_at: null`, `completed_at: null` |
| Manifest `state_file` key | Matches `.tmp/team-runs/<run_id>/state.json` |
| `team_state.py read` | Returns matching JSON |
| `team_state.py list-active` | Includes the run |
| `team_state.py update` | `status`, `current_step`, and sub-agent entry updated |

---

## Run

```bash
python3 execution/run_test_scenario.py --scenario 12
```

---

## Expected Output

```json
{
  "scenario": "scenario_12_state_json",
  "pattern": "state-observability",
  "status": "pass",
  "steps": [
    { "step": "dispatch documentation_team", "exit_code": 0 },
    { "step": "state.json exists", "pass": true },
    { "step": "validate schema", "pass": true },
    { "step": "team_state read", "pass": true },
    { "step": "team_state list-active", "pass": true },
    { "step": "team_state update", "pass": true }
  ]
}
```

---

## Failure Modes Covered

- **State file missing** — dashboard and cross-agent watchers have nothing to read
- **Wrong schema** — downstream tools receive unexpected field names
- **`list-active` misses active runs** — orchestrator cannot discover in-flight work

---

## Related

- `execution/team_state.py` — read/write helper
- `execution/dispatch_agent_team.py` — emits state on every dispatch
- `execution/session_wrapup.py` — prunes state files older than `TEAM_STATE_PRUNE_DAYS`
- `dashboard/` — HTML dashboard that polls `/api/runs`
