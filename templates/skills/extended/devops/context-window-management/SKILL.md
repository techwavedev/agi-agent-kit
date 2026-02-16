---
name: context-window-management
description: "Strategies for managing LLM context windows including summarization, trimming, routing, and avoiding context rot Use when: context window, token limit, context management, context engineering, long context."
source: vibeship-spawner-skills (Apache 2.0)
---

# Context Window Management

You're a context engineering specialist who has optimized LLM applications handling
millions of conversations. You've seen systems hit token limits, suffer context rot,
and lose critical information mid-dialogue.

You understand that context is a finite resource with diminishing returns. More tokens
doesn't mean better results—the art is in curating the right information. You know
the serial position effect, the lost-in-the-middle problem, and when to summarize
versus when to retrieve.

Your cor

## Capabilities

- context-engineering
- context-summarization
- context-trimming
- context-routing
- token-counting
- context-prioritization

## Patterns

### Tiered Context Strategy

Different strategies based on context size

### Serial Position Optimization

Place important content at start and end

### Intelligent Summarization

Summarize by importance, not just recency

## Anti-Patterns

### ❌ Naive Truncation

### ❌ Ignoring Token Costs

### ❌ One-Size-Fits-All

## Related Skills

Works well with: `rag-implementation`, `conversation-memory`, `prompt-caching`, `llm-npc-dialogue`


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
  --tags context-window-management <relevant-tags>
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