# Scenario 02: Parallel Sub-Agents on Independent Domains

**Pattern:** `dispatching-parallel-agents`  
**Team used:** `documentation_team` (dispatched twice, different domains)  
**Sub-agents:** Two independent `doc-writer` instances

---

## Goal

Validate that the framework supports dispatching multiple agents on independent problem domains simultaneously — each with its own context, run ID, and memory entry.

---

## What This Tests

| Test Point | Description |
|---|---|
| Independent dispatch | Two dispatches of `documentation_team` with different payloads |
| Unique run IDs | Each dispatch gets a unique `run_id` (no collision) |
| Context isolation | Each manifest carries only its own payload |
| No shared state conflict | Both can coexist without interfering |

---

## Run

```bash
python3 execution/run_test_scenario.py --scenario 2
```

---

## Expected Output

```json
{
  "scenario": "scenario_02_parallel_subagents",
  "pattern": "dispatching-parallel-agents",
  "status": "pass",
  "steps": [
    { "step": "dispatch domain_1", "exit_code": 0 },
    { "step": "dispatch domain_2", "exit_code": 0 },
    { "step": "validate parallel dispatches", "run_ids_unique": true }
  ]
}
```

---

## Manual Walkthrough (for human-in-the-loop testing)

1. Identify two independent code changes (e.g., `session_boot.py` and `memory_manager.py`)
2. Dispatch two documentation teams concurrently:

```bash
# Domain 1
python3 execution/dispatch_agent_team.py \
  --team documentation_team \
  --payload '{"changed_files": ["execution/session_boot.py"], "commit_msg": "feat: add auto-fix", "change_type": "feat"}'

# Domain 2 (independent)
python3 execution/dispatch_agent_team.py \
  --team documentation_team \
  --payload '{"changed_files": ["execution/memory_manager.py"], "commit_msg": "fix: empty result", "change_type": "fix"}'
```

3. Verify both manifests have unique `run_id` values
4. Confirm neither manifest contains the other's `changed_files`
5. Invoke both doc-writer sub-agents (they work on different files — no conflict)
