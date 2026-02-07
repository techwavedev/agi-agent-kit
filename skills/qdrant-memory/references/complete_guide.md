# Qdrant Memory Skill - Complete Guide

Complete setup, usage, and testing documentation for the Qdrant-powered token optimization system.

---

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Qdrant Setup](#qdrant-setup)
4. [Environment Configuration](#environment-configuration)
5. [Collection Initialization](#collection-initialization)
6. [Usage Guide](#usage-guide)
7. [Testing](#testing)
8. [Troubleshooting](#troubleshooting)
9. [Production Considerations](#production-considerations)

---

## Overview

The Qdrant Memory Skill provides intelligent token optimization through:

| Feature              | Token Savings | Use Case                                     |
| -------------------- | ------------- | -------------------------------------------- |
| **Semantic Cache**   | 100%          | Avoid LLM calls for repeated/similar queries |
| **Long-Term Memory** | 80-95%        | Retrieve only relevant context chunks        |
| **Hybrid Search**    | 87%           | Combine vectors with keyword filtering       |

### Architecture

```
USER QUERY
    │
    ▼
┌─────────────────────────────┐
│  1. Semantic Cache Check    │ ──── Cache Hit? → Return cached (100% savings)
└─────────────────────────────┘
    │ Cache Miss
    ▼
┌─────────────────────────────┐
│  2. Context Retrieval       │ ──── Retrieve top-K relevant chunks
└─────────────────────────────┘
    │
    ▼
┌─────────────────────────────┐
│  3. LLM Call (optimized)    │ ──── Only 1K tokens instead of 20K
└─────────────────────────────┘
```

---

## Prerequisites

### Required

- **Python 3.9+** with pip
- **OpenAI API Key** (for embeddings)
- **Docker** (for local Qdrant) OR **Qdrant Cloud** account

### Optional

- Node.js 18+ (for MCP server)
- Local embedding models (for offline use)

### Python Dependencies

```bash
# Required for scripts
pip install requests

# Optional for local embeddings
pip install sentence-transformers torch
```

---

## Qdrant Setup

### Option 1: Docker (Recommended for Development)

```bash
# Pull and run Qdrant
docker run -d \
  --name qdrant \
  -p 6333:6333 \
  -p 6334:6334 \
  -v $(pwd)/qdrant_storage:/qdrant/storage:z \
  qdrant/qdrant:latest

# Verify it's running
curl http://localhost:6333/health
# Expected: {"title":"qdrant - vector search engine","version":"..."}
```

### Option 2: Docker Compose

Create `docker-compose.qdrant.yml`:

```yaml
version: "3.8"
services:
  qdrant:
    image: qdrant/qdrant:latest
    container_name: qdrant
    ports:
      - "6333:6333" # REST API
      - "6334:6334" # gRPC
    volumes:
      - ./qdrant_storage:/qdrant/storage
    environment:
      - QDRANT__SERVICE__GRPC_PORT=6334
      - QDRANT__SERVICE__HTTP_PORT=6333
      # Uncomment for API key protection
      # - QDRANT__SERVICE__API_KEY=your-secret-key
    restart: unless-stopped
```

Run:

```bash
docker compose -f docker-compose.qdrant.yml up -d
```

### Option 3: Qdrant Cloud (Production)

1. Create account at [cloud.qdrant.io](https://cloud.qdrant.io)
2. Create a cluster (Free tier available)
3. Get your cluster URL and API key
4. Configure environment:

```bash
export QDRANT_URL="https://your-cluster-id.us-east4-0.gcp.cloud.qdrant.io:6333"
export QDRANT_API_KEY="your-api-key"
```

### Option 4: Kubernetes (EKS/Production)

```bash
# Add Qdrant Helm repo
helm repo add qdrant https://qdrant.github.io/qdrant-helm
helm repo update

# Install Qdrant
helm install qdrant qdrant/qdrant \
  --namespace qdrant \
  --create-namespace \
  --set replicaCount=3 \
  --set persistence.size=10Gi \
  --set service.type=ClusterIP
```

---

## Environment Configuration

### Create Environment File

```bash
# Create .env file in your project
cat > .env.qdrant << 'EOF'
# Qdrant Configuration
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=

# Collections
MEMORY_COLLECTION=agent_memory
CACHE_COLLECTION=semantic_cache

# OpenAI Configuration
OPENAI_API_KEY=sk-your-api-key-here
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIMENSION=1536

# Cache Settings
CACHE_THRESHOLD=0.92
CACHE_TTL_DAYS=7

# Memory Settings
MEMORY_TOP_K=5
MEMORY_THRESHOLD=0.7
EOF
```

### Load Environment

```bash
# In your shell
source .env.qdrant
export $(grep -v '^#' .env.qdrant | xargs)
```

### MCP Server Configuration

Add to your Claude Desktop or MCP config:

```json
{
  "mcpServers": {
    "qdrant-memory": {
      "command": "npx",
      "args": ["-y", "@qdrant/mcp-server-qdrant"],
      "env": {
        "QDRANT_URL": "http://localhost:6333",
        "QDRANT_API_KEY": "",
        "COLLECTION_NAME": "agent_memory"
      }
    }
  }
}
```

---

## Collection Initialization

### Initialize Collections

Navigate to the skill directory and run:

```bash
cd /path/to/agi/skills/qdrant-memory

# Initialize main memory collection
python scripts/init_collection.py \
  --collection agent_memory \
  --dimension 1536 \
  --distance cosine

# Initialize semantic cache collection
python scripts/init_collection.py \
  --collection semantic_cache \
  --dimension 1536 \
  --distance cosine
```

Expected output:

```
🔧 Initializing collection: agent_memory
   URL: http://localhost:6333
   Dimension: 1536
   Distance: cosine
✅ Collection created: {'status': 'ok', 'result': True}
📑 Creating payload indexes...
   type: created
   project: created
   timestamp: created
   tags: created
   model: created
   token_count: created
   score_threshold: created
{"status": "success", "collection": "agent_memory", "dimension": 1536, "distance": "cosine"}
```

### Verify Collections

```bash
# Check collections exist
curl http://localhost:6333/collections | jq

# Check specific collection
curl http://localhost:6333/collections/agent_memory | jq
```

---

## Usage Guide

### 1. Semantic Cache - 100% Token Savings

#### Check Cache Before LLM Call

```bash
# Check if a similar query exists
python scripts/semantic_cache.py check \
  --query "How do I reset my password?" \
  --threshold 0.92
```

**Cache Hit Response:**

```json
{
  "cache_hit": true,
  "score": 0.94,
  "query": "How can I reset my password?",
  "response": "To reset your password, go to Settings > Account > Reset Password...",
  "timestamp": "2026-01-22T10:30:00Z",
  "tokens_saved": 150
}
```

**Cache Miss Response:**

```json
{
  "cache_hit": false,
  "query": "How do I reset my password?"
}
```

#### Store Response in Cache

```bash
# After LLM generates a response, cache it
python scripts/semantic_cache.py store \
  --query "How do I reset my password?" \
  --response "To reset your password, navigate to Settings > Account > Reset Password. Click the 'Reset' button and follow the email instructions." \
  --model gpt-4 \
  --project api-catalogue
```

#### Clear Old Cache Entries

```bash
# Remove entries older than 7 days
python scripts/semantic_cache.py clear --older-than 7
```

### 2. Long-Term Memory - Context Optimization

#### Store a Memory

```bash
python scripts/memory_retrieval.py store \
  --content "We decided to use PostgreSQL for the user database due to ACID compliance requirements. MongoDB was considered but rejected for this use case." \
  --type decision \
  --project api-catalogue \
  --tags database architecture
```

#### Retrieve Relevant Context

```bash
# Retrieve memories about database decisions
python scripts/memory_retrieval.py retrieve \
  --query "What database did we choose and why?" \
  --type decision \
  --project api-catalogue \
  --top-k 5 \
  --threshold 0.7
```

**Response:**

```json
{
  "chunks": [
    {
      "content": "We decided to use PostgreSQL for the user database...",
      "score": 0.89,
      "type": "decision",
      "project": "api-catalogue",
      "timestamp": "2026-01-22T10:30:00Z",
      "tags": ["database", "architecture"],
      "token_estimate": 35
    }
  ],
  "total_chunks": 1,
  "total_tokens_estimate": 35,
  "query": "What database did we choose and why?"
}
```

#### List Memories

```bash
# List all decision memories for a project
python scripts/memory_retrieval.py list \
  --type decision \
  --project api-catalogue \
  --limit 20
```

### 3. Hybrid Search - Vector + Keyword

```bash
# Search for Kubernetes errors with specific error code
python scripts/hybrid_search.py \
  --query "kubernetes deployment failed" \
  --keyword error_code=ImagePullBackOff \
  --keyword namespace=production \
  --top-k 5 \
  --threshold 0.6
```

---

## Testing

### Test 1: Verify Qdrant Connection

```bash
# Check Qdrant health
curl -s http://localhost:6333/health | jq
```

Expected:

```json
{
  "title": "qdrant - vector search engine",
  "version": "1.x.x"
}
```

### Test 2: Collection Initialization

```bash
# Create test collection
python scripts/init_collection.py \
  --collection test_collection \
  --dimension 1536

# Verify
curl -s http://localhost:6333/collections/test_collection | jq '.result.status'
# Expected: "green"

# Cleanup
curl -X DELETE http://localhost:6333/collections/test_collection
```

### Test 3: Semantic Cache Round-Trip

```bash
export OPENAI_API_KEY="sk-your-key"

# Store a test response
python scripts/semantic_cache.py store \
  --query "What is the capital of France?" \
  --response "The capital of France is Paris." \
  --model gpt-4

# Check cache hit with exact query
python scripts/semantic_cache.py check \
  --query "What is the capital of France?" \
  --threshold 0.9

# Check cache hit with similar query
python scripts/semantic_cache.py check \
  --query "What's France's capital city?" \
  --threshold 0.85
```

### Test 4: Memory Storage and Retrieval

```bash
# Store test memories
python scripts/memory_retrieval.py store \
  --content "We implemented JWT authentication with RS256 signing." \
  --type decision \
  --project test-project \
  --tags auth security

python scripts/memory_retrieval.py store \
  --content "The API rate limit is set to 100 requests per minute per user." \
  --type technical \
  --project test-project \
  --tags api limits

# Retrieve by type
python scripts/memory_retrieval.py retrieve \
  --query "How is authentication implemented?" \
  --type decision \
  --top-k 3

# Retrieve without filter
python scripts/memory_retrieval.py retrieve \
  --query "API request limits" \
  --top-k 3
```

### Test 5: Hybrid Search

```bash
# Store test data with specific metadata
python scripts/memory_retrieval.py store \
  --content "Error: ImagePullBackOff in production namespace for api-gateway deployment" \
  --type error \
  --project kubernetes \
  --tags production error

# Hybrid search with keyword filter
python scripts/hybrid_search.py \
  --query "image pull error" \
  --keyword type=error \
  --top-k 5
```

### Test 6: End-to-End Token Savings Simulation

```bash
#!/bin/bash
# test_token_savings.sh

echo "=== Token Savings Simulation ==="

# Simulate first query (cache miss)
echo "1. First query (should be cache miss):"
python scripts/semantic_cache.py check \
  --query "Explain the architecture of our authentication system" \
  --threshold 0.9
echo ""

# Simulate LLM response and store
echo "2. Storing LLM response in cache:"
python scripts/semantic_cache.py store \
  --query "Explain the architecture of our authentication system" \
  --response "Our authentication system uses JWT tokens with RS256 signing. The flow is: 1) User submits credentials, 2) Server validates and issues JWT, 3) Client stores token, 4) Token is passed in Authorization header for subsequent requests. The token expires after 1 hour and can be refreshed using a refresh token." \
  --model gpt-4
echo ""

# Simulate similar query (should be cache hit)
echo "3. Similar query (should be cache hit - 100% savings):"
python scripts/semantic_cache.py check \
  --query "How does our auth system work?" \
  --threshold 0.85

echo ""
echo "=== Test Complete ==="
```

---

## Troubleshooting

### Connection Errors

```
Error: Cannot connect to Qdrant at http://localhost:6333
```

**Solutions:**

1. Verify Qdrant is running:

   ```bash
   docker ps | grep qdrant
   ```

2. Check port binding:

   ```bash
   curl http://localhost:6333/health
   ```

3. Check firewall/network:
   ```bash
   netstat -an | grep 6333
   ```

### Embedding Errors

```
Error: OPENAI_API_KEY environment variable not set
```

**Solution:**

```bash
export OPENAI_API_KEY="sk-your-key-here"
```

### Collection Not Found

```
Error: Collection 'agent_memory' not found
```

**Solution:**

```bash
python scripts/init_collection.py --collection agent_memory --dimension 1536
```

### Low Similarity Scores

If cache hits are rare:

1. Lower the threshold:

   ```bash
   python scripts/semantic_cache.py check --query "..." --threshold 0.8
   ```

2. Check embedding model consistency (use same model for store and search)

3. Verify content quality (longer, more detailed text = better matching)

### Memory Issues with Large Collections

For collections > 1M vectors:

```bash
# Enable disk-based index
curl -X PATCH http://localhost:6333/collections/agent_memory \
  -H "Content-Type: application/json" \
  -d '{
    "optimizers_config": {
      "memmap_threshold": 10000
    }
  }'
```

---

## Production Considerations

### High Availability

```yaml
# Qdrant HA configuration (Kubernetes)
replicaCount: 3
qdrant:
  config:
    cluster:
      enabled: true
    storage:
      wal:
        wal_capacity_mb: 256
```

### Performance Tuning

```json
{
  "optimizers_config": {
    "indexing_threshold": 20000,
    "memmap_threshold": 50000
  },
  "hnsw_config": {
    "m": 32,
    "ef_construct": 200
  }
}
```

### Backup Strategy

```bash
# Snapshot collection
curl -X POST "http://localhost:6333/collections/agent_memory/snapshots"

# List snapshots
curl "http://localhost:6333/collections/agent_memory/snapshots"

# Restore from snapshot
curl -X PUT "http://localhost:6333/collections/agent_memory/snapshots/recover" \
  -H "Content-Type: application/json" \
  -d '{"location": "/qdrant/snapshots/agent_memory/snapshot-2026-01-22.snapshot"}'
```

### Monitoring

Key metrics to monitor:

| Metric         | Warning | Critical |
| -------------- | ------- | -------- |
| Search Latency | > 100ms | > 500ms  |
| Memory Usage   | > 80%   | > 95%    |
| Indexing Queue | > 10K   | > 100K   |
| Cache Hit Rate | < 50%   | < 20%    |

### Security

```bash
# Enable API key authentication
docker run -d \
  -e QDRANT__SERVICE__API_KEY=your-secure-key \
  -p 6333:6333 \
  qdrant/qdrant

# Use API key in requests
export QDRANT_API_KEY="your-secure-key"
curl -H "api-key: $QDRANT_API_KEY" http://localhost:6333/collections
```

---

## Quick Reference

### Script Commands

| Action          | Command                                                                 |
| --------------- | ----------------------------------------------------------------------- |
| Init collection | `python scripts/init_collection.py --collection NAME`                   |
| Check cache     | `python scripts/semantic_cache.py check --query "..."`                  |
| Store cache     | `python scripts/semantic_cache.py store --query "..." --response "..."` |
| Clear cache     | `python scripts/semantic_cache.py clear --older-than 7`                 |
| Store memory    | `python scripts/memory_retrieval.py store --content "..." --type TYPE`  |
| Retrieve memory | `python scripts/memory_retrieval.py retrieve --query "..."`             |
| List memories   | `python scripts/memory_retrieval.py list --type TYPE`                   |
| Hybrid search   | `python scripts/hybrid_search.py --query "..." --keyword key=value`     |

### Environment Variables

| Variable            | Default                  | Description            |
| ------------------- | ------------------------ | ---------------------- |
| `QDRANT_URL`        | `http://localhost:6333`  | Qdrant server URL      |
| `QDRANT_API_KEY`    | (none)                   | API key if required    |
| `MEMORY_COLLECTION` | `agent_memory`           | Memory collection name |
| `CACHE_COLLECTION`  | `semantic_cache`         | Cache collection name  |
| `OPENAI_API_KEY`    | (required)               | OpenAI API key         |
| `EMBEDDING_MODEL`   | `text-embedding-3-small` | Embedding model        |

### Token Savings Cheat Sheet

| Scenario          | Before     | After     | Savings |
| ----------------- | ---------- | --------- | ------- |
| Repeated question | 8K tokens  | 0 tokens  | 100%    |
| Context retrieval | 20K tokens | 1K tokens | 95%     |
| Hybrid lookup     | 15K tokens | 2K tokens | 87%     |

---

## Next Steps

1. **Start small**: Begin with semantic caching for frequently asked questions
2. **Monitor savings**: Track token costs before/after implementation
3. **Tune thresholds**: Adjust similarity thresholds based on your use case
4. **Scale gradually**: Start with Docker, move to Qdrant Cloud for production
5. **Add memory types**: Customize memory categories for your domain
