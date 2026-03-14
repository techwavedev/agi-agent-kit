# Sub-Agent Directive: changelog-updater

## Identity

| Field      | Value                 |
|------------|-----------------------|
| Sub-agent  | `changelog-updater`   |
| Team       | `documentation_team`  |
| Invoked by | Team orchestrator after `doc-reviewer` gives ✅ |

---

## Goal

Append a new, well-formatted entry to `CHANGELOG.md` describing the current change. Entries must follow the existing CHANGELOG format precisely.

---

## Inputs

| Name            | Type   | Required | Description |
|-----------------|--------|----------|-------------|
| `commit_msg`    | string | ✅       | Short description of the change |
| `change_type`   | string | ✅       | feat / fix / refactor / docs / chore |
| `changed_files` | list   | ✅       | Files that were modified |
| `date`          | string | ✅       | ISO date string (YYYY-MM-DD) |

---

## Execution

1. **Read existing `CHANGELOG.md`** to understand the format in use

2. **Identify the version section to update:**
   - If the top section is `[Unreleased]` → append under it
   - If no `[Unreleased]` section exists → insert one at the top

3. **Compose the entry** following [Keep a Changelog](https://keepachangelog.com) format:
   ```markdown
   ### Added / Fixed / Changed / Removed / Deprecated / Security
   - <clear, one-line description of what changed>
   ```
   Map `change_type` → section:
   - `feat` → `Added`
   - `fix` → `Fixed`
   - `refactor` → `Changed`
   - `docs` → `Changed`
   - `chore` → `Changed`

4. **Write the updated `CHANGELOG.md`** using `write_to_file` or `replace_file_content`

5. **Store result to memory:**
   ```bash
   python3 execution/memory_manager.py store \
     --content "changelog-updater: appended entry for '<commit_msg>' on <date>" \
     --type decision \
     --tags changelog-updater documentation-team changelog
   ```

---

## Outputs

```json
{
  "sub_agent": "changelog-updater",
  "status": "pass|fail",
  "entry_appended": "- feat: add dispatch_agent_team.py for team orchestration",
  "section": "Added",
  "changelog_path": "CHANGELOG.md"
}
```

---

## Edge Cases

- **`CHANGELOG.md` does not exist:** Create it with standard header and `[Unreleased]` section
- **Multiple change types in one commit:** Use the most significant type (feat > fix > refactor > docs > chore)
- **Entry would be duplicate:** Check last 5 entries; if identical, skip with `"status": "skipped"`

---

## Quality Rules

- One line per change — no paragraph entries
- Write in past tense: "Added", "Fixed", "Updated" — not "Adds", "Fixes"
- Reference changed file names where helpful: `(execution/session_boot.py)`
- Keep entries factual — no marketing language
