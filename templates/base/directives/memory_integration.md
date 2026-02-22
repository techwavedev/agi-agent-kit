# Memory Integration Directive

## Goal

Ensure all AI agents use the **Hybrid Memory System (Qdrant + BM25)** by default to save tokens, preserve context, and avoid redundant work.

- **Semantic Memory (Qdrant)**: Concept matching (e.g., "how do I fix econnrefused")
- **Keyword Memory (BM25)**: Exact matching (e.g., "error 503", "sg-018f20ea", "API_KEY")

Using memory provides **90-100% token savings** on repeated tasks.

## Inputs

- User query (natural language)
- Project name (optional, for scoped retrieval)
- Memory type classification (auto-detected or explicit)

## Execution Protocol

### 1. Session Start (Run Once)

```bash
python3 execution/session_boot.py --auto-fix
```

Checks Qdrant, Ollama, collections, and BM25 index. Auto-heals if broken.

### 2. Before Every Complex Task

```bash
python3 execution/memory_manager.py auto --query "<user request summary>"
```

**Decision tree based on result:**

| Result            | Action                                                  |
| ----------------- | ------------------------------------------------------- |
| `cache_hit: true` | Use cached response directly. Inform user of cache hit. |
| `source: memory`  | Inject retrieved context chunks into your reasoning.    |
| `source: none`    | Proceed normally. Store the result when done.           |

### 3. Storing Knowledge (Auto-Indexed)

Whenever you solve a problem or make a decision:

```bash
python3 execution/memory_manager.py store \
  --content "Description of what was decided/solved" \
  --type decision \
  --project <project-name> \
  --tags relevant-tag1 relevant-tag2
```

> **Note:** This automatically updates both Qdrant (vectors) and BM25 (keywords).

### 4. Cache the Response

After completing a complex task:

```bash
python3 execution/memory_manager.py cache-store \
  --query "The original user question" \
  --response "The complete response that was generated"
```

## Hybrid Search Modes

If you need specific lookup behavior, use `hybrid_search.py` directly:

```bash
# True Hybrid (Default) - Best for general refactoring
python3 skills/qdrant-memory/scripts/hybrid_search.py --query "fix auth error" --mode hybrid

# Vector Only - Best for conceptual research
python3 skills/qdrant-memory/scripts/hybrid_search.py --query "authentication patterns" --mode vector

# Keyword Only - Best for error codes/IDs
python3 skills/qdrant-memory/scripts/hybrid_search.py --query "sg-018f20ea63e82eeb5" --mode keyword
```

## Memory Type Guide

| Type           | When to Store                                  | Retention |
| -------------- | ---------------------------------------------- | --------- |
| `decision`     | Architecture choice, tech selection, trade-off | Permanent |
| `code`         | Reusable pattern, snippet, config              | Permanent |
| `error`        | Bug fix with root cause and solution           | 90 days   |
| `technical`    | API docs, library quirks, config patterns      | Permanent |
| `conversation` | User preference, constraint, project context   | 30 days   |

## Edge Cases

- **Qdrant not running:** Log warning, proceed without memory. Never block user workflow.
- **BM25 missing:** Run `python3 execution/memory_manager.py bm25-sync` to rebuild.
- **Stale cache:** Cache entries older than 7 days are auto-cleared. Run `python3 execution/memory_manager.py cache-clear --older-than 7`.
- **User opt-out:** Respect "no cache", "fresh", "skip memory" keywords.
