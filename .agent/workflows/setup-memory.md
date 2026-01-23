---
description: Initialize the agent memory system with Qdrant for semantic caching and long-term memory
---

# Setup Memory System

This workflow initializes the full memory integration for automatic token optimization.

## Prerequisites

// turbo-all

1. Start Qdrant (if not running)

```bash
docker run -d --name qdrant -p 6333:6333 -v qdrant_storage:/qdrant/storage qdrant/qdrant
```

2. Start Ollama embedding server

```bash
ollama serve &
ollama pull nomic-embed-text
```

## Initialize Collections

3. Run the memory system initialization

```bash
python3 execution/init_memory_system.py --dimension 768
```

4. Verify the middleware is working

```bash
python3 execution/memory_middleware.py --test
```

## Validation

5. Check Qdrant has the collections

```bash
curl -s http://localhost:6333/collections | jq '.result.collections[].name'
```

Expected output:

- semantic_cache
- agent_memory

## Usage

Memory is now **automatic** for all operations:

- **Cache hits**: Similar queries return cached responses (100% token savings)
- **Context retrieval**: Relevant memories injected into prompts (80-95% reduction)
- **Auto-storage**: Decisions, code patterns, and errors saved automatically

### Opt-out

To skip memory for a specific query, use:

- "don't use cache"
- "no cache"
- "skip memory"
- "fresh" (at start of query)

## Monitoring

View metrics with:

```bash
python3 execution/memory_middleware.py --metrics
```
