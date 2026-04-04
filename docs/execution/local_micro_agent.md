# local_micro_agent.py

Route small, deterministic tasks to local Ollama models (Gemma 4, GLM) to save cloud API tokens. Supports model registry, automatic fallback, structured JSON output, and cost tracking.

## Purpose

Wraps Ollama's API with a model registry, automatic fallback chain, and structured output. Used by `task_router.py` for local execution and directly by agents for known-small tasks.

## Usage

### Simple task

```bash
python3 execution/local_micro_agent.py --task "Summarize this error" --input-text "TypeError: x is not a function"
```

### File input

```bash
python3 execution/local_micro_agent.py --task "Extract all function names" --input-file src/app.py
```

### Force a specific model

```bash
python3 execution/local_micro_agent.py --task "Classify this text" --model glm-4.7-flash
```

### JSON output

```bash
python3 execution/local_micro_agent.py --task "Parse these imports as JSON" --input-file x.py --json
```

### Raw text output (no metadata)

```bash
python3 execution/local_micro_agent.py --task "Convert to snake_case: getUserData" --raw
```

### Subcommands

```bash
python3 execution/local_micro_agent.py list-models   # Show available models
python3 execution/local_micro_agent.py health         # Ollama + model health check
```

## Arguments

| Flag | Required | Description |
|------|----------|-------------|
| `--task` | Yes | The instruction/task for the local model |
| `--model` | No | Force a specific model (default: auto-select by task) |
| `--input-file` | No | Path to a file to include as context |
| `--input-text` | No | Direct text to include as context |
| `--temperature` | No | Temperature (default: 0.0 for deterministic) |
| `--max-tokens` | No | Max tokens to generate (default: 1024) |
| `--json` | No | Force JSON format response |
| `--raw` | No | Output only the model response text (no metadata) |

## Model Registry

| Model | Tier | Strength | Max Tokens |
|-------|------|----------|------------|
| `gemma4:e4b` | fast | Code understanding, classification, extraction, summarization | 2048 |
| `glm-4.7-flash:latest` | medium | Reasoning, analysis, code generation, multi-step logic | 4096 |
| `nomic-embed-text:latest` | embedding | Embeddings only (not for generation) | N/A |

**Fallback chain:** `gemma4:e4b` -> `glm-4.7-flash:latest`. If preferred model fails, automatically tries the next.

## Output Format

Default (structured):
```json
{
  "status": "success",
  "model": "gemma4:e4b",
  "response": "get_user_profile_data",
  "metrics": {
    "elapsed_seconds": 1.23,
    "prompt_tokens": 45,
    "completion_tokens": 8,
    "total_tokens": 53,
    "tokens_per_second": 6.5
  },
  "cloud_tokens_saved": 53
}
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Ollama unreachable or model not available |
| 2 | Input file not found |
| 3 | Model inference error |
| 4 | All fallback models exhausted |

## Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `OLLAMA_URL` | `http://localhost:11434` | Ollama API endpoint |

## Dependencies

- Ollama running locally with at least one generation model
- No pip dependencies (uses stdlib `urllib`)
