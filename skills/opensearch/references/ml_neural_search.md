# ML/AI & Neural Search Reference

Comprehensive guide for machine learning and semantic search in OpenSearch.

## ML Commons Plugin

### Enable ML Commons

```yaml
# opensearch.yml
plugins.ml_commons.only_run_on_ml_node: false
plugins.ml_commons.model_access_control_enabled: true
plugins.ml_commons.native_memory_threshold: 90
plugins.ml_commons.allow_registering_model_via_url: true
```

### Cluster Settings

```json
PUT /_cluster/settings
{
  "persistent": {
    "plugins.ml_commons.only_run_on_ml_node": false,
    "plugins.ml_commons.model_access_control_enabled": true,
    "plugins.ml_commons.native_memory_threshold": 90
  }
}
```

---

## Model Management

### List Models

```json
GET /_plugins/_ml/models/_search
{
  "query": { "match_all": {} },
  "size": 100
}
```

### Register Model (Local)

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

### Register Model (Remote/Connector)

```json
POST /_plugins/_ml/connectors/_create
{
  "name": "Amazon Bedrock Titan Embeddings",
  "description": "Connector for Titan embedding model",
  "version": "1.0",
  "protocol": "aws_sigv4",
  "credential": {
    "access_key": "${aws.access_key}",
    "secret_key": "${aws.secret_key}"
  },
  "parameters": {
    "region": "us-east-1",
    "service_name": "bedrock"
  },
  "actions": [
    {
      "action_type": "predict",
      "method": "POST",
      "url": "https://bedrock-runtime.us-east-1.amazonaws.com/model/amazon.titan-embed-text-v1/invoke",
      "headers": {
        "Content-Type": "application/json"
      },
      "request_body": "{ \"inputText\": \"${parameters.inputText}\" }",
      "pre_process_function": "connector.pre_process.bedrock.embedding",
      "post_process_function": "connector.post_process.bedrock.embedding"
    }
  ]
}
```

### Deploy Model

```json
POST /_plugins/_ml/models/<model_id>/_deploy
```

### Undeploy Model

```json
POST /_plugins/_ml/models/<model_id>/_undeploy
```

### Delete Model

```json
DELETE /_plugins/_ml/models/<model_id>
```

---

## Pre-trained Models

### Recommended Models

| Model                                   | Dimensions | Use Case               |
| --------------------------------------- | ---------- | ---------------------- |
| `all-MiniLM-L6-v2`                      | 384        | Fast, general purpose  |
| `all-mpnet-base-v2`                     | 768        | Higher quality, slower |
| `paraphrase-multilingual-MiniLM-L12-v2` | 384        | Multilingual support   |
| `msmarco-distilbert-base-tas-b`         | 768        | Passage retrieval      |

### Register Pre-trained Model

```json
POST /_plugins/_ml/models/_register
{
  "name": "huggingface/sentence-transformers/all-MiniLM-L6-v2",
  "version": "1.0.1",
  "model_group_id": "<model_group_id>",
  "model_format": "TORCH_SCRIPT"
}
```

---

## Neural Search Pipelines

### Create Ingest Pipeline

```json
PUT /_ingest/pipeline/neural-search-pipeline
{
  "description": "Pipeline for neural search embeddings",
  "processors": [
    {
      "text_embedding": {
        "model_id": "<model_id>",
        "field_map": {
          "title": "title_embedding",
          "description": "description_embedding"
        }
      }
    }
  ]
}
```

### Multi-field Pipeline

```json
PUT /_ingest/pipeline/multi-field-embedding
{
  "description": "Generate embeddings for multiple fields",
  "processors": [
    {
      "text_embedding": {
        "model_id": "<model_id>",
        "field_map": {
          "title": "title_embedding"
        }
      }
    },
    {
      "text_embedding": {
        "model_id": "<model_id>",
        "field_map": {
          "content": "content_embedding"
        }
      }
    }
  ]
}
```

### Search Pipeline (Query-time Embedding)

```json
PUT /_search/pipeline/neural-search-pipeline
{
  "request_processors": [
    {
      "neural_query_enricher": {
        "neural_field_default_id": {
          "description_embedding": "<model_id>"
        }
      }
    }
  ]
}
```

---

## KNN Index Configuration

### Create KNN Index

```json
PUT /semantic-products
{
  "settings": {
    "index": {
      "knn": true,
      "knn.algo_param.ef_search": 100,
      "default_pipeline": "neural-search-pipeline"
    }
  },
  "mappings": {
    "properties": {
      "title": { "type": "text" },
      "description": { "type": "text" },
      "title_embedding": {
        "type": "knn_vector",
        "dimension": 384,
        "method": {
          "name": "hnsw",
          "space_type": "l2",
          "engine": "lucene",
          "parameters": {
            "ef_construction": 128,
            "m": 16
          }
        }
      },
      "description_embedding": {
        "type": "knn_vector",
        "dimension": 384,
        "method": {
          "name": "hnsw",
          "space_type": "cosinesimil",
          "engine": "nmslib",
          "parameters": {
            "ef_construction": 256,
            "m": 24
          }
        }
      }
    }
  }
}
```

### KNN Engines

| Engine   | Best For          | Space Types                   |
| -------- | ----------------- | ----------------------------- |
| `lucene` | General use, HNSW | l2, cosinesimil               |
| `nmslib` | High recall       | l2, cosinesimil, innerproduct |
| `faiss`  | Large scale       | l2, innerproduct              |

