# Scenario 09: Parallel Subagent Memory Isolation

**Pattern:** `parallel-memory-isolation`
**Script:** `test_qdrant_handoff.py --suite 3`
**Requires:** Qdrant + Ollama running

---

## Goal

Two subagents (`parallel-agent-alpha` and `parallel-agent-beta`) work independently
on the same task. Each stores its own results to Qdrant with a distinct `run_id`.
Verify that:

1. Point IDs assigned by Qdrant do not collide.
2. Each agent can retrieve its own data via a targeted query.

---

## What This Tests

| Test Point | Description |
|---|---|
| Both stores succeed | Each agent's `memory_manager.py store` exits 0 |
| Point ID uniqueness | Two distinct UUIDs returned — no collision in Qdrant |
| Alpha retrieves own data | Query using alpha's `run_id` returns alpha's chunk |
| Beta retrieves own data | Query using beta's `run_id` returns beta's chunk |

---

## Run

```bash
python3 execution/run_test_scenario.py --scenario 9
# or directly:
python3 execution/test_qdrant_handoff.py --suite 3 --verbose
```

---

## Expected Output

```json
{
  "suite": "suite_03_parallel_memory_isolation",
  "status": "pass",
  "steps": [
    { "step": "parallel-agent-alpha stores state", "exit_code": 0, "pass": true },
    { "step": "parallel-agent-beta stores state", "exit_code": 0, "pass": true },
    { "step": "validate point IDs are distinct (no collision)", "pass": true },
    { "step": "parallel-agent-alpha: retrieve own data, check isolation", "own_run_id_found": true, "pass": true },
    { "step": "parallel-agent-beta: retrieve own data, check isolation", "own_run_id_found": true, "pass": true }
  ]
}
```

---

## Notes

- The `other_leaked` field is recorded as a soft signal. Because BM25 + semantic search
  may surface both entries if queries are broad, leakage is logged but does not fail the
  suite. The hard requirement is that **each agent's own data must be findable**.
- For strict isolation guarantees, use Qdrant filter queries scoped by `run_id` tag.
