# Embedding Models Reference

This document compares embedding models for semantic caching and memory retrieval.

## Model Comparison

| Model                    | Provider    | Dimensions | Speed    | Quality   | Cost     | Best For           |
| ------------------------ | ----------- | ---------- | -------- | --------- | -------- | ------------------ |
| **`nomic-embed-text`**   | **Ollama**  | **768**    | **Fast** | **Good**  | **Free** | **Local/M3 Mac**   |
| `text-embedding-3-small` | OpenAI      | 1536       | Fast     | Good      | Low      | General use        |
| `text-embedding-3-large` | OpenAI      | 3072       | Medium   | Excellent | Medium   | High accuracy      |
| `text-embedding-ada-002` | OpenAI      | 1536       | Fast     | Good      | Low      | Legacy systems     |
| `all-MiniLM-L6-v2`       | HuggingFace | 384        | Fastest  | Good      | Free     | Local/private      |
| `all-mpnet-base-v2`      | HuggingFace | 768        | Medium   | Very Good | Free     | Local/balanced     |
| `e5-large-v2`            | HuggingFace | 1024       | Slow     | Excellent | Free     | Local/high quality |
| `voyage-large-2`         | Voyage AI   | 1024       | Medium   | Excellent | Low      | Code understanding |
| `jina-embeddings-v2`     | Jina AI     | 768        | Fast     | Good      | Low      | Multilingual       |

---

## Ollama (Recommended for Local/Private)

Ollama runs **entirely local** with Metal acceleration on M-series Macs. No API keys, no cloud calls, fully private.

### Setup

```bash
# Install
brew install ollama

# Start server (background)
ollama serve &

# Pull embedding model
ollama pull nomic-embed-text
```

### nomic-embed-text (Recommended)

```python
import json
from urllib.request import Request, urlopen

OLLAMA_URL = "http://localhost:11434"

def get_embedding(text: str) -> list:
    payload = {
        "model": "nomic-embed-text",
        "prompt": text
    }

    req = Request(
        f"{OLLAMA_URL}/api/embeddings",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    with urlopen(req, timeout=60) as response:
        result = json.loads(response.read().decode())
        return result["embedding"]
```

**Characteristics**:

- 768 dimensions
- Metal acceleration on M1/M2/M3 Macs
- ~500-1000 embeddings/second on M3
- Good quality for semantic similarity
- **100% private - no data leaves your machine**

### Other Ollama Embedding Models

| Model               | Dimensions | Size  | Quality            |
| ------------------- | ---------- | ----- | ------------------ |
| `nomic-embed-text`  | 768        | 274MB | Good (recommended) |
| `mxbai-embed-large` | 1024       | 670MB | Better             |
| `all-minilm`        | 384        | 45MB  | Fastest            |

```bash
# Pull alternative models
ollama pull mxbai-embed-large
ollama pull all-minilm
```

---

## OpenAI Models

### text-embedding-3-small (Recommended)

```python
import openai

def get_embedding(text: str) -> list:
    response = openai.embeddings.create(
        input=text,
        model="text-embedding-3-small"
    )
    return response.data[0].embedding
```

**Pricing**: $0.00002 / 1K tokens (~$0.02 per 1M tokens)

**Characteristics**:

- 1536 dimensions (same as ada-002)
- 33% better quality than ada-002
- 5x cheaper than ada-002
- Supports dimension reduction

### text-embedding-3-large

```python
response = openai.embeddings.create(
    input=text,
    model="text-embedding-3-large"
)
```

**Pricing**: $0.00013 / 1K tokens (~$0.13 per 1M tokens)

**When to use**:

- Critical cache matching (need 0.95+ precision)
- Technical documentation search
- Multi-language content

---

## Local Models (No API Cost)

### all-MiniLM-L6-v2 (Fastest)

```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')

def get_embedding(text: str) -> list:
    return model.encode(text).tolist()
```

**Characteristics**:

- 384 dimensions (smaller storage)
- ~14,200 sentences/second on GPU
- Good for high-volume, low-latency
- Quality: 68.06 on MTEB

### all-mpnet-base-v2 (Balanced)

```python
model = SentenceTransformer('all-mpnet-base-v2')
```

**Characteristics**:

