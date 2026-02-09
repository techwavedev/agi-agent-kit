---
description: Initialize the agent memory system with Qdrant for semantic caching and long-term memory
---

# Setup Memory System

This workflow initializes the full memory integration for automatic token optimization.

## Prerequisites

// turbo-all

1. Start Qdrant (if not running)

```bash
docker run -d --name qdrant -p 6333:6333 -p 6334:6334 -v qdrant_storage:/qdrant/storage qdrant/qdrant
```

2. Start Ollama and pull embedding model

```bash
ollama serve &
ollama pull nomic-embed-text
```

## Initialize Collections

3. Run session initialization (creates agent_memory + semantic_cache with 768d vectors)

```bash
python3 execution/session_init.py
```

## Validation

4. Verify health (Qdrant + Ollama + collections)

```bash
python3 execution/memory_manager.py health
```

Expected JSON output should show:

- `"qdrant": "ok"`
- `"embeddings": {"status": "ok"}`
- `"missing_collections": []`
- `"ready": true`

5. Test store + retrieve cycle

```bash
python3 execution/memory_manager.py store --content "Test memory: setup verified" --type technical --project test
python3 execution/memory_manager.py auto --query "setup verified"
```

## Usage

Memory is **automatic** when the agent follows the protocol in `directives/memory_integration.md`:

- **Session start**: Agent runs `python3 execution/session_init.py` (once per session)
- **Before complex tasks**: Agent runs `python3 execution/memory_manager.py auto --query "<summary>"`
- **After key decisions**: Agent runs `python3 execution/memory_manager.py store --content "..." --type decision`
- **After completing tasks**: Agent runs `python3 execution/memory_manager.py cache-store --query "..." --response "..."`

### Token Savings

| Scenario              | Without Memory | With Memory | Savings |
| --------------------- | -------------- | ----------- | ------- |
| Repeated question     | ~2000 tokens   | 0 tokens    | 100%    |
| Similar architecture  | ~5000 tokens   | ~500 tokens | 90%     |
| Past error resolution | ~3000 tokens   | ~300 tokens | 90%     |

### Opt-out

To skip memory for a specific query, use:

- "don't use cache"
- "no cache"
- "skip memory"
- "fresh" (at start of query)

## Monitoring

```bash
# Health check
python3 execution/memory_manager.py health

# List stored memories
python3 execution/memory_manager.py list --limit 20

# Clear stale cache (older than 7 days)
python3 execution/memory_manager.py cache-clear --older-than 7
```