### Space Types

| Space Type     | Description        |
| -------------- | ------------------ |
| `l2`           | Euclidean distance |
| `cosinesimil`  | Cosine similarity  |
| `innerproduct` | Dot product        |

---

## Neural Search Queries

### Basic Neural Query

```json
POST /semantic-products/_search
{
  "query": {
    "neural": {
      "description_embedding": {
        "query_text": "comfortable running shoes for marathon",
        "model_id": "<model_id>",
        "k": 10
      }
    }
  }
}
```

### Neural with Filter

```json
POST /semantic-products/_search
{
  "query": {
    "neural": {
      "description_embedding": {
        "query_text": "durable hiking boots",
        "model_id": "<model_id>",
        "k": 20,
        "filter": {
          "bool": {
            "must": [
              { "term": { "category": "footwear" } },
              { "range": { "price": { "lte": 200 } } }
            ]
          }
        }
      }
    }
  }
}
```

### KNN Query (Pre-computed Vector)

```json
POST /semantic-products/_search
{
  "query": {
    "knn": {
      "description_embedding": {
        "vector": [0.1, 0.2, 0.3, ...],
        "k": 10
      }
    }
  }
}
```

---

## Hybrid Search

### Neural + Keyword (Simple)

```json
POST /semantic-products/_search
{
  "query": {
    "hybrid": {
      "queries": [
        {
          "match": {
            "title": {
              "query": "running shoes",
              "boost": 0.3
            }
          }
        },
        {
          "neural": {
            "description_embedding": {
              "query_text": "running shoes",
              "model_id": "<model_id>",
              "k": 50
            }
          }
        }
      ]
    }
  }
}
```

### Hybrid with Normalization

```json
PUT /_search/pipeline/hybrid-pipeline
{
  "description": "Hybrid search with score normalization",
  "phase_results_processors": [
    {
      "normalization-processor": {
        "normalization": {
          "technique": "min_max"
        },
        "combination": {
          "technique": "arithmetic_mean",
          "parameters": {
            "weights": [0.3, 0.7]
          }
        }
      }
    }
  ]
}
```

```json
POST /semantic-products/_search?search_pipeline=hybrid-pipeline
{
  "query": {
    "hybrid": {
      "queries": [
        { "match": { "title": "running shoes" } },
        {
          "neural": {
            "description_embedding": {
              "query_text": "running shoes",
              "model_id": "<model_id>",
              "k": 50
            }
          }
        }
      ]
    }
  }
}
```

### Normalization Techniques

| Technique | Description                  |
| --------- | ---------------------------- |
| `min_max` | Scale scores to [0, 1] range |
| `l2`      | L2 normalization             |

### Combination Techniques

| Technique         | Description                 |
| ----------------- | --------------------------- |
| `arithmetic_mean` | Simple average with weights |
| `geometric_mean`  | Geometric average           |
| `harmonic_mean`   | Harmonic average            |

---

## Semantic Highlighting (Experimental)

```json
POST /semantic-products/_search
{
  "query": {
    "neural": {
      "description_embedding": {
        "query_text": "comfortable shoes",
        "model_id": "<model_id>",
        "k": 10
      }
    }
  },
  "highlight": {
    "fields": {
      "description": {}
    }
  }
}
```

---

## Reranking

### Cross-Encoder Reranking

```json
PUT /_search/pipeline/rerank-pipeline
{
  "response_processors": [
    {
      "rerank": {
        "ml_opensearch": {
          "model_id": "<cross_encoder_model_id>"
        },
        "context": {
          "document_fields": ["title", "description"]
        }
      }
    }
  ]
}
```

---

## Performance Tuning

### Index Settings

```json
PUT /semantic-index/_settings
{
  "index": {
    "knn.algo_param.ef_search": 100,
    "knn.space_type": "cosinesimil"
  }
}
```

### Reduce Memory Usage

```json
PUT /semantic-index
{
  "mappings": {
    "properties": {
      "embedding": {
        "type": "knn_vector",
        "dimension": 384,
        "data_type": "float16"  // Use 16-bit floats
      }
    }
  }
}
```

### Batch Indexing

```json
POST /_bulk
{"index":{"_index":"semantic-products","_id":"1","pipeline":"neural-search-pipeline"}}
{"title":"Running Shoes","description":"Lightweight and comfortable"}
{"index":{"_index":"semantic-products","_id":"2","pipeline":"neural-search-pipeline"}}
{"title":"Hiking Boots","description":"Durable and waterproof"}
```

---

## Model Monitoring

### Check Model Status

```json
GET /_plugins/_ml/models/<model_id>
```

### Model Stats

```json
GET /_plugins/_ml/models/<model_id>/_stats
```

### Profile Inference

```json
POST /_plugins/_ml/models/<model_id>/_predict
{
  "parameters": {
    "texts": ["Sample text to embed"]
  }
}
```

---

## Troubleshooting

### Model Not Found

```bash
# Check if model is registered
GET /_plugins/_ml/models/_search

# Check if model is deployed
GET /_plugins/_ml/models/<model_id>/_status
```

### Out of Memory

```yaml
# Increase native memory threshold
plugins.ml_commons.native_memory_threshold: 95

# Or use dedicated ML nodes
plugins.ml_commons.only_run_on_ml_node: true
```

### Slow Inference

1. Check model deployment status
2. Use smaller model (e.g., MiniLM instead of mpnet)
3. Batch requests when possible
4. Use dedicated ML nodes
