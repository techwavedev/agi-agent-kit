# task_router.py

Security-first intelligent task classifier and router. Auto-detects security-sensitive tasks and forces local-only execution. Classifies tasks by complexity and routes to local Ollama models or cloud APIs.

## Purpose

The orchestrator calls `task_router.py` before delegating any task to decide:
1. **Security**: Does the task touch secrets/tokens/credentials? → Force local, block cloud fallback.
2. **Cost**: Is the task small and deterministic? → Run locally for free.
3. **Quality**: Does the task need deep reasoning? → Delegate to cloud model.

## Usage

### Classify a task

```bash
python3 execution/task_router.py classify --task "Read .env and extract the DB password"
# → {"route": "local_required", "reason": "Security: task references sensitive data (.env, password)"}
```

### Route and execute

```bash
# Local tasks execute immediately via local_micro_agent.py
python3 execution/task_router.py route --task "Convert getUserData to snake_case"

# Cloud tasks return delegation instructions
python3 execution/task_router.py route --task "Architect a new caching layer"
```

### Split compound tasks

```bash
python3 execution/task_router.py split \
  --task "1) Read .env 2) summarize the log 3) architect caching"
# → 3 subtasks: local_required, local, cloud
```

### Batch classify

```bash
python3 execution/task_router.py batch --tasks-file tasks.json
```

### Routing statistics

```bash
python3 execution/task_router.py stats
```

## Subcommands

| Command | Description |
|---------|-------------|
| `classify` | Classify a task without executing (returns routing decision) |
| `route` | Classify and execute locally, or return cloud delegation |
| `split` | Decompose compound task into independently-routable subtasks |
| `batch` | Classify multiple tasks from a JSON file |
| `stats` | Show routing statistics (local vs cloud, security blocks) |

## Arguments

### classify

| Flag | Required | Description |
|------|----------|-------------|
| `--task` | Yes | Task text to classify |
| `--context` | No | Additional context for classification |

### route

| Flag | Required | Description |
|------|----------|-------------|
| `--task` | Yes | Task to route and potentially execute |
| `--input-file` | No | File to include as context |
| `--input-text` | No | Text context |
| `--model` | No | Force a specific local model |
| `--json` | No | Request JSON output from model |
| `--raw` | No | Raw text output only |

### split

| Flag | Required | Description |
|------|----------|-------------|
| `--task` | Yes | Compound task to decompose |

### batch

| Flag | Required | Description |
|------|----------|-------------|
| `--tasks-file` | Yes | JSON file containing task list |

## Routing Rules

| Signal | Route | Behavior |
|--------|-------|----------|
| `.env`, `password`, `token`, `api_key`, `credential`, `secret`, `jwt`, `bearer`, `private_key`, `pem` | `local_required` | Secrets never leave the machine. Cloud fallback BLOCKED. |
| `summarize`, `classify`, `extract`, `parse`, `format`, `convert`, `validate`, `count`, `sort`, `filter` | `local` | Small deterministic task. Cloud fallback allowed if local fails. |
| `architect`, `refactor`, `review`, `implement`, `design system`, `optimize algorithm`, `write documentation` | `cloud` | Needs deep reasoning. Delegated to Claude/Gemini. |
| Short task (<=15 words), no other signals | `local` | Heuristic: likely simple. |
| Long task, no other signals | `cloud` | Heuristic: likely complex. |

## Output Format

### classify

```json
{
  "route": "local_required",
  "reason": "Security: task references sensitive data (.env, password). Must stay local.",
  "security_flags": [".env", "password"],
  "complexity": "low",
  "suggested_model": "gemma4:e4b",
  "confidence": 0.95
}
```

### route (executed locally)

```json
{
  "status": "executed_locally",
  "classification": { "route": "local", "..." : "..." },
  "result": { "response": "get_user_data", "metrics": { "..." : "..." } }
}
```

### route (cloud delegation)

```json
{
  "status": "delegate_to_cloud",
  "classification": { "route": "cloud", "..." : "..." },
  "message": "Task requires cloud model. Orchestrator should handle."
}
```

### split

```json
{
  "original_task": "...",
  "subtask_count": 3,
  "subtasks": [ { "step": 1, "task": "...", "route": "local_required" }, "..." ],
  "local_count": 2,
  "cloud_count": 1,
  "security_sensitive": 1
}
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Invalid arguments |
| 2 | Ollama unavailable (for local-only tasks) |
| 3 | Processing error |
| 4 | Security violation (secrets would be sent to cloud) |

## Stats Tracking

Routing decisions are tracked in `.tmp/task_router_stats.json`:

```json
{
  "total": 6,
  "by_route": { "local": 3, "local_required": 1, "cloud": 2 },
  "last_updated": "2026-04-04T15:51:04"
}
```

## Dependencies

- `execution/local_micro_agent.py` (for local execution via `route` command)
- Ollama running locally (for local/local_required routes)
- No pip dependencies (uses stdlib)
