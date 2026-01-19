# Query DSL Reference

Complete reference for OpenSearch Query DSL patterns.

## Full-Text Queries

### Match Query

```json
{
  "query": {
    "match": {
      "message": {
        "query": "error connection",
        "operator": "and",
        "fuzziness": "AUTO"
      }
    }
  }
}
```

### Multi-Match Query

```json
{
  "query": {
    "multi_match": {
      "query": "kubernetes deployment",
      "fields": ["title^3", "description^2", "content"],
      "type": "best_fields",
      "tie_breaker": 0.3
    }
  }
}
```

**Types:**

- `best_fields` - Score from best matching field
- `most_fields` - Combine scores from all fields
- `cross_fields` - Treat fields as one field
- `phrase` - Match as phrase
- `phrase_prefix` - Match phrase prefix

### Match Phrase

```json
{
  "query": {
    "match_phrase": {
      "message": {
        "query": "connection timed out",
        "slop": 2
      }
    }
  }
}
```

### Query String

```json
{
  "query": {
    "query_string": {
      "query": "status:error AND service:(api OR auth)",
      "default_field": "message",
      "analyze_wildcard": true
    }
  }
}
```

---

## Term-Level Queries

### Term Query (Exact Match)

```json
{
  "query": {
    "term": {
      "status.keyword": "ERROR"
    }
  }
}
```

### Terms Query (Multiple Values)

```json
{
  "query": {
    "terms": {
      "service": ["api-gateway", "auth-service", "user-service"]
    }
  }
}
```

### Range Query

```json
{
  "query": {
    "range": {
      "@timestamp": {
        "gte": "now-1h",
        "lt": "now",
        "time_zone": "+01:00"
      }
    }
  }
}
```

```json
{
  "query": {
    "range": {
      "response_time_ms": {
        "gte": 500,
        "lte": 5000
      }
    }
  }
}
```

### Exists Query

```json
{
  "query": {
    "exists": {
      "field": "error.stack_trace"
    }
  }
}
```

### Prefix Query

```json
{
  "query": {
    "prefix": {
      "hostname.keyword": "prod-api-"
    }
  }
}
```

### Wildcard Query

```json
{
  "query": {
    "wildcard": {
      "email.keyword": "*@company.com"
    }
  }
}
```

### Regexp Query

```json
{
  "query": {
    "regexp": {
      "trace_id": "[a-f0-9]{32}"
    }
  }
}
```

---

## Compound Queries

### Bool Query

```json
{
  "query": {
    "bool": {
      "must": [
        { "match": { "status": "error" } },
        { "range": { "@timestamp": { "gte": "now-24h" } } }
      ],
      "should": [
        { "term": { "priority": "high" } },
        { "term": { "priority": "critical" } }
      ],
      "must_not": [{ "term": { "acknowledged": true } }],
      "filter": [{ "term": { "environment": "production" } }],
      "minimum_should_match": 1,
      "boost": 1.0
    }
  }
}
```

**Clauses:**

- `must` - Must match, contributes to score
- `should` - Optional, contributes to score
- `must_not` - Must not match, no scoring
- `filter` - Must match, no scoring (cached)

### Boosting Query

```json
{
  "query": {
    "boosting": {
      "positive": {
        "match": { "content": "kubernetes" }
      },
      "negative": {
        "term": { "deprecated": true }
      },
      "negative_boost": 0.5
    }
  }
}
```

### Constant Score

```json
{
  "query": {
    "constant_score": {
      "filter": {
        "term": { "status": "published" }
      },
      "boost": 1.2
    }
  }
}
```

### Dis Max Query

```json
{
  "query": {
    "dis_max": {
      "queries": [
        { "match": { "title": "kubernetes" } },
        { "match": { "body": "kubernetes" } }
      ],
      "tie_breaker": 0.7
    }
  }
}
```

---

## Aggregations

### Bucket Aggregations

```json
{
  "size": 0,
  "aggs": {
    "by_service": {
      "terms": {
        "field": "service.keyword",
        "size": 20,
        "order": { "_count": "desc" }
      }
    },
    "by_hour": {
      "date_histogram": {
        "field": "@timestamp",
        "fixed_interval": "1h",
        "min_doc_count": 0,
        "extended_bounds": {
          "min": "now-24h",
          "max": "now"
        }
      }
    },
    "response_ranges": {
      "range": {
        "field": "response_time_ms",
        "ranges": [
          { "to": 100, "key": "fast" },
          { "from": 100, "to": 500, "key": "normal" },
          { "from": 500, "key": "slow" }
        ]
      }
    }
  }
}
```

