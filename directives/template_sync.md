# Template Sync Directive

## Goal

Keep `templates/base/` (the public NPM scaffold) in sync with root development files. The root is always the source of truth.

## Sync Rules

### Always Synced (root → template)

These files MUST be identical between root and `templates/base/`:

| File/Dir | Notes |
|----------|-------|
| `AGENTS.md` | Core instructions — must match exactly |
| `execution/*.py` | All 9 execution scripts |
| `skill-creator/` | Entire directory |
| `data/workflows.json` | Playbook definitions |
| `directives/memory_integration.md` | Memory protocol |
| `directives/release_process.md` | Release SOP |
| `directives/subagents/*.md` | All sub-agent definitions |
| `directives/teams/*.md` | All team manifests |
| `.agent/rules/core_rules.md` | Core operating rules |
| `.agent/rules/agent_team_rules.md` | Team dispatch rules |

### Partially Synced

| Root | Template | Rule |
|------|----------|------|
| `skills/` | `templates/skills/core/` | Only core skills (qdrant-memory, documentation, pdf-reader, webcrawler) |
| `.agent/workflows/` | `templates/base/.agent/workflows/` | Only `memory-usage.md` and `run-agent-team-tests.md` |
| `README.md` | `templates/base/README.md` | Template has its own README |
| `CHANGELOG.md` | `templates/base/CHANGELOG.md` | Shared changelog |

### Never Synced (private-only)

- `directives/framework_development.md`
- `directives/template_sync.md`
- `directives/skill_development.md`
- `execution/sync_to_template.py`
- `execution/validate_template.py`
- `.agent/rules/framework_dev_rules.md`
- `.agent/rules/versioning_rules.md`
- `.agent/workflows/release-protocol.md`
- `.agent/scripts/release_gate.py`
- `skills/upstream-sync/`
- `.github/`

## Execution

```bash
# Preview what would change
python3 execution/sync_to_template.py --check

# Sync all mapped files
python3 execution/sync_to_template.py --sync

# Sync specific file
python3 execution/sync_to_template.py --files execution/memory_manager.py

# Validate template after sync
python3 execution/validate_template.py
```

## Edge Cases

- **New execution script added**: Add it to the sync map in `sync_to_template.py` AND update this directive.
- **Template-only files** (e.g., `.env.example`, `tests/agents/`): These live only in `templates/base/` and are not touched by sync.
- **Conflict detected**: Sync script will show diff and abort. Resolve manually, then re-run.
