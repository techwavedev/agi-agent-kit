# Scenario 08: Cross-Subagent Handoff Persistence

**Pattern:** `cross-agent-handoff`
**Script:** `test_qdrant_handoff.py --suite 2`
**Requires:** Qdrant + Ollama running

---

## Goal

Validate the Dynamic State Handoff protocol from `AGENTS.md`. Agent A completes its
work and writes a structured `handoff_state` object to Qdrant. Agent B then queries
Qdrant and must recover all three required fields:

| Field | Purpose |
|---|---|
| `state` | Data / file paths produced by Agent A |
| `next_steps` | Explicit instructions for Agent B |
| `validation_requirements` | Commands Agent B must run to verify Agent A's work |

---

## What This Tests

| Test Point | Description |
|---|---|
| Agent A store | `memory_manager.py store` with handoff_state JSON exits 0 |
| Agent B retrieval | Semantic query returns chunk containing the run_id fingerprint |
| Field completeness | All three required handoff fields present in retrieved blob |
| No shared context needed | Agent B requires only the Qdrant query — no direct IPC |

---

## Run

```bash
python3 execution/run_test_scenario.py --scenario 8
# or directly:
python3 execution/test_qdrant_handoff.py --suite 2 --verbose
```

---

## Expected Output

```json
{
  "suite": "suite_02_cross_agent_handoff",
  "status": "pass",
  "steps": [
    { "step": "agent-a stores handoff_state", "exit_code": 0, "pass": true },
    { "step": "agent-b retrieves handoff_state", "handoff_found": true, "pass": true },
    {
      "step": "validate handoff_state fields (state, next_steps, validation_requirements)",
      "has_state": true,
      "has_next_steps": true,
      "has_validation_requirements": true,
      "pass": true
    }
  ]
}
```

---

## Manual Walkthrough

1. Run `python3 execution/memory_manager.py store` manually with a JSON blob containing
   `state`, `next_steps`, and `validation_requirements`.
2. Query with `python3 execution/memory_manager.py retrieve --query "<your probe>"`.
3. Confirm all three fields appear in the returned `context_chunks`.
