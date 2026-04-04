# dispatch_agent_team.py

Dispatch a named agent team by reading its directive and preparing a structured manifest of sub-agents. Supports sequential and parallel execution modes.

## Purpose

Reads a team directive from `directives/teams/<team_id>.md`, extracts sub-agent definitions, builds a dispatch manifest, and stores the event to Qdrant memory. In parallel mode, creates isolated git worktrees for each sub-agent via `worktree_isolator.py`.

## Usage

### Sequential (default)

```bash
python3 execution/dispatch_agent_team.py \
  --team documentation_team \
  --payload '{"changed_files": ["execution/foo.py"], "commit_msg": "feat: add foo"}'
```

### Parallel (worktree isolation)

```bash
python3 execution/dispatch_agent_team.py \
  --team code_review_team \
  --payload '{"changed_files": ["src/api.py"]}' \
  --parallel
```

### Parallel with partition validation

```bash
python3 execution/dispatch_agent_team.py \
  --team code_review_team \
  --payload '{"changed_files": ["src/api.py"]}' \
  --parallel \
  --partitions '{"agent-1": ["src/api/**"], "agent-2": ["tests/**"]}'
```

### Claude Code-native dispatch

```bash
python3 execution/dispatch_agent_team.py \
  --team documentation_team \
  --payload '{"changed_files": ["execution/foo.py"], "commit_msg": "feat: add foo"}' \
  --claude --claude-mode native
```

## Arguments

| Flag | Required | Description |
|------|----------|-------------|
| `--team` | Yes | Team ID matching `directives/teams/<id>.md` |
| `--payload` | Yes | JSON string with task context |
| `--parallel` | No | Run sub-agents in parallel using git worktree isolation |
| `--partitions` | No | JSON mapping agent IDs to file globs (validates no overlap before dispatch) |
| `--dry-run` | No | Print manifest without storing to Qdrant |
| `--claude` | No | Force Claude Code-native output via `claude_dispatch.py` |
| `--no-claude` | No | Force standard manifest even if Claude Code env is detected |
| `--claude-mode` | No | Claude dispatch mode: `native` (default), `fallback`, `schedule` |
| `--project` | No | Project name for Qdrant tagging (default: `agi-agent-kit`; used with `--claude`) |

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success, manifest printed to stdout |
| 1 | Invalid arguments |
| 2 | Team directive not found / worktree creation failed |
| 3 | Invalid payload JSON |
| 4 | Memory store error |
| 5 | Partition overlap detected (parallel mode) |

## Execution Modes

**Sequential**: Sub-agents run in order. Each can produce a `handoff_state` object for the next agent. The orchestrator stores handoff state to Qdrant and passes it forward.

**Parallel (worktree)**: Each sub-agent gets its own git worktree (isolated directory + branch). All agents run simultaneously. After completion, `worktree_isolator.py merge-all` merges branches back sequentially.

## Claude Code Integration

When `--claude` is passed (or when `CLAUDE_CODE`/`CLAUDE_SESSION_ID` environment variables are detected), the script pipes the manifest through `claude_dispatch.py` for native Agent tool output. Use `--no-claude` to suppress auto-detection. If `claude_dispatch.py` fails, the script falls back to standard manifest output.

## Dependencies

- `directives/teams/<team_id>.md` (team definition)
- `directives/subagents/<agent>.md` (sub-agent directives)
- `execution/memory_manager.py` (Qdrant storage)
- `execution/worktree_isolator.py` (parallel mode only)
