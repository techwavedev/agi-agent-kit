---
name: qdrant-memory
description: Intelligent token optimization through Qdrant-powered semantic caching and long-term memory. Use for: (1) Semantic Cache - avoid LLM calls entirely for semantically similar queries (100% token savings), (2) Long-Term Memory - retrieve only relevant context chunks instead of full conversation history (80-95% context reduction), (3) Hybrid Search - combine vector similarity with keyword filtering for technical queries, (4) Memory Management - store and retrieve conversation memories, decisions, and code patterns with metadata filtering. Triggers when needing to cache responses, remember past interactions, optimize context windows, or implement RAG patterns.
---

# Qdrant Memory Skill

Token optimization engine using Qdrant vector database for semantic caching and intelligent memory retrieval.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      USER QUERY                              │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  1. SEMANTIC CACHE CHECK (Cache Hit = 100% Token Savings)   │
│  ┌─────────────────┐    ┌─────────────────────────────────┐ │
│  │   Embed Query   │───▶│  Search Qdrant (similarity>0.9) │ │
│  └─────────────────┘    └─────────────────────────────────┘ │
│                                      │                       │
│                    ┌─────────────────┴──────────────────┐    │
│                    ▼                                    ▼    │
│            [CACHE HIT]                          [CACHE MISS] │
│            Return cached                        Continue to  │
│            response                             LLM          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  2. CONTEXT RETRIEVAL (RAG - 80-95% Context Reduction)      │
│  ┌─────────────────┐    ┌─────────────────────────────────┐ │
│  │  Identify Need  │───▶│  Retrieve Top-K Relevant Chunks │ │
│  └─────────────────┘    └─────────────────────────────────┘ │
│         Instead of 20K tokens ───▶ Only 500-1000 tokens     │
└─────────────────────────────────────────────────────────────┘
```

---

## Quick Start

### MCP Server Configuration

```json
{
  "qdrant-mcp": {
    "command": "npx",
    "args": ["-y", "@qdrant/mcp-server-qdrant"],
    "env": {
      "QDRANT_URL": "http://localhost:6333",
      "QDRANT_API_KEY": "${QDRANT_API_KEY}",
      "COLLECTION_NAME": "agent_memory"
    }
  }
}
```

### Initialize Memory Collection

Run `scripts/init_collection.py` to create the optimized collection:

```bash
python scripts/init_collection.py --collection agent_memory --dimension 1536
```

---

## Core Capabilities

### 1. Semantic Cache (Maximum Token Savings)

**Purpose**: Avoid LLM calls entirely for semantically similar queries.

**Flow**:

1. Embed incoming query
2. Search Qdrant for similar past queries (threshold > 0.9)
3. If match found → return cached response (100% token savings)
4. If no match → proceed to LLM, then cache result

**Implementation**:

```python
# Cache check before LLM call
from scripts.semantic_cache import check_cache, store_response

# Check cache first
cached = check_cache(query, similarity_threshold=0.92)
if cached:
    return cached["response"]  # 100% token savings

# Generate response with LLM
response = llm.generate(query)

# Store for future cache hits
store_response(query, response, metadata={
    "type": "cache",
    "model": "gpt-4",
    "tokens_saved": len(response.split())
})
```

**Collection Schema**:

```json
{
  "collection": "semantic_cache",
  "vectors": {
    "size": 1536,
    "distance": "Cosine"
  },
  "payload_schema": {
    "query": "keyword",
    "response": "text",
    "timestamp": "datetime",
    "model": "keyword",
    "token_count": "integer"
  }
}
```

### 2. Long-Term Memory (Context Optimization)

**Purpose**: Retrieve only relevant context instead of full conversation history.

**Problem**: 20,000 token conversation history → Expensive + Confuses model
**Solution**: Query Qdrant → Return only top 3-5 relevant chunks (500-1000 tokens)

**Memory Types**:

| Type             | Payload Filter         | Use Case                            |
| ---------------- | ---------------------- | ----------------------------------- |
| `decision`       | `type: "decision"`     | Past architectural/design decisions |
| `code_pattern`   | `type: "code"`         | Previously written code patterns    |
| `error_solution` | `type: "error"`        | How past errors were resolved       |
| `conversation`   | `type: "conversation"` | Key conversation points             |
| `technical`      | `type: "technical"`    | Technical knowledge/docs            |

**Implementation**:

```python
from scripts.memory_retrieval import retrieve_context

# Instead of passing 20K tokens of history:
relevant_chunks = retrieve_context(
    query="What did we decide about the database architecture?",
    filters={"type": "decision"},
    top_k=5,
    score_threshold=0.7
)

