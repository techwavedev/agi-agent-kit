# Skills Catalog

> **Auto-generated Documentation** — Last updated: 2026-01-23 16:32
>
> This catalog is automatically maintained. Update it by running:
>
> ```bash
> python skill-creator/scripts/update_catalog.py --skills-dir skills/
> ```

This document provides comprehensive documentation on available skills, how to use them, and when each skill should be triggered.

---

## Table of Contents

- [What Are Skills?](#what-are-skills)
- [Available Skills](#available-skills)
  - [Documentation](#documentation)
  - [Pdf Reader](#pdf-reader)
  - [Qdrant Memory](#qdrant-memory)
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

### Documentation

| Property     | Value                   |
| ------------ | ----------------------- |
| **Name**     | `documentation`         |
| **Location** | `skills/documentation/` |
| **Type**     | Standalone              |

**Description:** "Automated documentation maintenance and generation skill. Triggers when: (1) Code is added, changed, updated, or deleted in any skill, (2) New scripts or references are created, (3) SKILL.md files are modified, (4) User requests documentation updates, (5) Skills catalog needs regeneration, (6) README or AGENTS.md need updates reflecting code changes. Use for generating technical documentation, updating docs after code changes, producing changelogs, ensuring documentation stays synchronized with the codebase, and maintaining the skills catalog."

**Scripts:**

| Script                          | Purpose                    |
| ------------------------------- | -------------------------- |
| `scripts/analyze_code.py`       | _[See script for details]_ |
| `scripts/detect_changes.py`     | _[See script for details]_ |
| `scripts/generate_changelog.py` | _[See script for details]_ |
| `scripts/sync_docs.py`          | _[See script for details]_ |
| `scripts/update_skill_docs.py`  | _[See script for details]_ |

**References:**

- `references/best_practices.md`

---

### Pdf Reader

| Property     | Value                |
| ------------ | -------------------- |
| **Name**     | `pdf-reader`         |
| **Location** | `skills/pdf-reader/` |
| **Type**     | Standalone           |

**Description:** Extract text from PDF files for manipulation, search, and reference. Use when needing to read PDF content, extract text from documents, search within PDFs, or convert PDF to text for further processing. Supports multiple extraction methods (pdfplumber, PyMuPDF, pdfminer) with automatic fallback.

**Scripts:**

| Script                    | Purpose                    |
| ------------------------- | -------------------------- |
| `scripts/extract_text.py` | _[See script for details]_ |

**References:**

- `references/pdf_libraries.md`

---

### Qdrant Memory

| Property     | Value                   |
| ------------ | ----------------------- |
| **Name**     | `qdrant-memory`         |
| **Location** | `skills/qdrant-memory/` |
| **Type**     | Standalone              |

**Description:** "Intelligent token optimization through Qdrant-powered semantic caching and long-term memory. Use for (1) Semantic Cache - avoid LLM calls entirely for semantically similar queries with 100% token savings, (2) Long-Term Memory - retrieve only relevant context chunks instead of full conversation history with 80-95% context reduction, (3) Hybrid Search - combine vector similarity with keyword filtering for technical queries, (4) Memory Management - store and retrieve conversation memories, decisions, and code patterns with metadata filtering. Triggers when needing to cache responses, remember past interactions, optimize context windows, or implement RAG patterns."

**Scripts:**

| Script                               | Purpose                    |
| ------------------------------------ | -------------------------- |
| `scripts/benchmark_token_savings.py` | _[See script for details]_ |
| `scripts/embedding_utils.py`         | _[See script for details]_ |
| `scripts/hybrid_search.py`           | _[See script for details]_ |
| `scripts/init_collection.py`         | _[See script for details]_ |
| `scripts/memory_retrieval.py`        | _[See script for details]_ |
| `scripts/semantic_cache.py`          | _[See script for details]_ |
| `scripts/test_skill.py`              | _[See script for details]_ |

**References:**

- `references/advanced_patterns.md`
- `references/collection_schemas.md`
- `references/complete_guide.md`
- `references/embedding_models.md`

---

### Webcrawler

| Property     | Value                |
| ------------ | -------------------- |
| **Name**     | `webcrawler`         |
| **Location** | `skills/webcrawler/` |
| **Type**     | Standalone           |

**Description:** "Documentation harvesting agent for crawling and extracting content from documentation websites. Use for crawling documentation sites and extracting all pages about a subject, building offline knowledge bases from online docs, harvesting API references, tutorials, or guides from documentation portals, creating structured markdown exports from multi-page documentation, and downloading and organizing technical docs for embedding or RAG pipelines. Supports recursive crawling with depth control, content filtering, and structured output."

**Scripts:**

| Script                    | Purpose                    |
| ------------------------- | -------------------------- |
| `scripts/crawl_docs.py`   | _[See script for details]_ |
| `scripts/extract_page.py` | _[See script for details]_ |
| `scripts/filter_docs.py`  | _[See script for details]_ |

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

_This catalog is part of the [3-Layer Architecture](../AGENTS.md) for reliable AI agent operations._
