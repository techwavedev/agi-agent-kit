# Collection Schemas Reference

This document provides detailed collection schemas for different memory use cases.

## Standard Agent Memory Collection

Optimized for general-purpose agent memory storage.

```json
PUT /collections/agent_memory
{
  "vectors": {
    "size": 1536,
    "distance": "Cosine"
  },
  "optimizers_config": {
    "indexing_threshold": 10000,
    "memmap_threshold": 20000
  },
  "hnsw_config": {
    "m": 16,
    "ef_construct": 100,
    "full_scan_threshold": 10000
  }
}
```

### Payload Schema

| Field         | Type      | Purpose                   | Indexed        |
| ------------- | --------- | ------------------------- | -------------- |
| `content`     | text      | The actual memory content | No (too large) |
| `type`        | keyword   | Memory category           | Yes            |
| `project`     | keyword   | Project association       | Yes            |
| `timestamp`   | datetime  | Creation time             | Yes            |
| `tags`        | keyword[] | Categorical tags          | Yes            |
| `model`       | keyword   | Embedding model used      | Yes            |
| `token_count` | integer   | Token estimate            | Yes            |
| `user_id`     | keyword   | User association          | Yes (optional) |
| `session_id`  | keyword   | Session tracking          | Yes (optional) |

### Memory Types

| Type           | Description                    | Typical Retention |
| -------------- | ------------------------------ | ----------------- |
| `decision`     | Architectural/design decisions | Permanent         |
| `code`         | Code patterns and snippets     | 90 days           |
| `error`        | Error resolutions              | 60 days           |
| `conversation` | Key conversation points        | 30 days           |
| `technical`    | Technical documentation        | Permanent         |
| `cache`        | Semantic cache entries         | 7 days            |

---

## Semantic Cache Collection

Optimized for fast similarity lookups with high precision.

```json
PUT /collections/semantic_cache
{
  "vectors": {
    "size": 1536,
    "distance": "Cosine"
  },
  "optimizers_config": {
    "indexing_threshold": 5000,
    "memmap_threshold": 10000
  },
  "hnsw_config": {
    "m": 32,
    "ef_construct": 200,
    "full_scan_threshold": 5000
  }
}
```

### Cache Payload Schema

| Field         | Type     | Purpose                        |
| ------------- | -------- | ------------------------------ |
| `query`       | keyword  | Original query (for debugging) |
| `response`    | text     | Cached LLM response            |
| `timestamp`   | datetime | Cache entry time               |
| `model`       | keyword  | Model that generated response  |
| `token_count` | integer  | Response token count           |
| `ttl_days`    | integer  | Time-to-live in days           |

### Cache Hit Thresholds

| Similarity | Confidence | Action                        |
| ---------- | ---------- | ----------------------------- |
| ≥ 0.95     | Very High  | Return cached, log hit        |
| 0.90-0.94  | High       | Return cached with disclaimer |
| 0.85-0.89  | Medium     | Offer cached, allow refresh   |
| < 0.85     | Low        | Proceed to LLM                |

---

## Multi-Tenant Collection

For applications serving multiple users/projects.

```json
PUT /collections/multi_tenant_memory
{
  "vectors": {
    "size": 1536,
    "distance": "Cosine"
  },
  "optimizers_config": {
    "indexing_threshold": 20000
  },
  "hnsw_config": {
    "m": 16,
    "ef_construct": 128
  }
}
```

### Tenant Isolation Patterns

**Pattern 1: Payload Filtering**

```json
{
  "filter": {
    "must": [{ "key": "tenant_id", "match": { "value": "tenant_123" } }]
  }
}
```

**Pattern 2: Collection per Tenant**

```
tenant_123_memory/
tenant_456_memory/
tenant_789_memory/
```

### Recommended: Shard Key Optimization

For large multi-tenant deployments:

```json
{
  "shard_number": 4,
  "replication_factor": 2,
  "write_consistency_factor": 1
}
```

---

## Code Patterns Collection

Optimized for code snippet retrieval.

```json
PUT /collections/code_patterns
{
  "vectors": {
    "size": 1536,
    "distance": "Cosine"
  }
}
```

### Code Payload Schema

| Field          | Type    | Purpose                          |
| -------------- | ------- | -------------------------------- |
| `code`         | text    | The actual code                  |
| `language`     | keyword | Programming language             |
| `framework`    | keyword | Framework (React, FastAPI, etc.) |
| `pattern_type` | keyword | Pattern category                 |
| `description`  | text    | What the code does               |
| `file_path`    | keyword | Original file location           |
| `project`      | keyword | Source project                   |

### Pattern Types

- `api_endpoint`
- `database_query`
- `authentication`
- `error_handling`
- `data_transformation`
- `testing`
- `configuration`

---

## Indexing Best Practices

### When to Create Payload Indexes

```json
PUT /collections/{collection}/index
{
  "field_name": "type",
  "field_schema": "keyword"
}
```

**Index when**:

- Field is frequently filtered
- Field has high cardinality but limited unique values
- Field is used in range queries

**Don't index**:

- Large text fields (content, code)
- Fields rarely used in filters
- Fields with extremely high cardinality (UUIDs used once)

### HNSW Parameter Tuning

| Parameter      | Low Value | High Value | Trade-off              |
| -------------- | --------- | ---------- | ---------------------- |
| `m`            | 4         | 64         | Memory vs. Recall      |
| `ef_construct` | 50        | 500        | Index time vs. Quality |
| `ef` (search)  | 50        | 500        | Speed vs. Accuracy     |

**Recommended defaults**:

- Development: `m=16, ef_construct=100`
- Production: `m=32, ef_construct=200`
- High-precision: `m=48, ef_construct=400`