# Build optimized prompt with only relevant context
prompt = f"""
Relevant Context:
{relevant_chunks}

User Question: {user_query}
"""
# Now only ~1000 tokens instead of 20,000
```

### 3. Hybrid Search (Vector + Keyword)

**Purpose**: Combine semantic similarity with exact keyword matching for technical queries.

**When to use**: Error codes, variable names, specific identifiers

```python
from scripts.hybrid_search import hybrid_query

results = hybrid_query(
    text_query="kubernetes deployment failed",
    keyword_filters={
        "error_code": "ImagePullBackOff",
        "namespace": "production"
    },
    fusion_weights={"text": 0.7, "keyword": 0.3}
)
```

---

## MCP Tools Reference

| Tool                         | Purpose                         |
| ---------------------------- | ------------------------------- |
| `qdrant_store_memory`        | Store embeddings with metadata  |
| `qdrant_search_memory`       | Semantic search with filters    |
| `qdrant_delete_memory`       | Remove memories by ID or filter |
| `qdrant_list_collections`    | View available collections      |
| `qdrant_get_collection_info` | Collection stats and config     |

### Store Memory

```json
{
  "tool": "qdrant_store_memory",
  "arguments": {
    "content": "We decided to use PostgreSQL for user data due to ACID compliance requirements",
    "metadata": {
      "type": "decision",
      "project": "api-catalogue",
      "date": "2026-01-22",
      "tags": ["database", "architecture"]
    }
  }
}
```

### Search Memory

```json
{
  "tool": "qdrant_search_memory",
  "arguments": {
    "query": "database architecture decisions",
    "filter": {
      "must": [{ "key": "type", "match": { "value": "decision" } }]
    },
    "limit": 5,
    "score_threshold": 0.7
  }
}
```

---

## Payload Filtering Patterns

### Filter by Type

```json
{
  "filter": {
    "must": [{ "key": "type", "match": { "value": "technical" } }]
  }
}
```

### Filter by Project + Date Range

```json
{
  "filter": {
    "must": [
      { "key": "project", "match": { "value": "api-catalogue" } },
      { "key": "timestamp", "range": { "gte": "2026-01-01" } }
    ]
  }
}
```

### Exclude Certain Tags

```json
{
  "filter": {
    "must_not": [
      { "key": "tags", "match": { "any": ["deprecated", "archived"] } }
    ]
  }
}
```

---

## Collection Design Patterns

### Single Collection (Simple)

```
agent_memory/
├── type: "cache" | "decision" | "code" | "error" | "conversation"
├── project: "<project_name>"
├── timestamp: "<ISO8601>"
└── content: "<text>"
```

### Multi-Collection (Advanced)

| Collection       | Purpose                 | Retention |
| ---------------- | ----------------------- | --------- |
| `semantic_cache` | Query-response cache    | 7 days    |
| `decisions`      | Architectural decisions | Permanent |
| `code_patterns`  | Reusable code snippets  | 90 days   |
| `conversations`  | Key conversation points | 30 days   |
| `errors`         | Error solutions         | 60 days   |

---

## Token Savings Metrics

Track savings with metadata:

```python
{
    "tokens_input_saved": 15000,
    "tokens_output_saved": 2000,
    "cost_saved_usd": 0.27,
    "cache_hit": True,
    "retrieval_latency_ms": 45
}
```

**Expected Savings**:

| Scenario          | Without Qdrant | With Qdrant | Savings |
| ----------------- | -------------- | ----------- | ------- |
| Repeated question | 8K tokens      | 0 tokens    | 100%    |
| Context retrieval | 20K tokens     | 1K tokens   | 95%     |
| Hybrid lookup     | 15K tokens     | 2K tokens   | 87%     |

---

## Best Practices

### Embedding Model Selection

| Model                    | Dimensions | Speed   | Quality   | Use Case      |
| ------------------------ | ---------- | ------- | --------- | ------------- |
| `text-embedding-3-small` | 1536       | Fast    | Good      | General use   |
| `text-embedding-3-large` | 3072       | Medium  | Excellent | High accuracy |
| `all-MiniLM-L6-v2`       | 384        | Fastest | Good      | Local/private |

### Cache Invalidation

- **Time-based**: Expire cache entries after N days
- **Manual**: Clear cache when underlying data changes
- **Version-based**: Include model version in metadata

### Memory Hygiene

1. **Deduplicate**: Check similarity before storing
2. **Prune**: Remove low-value memories periodically
3. **Compress**: Summarize long conversations before storing

---

## References

- See `references/collection_schemas.md` for complete schema definitions
- See `references/embedding_models.md` for model comparisons
- See `references/advanced_patterns.md` for RAG optimization patterns
