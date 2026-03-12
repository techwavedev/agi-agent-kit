# Team Directive: Documentation Team

> **Trigger:** Every time code changes touch `execution/`, `skills/`, `templates/`, or `directives/`, this team MUST be dispatched before the task is marked complete.

## Team Identity

| Field       | Value                |
|-------------|----------------------|
| Team ID     | `documentation_team` |
| Role        | Keep documentation in sync with code at all times |
| Trigger     | Code change (automatic) |
| Mode        | Sequential (reviewer depends on writer's output) |

---

## Goal

Ensure documentation always reflects the current state of the codebase. No code change is considered complete until the documentation team has run and passed.

---

## Sub-Agents (in order)

### 1. `doc-writer`
- **Directive:** `directives/subagents/doc_writer.md`
- **Role:** Reads changed files, creates or updates relevant documentation
- **Output:** Updated or created markdown files in `docs/`

### 2. `doc-reviewer`
- **Directive:** `directives/subagents/doc_reviewer.md`
- **Role:** Validates documentation accuracy against actual code
- **Output:** Approval (`✅`) or list of gaps (`❌`) to fix
- **On failure:** `doc-writer` must fix gaps, then `doc-reviewer` checks again (max 2 loops)

### 3. `changelog-updater`
- **Directive:** `directives/subagents/changelog_updater.md`
- **Role:** Appends a new entry to `CHANGELOG.md` for this change
- **Output:** Updated `CHANGELOG.md` with dated entry
- **Runs after:** `doc-reviewer` gives `✅` approval

---

## Inputs

```json
{
  "changed_files": ["<list of changed file paths>"],
  "commit_msg": "<short description of the change>",
  "change_type": "feat|fix|refactor|docs|chore"
}
```

---

## Execution Protocol

```
dispatch_agent_team.py --team documentation_team --payload <json>
  │
  ├── [1] doc-writer runs
  │     └── reads changed_files → updates/creates docs
  │
  ├── [2] doc-reviewer runs
  │     ├── ✅ approved → proceed
  │     └── ❌ gaps found → doc-writer re-runs (loop, max 2x)
  │
  └── [3] changelog-updater runs
        └── appends entry to CHANGELOG.md
```

---

## Outputs

```json
{
  "team": "documentation_team",
  "run_id": "<uuid>",
  "status": "pass|fail",
  "sub_agents": {
    "doc_writer": { "status": "pass", "files_updated": [] },
    "doc_reviewer": { "status": "pass", "loops": 1 },
    "changelog_updater": { "status": "pass", "entry": "<text>" }
  },
  "overall_status": "pass|fail"
}
```

---

## Edge Cases

- **No docs directory exists:** `doc-writer` creates `docs/` automatically
- **CHANGELOG.md missing:** `changelog-updater` creates it with standard header
- **Reviewer loops > 2:** Team fails with `"status": "fail"` — escalate to the primary agent
- **Changed files are purely tests:** Skip `doc-writer`, only run `changelog-updater`

---

## Memory Integration

```bash
# Read shared context before starting
python3 execution/memory_manager.py auto --query "documentation_team <commit_msg>"

# Store results after completion
python3 execution/memory_manager.py store \
  --content "documentation_team run: <commit_msg>. Files updated: <list>" \
  --type decision \
  --tags documentation_team doc-automation
```
