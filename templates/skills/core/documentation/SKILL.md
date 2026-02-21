---
name: documentation
description: "Automated documentation maintenance and generation skill. Triggers when: (1) Code is added, changed, updated, or deleted in any skill, (2) New scripts or references are created, (3) SKILL.md files are modified, (4) User requests documentation updates, (5) Skills catalog needs regeneration, (6) README or AGENTS.md need updates reflecting code changes. Use for generating technical documentation, updating docs after code changes, producing changelogs, ensuring documentation stays synchronized with the codebase, and maintaining the skills catalog."
---

# Documentation Skill

Intelligent documentation maintenance agent that automatically detects code changes across skills and the repository, then updates, upgrades, or generates documentation to keep everything synchronized.

> **Last Updated:** 2026-01-23

---

## Quick Start

```bash
# Detect changes and generate a documentation update report
python skills/documentation/scripts/detect_changes.py \
  --scope skills/ \
  --output .tmp/docs/change-report.md

# Update documentation for a specific skill after changes
python skills/documentation/scripts/update_skill_docs.py \
  --skill qdrant-memory \
  --changelog

# Full repository documentation sync
python skills/documentation/scripts/sync_docs.py \
  --skills-dir skills/ \
  --update-catalog \
  --update-readme
```

---

## Core Workflow

1. **Detect Changes** — Scan for code changes (added, modified, deleted files)
2. **Analyze Impact** — Determine which documentation needs updating
3. **Generate Updates** — Produce updated or new documentation
4. **Format & Lint** — Run `npx markdownlint-cli "**/*.md" --fix` to resolve formatting issues like MD001, MD041, MD060
5. **Synchronize Catalog** — Update SKILLS_CATALOG.md if skills changed
6. **Produce Changelog** — Create a changelog entry for significant changes
7. **Validate** — Verify all documentation is synchronized

---

## Scripts

### `detect_changes.py` — Change Detection Engine

Scans the repository or specific directories to detect code changes since the last documentation update.

```bash
python skills/documentation/scripts/detect_changes.py \
  --scope <path>              # Directory to scan (required)
  --since <commit|date>       # Compare since commit/date (default: last tag)
  --output <file>             # Output report file (default: stdout)
  --format <md|json>          # Output format (default: md)
  --include-git               # Use git diff for precise changes (default: true)
```

**Outputs:**

- List of added files with paths
- List of modified files with change summaries
- List of deleted files
- Impacted skills and documentation

### `update_skill_docs.py` — Skill Documentation Updater

Updates documentation for a specific skill based on detected changes.

```bash
python skills/documentation/scripts/update_skill_docs.py \
  --skill <skill-name>        # Skill to update (required)
  --skills-dir <path>         # Skills directory (default: skills/)
  --changelog                 # Generate changelog entry (optional)
  --analyze-scripts           # Analyze script docstrings (default: true)
  --update-references         # Update references list (default: true)
```

**Capabilities:**

- Extracts docstrings from Python scripts
- Updates SKILL.md sections: Scripts, References, Quick Start
- Adds "Last Updated" timestamp
- Generates changelog entries

### `sync_docs.py` — Full Documentation Synchronization

Orchestrates a complete documentation update across the entire repository.

```bash
python skills/documentation/scripts/sync_docs.py \
  --skills-dir <path>         # Skills directory (required)
  --update-catalog            # Update SKILLS_CATALOG.md (default: true)
  --update-readme             # Update README.md if exists (optional)
  --dry-run                   # Preview changes without writing (optional)
  --report <file>             # Save sync report (optional)
```

### `generate_changelog.py` — Changelog Generator

Creates structured changelog entries from detected changes.

```bash
python skills/documentation/scripts/generate_changelog.py \
  --scope <path>              # Directory to analyze (required)
  --since <commit|date>       # Changes since (required)
  --output <file>             # Output file (default: CHANGELOG.md)
  --format <keep-a-changelog> # Changelog format (default: keep-a-changelog)
```

### `analyze_code.py` — Code Analysis for Documentation

Analyzes Python files to extract documentation-relevant information.

```bash
python skills/documentation/scripts/analyze_code.py \
  --file <path>               # File to analyze (required)
  --output <format>           # Output: summary, full, json (default: summary)
```

**Extracts:**

- Module docstrings
- Function/class signatures
- Parameter descriptions
- Return types
- Usage examples from docstrings

---

## Configuration

### Documentation Update Triggers

The skill tracks and responds to these change types:

| File Pattern               | Documentation Impact            |
| -------------------------- | ------------------------------- |
| `skills/*/SKILL.md`        | Skills catalog update required  |
| `skills/*/scripts/*.py`    | Skill scripts section update    |
| `skills/*/references/*.md` | Skill references section update |
| `execution/*.py`           | Execution scripts documentation |
| `directives/*.md`          | Directives catalog if exists    |
| `AGENTS.md`                | Architecture documentation      |
| `*.py` (any)               | Potential README, module docs   |

### Ignore Patterns

Files excluded from documentation tracking:

```
.tmp/
.git/
__pycache__/
*.pyc
.DS_Store
node_modules/
```

---

## Output Formats

### Change Report (Markdown)

