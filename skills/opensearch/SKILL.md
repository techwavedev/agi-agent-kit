---
name: opensearch
description: OpenSearch specialist covering querying (Query DSL, SQL), performance optimization, cluster management, monitoring, OpenSearch Dashboards, ML/AI (neural search, embeddings, ML Commons), data ingestion (Logstash, Fluent Bit, Data Prepper), OpenSearch Operator for Kubernetes, and MCP integration. Use for any task involving: (1) Writing or optimizing OpenSearch queries, (2) Index design and mapping, (3) Cluster health and performance tuning, (4) OpenSearch Dashboards visualization, (5) Neural/semantic search with vectors, (6) Log and data ingestion pipelines, (7) Kubernetes deployments with OpenSearch Operator.
---

# OpenSearch Skill

Expert-level guidance for OpenSearch operations, from query optimization to ML-powered semantic search.

## Quick Reference

| Task           | Command/Tool           |
| -------------- | ---------------------- |
| Cluster Health | `GET _cluster/health`  |
| List Indices   | `GET _cat/indices?v`   |
| Index Mapping  | `GET <index>/_mapping` |
| Search         | `POST <index>/_search` |
| Bulk Ingest    | `POST _bulk`           |
| SQL Query      | `POST _plugins/_sql`   |

---

## MCP Server Configuration

### Option 1: Standalone MCP Server

```json
{
  "opensearch-mcp": {
    "command": "npx",
    "args": ["-y", "opensearch-mcp-server"],
    "env": {
      "OPENSEARCH_URL": "https://localhost:9200",
      "OPENSEARCH_USERNAME": "admin",
      "OPENSEARCH_PASSWORD": "${OPENSEARCH_PASSWORD}",
      "OPENSEARCH_SSL_VERIFY": "false"
    }
  }
}
```

### Option 2: Built-in MCP (OpenSearch 3.0+)

Enabled via ML Commons plugin. Configure in `opensearch.yml`:

```yaml
plugins.ml_commons.mcp_server.enabled: true
plugins.ml_commons.mcp_server.transport.port: 9600
```

Run `scripts/configure_mcp.py` to auto-configure.

---

## MCP Tools

| Tool                       | Purpose                        |
| -------------------------- | ------------------------------ |
| `ListIndexTool`            | List all indices with stats    |
| `IndexMappingTool`         | Get mapping for specific index |
| `SearchIndexTool`          | Execute Query DSL searches     |
| `ClusterHealthTool`        | Check cluster health status    |
| `CountTool`                | Count documents matching query |
| `ExplainTool`              | Explain query match scoring    |
| `MsearchTool`              | Execute multiple searches      |
| `GetShardsTool`            | Get shard information          |
| `GenericOpenSearchApiTool` | Call any OpenSearch API        |

---

## Query DSL Patterns

### Basic Match Query

```json
{
  "query": {
    "match": {
      "message": "error connection timeout"
    }
  }
}
```

### Bool Query (AND/OR/NOT)

```json
{
  "query": {
    "bool": {
      "must": [{ "match": { "status": "error" } }],
      "should": [
        { "match": { "service": "api-gateway" } },
        { "match": { "service": "auth-service" } }
      ],
      "must_not": [{ "term": { "environment": "development" } }],
      "filter": [{ "range": { "@timestamp": { "gte": "now-1h" } } }],
      "minimum_should_match": 1
    }
  }
}
```

### Aggregations

```json
{
  "size": 0,
  "aggs": {
    "status_codes": {
      "terms": { "field": "response.status_code" },
      "aggs": {
        "avg_duration": { "avg": { "field": "duration_ms" } }
      }
    },
    "requests_over_time": {
      "date_histogram": {
        "field": "@timestamp",
        "fixed_interval": "5m"
      }
    }
  }
}
```

### Full-Text with Highlighting

```json
{
  "query": {
    "multi_match": {
      "query": "kubernetes deployment failed",
      "fields": ["title^2", "description", "logs"]
    }
  },
  "highlight": {
    "fields": {
      "description": {},
      "logs": { "fragment_size": 150 }
    }
  }
}
```