### Metric Aggregations

```json
{
  "size": 0,
  "aggs": {
    "avg_response": { "avg": { "field": "response_time_ms" } },
    "max_response": { "max": { "field": "response_time_ms" } },
    "min_response": { "min": { "field": "response_time_ms" } },
    "sum_bytes": { "sum": { "field": "bytes_transferred" } },
    "request_count": { "value_count": { "field": "request_id" } },
    "unique_users": { "cardinality": { "field": "user_id" } },
    "response_stats": { "stats": { "field": "response_time_ms" } },
    "percentiles": {
      "percentiles": {
        "field": "response_time_ms",
        "percents": [50, 90, 95, 99]
      }
    }
  }
}
```

### Nested Aggregations

```json
{
  "size": 0,
  "aggs": {
    "by_service": {
      "terms": { "field": "service.keyword" },
      "aggs": {
        "by_status": {
          "terms": { "field": "status.keyword" },
          "aggs": {
            "avg_duration": { "avg": { "field": "duration_ms" } }
          }
        },
        "error_rate": {
          "filter": { "term": { "status": "error" } },
          "aggs": {
            "count": { "value_count": { "field": "_id" } }
          }
        }
      }
    }
  }
}
```

### Pipeline Aggregations

```json
{
  "size": 0,
  "aggs": {
    "by_hour": {
      "date_histogram": {
        "field": "@timestamp",
        "fixed_interval": "1h"
      },
      "aggs": {
        "avg_latency": { "avg": { "field": "latency_ms" } },
        "latency_diff": {
          "derivative": { "buckets_path": "avg_latency" }
        },
        "moving_avg_latency": {
          "moving_avg": {
            "buckets_path": "avg_latency",
            "window": 5
          }
        }
      }
    }
  }
}
```

---

## Pagination

### Standard Pagination

```json
{
  "from": 0,
  "size": 20,
  "query": { ... }
}
```

**Limit:** `from + size` ≤ 10,000 by default.

### Search After (Deep Pagination)

```json
{
  "size": 20,
  "sort": [
    { "@timestamp": "desc" },
    { "_id": "asc" }
  ],
  "search_after": ["2024-01-20T00:00:00.000Z", "doc123"],
  "query": { ... }
}
```

### Scroll API (Bulk Export)

```bash
# Initial request
POST /logs/_search?scroll=5m
{
  "size": 1000,
  "query": { "match_all": {} }
}

# Continue with scroll_id
POST /_search/scroll
{
  "scroll": "5m",
  "scroll_id": "<scroll_id>"
}

# Clear scroll
DELETE /_search/scroll
{
  "scroll_id": ["<scroll_id>"]
}
```

### Point in Time (PIT)

```bash
# Create PIT
POST /logs/_pit?keep_alive=5m

# Search with PIT
POST /_search
{
  "pit": {
    "id": "<pit_id>",
    "keep_alive": "5m"
  },
  "size": 100,
  "query": { ... },
  "search_after": [...]
}

# Delete PIT
DELETE /_pit
{
  "id": "<pit_id>"
}
```

---

## Scoring & Relevance

### Function Score

```json
{
  "query": {
    "function_score": {
      "query": { "match": { "title": "kubernetes" } },
      "functions": [
        {
          "filter": { "term": { "featured": true } },
          "weight": 2
        },
        {
          "field_value_factor": {
            "field": "popularity",
            "factor": 1.2,
            "modifier": "sqrt",
            "missing": 1
          }
        },
        {
          "gauss": {
            "publish_date": {
              "origin": "now",
              "scale": "7d",
              "decay": 0.5
            }
          }
        }
      ],
      "score_mode": "multiply",
      "boost_mode": "multiply"
    }
  }
}
```

### Explain Query

```json
POST /index/_explain/doc_id
{
  "query": {
    "match": { "title": "kubernetes" }
  }
}
```

---

## SQL Plugin

```json
POST /_plugins/_sql
{
  "query": "SELECT service, COUNT(*) as count, AVG(response_time_ms) as avg_response FROM logs WHERE status = 'error' AND @timestamp > NOW() - INTERVAL 1 HOUR GROUP BY service ORDER BY count DESC LIMIT 10"
}
```

### SQL to DSL Translation

```json
POST /_plugins/_sql/_explain
{
  "query": "SELECT * FROM logs WHERE status = 'error'"
}
```
