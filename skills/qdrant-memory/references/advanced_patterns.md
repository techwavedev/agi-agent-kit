# Advanced Patterns Reference

This document covers advanced RAG optimization patterns for maximum token savings.

## Pattern 1: Hierarchical Memory

Store memories at multiple granularities for optimal retrieval.

```
┌─────────────────────────────────────────────┐
│  SUMMARY LEVEL (Low detail, fast lookup)    │
│  "We discussed database architecture"       │
├─────────────────────────────────────────────┤
│  CHUNK LEVEL (Medium detail)                │
│  "Decided PostgreSQL for ACID compliance"   │
├─────────────────────────────────────────────┤
│  DETAIL LEVEL (Full context)                │
│  "After evaluating MongoDB, PostgreSQL,     │
│   and MySQL, we chose PostgreSQL because..."│
└─────────────────────────────────────────────┘
```

### Implementation

```python
def store_hierarchical(content: str, metadata: dict):
    """Store at multiple granularities."""

    # Level 1: Full content
    store_memory(content, type="detail", **metadata)

    # Level 2: Summary (use LLM to summarize)
    summary = summarize(content)
    store_memory(summary, type="summary", parent_id=detail_id, **metadata)

    # Level 3: Keywords/tags for fast lookup
    keywords = extract_keywords(content)
    store_memory(" ".join(keywords), type="index", parent_id=detail_id, **metadata)
```

### Retrieval Strategy

1. First search `type=index` for fast matching
2. If match found, retrieve parent `type=summary`
3. If more detail needed, retrieve `type=detail`

---

## Pattern 2: Sliding Window Chunking

Optimal chunk size for context retrieval.

### Chunk Size Guidelines

| Content Type    | Optimal Chunk  | Overlap    |
| --------------- | -------------- | ---------- |
| Code            | 500-800 tokens | 100 tokens |
| Documentation   | 300-500 tokens | 50 tokens  |
| Conversation    | 200-300 tokens | 25 tokens  |
| Technical specs | 400-600 tokens | 75 tokens  |

### Implementation

```python
def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list:
    """Split text into overlapping chunks."""
    words = text.split()
    chunks = []

    for i in range(0, len(words), chunk_size - overlap):
        chunk = " ".join(words[i:i + chunk_size])
        chunks.append(chunk)

    return chunks

def store_chunked(document: str, metadata: dict):
    """Store document as overlapping chunks."""
    chunks = chunk_text(document)

    for i, chunk in enumerate(chunks):
        store_memory(
            chunk,
            type="chunk",
            chunk_index=i,
            total_chunks=len(chunks),
            **metadata
        )
```

---

## Pattern 3: Query Expansion

Improve recall by expanding queries.

### Synonym Expansion

```python
def expand_query(query: str) -> list:
    """Generate query variations for better recall."""
    variations = [query]

    # Add variations
    variations.append(query.lower())
    variations.append(rephrase_with_llm(query))

    return variations

def search_with_expansion(query: str, top_k: int = 5):
    """Search with multiple query variations, dedupe results."""
    all_results = {}

    for variation in expand_query(query):
        results = retrieve_context(variation, top_k=top_k)
        for r in results["chunks"]:
            # Keep highest scoring version
            if r["content"] not in all_results or r["score"] > all_results[r["content"]]["score"]:
                all_results[r["content"]] = r

    return sorted(all_results.values(), key=lambda x: x["score"], reverse=True)[:top_k]
```

---

## Pattern 4: Relevance Feedback Loop

Improve retrieval quality over time.

### Implicit Feedback

```python
def log_usage(query: str, retrieved: list, used_chunks: list):
    """Log which retrieved chunks were actually used."""
    for chunk in retrieved:
        was_used = chunk["content"] in used_chunks
        store_feedback(
            query=query,
            chunk_id=chunk["id"],
            was_used=was_used,
            score=chunk["score"]
        )

def boost_frequently_used(results: list) -> list:
    """Boost chunks that are frequently used."""
    for result in results:
        usage_rate = get_usage_rate(result["id"])
        result["boosted_score"] = result["score"] * (1 + usage_rate * 0.2)

    return sorted(results, key=lambda x: x["boosted_score"], reverse=True)
```

### Explicit Feedback

```json
{
  "tool": "qdrant_update_memory",
  "arguments": {
    "id": "memory_123",
    "payload": {
      "relevance_score": 0.95,
      "last_useful": "2026-01-22T12:00:00Z",
      "usage_count": 15
    }
  }
}
```

---

## Pattern 5: Context Window Packing

Maximize information density in the context window.

### Token Budget Allocation

```
Total Budget: 4000 tokens
├── System Prompt: 500 tokens (fixed)
├── Retrieved Context: 2000 tokens (variable)
├── User Query: 200 tokens (variable)
└── Response Space: 1300 tokens (reserved)
```

### Packing Algorithm

