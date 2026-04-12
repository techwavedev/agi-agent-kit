# Scenario 11: Output Gates (Bash Validation)

**Pattern:** `output-gate`
**Tests:** Sub-agents with an `## Output Gate` section emit a hallucination-proof bash gate in the dispatch manifest; the orchestrator is instructed to run it and trust stdout over self-reports.

---

## Goal

Validate that `dispatch_agent_team.py`:

1. Parses the optional `## Output Gate` section from a sub-agent directive
2. Emits a `validation_gate` entry in the manifest with a bash command that prints `VALIDATION:PASS` or `VALIDATION:FAIL:<path>`
3. Resolves `{{run_id}}` and `{{payload.<key>}}` placeholders
4. Updates the orchestrator instructions to mandate running the gate before advancing

This closes a known failure mode: LLM orchestrators fabricate success reports when sub-agents produce empty or missing outputs. The gate is deterministic bash — no LLM judgment, no hallucination surface.

---

## What This Tests

| Test Point | Expected |
|---|---|
| Directive without `## Output Gate` | Manifest entry has NO `validation_gate` key |
| Directive with `## Output Gate` | Manifest entry has `validation_gate.command` + `output_files` + `on_fail` |
| Placeholder substitution | `{{run_id}}` and `{{payload.key}}` resolved in `output_files` |
| Gate command (PASS) | `bash -c "<command>"` exits 0 and prints `VALIDATION:PASS` when file exists |
| Gate command (FAIL) | `bash -c "<command>"` exits 1 and prints `VALIDATION:FAIL:<path>` when file missing |
| Orchestrator instructions | Reference `validation_gate.command`, "VALIDATION:PASS", retry-once-then-user pattern |

---

## Run

```bash
# Sequential dispatch using the documentation_team (changelog-updater declares a gate)
python3 execution/dispatch_agent_team.py \
  --team documentation_team \
  --payload '{"changed_files":["execution/dispatch_agent_team.py"],"commit_msg":"test","change_type":"test"}' \
  --dry-run | python3 -c "
import json, sys, subprocess
m = json.load(sys.stdin)
gated = [sa for sa in m['sub_agents'] if 'validation_gate' in sa]
assert gated, 'expected at least one sub-agent with a validation_gate'
cmd = gated[0]['validation_gate']['command']
rc = subprocess.run(['bash','-c', cmd], capture_output=True, text=True)
assert 'VALIDATION:PASS' in rc.stdout or 'VALIDATION:FAIL' in rc.stdout
print('OK')
"
```

---

## Expected Output

```
OK
```

Exit code `0` means:
- The manifest exposes gated sub-agents correctly
- The emitted bash command is syntactically valid and emits a recognizable verdict

---

## Failure Modes Covered

- **Fabricated success** — Orchestrator can no longer claim a sub-agent succeeded if `test -s` reports otherwise
- **Missing outputs** — Empty or non-existent files fail the gate loudly with the exact path
- **Retry-once-then-escalate** — Gate failure forces a deterministic retry → user prompt path, not silent skipping

---

## Related

- `execution/dispatch_agent_team.py` — `parse_output_gate`, `build_validation_gate`, `substitute_gate_placeholders`
- `directives/subagents/changelog_updater.md` — first sub-agent to declare an `## Output Gate`
- Inspired by `opensquad` `docs/superpowers/specs/2026-03-27-pipeline-bash-gates-design.md`
