---
name: firecrawl-scraper
description: Deep web scraping, screenshots, PDF parsing, and website crawling using Firecrawl API
---

# firecrawl-scraper

## Overview
Deep web scraping, screenshots, PDF parsing, and website crawling using Firecrawl API

## When to Use
- When you need deep content extraction from web pages
- When page interaction is required (clicking, scrolling, etc.)
- When you want screenshots or PDF parsing
- When batch scraping multiple URLs

## Installation
```bash
npx skills add -g BenedictKing/firecrawl-scraper
```

## Step-by-Step Guide
1. Install the skill using the command above
2. Configure Firecrawl API key
3. Use naturally in Claude Code conversations

## Examples
See [GitHub Repository](https://github.com/BenedictKing/firecrawl-scraper) for examples.

## Best Practices
- Configure API keys via environment variables

## Troubleshooting
See the GitHub repository for troubleshooting guides.

## Related Skills
- context7-auto-research, tavily-web, exa-search, codex-review


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
  --tags firecrawl-scraper <relevant-tags>
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