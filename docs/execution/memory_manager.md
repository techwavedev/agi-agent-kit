# memory_manager.py

Unified memory management wrapper for all Qdrant-based operations. Provides a single CLI entry point for all agents to store, retrieve, and manage memories with spatial scoping, AAAK compression, and temporal filtering.

## Purpose

Bridges agents (Claude, Gemini, Cursor, etc.) to the Qdrant vector memory backend. Handles semantic caching, hybrid search (Vector + BM25), AAAK symbolic compression, spatial isolation (Wing/Room), temporal validity ledgers, and AI-driven contradiction resolution.

## Usage

### Auto-query (primary agent entry point)

Check semantic cache first, then retrieve context via hybrid search:

```bash
python3 execution/memory_manager.py auto --query "How to set up auth middleware?" --project myapp
```

With spatial scoping:

```bash
python3 execution/memory_manager.py auto --query "payment webhook config" --project myapp --wing services --room payments
```

### Store a memory

```bash
python3 execution/memory_manager.py store \
  --content "We decided to use Stripe for payments" \
  --type decision \
  --project myapp \
  --wing services \
  --room payments \
  --tags stripe payments
```

With AAAK compression (reduces token count, preserves original in metadata):

```bash
python3 execution/memory_manager.py store \
  --content "The auth service uses JWT tokens with 1h expiry and refresh via /api/auth/refresh" \
  --type technical \
  --project myapp \
  --wing auth \
  --room tokens \
  --compress-aaak
```

With temporal expiry (auto-expire after N days):

```bash
python3 execution/memory_manager.py store \
  --content "Temp API key for staging: use key ABC123" \
  --type technical \
  --project myapp \
  --expire-days 7
```

With contradiction resolution (AI checks for and invalidates conflicting facts):

```bash
python3 execution/memory_manager.py store \
  --content "Auth now uses OAuth2 instead of JWT" \
  --type decision \
  --project myapp \
  --wing auth \
  --room tokens \
  --resolve-contradictions
```

### Retrieve context

```bash
python3 execution/memory_manager.py retrieve \
  --query "database architecture" \
  --project myapp \
  --wing backend \
  --room database \
  --top-k 5
```

### Cache a response

```bash
python3 execution/memory_manager.py cache-store \
  --query "How to deploy?" \
  --response "Run npm run deploy..."
```

### Health check

```bash
python3 execution/memory_manager.py health
```

### List memories

```bash
python3 execution/memory_manager.py list --project myapp --type decision
```

### Sync knowledge files

```bash
python3 execution/memory_manager.py knowledge-sync --project myapp
```

## Spatial Scoping (Wing/Room)

Memories are organized into **Wings** (broad domain areas) and **Rooms** (specific topics). This prevents cross-contamination between unrelated contexts.

```
Wing: "services"
├── Room: "payments"     → Stripe config, webhook URLs
├── Room: "auth"         → JWT settings, OAuth2 decisions
└── Room: "notifications"→ Email templates, push config

Wing: "infrastructure"
├── Room: "database"     → PostgreSQL settings, migrations
└── Room: "deployment"   → Docker config, CI/CD
```

When querying with `--wing` and `--room`, only memories in that exact scope are returned. Querying `wing=services, room=auth` will never return payment data.

## AAAK Compression

When `--compress-aaak` is used:
1. The **original text** is preserved in `original_text` metadata field (zero-loss recovery)
2. The **compressed AAAK dialect** replaces the content for vector storage
3. Token count drops significantly (typically 40-70% reduction)

The original text is always recoverable via the `original_text` field in retrieval results.

## Temporal Filtering

When `--expire-days N` is used:
- A `valid_until` Unix timestamp is stored in the memory metadata
- Expired memories can be filtered out using Qdrant's `must_not` range filters

## Contradiction Resolution

When `--resolve-contradictions` is used (requires `--wing` and `--room`):
1. Existing facts in the same Wing/Room are retrieved
2. The local micro agent (or cloud fallback) evaluates if the new fact contradicts any existing fact
3. Contradicted facts are marked as deprecated in Qdrant

## Output Fields

Retrieval results include:

| Field | Description |
|-------|-------------|
| `content` | The stored content (may be AAAK-compressed) |
| `original_text` | The uncompressed original (if AAAK was used) |
| `wing` | Spatial wing scope |
| `room` | Spatial room scope |
| `valid_until` | Temporal expiry timestamp (null = never expires) |
| `point_id` | Qdrant point UUID |
| `vector_score` | Cosine similarity score |
| `text_score` | BM25 keyword match score |
| `type` | Memory type (decision, code, error, technical, conversation) |
| `project` | Project name |
| `tags` | Associated tags |
| `timestamp` | Storage timestamp |

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | No results / cache miss |
| 2 | Connection error (Qdrant or embedding service down) |
| 3 | Operation error |

## Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `QDRANT_URL` | `http://localhost:6333` | Qdrant server URL |
| `OLLAMA_URL` | `http://localhost:11434` | Ollama embeddings URL |
| `MEMORY_COLLECTION` | `agent_memory` | Qdrant collection name |
| `CACHE_COLLECTION` | `semantic_cache` | Cache collection name |
| `EMBEDDING_PROVIDER` | `ollama` | `ollama`, `openai`, or `bedrock` |

## Dependencies

- Qdrant running with `agent_memory` and `semantic_cache` collections
- Ollama with `nomic-embed-text` model (or alternative embedding provider)
- Optional: BM25 index for hybrid search
- Optional: AAAK compressor for token reduction
- Optional: Langfuse for observability tracing
