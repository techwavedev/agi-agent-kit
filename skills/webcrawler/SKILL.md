---
name: webcrawler
description: "Documentation harvesting agent for crawling and extracting content from documentation websites. Use for crawling documentation sites and extracting all pages about a subject, building offline knowledge bases from online docs, harvesting API references, tutorials, or guides from documentation portals, creating structured markdown exports from multi-page documentation, and downloading and organizing technical docs for embedding or RAG pipelines. Supports recursive crawling with depth control, content filtering, and structured output."
---

# Webcrawler Skill

Intelligent documentation harvesting agent that recursively crawls documentation websites and extracts structured content about specific subjects.

> **Last Updated:** 2026-02-07

---

## Quick Start

```bash
# Crawl Python documentation about async/await
python skills/webcrawler/scripts/crawl_docs.py \
  --url "https://docs.python.org/3/library/asyncio.html" \
  --subject "asyncio" \
  --depth 2 \
  --output .tmp/docs/python-asyncio/

# Crawl React documentation
python skills/webcrawler/scripts/crawl_docs.py \
  --url "https://react.dev/" \
  --subject "React" \
  --depth 3 \
  --output .tmp/docs/react/

# Extract only API reference pages
python skills/webcrawler/scripts/crawl_docs.py \
  --url "https://expressjs.com/en/4x/api.html" \
  --subject "Express API" \
  --filter "api" \
  --output .tmp/docs/express-api/
```

---

## Core Workflow

1. **Initialize Crawl** — Provide base URL and subject focus
2. **Discover Pages** — Recursively find all linked documentation pages
3. **Filter Content** — Keep only pages matching the subject criteria
4. **Extract Content** — Convert HTML to clean markdown
5. **Organize Output** — Structure files in a navigable hierarchy
6. **Generate Index** — Create a master index with all harvested pages

---

## Scripts

### `crawl_docs.py` — Main Documentation Crawler

The primary crawling script that handles recursive page discovery and content extraction.

```bash
python skills/webcrawler/scripts/crawl_docs.py \
  --url <base-url>           # Starting URL (required)
  --subject <topic>          # Subject focus for filtering (required)
  --output <directory>       # Output directory (default: .tmp/crawled/)
  --depth <n>                # Max crawl depth (default: 2)
  --filter <pattern>         # URL path filter pattern (optional)
  --delay <seconds>          # Delay between requests (default: 0.5)
  --max-pages <n>            # Maximum pages to crawl (default: 100)
  --same-domain              # Stay within same domain (default: true)
  --include-code             # Preserve code blocks (default: true)
  --format <md|json|both>    # Output format (default: both)
```

**Outputs:**

- `index.md` — Master index with links to all pages
- `pages/*.md` — Individual markdown files per page
- `metadata.json` — Crawl metadata and page inventory
- `content.json` — Structured JSON with all extracted content

### `extract_page.py` — Single Page Extractor

Extract content from a single documentation page.

```bash
python skills/webcrawler/scripts/extract_page.py \
  --url <page-url>           # Page to extract (required)
  --output <file>            # Output file (default: stdout)
  --format <md|json>         # Output format (default: md)
  --include-links            # Include internal links (default: true)
```

### `filter_docs.py` — Post-Crawl Filtering

Filter already-crawled documentation by subject or pattern.

```bash
python skills/webcrawler/scripts/filter_docs.py \
  --input <crawl-dir>        # Crawled docs directory (required)
  --subject <topic>          # Subject to filter for (required)
  --output <directory>       # Filtered output directory (required)
  --threshold <0.0-1.0>      # Relevance threshold (default: 0.3)
```

---

## Configuration

### Rate Limiting & Politeness

The crawler respects `robots.txt` and implements polite crawling:

- **Default delay**: 0.5s between requests
- **User-Agent**: Identifies as documentation harvester
- **robots.txt**: Honored by default (disable with `--ignore-robots`)

### Domain Handling

| Mode                 | Behavior                                     |
| -------------------- | -------------------------------------------- |
| `--same-domain`      | Only crawl pages on the starting domain      |
| `--same-path`        | Only crawl pages under the starting URL path |
| `--allow-subdomains` | Include subdomains (e.g., api.example.com)   |

### Content Extraction

The crawler uses intelligent content extraction:

1. **Main content detection** — Finds `<main>`, `<article>`, or content containers
2. **Navigation removal** — Strips headers, footers, sidebars
3. **Code preservation** — Maintains code blocks with language hints
4. **Link normalization** — Converts relative links to absolute
5. **Image handling** — Optionally downloads and references images

