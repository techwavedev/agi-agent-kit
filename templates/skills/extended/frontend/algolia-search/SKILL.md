---
name: algolia-search
description: "Expert patterns for Algolia search implementation, indexing strategies, React InstantSearch, and relevance tuning Use when: adding search to, algolia, instantsearch, search api, search functionality."
source: vibeship-spawner-skills (Apache 2.0)
---

# Algolia Search Integration

## Patterns

### React InstantSearch with Hooks

Modern React InstantSearch setup using hooks for type-ahead search.

Uses react-instantsearch-hooks-web package with algoliasearch client.
Widgets are components that can be customized with classnames.

Key hooks:
- useSearchBox: Search input handling
- useHits: Access search results
- useRefinementList: Facet filtering
- usePagination: Result pagination
- useInstantSearch: Full state access


### Next.js Server-Side Rendering

SSR integration for Next.js with react-instantsearch-nextjs package.

Use <InstantSearchNext> instead of <InstantSearch> for SSR.
Supports both Pages Router and App Router (experimental).

Key considerations:
- Set dynamic = 'force-dynamic' for fresh results
- Handle URL synchronization with routing prop
- Use getServerState for initial state


### Data Synchronization and Indexing

Indexing strategies for keeping Algolia in sync with your data.

Three main approaches:
1. Full Reindexing - Replace entire index (expensive)
2. Full Record Updates - Replace individual records
3. Partial Updates - Update specific attributes only

Best practices:
- Batch records (ideal: 10MB, 1K-10K records per batch)
- Use incremental updates when possible
- partialUpdateObjects for attribute-only changes
- Avoid deleteBy (computationally expensive)


## ⚠️ Sharp Edges

| Issue | Severity | Solution |
|-------|----------|----------|
| Issue | critical | See docs |
| Issue | high | See docs |
| Issue | medium | See docs |
| Issue | medium | See docs |
| Issue | medium | See docs |
| Issue | medium | See docs |
| Issue | medium | See docs |
| Issue | medium | See docs |


---

## 🧠 AGI Framework Integration

> **Adapted for [@techwavedev/agi-agent-kit](https://www.npmjs.com/package/@techwavedev/agi-agent-kit)**
> Original source: [antigravity-awesome-skills](https://github.com/sickn33/antigravity-awesome-skills)

### Hybrid Memory Integration (Qdrant + BM25)

Before executing complex tasks with this skill:
```bash
python3 execution/memory_manager.py auto --query "<task summary>"
```

**Decision Tree:**
- **Cache hit?** Use cached response directly — no need to re-process.
- **Memory match?** Inject `context_chunks` into your reasoning.
- **No match?** Proceed normally, then store results:

```bash
python3 execution/memory_manager.py store \
  --content "Description of what was decided/solved" \
  --type decision \
  --tags algolia-search <relevant-tags>
```

> **Note:** Storing automatically updates both Vector (Qdrant) and Keyword (BM25) indices.

### Agent Team Collaboration

- **Strategy**: This skill communicates via the shared memory system.
- **Orchestration**: Invoked by `orchestrator` via intelligent routing.
- **Context Sharing**: Always read previous agent outputs from memory before starting.

### Local LLM Support

When available, use local Ollama models for embedding and lightweight inference:
- Embeddings: `nomic-embed-text` via Qdrant memory system
- Lightweight analysis: Local models reduce API costs for repetitive patterns