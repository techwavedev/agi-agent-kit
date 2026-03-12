---
name: firecrawl-scraper
description: "Deep web scraping, screenshots, PDF parsing, and website crawling using Firecrawl API"
risk: unknown
source: community
date_added: "2026-02-27"
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

<!-- AGI-INTEGRATION-START -->

## AGI Framework Integration

> **Adapted for [@techwavedev/agi-agent-kit](https://www.npmjs.com/package/@techwavedev/agi-agent-kit)**
> Original source: [antigravity-awesome-skills](https://github.com/sickn33/antigravity-awesome-skills)

### Memory-First Protocol

Cache data schemas, transformation rules, and query patterns. BM25 excels at finding specific column names, table references, and SQL patterns.

```bash
# Check for prior data engineering context before starting
python3 execution/memory_manager.py auto --query "data processing patterns and pipeline configurations for Firecrawl Scraper"
```

### Storing Results

After completing work, store data engineering decisions for future sessions:

```bash
python3 execution/memory_manager.py store \
  --content "Data pipeline: ETL from PostgreSQL to Qdrant, 50K records/batch, incremental sync via updated_at" \
  --type technical --project <project> \
  --tags firecrawl-scraper data
```

### Multi-Agent Collaboration

Share data schema changes with backend and frontend agents so they update their models accordingly.

```bash
python3 execution/cross_agent_context.py store \
  --agent "<your-agent>" \
  --action "Data pipeline implemented — ETL processing with validation, deduplication, and error recovery" \
  --project <project>
```

<!-- AGI-INTEGRATION-END -->
