---
name: upstream-sync
description: "Synchronize upstream fork repositories with the agi-agent-kit codebase. Detects new/updated content from forked repos, creates feature branches, and applies framework adaptations."
---

# Upstream Fork Sync

## When to Use

- When the user asks to sync, update, or check upstream forks
- When `/upstream-sync` is invoked
- Periodically (weekly) to check for upstream updates
- Before a release, to ensure we have the latest community improvements

## Upstream Registry

All tracked forks are defined in `upstream_registry.json` (same directory as this file). Each entry specifies:

- `fork` / `upstream`: GitHub org/repo for our fork and the original
- `local_paths`: Where the content lives in our codebase
- `sync_strategy`: How to handle the merge (see below)
- `priority`: 1=critical, 2=important, 3=reference

## Sync Strategies

| Strategy | Behavior |
|----------|----------|
| `skill-adapt` | Clone → run `scripts/adapt_extended_skills.py` → AGI blocks injected |
| `skill-diff` | Clone → diff each skill → update changed ones → preserve AGI blocks |
| `full-replace` | Clone → replace content → preserve `<!-- AGI-INTEGRATION-START -->` markers |
| `inspect-merge` | Clone fork + upstream → compare divergence → produce merge report |
| `reference-only` | Clone → summarize new features/patterns → no auto-merge |

## Execution

### Full Sync (all repos)

```bash
python3 skills/upstream-sync/scripts/sync_upstream.py --all
```

### Single Repo Sync

```bash
python3 skills/upstream-sync/scripts/sync_upstream.py --id awesome-skills
python3 skills/upstream-sync/scripts/sync_upstream.py --id superpowers
python3 skills/upstream-sync/scripts/sync_upstream.py --id ui-ux-pro-max
python3 skills/upstream-sync/scripts/sync_upstream.py --id auto-claude
```

### Dry Run (preview only)

```bash
python3 skills/upstream-sync/scripts/sync_upstream.py --all --dry-run
```

### Options

| Flag | Description |
|------|-------------|
| `--all` | Sync all registered upstreams |
| `--id <id>` | Sync specific upstream by ID |
| `--dry-run` | Preview changes, don't modify files |
| `--branch` | Auto-create `feat/upstream-sync-<id>` branch |
| `--priority <N>` | Only sync priority ≤ N (default: all) |
| `--report <path>` | Save JSON report to file |

## Output

The script produces a JSON report for each synced repo:

```json
{
  "id": "superpowers",
  "status": "changes_found",
  "new_skills": ["skill-x", "skill-y"],
  "updated_skills": ["brainstorming", "test-driven-development"],
  "unchanged": 8,
  "branch": "feat/upstream-sync-superpowers",
  "merge_conflicts": []
}
```

## Memory Integration

```bash
# Before sync: check if we've synced recently
python3 execution/memory_manager.py auto --query "upstream sync <id>"

# After sync: store what changed
python3 execution/memory_manager.py store \
  --content "Upstream sync <id>: N new, M updated skills" \
  --type decision --project agi-agent-kit \
  --tags upstream-sync <id>
```

## Edge Cases

- **Fork has diverged** (e.g., Auto-Claude/Aperant): Use `inspect-merge` — produces diff report, does NOT auto-merge
- **AGI integration block already exists**: Preserved via `<!-- AGI-INTEGRATION-START/END -->` markers
- **New skills from upstream conflict with core/knowledge**: Skipped (already in higher tier)
- **Upstream repo is private/deleted**: Logged as error, continues with next repo
