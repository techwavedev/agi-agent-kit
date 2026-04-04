# Skills Catalog

> **Auto-generated Documentation** — Last updated: 2026-04-04 15:54
>
> This catalog is automatically maintained. Update it by running:
> ```bash
> python skill-creator/scripts/update_catalog.py --skills-dir skills/
> ```

This document provides comprehensive documentation on available skills, how to use them, and when each skill should be triggered.

---

## Table of Contents

- [What Are Skills?](#what-are-skills)
- [Available Skills](#available-skills)
  - [Cowork Export](#cowork-export)
  - [Documentation](#documentation)
  - [Notebooklm](#notebooklm)
  - [Pdf Reader](#pdf-reader)
  - [Qdrant Memory](#qdrant-memory)
  - [Supply Chain Monitor](#supply-chain-monitor)
  - [Upstream Sync](#upstream-sync)
  - [Webcrawler](#webcrawler)
- [Using Skills](#using-skills)
- [Creating New Skills](#creating-new-skills)
- [Maintenance](#maintenance)

---

## What Are Skills?

**Skills** are modular, self-contained packages that extend the AI agent's capabilities with specialized knowledge, workflows, and tools.

### Skill Structure

```
skill-name/
├── SKILL.md           # (required) Main instruction file
├── scripts/           # (optional) Executable scripts
├── references/        # (optional) Documentation
└── assets/            # (optional) Templates, images, etc.
```

---

## Available Skills

### Cowork Export

| Property | Value |
| -------- | ----- |
| **Name** | `cowork-export` |
| **Location** | `skills/cowork-export/` |
| **Type** | Standalone |

**Description:** "Export current session context as a portable briefing document for Claude on claude.ai (Cowork). Use when the user wants to delegate tasks to Claude web, schedule work in Cowork, or hand off context to a remote Claude instance. Triggers on: 'export to cowork', 'cowork briefing', 'send to claude.ai', 'schedule in cowork', 'remote agent context'."

**Scripts:**

| Script | Purpose |
| ------ | ------- |
| `scripts/export_context.py` | *[See script for details]* |

**References:**
- `references/cowork-patterns.md`

---

### Documentation

| Property | Value |
| -------- | ----- |
| **Name** | `documentation` |
| **Location** | `skills/documentation/` |
| **Type** | Standalone |

**Description:** "Automated documentation maintenance and generation skill. Triggers when: (1) Code is added, changed, updated, or deleted in any skill, (2) New scripts or references are created, (3) SKILL.md files are modified, (4) User requests documentation updates, (5) Skills catalog needs regeneration, (6) README or AGENTS.md need updates reflecting code changes. Use for generating technical documentation, updating docs after code changes, producing changelogs, ensuring documentation stays synchronized with the codebase, and maintaining the skills catalog."

**Scripts:**

| Script | Purpose |
| ------ | ------- |
| `scripts/analyze_code.py` | *[See script for details]* |
| `scripts/detect_changes.py` | *[See script for details]* |
| `scripts/generate_changelog.py` | *[See script for details]* |
| `scripts/sync_docs.py` | *[See script for details]* |
| `scripts/update_skill_docs.py` | *[See script for details]* |

**References:**
- `references/best_practices.md`

---

### Notebooklm

| Property | Value |
| -------- | ----- |
| **Name** | `notebooklm` |
| **Location** | `skills/notebooklm/` |
| **Type** | Standalone |

**Description:** "Use this skill to query your Google NotebookLM notebooks directly from Claude Code for source-grounded, citation-backed answers from Gemini. Browser automation, library management, persistent auth...."

**Scripts:**

| Script | Purpose |
| ------ | ------- |
| `scripts/ask_question.py` | *[See script for details]* |
| `scripts/auth_manager.py` | *[See script for details]* |
| `scripts/browser_session.py` | *[See script for details]* |
| `scripts/browser_utils.py` | *[See script for details]* |
| `scripts/cleanup_manager.py` | *[See script for details]* |
| `scripts/config.py` | *[See script for details]* |
| `scripts/notebook_manager.py` | *[See script for details]* |
| `scripts/run.py` | *[See script for details]* |
| `scripts/setup_environment.py` | *[See script for details]* |

**References:**
- `references/api_reference.md`
- `references/troubleshooting.md`
- `references/usage_patterns.md`

---

### Pdf Reader

| Property | Value |
| -------- | ----- |
| **Name** | `pdf-reader` |
| **Location** | `skills/pdf-reader/` |
| **Type** | Standalone |

**Description:** Extract text from PDF files for manipulation, search, and reference. Use when needing to read PDF content, extract text from documents, search within PDFs, or convert PDF to text for further processing. Supports multiple extraction methods (pdfplumber, PyMuPDF, pdfminer) with automatic fallback.

**Scripts:**

| Script | Purpose |
| ------ | ------- |
| `scripts/extract_text.py` | *[See script for details]* |

**References:**
- `references/pdf_libraries.md`

---

### Qdrant Memory

| Property | Value |
| -------- | ----- |
| **Name** | `qdrant-memory` |
| **Location** | `skills/qdrant-memory/` |
| **MCP Server** | `mcp_server.py` |
| **Type** | Standalone |

**Description:** "Intelligent token optimization through Qdrant-powered semantic caching and long-term memory. Use for (1) Semantic Cache - avoid LLM calls entirely for semantically similar queries with 100% token savings, (2) Long-Term Memory - retrieve only relevant context chunks instead of full conversation history with 80-95% context reduction, (3) Hybrid Search - combine vector similarity with keyword filtering for technical queries, (4) Memory Management - store and retrieve conversation memories, decisions, and code patterns with metadata filtering. Triggers when needing to cache responses, remember past interactions, optimize context windows, or implement RAG patterns."

**Scripts:**

| Script | Purpose |
| ------ | ------- |
| `scripts/benchmark_token_savings.py` | *[See script for details]* |
| `scripts/bm25_index.py` | *[See script for details]* |
| `scripts/embedding_utils.py` | *[See script for details]* |
| `scripts/hybrid_search.py` | *[See script for details]* |
| `scripts/init_collection.py` | *[See script for details]* |
| `scripts/memory_retrieval.py` | *[See script for details]* |
| `scripts/semantic_cache.py` | *[See script for details]* |
| `scripts/test_skill.py` | *[See script for details]* |

**References:**
- `references/advanced_patterns.md`
- `references/collection_schemas.md`
- `references/complete_guide.md`
- `references/embedding_models.md`

---

### Supply Chain Monitor

| Property | Value |
| -------- | ----- |
| **Name** | `supply-chain-monitor` |
| **Location** | `skills/supply-chain-monitor/` |
| **Type** | Standalone |

**Description:** >

**Scripts:**

| Script | Purpose |
| ------ | ------- |
| `scripts/extract_packages.py` | *[See script for details]* |
| `scripts/scrape_thn.py` | *[See script for details]* |
| `scripts/update_blocklist.py` | *[See script for details]* |

**References:**
- `references/thn_selectors.md`

---

### Upstream Sync

| Property | Value |
| -------- | ----- |
| **Name** | `upstream-sync` |
| **Location** | `skills/upstream-sync/` |
| **Type** | Standalone |

**Description:** "Synchronize upstream fork repositories with the agi-agent-kit codebase. Detects new/updated content from forked repos, creates feature branches, and applies framework adaptations."

**Scripts:**

| Script | Purpose |
| ------ | ------- |
| `scripts/sync_upstream.py` | *[See script for details]* |

---

### Webcrawler

| Property | Value |
| -------- | ----- |
| **Name** | `webcrawler` |
| **Location** | `skills/webcrawler/` |
| **Type** | Standalone |

**Description:** "Documentation harvesting agent for crawling and extracting content from documentation websites. Use for crawling documentation sites and extracting all pages about a subject, building offline knowledge bases from online docs, harvesting API references, tutorials, or guides from documentation portals, creating structured markdown exports from multi-page documentation, and downloading and organizing technical docs for embedding or RAG pipelines. Supports recursive crawling with depth control, content filtering, and structured output."

**Scripts:**

| Script | Purpose |
| ------ | ------- |
| `scripts/crawl_docs.py` | *[See script for details]* |
| `scripts/extract_page.py` | *[See script for details]* |
| `scripts/filter_docs.py` | *[See script for details]* |

**References:**
- `references/advanced_crawling.md`

---
## Using Skills

Skills are automatically triggered based on the user's request matching the skill description. You can also explicitly invoke a skill:

```
"Use the <skill-name> skill to <task>"
```

---

## Creating New Skills

```bash
# Initialize a new skill
python skill-creator/scripts/init_skill.py my-new-skill --path skills/

# Package the skill
python skill-creator/scripts/package_skill.py skills/my-new-skill
```

For detailed guidance, see: `skill-creator/SKILL_skillcreator.md`

---

## Maintenance

### Updating This Catalog

**IMPORTANT:** This catalog must be updated whenever skills are created, modified, or deleted.

```bash
python skill-creator/scripts/update_catalog.py --skills-dir skills/
```

---

*This catalog is part of the [3-Layer Architecture](../AGENTS.md) for reliable AI agent operations.*