See `references/query_dsl.md` for complete patterns.

---

## Index Design

### Mapping Best Practices

```json
PUT /logs-2024.01
{
  "settings": {
    "number_of_shards": 3,
    "number_of_replicas": 1,
    "refresh_interval": "30s",
    "index.mapping.total_fields.limit": 2000
  },
  "mappings": {
    "dynamic": "strict",
    "properties": {
      "@timestamp": { "type": "date" },
      "message": { "type": "text", "analyzer": "standard" },
      "level": { "type": "keyword" },
      "service": { "type": "keyword" },
      "trace_id": { "type": "keyword" },
      "duration_ms": { "type": "long" },
      "metadata": {
        "type": "object",
        "dynamic": true
      }
    }
  }
}
```

### Index Templates

```json
PUT _index_template/logs-template
{
  "index_patterns": ["logs-*"],
  "priority": 100,
  "template": {
    "settings": {
      "number_of_shards": 3,
      "number_of_replicas": 1
    },
    "mappings": {
      "properties": {
        "@timestamp": { "type": "date" },
        "message": { "type": "text" }
      }
    }
  }
}
```

### Index Lifecycle Management (ISM)

```json
PUT _plugins/_ism/policies/log-retention
{
  "policy": {
    "description": "Log retention policy",
    "default_state": "hot",
    "states": [
      {
        "name": "hot",
        "actions": [],
        "transitions": [
          { "state_name": "warm", "conditions": { "min_index_age": "7d" } }
        ]
      },
      {
        "name": "warm",
        "actions": [
          { "replica_count": { "number_of_replicas": 0 } },
          { "force_merge": { "max_num_segments": 1 } }
        ],
        "transitions": [
          { "state_name": "delete", "conditions": { "min_index_age": "30d" } }
        ]
      },
      {
        "name": "delete",
        "actions": [{ "delete": {} }]
      }
    ]
  }
}
```

---

## Performance Optimization

### Query Optimization

| Issue                 | Solution                                                |
| --------------------- | ------------------------------------------------------- |
| Slow full-text search | Use `keyword` for exact matches, limit `_source` fields |
| High memory usage     | Avoid `*` wildcards, use pagination with `search_after` |
| Slow aggregations     | Pre-aggregate with transforms, use `doc_values`         |
| Large result sets     | Use `scroll` or `point-in-time` for deep pagination     |

### Shard Sizing

- **Target:** 10-50GB per shard
- **Max docs:** ~2 billion per shard
- **Rule:** `shards = index_size / 30GB`

### Indexing Performance

```json
PUT /high-throughput-index/_settings
{
  "index": {
    "refresh_interval": "30s",
    "translog.durability": "async",
    "translog.sync_interval": "30s"
  }
}
```

### Search Performance

```json
{
  "_source": ["field1", "field2"],
  "track_total_hits": false,
  "size": 20,
  "query": { ... }
}
```

See `references/optimization.md` for detailed tuning guide.

---

## ML/AI & Neural Search

### Enable ML Commons

```yaml
# opensearch.yml
plugins.ml_commons.only_run_on_ml_node: false
plugins.ml_commons.model_access_control_enabled: true
plugins.ml_commons.native_memory_threshold: 90
```

### Deploy Embedding Model

```json
POST /_plugins/_ml/models/_register
{
  "name": "sentence-transformers/all-MiniLM-L6-v2",
  "version": "1.0.1",
  "model_format": "TORCH_SCRIPT",
  "model_config": {
    "model_type": "bert",
    "embedding_dimension": 384,
    "framework_type": "sentence_transformers"
  }
}
```

### Neural Search Pipeline

```json
PUT /_ingest/pipeline/neural-pipeline
{
  "description": "Generate embeddings for semantic search",
  "processors": [
    {
      "text_embedding": {
        "model_id": "<model_id>",
        "field_map": {
          "description": "description_embedding"
        }
      }
    }
  ]
}
```

### KNN Index for Vectors