```markdown
# Documentation Change Report

> Generated: 2026-01-23 13:45

## Summary

- **Added:** 3 files
- **Modified:** 5 files
- **Deleted:** 1 file

## Impacted Documentation

- [ ] SKILLS_CATALOG.md (skill added)
- [ ] skills/qdrant-memory/SKILL.md (new script)
- [ ] README.md (features updated)

## Detailed Changes

### Added Files

| File                                   | Type   | Impact                        |
| -------------------------------------- | ------ | ----------------------------- |
| skills/qdrant-memory/scripts/backup.py | Script | Update qdrant-memory SKILL.md |

### Modified Files

...
```

### Changelog Entry

```markdown
## [Unreleased]

### Added

- New backup script for Qdrant Memory skill (`skills/qdrant-memory/scripts/backup.py`)

### Changed

- Updated webcrawler depth limit handling
- Improved error messages in pdf-reader

### Removed

- Deprecated legacy export format
```

---

## Common Workflows

### 1. After Modifying a Skill

```bash
# Update the skill's documentation
python skills/documentation/scripts/update_skill_docs.py \
  --skill qdrant-memory \
  --changelog

# Then update the catalog
python skill-creator/scripts/update_catalog.py --skills-dir skills/
```

### 2. After Creating a New Skill

```bash
# Sync all documentation (includes catalog update)
python skills/documentation/scripts/sync_docs.py \
  --skills-dir skills/ \
  --update-catalog

# Or manually update catalog
python skill-creator/scripts/update_catalog.py --skills-dir skills/
```

### 3. Generate Change Report for Review

```bash
# See what documentation needs updating
python skills/documentation/scripts/detect_changes.py \
  --scope skills/ \
  --since "1 week ago" \
  --output .tmp/docs/weekly-changes.md
```

### 4. Full Repository Audit

```bash
# Complete documentation synchronization
python skills/documentation/scripts/sync_docs.py \
  --skills-dir skills/ \
  --update-catalog \
  --report .tmp/docs/sync-report.md
```

---

## Integration with Skill Lifecycle

This skill integrates with the skill-creator workflow:

```
┌─────────────────────────────────────────────────────────────┐
│  SKILL LIFECYCLE                                            │
│  ↓                                                          │
│  1. Create skill (init_skill.py)                           │
│  ↓                                                          │
│  2. Develop skill (edit SKILL.md, add scripts)             │
│  ↓                                                          │
│  3. DOCUMENTATION SKILL: Update skill docs                 │
│     └─ update_skill_docs.py --skill <name>                 │
│  ↓                                                          │
│  4. Package skill (package_skill.py)                       │
│  ↓                                                          │
│  5. DOCUMENTATION SKILL: Sync catalog                      │
│     └─ update_catalog.py (mandatory)                       │
│  ↓                                                          │
│  6. DOCUMENTATION SKILL: Generate changelog                │
│     └─ generate_changelog.py (optional)                    │
└─────────────────────────────────────────────────────────────┘
```

---

## Best Practices

### Documentation Updates

1. **Run after every code change** — Don't let docs drift from code
2. **Use dry-run first** — Preview changes before applying
3. **Include changelogs** — Track what changed and why
4. **Validate synchronization** — Ensure all docs are current

### Change Detection

1. **Use git-based detection** — Most accurate for tracking changes
2. **Scope appropriately** — Focus on relevant directories
3. **Review reports** — Don't blindly accept all changes

### Documentation Quality

1. **Extract from docstrings** — Keep source of truth in code
2. **Keep examples current** — Update usage examples with code
3. **Maintain cross-references** — Link related documentation

---

## Troubleshooting

| Issue                   | Cause                      | Solution                               |
| ----------------------- | -------------------------- | -------------------------------------- |
| **No changes detected** | Git not tracking files     | Run `git add` before detection         |
| **Missing docstrings**  | Scripts lack documentation | Add module/function docstrings         |
| **Catalog out of sync** | Skill added manually       | Run update_catalog.py                  |
| **Stale timestamps**    | Last Updated not set       | Update SKILL.md manually or via script |

---

## Dependencies

Required Python packages:

```bash
# Core dependencies (usually available)
pip install pyyaml gitpython
```

---

## Related Skills

- **[skill-creator](../../skill-creator/SKILL_skillcreator.md)** — Create and package new skills
- **[webcrawler](../webcrawler/SKILL.md)** — Harvest external documentation
- **[pdf-reader](../pdf-reader/SKILL.md)** — Extract text from PDF docs

---

## External Resources

- [Keep a Changelog](https://keepachangelog.com/) — Changelog format standard
- [Google Style Python Docstrings](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings)

## AGI Framework Integration

### Qdrant Memory Integration

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
  --tags documentation <relevant-tags>
```

> **Note:** Storing automatically updates both Vector (Qdrant) and Keyword (BM25) indices.

### Agent Team Collaboration- **Strategy**: This skill communicates via the shared memory system.
- **Orchestration**: Invoked by `orchestrator` via intelligent routing.
- **Context Sharing**: Always read previous agent outputs from memory before starting.

### Local LLM Support

When available, use local Ollama models for embedding and lightweight inference:
- Embeddings: `nomic-embed-text` via Qdrant memory system
- Lightweight analysis: Local models reduce API costs for repetitive patterns