```python
def pack_context(chunks: list, token_budget: int = 2000) -> str:
    """Pack most relevant chunks within token budget."""
    packed = []
    current_tokens = 0

    # Sort by relevance score
    sorted_chunks = sorted(chunks, key=lambda x: x["score"], reverse=True)

    for chunk in sorted_chunks:
        chunk_tokens = chunk["token_estimate"]
        if current_tokens + chunk_tokens <= token_budget:
            packed.append(chunk["content"])
            current_tokens += chunk_tokens
        else:
            # Try to fit partial chunk
            remaining = token_budget - current_tokens
            if remaining > 100:  # Worth including partial
                words = chunk["content"].split()[:remaining]
                packed.append(" ".join(words) + "...")
            break

    return "\n\n---\n\n".join(packed)
```

---

## Pattern 6: Semantic Deduplication

Avoid storing redundant information.

```python
def should_store(new_content: str, threshold: float = 0.9) -> bool:
    """Check if similar content already exists."""
    similar = retrieve_context(
        new_content,
        top_k=1,
        score_threshold=threshold
    )

    if similar["total_chunks"] > 0:
        print(f"Similar content exists (score: {similar['chunks'][0]['score']})")
        return False

    return True

def store_if_unique(content: str, **metadata):
    """Only store if semantically unique."""
    if should_store(content):
        return store_memory(content, **metadata)
    else:
        return {"status": "skipped", "reason": "duplicate"}
```

---

## Pattern 7: Time-Decayed Relevance

Recent information is often more relevant.

### Decay Function

```python
import math
from datetime import datetime, timedelta

def time_decay_score(base_score: float, timestamp: str, half_life_days: int = 30) -> float:
    """Apply exponential decay based on age."""
    age = datetime.utcnow() - datetime.fromisoformat(timestamp)
    age_days = age.total_seconds() / 86400

    decay = math.exp(-0.693 * age_days / half_life_days)  # ln(2) ≈ 0.693
    return base_score * decay

def retrieve_with_recency(query: str, top_k: int = 5):
    """Retrieve and re-rank with time decay."""
    results = retrieve_context(query, top_k=top_k * 2)

    for chunk in results["chunks"]:
        chunk["decayed_score"] = time_decay_score(
            chunk["score"],
            chunk["timestamp"]
        )

    # Re-rank by decayed score
    results["chunks"] = sorted(
        results["chunks"],
        key=lambda x: x["decayed_score"],
        reverse=True
    )[:top_k]

    return results
```

---

## Pattern 8: Multi-Collection Routing

Route queries to specialized collections.

```python
COLLECTION_ROUTES = {
    "code": "code_patterns",
    "error": "error_solutions",
    "decision": "decisions",
    "api": "api_documentation",
    "default": "agent_memory"
}

def classify_query(query: str) -> str:
    """Classify query to route to appropriate collection."""
    # Simple keyword-based routing
    if any(kw in query.lower() for kw in ["code", "function", "class", "implement"]):
        return "code"
    if any(kw in query.lower() for kw in ["error", "exception", "failed", "bug"]):
        return "error"
    if any(kw in query.lower() for kw in ["decision", "decided", "chose", "why"]):
        return "decision"
    return "default"

def routed_search(query: str, **kwargs):
    """Search the appropriate collection based on query type."""
    query_type = classify_query(query)
    collection = COLLECTION_ROUTES[query_type]

    return retrieve_context(query, collection=collection, **kwargs)
```

---

## Token Savings Calculations

### Semantic Cache ROI

```python
def calculate_cache_roi(
    cache_hit_rate: float,
    avg_query_tokens: int,
    avg_response_tokens: int,
    embedding_cost_per_1k: float = 0.00002,
    llm_input_cost_per_1k: float = 0.01,
    llm_output_cost_per_1k: float = 0.03
):
    """Calculate cost savings from semantic caching."""

    # Cost with caching (embedding only on cache hit)
    cache_cost = embedding_cost_per_1k * avg_query_tokens / 1000

    # Cost without caching (full LLM call)
    llm_cost = (
        llm_input_cost_per_1k * avg_query_tokens / 1000 +
        llm_output_cost_per_1k * avg_response_tokens / 1000
    )

    # Blended cost with cache
    blended_cost = (cache_hit_rate * cache_cost) + ((1 - cache_hit_rate) * llm_cost)

    savings = (llm_cost - blended_cost) / llm_cost * 100

    return {
        "cache_cost_per_query": cache_cost,
        "llm_cost_per_query": llm_cost,
        "blended_cost_per_query": blended_cost,
        "savings_percentage": f"{savings:.1f}%"
    }
```

### Context Reduction ROI

```python
def calculate_context_roi(
    original_context_tokens: int,
    retrieved_tokens: int,
    llm_input_cost_per_1k: float = 0.01
):
    """Calculate savings from context reduction."""

    original_cost = llm_input_cost_per_1k * original_context_tokens / 1000
    optimized_cost = llm_input_cost_per_1k * retrieved_tokens / 1000

    tokens_saved = original_context_tokens - retrieved_tokens
    savings = (original_cost - optimized_cost) / original_cost * 100

    return {
        "original_tokens": original_context_tokens,
        "optimized_tokens": retrieved_tokens,
        "tokens_saved": tokens_saved,
        "savings_percentage": f"{savings:.1f}%"
    }
```