```json
PUT /semantic-index
{
  "settings": {
    "index.knn": true,
    "default_pipeline": "neural-pipeline"
  },
  "mappings": {
    "properties": {
      "description": { "type": "text" },
      "description_embedding": {
        "type": "knn_vector",
        "dimension": 384,
        "method": {
          "name": "hnsw",
          "space_type": "cosinesimil",
          "engine": "nmslib",
          "parameters": {
            "ef_construction": 128,
            "m": 16
          }
        }
      }
    }
  }
}
```

### Semantic Search Query

```json
{
  "query": {
    "neural": {
      "description_embedding": {
        "query_text": "machine learning for log analysis",
        "model_id": "<model_id>",
        "k": 10
      }
    }
  }
}
```

### Hybrid Search (Semantic + Keyword)

```json
{
  "query": {
    "hybrid": {
      "queries": [
        {
          "match": {
            "description": "machine learning"
          }
        },
        {
          "neural": {
            "description_embedding": {
              "query_text": "machine learning",
              "model_id": "<model_id>",
              "k": 10
            }
          }
        }
      ]
    }
  }
}
```

See `references/ml_neural_search.md` for complete ML patterns.

---

## Data Ingestion

### Logstash Pipeline

```ruby
input {
  beats { port => 5044 }
}

filter {
  grok {
    match => { "message" => "%{TIMESTAMP_ISO8601:timestamp} %{LOGLEVEL:level} %{GREEDYDATA:message}" }
  }
  date {
    match => [ "timestamp", "ISO8601" ]
    target => "@timestamp"
  }
}

output {
  opensearch {
    hosts => ["https://opensearch:9200"]
    index => "logs-%{+YYYY.MM.dd}"
    user => "admin"
    password => "${OPENSEARCH_PASSWORD}"
    ssl => true
    ssl_certificate_verification => false
  }
}
```

### Fluent Bit

```ini
[OUTPUT]
    Name            opensearch
    Match           *
    Host            opensearch
    Port            9200
    Index           fluent-bit
    HTTP_User       admin
    HTTP_Passwd     ${OPENSEARCH_PASSWORD}
    tls             On
    tls.verify      Off
    Suppress_Type_Name On
```

### Data Prepper

```yaml
# data-prepper-config.yaml
log-pipeline:
  source:
    otel_logs_source:
      port: 21892
  processor:
    - grok:
        match:
          log: "%{TIMESTAMP_ISO8601:timestamp} %{LOGLEVEL:level}"
  sink:
    - opensearch:
        hosts: ["https://opensearch:9200"]
        username: "admin"
        password: "${OPENSEARCH_PASSWORD}"
        index: "otel-logs"
```

### Bulk API

```bash
curl -X POST "https://localhost:9200/_bulk" \
  -H "Content-Type: application/x-ndjson" \
  -u admin:$OPENSEARCH_PASSWORD \
  --data-binary @bulk-data.ndjson
```

```json
{"index":{"_index":"logs","_id":"1"}}
{"@timestamp":"2024-01-20T00:00:00Z","message":"Log entry 1"}
{"index":{"_index":"logs","_id":"2"}}
{"@timestamp":"2024-01-20T00:00:01Z","message":"Log entry 2"}
```

See `references/ingestion.md` for complete patterns.

---

## OpenSearch Dashboards

### Saved Search

Create reusable search definitions for:

- Log analysis patterns
- Error tracking queries
- Performance monitoring

### Visualizations

| Type       | Use Case                |
| ---------- | ----------------------- |
| Line       | Time-series metrics     |
| Bar        | Categorical comparisons |
| Pie        | Distribution            |
| Data Table | Detailed breakdowns     |
| Metric     | Single KPIs             |
| Gauge      | Threshold-based metrics |

### Dashboard Best Practices

1. **Limit visualizations**: 10-15 per dashboard
2. **Use time filters**: Global time picker for consistency
3. **Organize by role**: Create role-specific dashboards
4. **Performance**: Avoid expensive aggregations

---

## Cluster Monitoring

### Key Metrics

