# claude_dispatch.py

Translate standard dispatch manifests into Claude Code-native Agent tool instructions. Supports native, fallback, and schedule (cloud) modes.

## Purpose

Adapts agent team manifests for Claude Code's native Agent tool. In native mode, generates per-sub-agent prompts with memory integration, cross-agent context, and handoff protocol. In schedule mode, produces self-contained prompts for cloud task execution. Falls back to raw manifest passthrough when Claude Code is unavailable.

## Usage

### From team ID + payload (native mode)

```bash
python3 execution/claude_dispatch.py \
  --team documentation_team \
  --payload '{"changed_files": ["execution/foo.py"], "commit_msg": "feat: add foo"}' \
  --mode native
```

### From existing manifest file

```bash
python3 execution/claude_dispatch.py --manifest .tmp/manifest.json --mode native
```

### Schedule mode (cloud dispatch)

```bash
python3 execution/claude_dispatch.py \
  --team qa_team \
  --payload '{"task": "nightly tests"}' \
  --mode schedule
```

### Health check

```bash
python3 execution/claude_dispatch.py health
```

## Arguments

| Flag | Required | Description |
|------|----------|-------------|
| `--team` | Conditional | Team ID matching `directives/teams/<id>.md`. Required unless `--manifest` is provided. |
| `--payload` | Conditional | JSON string with task context. Required with `--team`. |
| `--manifest` | Conditional | Path to existing manifest JSON file. Alternative to `--team`/`--payload`. |
| `--mode` | No | Output mode: `native` (default), `fallback`, `schedule` |
| `--cloud` | No | Alias for `--mode schedule` |
| `--project` | No | Project name for Qdrant tagging (default: `agi-agent-kit`) |
| `--dry-run` | No | Output without storing dispatch event to Qdrant |

## Subcommands

| Command | Description |
|---------|-------------|
| `health` | Check Claude Code detection, Qdrant availability, team directives |

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Invalid arguments / health check degraded |
| 2 | Team directive or manifest not found |
| 3 | Invalid JSON (payload or manifest) |
| 4 | Processing error |
| 5 | Claude Code not detected (non-fatal warning in native mode) |

## Output Modes

**Native**: Generates `agent_calls` array with per-sub-agent prompts, isolation settings (worktree for parallel teams), and post-dispatch memory/broadcast commands. Designed for Claude Code's Agent tool.

**Schedule**: Produces a single self-contained prompt combining all sub-agents sequentially, with cloud environment setup (session boot). Suitable for `/schedule` or Cloud Tasks.

**Fallback**: Returns the raw manifest unchanged for non-Claude orchestrators.

## Dependencies

- `execution/dispatch_agent_team.py` (manifest generation when using `--team`/`--payload`)
- `execution/memory_manager.py` (dispatch event storage)
- `directives/teams/<team_id>.md` (team definitions)
- `directives/subagents/<agent>.md` (sub-agent directive content)
