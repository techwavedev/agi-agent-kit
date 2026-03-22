# worktree_isolator.py

Git worktree lifecycle manager for parallel agent isolation. Each agent gets its own worktree (isolated repo copy) on a dedicated branch, then merges back when done.

## Purpose

Enables parallel agent execution without merge conflicts. Worktrees are created in `/tmp/agi-worktrees/<project>/` to avoid cloud-synced filesystem slowness. Used by `dispatch_agent_team.py --parallel` under the hood.

## Commands

### `create` — Create isolated worktree for one agent

```bash
python3 execution/worktree_isolator.py create --agent doc-writer --run-id abc123 [--base-branch main]
```

### `create-all` — Create worktrees for all agents in a run

```bash
python3 execution/worktree_isolator.py create-all --agents '["doc-writer","reviewer"]' [--run-id abc123] [--base-branch main]
```

### `merge` — Merge one agent's branch back to base

```bash
python3 execution/worktree_isolator.py merge --agent doc-writer --run-id abc123 [--strategy merge|rebase]
```

### `merge-all` — Sequentially merge all agent branches from a run

```bash
python3 execution/worktree_isolator.py merge-all --run-id abc123 [--strategy merge|rebase]
```

### `cleanup` — Remove worktree and optionally delete branch

```bash
python3 execution/worktree_isolator.py cleanup --agent doc-writer --run-id abc123 [--keep-branch]
```

### `status` — List all active agent worktrees

```bash
python3 execution/worktree_isolator.py status [--run-id abc123]
```

### `validate-partitions` — Check file partitions for overlap

```bash
python3 execution/worktree_isolator.py validate-partitions \
  --partitions '{"agent-1": ["src/api/**"], "agent-2": ["src/ui/**"]}'
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Invalid arguments |
| 2 | Git error (worktree create/merge failed) |
| 3 | Merge conflict detected |
| 4 | Partition overlap detected |

## Edge Cases

- **Worktree already exists**: `create` fails with exit 2. Use `cleanup` first or pick a new `--run-id`.
- **Merge conflicts**: `merge` / `merge-all` return exit 3 with conflict details and a resolution hint command.
- **Cloud-synced repos**: Worktrees go to `/tmp/` automatically to avoid Synology/iCloud/Dropbox latency.
- **`.env` not copied**: The script auto-copies `.env` from root into each new worktree.
- **Partial merge-all failure**: Successfully-merged agents stay merged; conflicting ones are aborted and listed separately.

## Dependencies

- Git (with worktree support, 2.5+)
- Called by `dispatch_agent_team.py --parallel`