```bash
# Cluster health
GET _cluster/health

# Node stats
GET _nodes/stats

# Index stats
GET _stats

# Pending tasks
GET _cluster/pending_tasks

# Hot threads
GET _nodes/hot_threads
```

### Alert Conditions

| Metric           | Warning | Critical |
| ---------------- | ------- | -------- |
| Cluster Status   | Yellow  | Red      |
| Heap Usage       | 75%     | 90%      |
| Disk Usage       | 80%     | 90%      |
| Search Latency   | 500ms   | 2000ms   |
| Indexing Latency | 100ms   | 500ms    |

### Performance Analyzer

```bash
# Enable Performance Analyzer
curl -X POST "https://localhost:9200/_plugins/_performanceanalyzer/cluster/config" \
  -H "Content-Type: application/json" \
  -d '{"enabled": true}'
```

See `references/monitoring.md` for alerting setup.

---

## OpenSearch Operator (Kubernetes)

### Installation

```bash
# Add Helm repo
helm repo add opensearch-operator https://opster.github.io/opensearch-k8s-operator/
helm repo update

# Install operator
helm install opensearch-operator opensearch-operator/opensearch-operator \
  --namespace opensearch-operator-system \
  --create-namespace
```

### Cluster CRD

```yaml
apiVersion: opensearch.opster.io/v1
kind: OpenSearchCluster
metadata:
  name: my-cluster
  namespace: opensearch
spec:
  general:
    serviceName: my-cluster
    version: 2.11.0
    httpPort: 9200
    vendor: opensearch
    setVMMaxMapCount: true
  dashboards:
    enable: true
    replicas: 1
    version: 2.11.0
  nodePools:
    - component: masters
      replicas: 3
      diskSize: "30Gi"
      roles:
        - master
        - data
      resources:
        requests:
          memory: "4Gi"
          cpu: "1000m"
        limits:
          memory: "4Gi"
          cpu: "2000m"
      persistence:
        storageClass: gp3
        accessModes:
          - ReadWriteOnce
```

### Security Configuration

```yaml
spec:
  security:
    config:
      securityConfigSecret:
        name: security-config
      adminCredentialsSecret:
        name: admin-credentials
    tls:
      transport:
        generate: true
      http:
        generate: true
```

See `references/operator.md` for complete Kubernetes patterns.

---

## Testing

### Query Validation

```bash
# Validate query syntax
POST /index/_validate/query?explain=true
{
  "query": { "match": { "field": "value" } }
}

# Profile query execution
POST /index/_search
{
  "profile": true,
  "query": { ... }
}
```

### Performance Testing

```bash
# opensearch-benchmark (rally fork)
opensearch-benchmark execute-test \
  --pipeline=benchmark-only \
  --target-hosts=https://localhost:9200 \
  --client-options="use_ssl:true,verify_certs:false,basic_auth_user:'admin',basic_auth_password:'admin'"
```

---

## Security

### Authentication

| Method         | Configuration               |
| -------------- | --------------------------- |
| Internal Users | `internal_users.yml`        |
| LDAP           | `config.yml` ldap section   |
| SAML           | `config.yml` saml section   |
| OpenID         | `config.yml` openid section |

### Role-Based Access Control

```yaml
# roles.yml
log_reader:
  cluster_permissions:
    - cluster_composite_ops_ro
  index_permissions:
    - index_patterns:
        - "logs-*"
      allowed_actions:
        - read
        - search
```

### Field-Level Security

```yaml
index_permissions:
  - index_patterns: ["sensitive-*"]
    allowed_actions: ["read"]
    fls:
      - "~password"
      - "~ssn"
```

---

## References

- [OpenSearch Documentation](https://opensearch.org/docs/latest/)
- [Query DSL Reference](https://opensearch.org/docs/latest/query-dsl/)
- [ML Commons](https://opensearch.org/docs/latest/ml-commons-plugin/index/)
- [OpenSearch Operator GitHub](https://github.com/opensearch-project/opensearch-k8s-operator)
- [OpenSearch Operator Docs](https://docs.opensearch.org/latest/install-and-configure/install-opensearch/operator/)
- See `references/` for detailed guides