- 768 dimensions
- ~2,800 sentences/second on GPU
- Better quality than MiniLM
- Quality: 69.57 on MTEB

### e5-large-v2 (Highest Quality Local)

```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('intfloat/e5-large-v2')

def get_embedding(text: str) -> list:
    # e5 models require instruction prefix
    return model.encode(f"query: {text}").tolist()
```

**Characteristics**:

- 1024 dimensions
- ~700 sentences/second on GPU
- Excellent for technical content
- Quality: 75.24 on MTEB

---

## Code-Specialized Models

### voyage-code-2

Best for code understanding and technical documentation.

```python
import voyageai

vo = voyageai.Client()

def get_embedding(text: str) -> list:
    result = vo.embed(text, model="voyage-code-2")
    return result.embeddings[0]
```

**Use when**:

- Code pattern retrieval
- Technical error matching
- API documentation search

### CodeBERT

```python
from transformers import AutoTokenizer, AutoModel
import torch

tokenizer = AutoTokenizer.from_pretrained("microsoft/codebert-base")
model = AutoModel.from_pretrained("microsoft/codebert-base")

def get_embedding(code: str) -> list:
    inputs = tokenizer(code, return_tensors="pt", truncation=True, max_length=512)
    with torch.no_grad():
        outputs = model(**inputs)
    return outputs.last_hidden_state.mean(dim=1).squeeze().tolist()
```

---

## Dimension Reduction

### OpenAI Shortening

```python
response = openai.embeddings.create(
    input=text,
    model="text-embedding-3-small",
    dimensions=512  # Reduce from 1536
)
```

**Trade-offs**:

- 512 dims: ~3% quality loss, 66% storage savings
- 256 dims: ~8% quality loss, 83% storage savings

### PCA Reduction (Local Models)

```python
from sklearn.decomposition import PCA

# Fit PCA on training embeddings
pca = PCA(n_components=256)
pca.fit(training_embeddings)

# Reduce new embeddings
reduced = pca.transform([embedding])
```

---

## Selection Guide

### By Use Case

| Use Case                 | Recommended Model               |
| ------------------------ | ------------------------------- |
| **Local/M3 Mac**         | **`nomic-embed-text` (Ollama)** |
| General semantic cache   | `text-embedding-3-small`        |
| High-precision matching  | `text-embedding-3-large`        |
| Local/private deployment | `nomic-embed-text` (Ollama)     |
| Code pattern matching    | `voyage-code-2`                 |
| Multi-language support   | `jina-embeddings-v2`            |
| Budget-conscious         | `nomic-embed-text` (Ollama)     |

### By Volume

| Daily Volume  | Recommended Approach |
| ------------- | -------------------- |
| Any volume    | Ollama (local, free) |
| < 10K queries | OpenAI API           |
| 10K - 100K    | Hybrid (cache + API) |
| > 100K        | Ollama (local)       |

### By Latency Requirements

| Requirement | Model                   | Expected Latency |
| ----------- | ----------------------- | ---------------- |
| < 10ms      | Ollama nomic-embed-text | 2-5ms (M3)       |
| < 10ms      | Local MiniLM            | 5-8ms            |
| < 50ms      | Local mpnet             | 20-40ms          |
| < 200ms     | OpenAI small            | 50-150ms         |
| < 500ms     | OpenAI large            | 100-300ms        |

---

## Environment Configuration

```bash
# .env file

# === OLLAMA (Recommended - Local/Private) ===
EMBEDDING_PROVIDER=ollama
OLLAMA_URL=http://localhost:11434
EMBEDDING_MODEL=nomic-embed-text
EMBEDDING_DIMENSION=768

# === OPENAI (Cloud) ===
# EMBEDDING_PROVIDER=openai
# EMBEDDING_MODEL=text-embedding-3-small
# EMBEDDING_DIMENSION=1536
# OPENAI_API_KEY=sk-...
```

## Caching Embeddings

To avoid redundant embedding calls:

```python
import hashlib
from functools import lru_cache

@lru_cache(maxsize=10000)
def get_cached_embedding(text_hash: str, text: str) -> tuple:
    return tuple(get_embedding(text))

def embed_with_cache(text: str) -> list:
    text_hash = hashlib.md5(text.encode()).hexdigest()
    return list(get_cached_embedding(text_hash, text))
```
