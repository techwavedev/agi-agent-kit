# Memory Integration Directive

## Goal

Ensure all AI agents use the Qdrant-powered memory system by default to save tokens and preserve context across sessions. Embedding is handled locally via Ollama (`nomic-embed-text`, 768 dimensions) at zero cost.

## Inputs

- User query (natural language)
- Project name (optional, for scoped retrieval)
- Memory type classification (auto-detected or explicit)

## Prerequisites

| Component          | Required | Check Command                                       |
| ------------------ | -------- | --------------------------------------------------- |
| Qdrant (Docker)    | Yes      | `curl http://localhost:6333/collections`             |
| Ollama             | Yes      | `curl http://localhost:11434/api/tags`               |
| nomic-embed-text   | Yes      | `ollama pull nomic-embed-text`                       |
| Collections setup  | Yes      | `python3 execution/session_init.py`                  |

## Execution Protocol

### 1. Session Start (Run Once)

```bash
python3 execution/session_init.py
```

This verifies Qdrant, Ollama, and creates `agent_memory` (768d) and `semantic_cache` (768d) collections if they don't exist.

### 2. Before Every Complex Task

```bash
python3 execution/memory_manager.py auto --query "<user request summary>"
```

**Decision tree based on result:**

| Result             | Action                                                   |
| ------------------ | -------------------------------------------------------- |
| `cache_hit: true`  | Use cached response directly. Inform user of cache hit.  |
| `source: memory`   | Inject retrieved context chunks into your reasoning.     |
| `source: none`     | Proceed normally. Store the result when done.            |

### 3. After Key Decisions or Solutions

```bash
python3 execution/memory_manager.py store \
  --content "Description of what was decided/solved" \
  --type decision \
  --project <project-name> \
  --tags relevant-tag1 relevant-tag2
```

### 4. After Completing a Complex Task (Cache the Response)

```bash
python3 execution/memory_manager.py cache-store \
  --query "The original user question" \
  --response "The complete response that was generated"
```

## Memory Type Guide

| Type           | When to Store                                    | Retention |
| -------------- | ------------------------------------------------ | --------- |
| `decision`     | Architecture choice, tech selection, trade-off   | Permanent |
| `code`         | Reusable pattern, snippet, config                | Permanent |
| `error`        | Bug fix with root cause and solution             | 90 days   |
| `technical`    | API docs, library quirks, config patterns        | Permanent |
| `conversation` | User preference, constraint, project context     | 30 days   |

## Token Savings Reference

| Scenario              | Without Memory | With Memory | Savings |
| --------------------- | -------------- | ----------- | ------- |
| Repeated question     | ~2000 tokens   | 0 tokens    | 100%    |
| Similar architecture  | ~5000 tokens   | ~500 tokens | 90%     |
| Past error resolution | ~3000 tokens   | ~300 tokens | 90%     |
| Context from history  | ~10000 tokens  | ~1000 tokens| 90%     |

## Edge Cases

- **Qdrant not running:** Log warning, proceed without memory. Never block user workflow.
- **Ollama not running:** Same as above. Memory is optional, never mandatory for task completion.
- **Stale cache:** Cache entries older than 7 days are auto-cleared. Run `python3 execution/memory_manager.py cache-clear --older-than 7` manually if needed.
- **Dimension mismatch:** If switching providers (e.g., OpenAI→Ollama), run `python3 execution/session_init.py --force` to recreate collections with correct dimensions.
- **User opt-out:** Respect "no cache", "fresh", "skip memory" keywords.

## Outputs

- Cached responses (in Qdrant `semantic_cache` collection)
- Stored memories (in Qdrant `agent_memory` collection)
- Session health report (JSON from `session_init.py`)
