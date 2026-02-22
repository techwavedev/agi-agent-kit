# Scenario 03: Documentation Team Triggered on Code Change

**Pattern:** `doc-team-on-code` ← **Primary use case**  
**Team used:** `documentation_team`  
**Sub-agents:** `doc-writer` → `doc-reviewer` → `changelog-updater`

---

## Goal

Validate the core pattern: every coding action that changes `execution/`, `skills/`, `templates/`, or `directives/` must automatically trigger the documentation team. This ensures docs never go stale.

---

## What This Tests

| Test Point | Description |
|---|---|
| Team trigger on code change | `documentation_team` dispatched when code files change |
| All 3 sub-agents present | `doc-writer`, `doc-reviewer`, `changelog-updater` in manifest |
| Sub-agent directives exist | All directive files found on disk |
| Correct execution order | Sequential: writer → reviewer → changelog |
| Payload carries context | `changed_files`, `commit_msg`, `change_type` passed through |

---

## Run

```bash
python3 execution/run_test_scenario.py --scenario 3
```

---

## Expected Output

```json
{
  "scenario": "scenario_03_doc_team_on_code",
  "pattern": "doc-team-on-code",
  "status": "pass",
  "steps": [
    { "step": "trigger documentation_team on code change", "exit_code": 0 },
    {
      "step": "validate team has all 3 documentation sub-agents",
      "expected": ["doc-writer", "doc-reviewer", "changelog-updater"],
      "found": ["doc-writer", "doc-reviewer", "changelog-updater"],
      "pass": true
    },
    {
      "step": "validate all sub-agent directives exist",
      "pass": true
    }
  ]
}
```

---

## Manual Walkthrough (the full pattern)

This is the scenario to run whenever you make a code change to validate the framework is working:

```bash
# 1. Make a code change (example: edit session_boot.py)

# 2. Trigger doc team — this is what should happen automatically per agent_team_rules.md
python3 execution/dispatch_agent_team.py \
  --team documentation_team \
  --payload '{
    "changed_files": ["execution/session_boot.py"],
    "commit_msg": "feat: add --auto-fix flag to session boot",
    "change_type": "feat"
  }'

# 3. Read the manifest — invoke doc-writer:
#    Read directives/subagents/doc_writer.md
#    → Read execution/session_boot.py
#    → Update or create docs/execution/session_boot.md

# 4. Invoke doc-reviewer:
#    Read directives/subagents/doc_reviewer.md
#    → Compare doc vs code → output ✅ or ❌ with gaps

# 5. If gaps found → doc-writer fixes → doc-reviewer re-checks (max 2 loops)

# 6. Once ✅, invoke changelog-updater:
#    Read directives/subagents/changelog_updater.md
#    → Append to CHANGELOG.md under [Unreleased] > Added

# 7. Check results:
python3 execution/agent_team_result.py --team documentation_team
```

---

## Why This Matters

Without this pattern:
- Docs drift from code silently
- CHANGELOG goes stale
- Next developer (or agent) has wrong context

With this pattern:
- Documentation is **a side effect of coding** — automatic, not optional
- Every commit is self-documenting
- Memory system stays accurate for future agent sessions
