# Agent Memory Integration

> **Status**: ENABLED BY DEFAULT
> **Opt-out**: User says "don't use cache", "no cache", "skip memory", or "fresh"

---

## Overview

All agent operations automatically use the Qdrant-powered memory system for:

1. **Semantic Caching** — Avoid redundant LLM calls (100% token savings)
2. **Context Retrieval** — Inject relevant memories instead of full history (80-95% savings)
3. **Knowledge Persistence** — Store decisions, patterns, and solutions for future use

---

## Automatic Behavior

### Before Every Query

```
┌─────────────────────────────────────────────────────────────┐
│  1. CHECK OPT-OUT FLAGS                                      │
│     └─ User said "no cache/fresh/skip memory"? → Skip cache │
│                                                              │
│  2. SEMANTIC CACHE CHECK (threshold: 0.92 similarity)       │
│     └─ Similar query found? → Return cached response        │
│     └─ No match? → Continue to step 3                       │
│                                                              │
│  3. CONTEXT RETRIEVAL (top 5 relevant memories)             │
│     └─ Inject relevant decisions, patterns, solutions       │
│     └─ Reduces context window by 80-95%                     │
│                                                              │
│  4. EXECUTE QUERY                                            │
│     └─ Process with enriched context                        │
│                                                              │
│  5. STORE RESPONSE                                           │
│     └─ Cache for future similar queries                     │
│     └─ Auto-categorize: decision, code, error, technical    │
└─────────────────────────────────────────────────────────────┘
```

### After Important Operations

Automatically store in long-term memory:

| Event Type            | Memory Type    | Example                                   |
| --------------------- | -------------- | ----------------------------------------- |
| Architecture decision | `decision`     | "We chose PostgreSQL for ACID compliance" |
| Code pattern created  | `code`         | Script implementations, reusable patterns |
| Error resolved        | `error`        | Bug fix with root cause and solution      |
| Documentation created | `technical`    | API docs, architecture diagrams           |
| Key conversation      | `conversation` | Important user preferences, requirements  |

---

## Opt-Out Triggers

The user can disable caching for specific queries by using these phrases:

- "don't use cache"
- "no cache"
- "skip memory"
- "fresh" (at start of query)
- "without caching"
- "ignore cache"

**Example:**

```
USER: fresh - what's the status of the EKS cluster?
→ Memory check SKIPPED, live data fetched
```

---

## Memory Types

| Type           | Purpose                                | TTL       |
| -------------- | -------------------------------------- | --------- |
| `cache`        | Query-response pairs for deduplication | 7 days    |
| `decision`     | Architectural and design decisions     | Permanent |
| `code`         | Code patterns and implementations      | 90 days   |
| `error`        | Error resolutions and troubleshooting  | 60 days   |
| `technical`    | Technical documentation and knowledge  | Permanent |
| `conversation` | Key conversation points                | 30 days   |

---

## Implementation

### Middleware Location

```
execution/memory_middleware.py
```

### Usage in Scripts

```python
from execution.memory_middleware import MemoryMiddleware, memory_wrap

# Automatic caching via decorator
@memory_wrap
def process_query(query):
    return llm_call(query)

# Manual control
memory = MemoryMiddleware()

# Check cache
cached = memory.check_cache(query)
if cached:
    return cached["response"]

# Retrieve context
context = memory.retrieve_context(query, memory_types=["decision", "code"])

# Store response
memory.store_response(query, response)

# Store important memory
memory.store_memory(
    content="We decided to use Karpenter for node autoscaling",
    memory_type="decision",
    metadata={"project": "eks-nonprod", "tags": ["infrastructure"]}
)
```

### CLI Commands

```bash
# Check middleware status
python execution/memory_middleware.py --status

# View metrics
python execution/memory_middleware.py --metrics

# Test connection
python execution/memory_middleware.py --test

# Clean expired cache
python execution/memory_middleware.py --cleanup
```

---

## Prerequisites

1. **Qdrant Running**

   ```bash
   docker run -d -p 6333:6333 qdrant/qdrant
   ```

2. **Collections Initialized**

   ```bash
   python skills/qdrant-memory/scripts/init_collection.py --collection semantic_cache --dimension 768
   python skills/qdrant-memory/scripts/init_collection.py --collection agent_memory --dimension 768
   ```

3. **Embedding Provider Running**
   ```bash
   # Ollama (recommended)
   ollama serve &
   ollama pull nomic-embed-text
   ```

---

## Metrics Tracking

The middleware tracks:

- `cache_hits` — Number of queries served from cache
- `cache_misses` — Number of queries that required LLM
- `tokens_saved` — Estimated tokens saved from caching
- `cache_hit_rate` — Percentage of cache hits

Access via:

```python
memory = MemoryMiddleware()
print(memory.get_metrics())
```

---

## Environment Variables

| Variable             | Default                 | Description                   |
| -------------------- | ----------------------- | ----------------------------- |
| `MEMORY_ENABLED`     | `true`                  | Enable/disable memory         |
| `QDRANT_URL`         | `http://localhost:6333` | Qdrant server URL             |
| `EMBEDDING_PROVIDER` | `ollama`                | ollama, bedrock, or openai    |
| `CACHE_THRESHOLD`    | `0.92`                  | Similarity threshold for hits |
| `CACHE_TTL_DAYS`     | `7`                     | Days before cache expires     |

---

## Troubleshooting

| Issue                      | Solution                                  |
| -------------------------- | ----------------------------------------- |
| "Qdrant not available"     | Start Qdrant: `docker start qdrant`       |
| "Embeddings not available" | Start Ollama: `ollama serve`              |
| Low cache hit rate         | Lower `CACHE_THRESHOLD` (e.g., 0.88)      |
| Stale cached responses     | Run `--cleanup` or lower `CACHE_TTL_DAYS` |
| Memory not persisting      | Check Qdrant storage volume is mounted    |
