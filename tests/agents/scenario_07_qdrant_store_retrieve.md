# Scenario 07: Qdrant Store/Retrieve Round-Trip

**Pattern:** `qdrant-memory-fidelity`
**Script:** `test_qdrant_handoff.py --suite 1`
**Requires:** Qdrant + Ollama running

---

## Goal

Establish baseline memory correctness: content stored by an agent is retrievable
verbatim. A unique probe token is stored, then a semantic query is used to retrieve
it. The probe token must appear in the returned `context_chunks`.

---

## What This Tests

| Test Point | Description |
|---|---|
| Store exit code | `memory_manager.py store` exits 0 |
| Point ID returned | Store response contains a non-null `id` / `point_id` |
| Retrieve finds probe | Semantic query for the probe token returns a chunk containing it |
| No silent failures | Every step is auditable via structured JSON |

---

## Run

```bash
python3 execution/run_test_scenario.py --scenario 7
# or directly:
python3 execution/test_qdrant_handoff.py --suite 1 --verbose
```

---

## Expected Output

```json
{
  "suite": "suite_01_store_retrieve_round_trip",
  "status": "pass",
  "steps": [
    { "step": "store probe content", "exit_code": 0, "pass": true },
    { "step": "retrieve probe content", "probe_found_in_results": true, "pass": true },
    { "step": "validate point id returned by store", "pass": true }
  ]
}
```

---

## Notes

- Each run generates a fresh UUID probe token to avoid false positives from previous test runs.
- BM25 hybrid search improves recall but requires the BM25 index to be populated.
- If Qdrant is unavailable, the test runner exits with code 2 (not 3).
