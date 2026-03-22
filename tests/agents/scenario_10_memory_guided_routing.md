# Scenario 10: Memory-Guided Orchestrator Routing

**Pattern:** `memory-guided-routing`
**Script:** `test_qdrant_handoff.py --suite 4`
**Requires:** Qdrant + Ollama running

---

## Goal

Validate that an orchestrator can use Qdrant memory as its decision store for team
routing. The orchestrator:

1. Receives a result from `code_review_team` (PASS).
2. Stores a routing decision in Qdrant: "next team = qa_team".
3. Later queries Qdrant to recall that decision.
4. Dispatches `qa_team` based on the retrieved context — not hardcoded logic.

This tests the memory-first principle: the orchestrator **does not assume** the next
step; it reads it from memory.

---

## What This Tests

| Test Point | Description |
|---|---|
| Routing decision stored | `memory_manager.py store` with decision JSON exits 0 |
| Decision retrievable | Query returns chunk containing `task_id` and `qa_team` |
| Next team extractable | String `qa_team` present in retrieved blob |
| Dispatch succeeds | `dispatch_agent_team.py --team qa_team` (dry-run) exits 0 |

---

## Run

```bash
python3 execution/run_test_scenario.py --scenario 10
# or directly:
python3 execution/test_qdrant_handoff.py --suite 4 --verbose
```

---

## Expected Output

```json
{
  "suite": "suite_04_memory_guided_routing",
  "status": "pass",
  "steps": [
    { "step": "orchestrator stores routing decision", "exit_code": 0, "pass": true },
    {
      "step": "orchestrator retrieves routing decision",
      "decision_found": true,
      "next_team_extractable": true,
      "pass": true
    },
    {
      "step": "dispatch qa_team based on memory-retrieved routing decision",
      "exit_code": 0,
      "team": "qa_team",
      "pass": true
    }
  ]
}
```

---

## Manual Walkthrough

1. Store a routing decision:
   ```bash
   python3 execution/memory_manager.py store \
     --content '{"next_recommended_team":"qa_team","outcome":"PASS"}' \
     --type decision --project my-app --tags routing qa_team
   ```
2. Retrieve it:
   ```bash
   python3 execution/memory_manager.py retrieve \
     --query "next team after code review passed" --top-k 3
   ```
3. Dispatch based on result:
   ```bash
   python3 execution/dispatch_agent_team.py \
     --team qa_team \
     --payload '{"changed_files":["execution/dispatch_agent_team.py"],"test_runner":"pytest"}' \
     --dry-run
   ```