---

## Output Structure

```
.tmp/docs/<subject>/
├── index.md              # Master index with TOC
├── metadata.json         # Crawl metadata
├── content.json          # Structured JSON export
└── pages/
    ├── getting-started.md
    ├── installation.md
    ├── api-reference.md
    ├── configuration/
    │   ├── basic.md
    │   └── advanced.md
    └── troubleshooting.md
```

### Index Format

```markdown
# <Subject> Documentation

> Crawled from: <base-url>
> Pages: <count>
> Date: <timestamp>

## Table of Contents

- [Getting Started](pages/getting-started.md)
- [Installation](pages/installation.md)
- [API Reference](pages/api-reference.md)
- Configuration
  - [Basic](pages/configuration/basic.md)
  - [Advanced](pages/configuration/advanced.md)
- [Troubleshooting](pages/troubleshooting.md)
```

---

## Common Workflows

### 1. Harvest API Documentation

```bash
# Crawl API docs with deep recursion
python skills/webcrawler/scripts/crawl_docs.py \
  --url "https://api.example.com/docs" \
  --subject "Example API" \
  --depth 4 \
  --filter "/api/" \
  --output .tmp/docs/example-api/
```

### 2. Build RAG Knowledge Base

```bash
# Crawl and export as JSON for embedding
python skills/webcrawler/scripts/crawl_docs.py \
  --url "https://docs.example.com" \
  --subject "Example Docs" \
  --depth 3 \
  --format json \
  --output .tmp/rag/example/

# The content.json can be fed directly to embedding pipelines
```

### 3. Offline Documentation Mirror

```bash
# Full documentation harvest
python skills/webcrawler/scripts/crawl_docs.py \
  --url "https://docs.kubernetes.io/docs/concepts/" \
  --subject "Kubernetes Concepts" \
  --depth 5 \
  --max-pages 500 \
  --include-images \
  --output .tmp/docs/k8s-concepts/
```

### 4. Focused Topic Extraction

```bash
# Crawl, then filter to specific topic
python skills/webcrawler/scripts/crawl_docs.py \
  --url "https://developer.hashicorp.com/terraform/docs" \
  --subject "Terraform" \
  --depth 3 \
  --output .tmp/docs/terraform-full/

# Filter to AWS provider only
python skills/webcrawler/scripts/filter_docs.py \
  --input .tmp/docs/terraform-full/ \
  --subject "AWS Provider" \
  --output .tmp/docs/terraform-aws/
```

---

## Best Practices

### Crawling

1. **Start shallow** — Begin with `--depth 1` to test, then increase
2. **Use filters** — Narrow scope with `--filter` patterns
3. **Set page limits** — Use `--max-pages` to prevent runaway crawls
4. **Respect rate limits** — Increase `--delay` for slower servers

### Content Quality

1. **Subject focus** — Be specific with `--subject` for better filtering
2. **Review index** — Check `index.md` to verify crawl coverage
3. **Post-filter** — Use `filter_docs.py` to refine results

### Storage

1. **Use `.tmp/`** — Store crawled docs in the temp directory
2. **Organize by subject** — Create subdirectories per topic
3. **Version with dates** — Add timestamps for recurring crawls

---

## Troubleshooting

| Issue                   | Cause                       | Solution                                |
| ----------------------- | --------------------------- | --------------------------------------- |
| **403 Forbidden**       | Blocked by server           | Increase delay, check robots.txt        |
| **Empty pages**         | JavaScript-rendered content | Use `--render-js` (requires Playwright) |
| **Too many pages**      | Unbounded crawl             | Lower depth, use filters                |
| **Duplicate content**   | Same page via multiple URLs | Enabled by default (URL normalization)  |
| **Missing code blocks** | Extraction issue            | Check `--include-code` is enabled       |

---

## Dependencies

Required Python packages:

```bash
pip install requests beautifulsoup4 html2text lxml
# Optional for JavaScript rendering:
pip install playwright && playwright install
```

---

## Related Skills

- **[qdrant-memory](../qdrant-memory/SKILL.md)** — Store crawled docs in vector database for RAG
- **[pdf-reader](../pdf-reader/SKILL.md)** — Extract text from PDF documentation

---

## External Resources

- [Scrapy Documentation](https://docs.scrapy.org/) — For complex crawling needs
- [html2text](https://github.com/Alir3z4/html2text) — HTML to Markdown conversion
- [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/bs4/doc/) — HTML parsing
