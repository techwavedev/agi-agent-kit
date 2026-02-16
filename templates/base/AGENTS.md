# Agent Instructions

> `CLAUDE.md`, `GEMINI.md`, `OPENCODE.md`, `COPILOT.md`, and `OPENCLAW.md` are symlinks to this file, so the same instructions load in any AI environment.

---

## ⚡ Session Boot Protocol (MANDATORY)

**Run this ONCE at the start of every session, before any other work:**

```bash
python3 execution/session_boot.py --auto-fix
```

This single command checks Qdrant, Ollama, embedding models, and collections. If anything is missing, `--auto-fix` repairs it automatically. If the output shows `"memory_ready": true`, proceed normally. If it shows issues, follow the printed instructions.

**Why this matters:** The memory system provides 80-100% token savings on repeated work. Skipping this step means every query pays full token cost.

---

## Getting Started

### Installation

Run this command in any directory where you want to scaffold a new AI agent:

```bash
npx @techwavedev/agi-agent-kit init
```

### Dependencies

This toolkit relies on Python scripts for deterministic execution. Ensure you have the following installed:

1. **Python 3.8+**: `python3 --version`
2. **Pip Dependencies**:
   ```bash
   pip install requests beautifulsoup4 html2text lxml qdrant-client
   ```

### Updates

To update the kit to the latest version:

```bash
# Clear npx cache to force latest version download
rm -rf ~/.npm/_npx
npx @techwavedev/agi-agent-kit init
```

---

## Core Philosophy: Determinism Over Probability

LLMs are probabilistic, but business logic requires consistency. This system fixes that mismatch by **pushing complexity into deterministic code** and letting the agent focus on intelligent decision-making.

**Why it matters:** 90% accuracy per step = 59% success over 5 steps. The solution is to minimize probabilistic steps by delegating execution to reliable scripts.

---

## The 3-Layer Architecture

### Layer 1: Directives (Intent)

**Location:** `directives/`

Directives are SOPs written in Markdown that define:

- **Goal**: What needs to be accomplished
- **Inputs**: Required data, context, or parameters
- **Tools**: Which execution scripts to use
- **Outputs**: Expected deliverables and their format
- **Edge Cases**: Known failure modes and how to handle them

Think of directives as instructions you'd give a capable but literal-minded employee. They bridge human intent to machine execution.

```markdown
# Example: directives/scrape_competitor_pricing.md

## Goal

Scrape pricing data from competitor websites and compile into a comparison sheet.

## Inputs

- `competitors.json` - List of competitor URLs and selectors
- Target date range (optional, defaults to current)

## Execution

1. Run `execution/scrape_single_site.py` for each competitor
2. Run `execution/normalize_pricing.py` to standardize formats
3. Run `execution/export_to_sheets.py` to push to Google Sheets

## Outputs

- Google Sheet with pricing comparison (link in `.tmp/output_links.json`)
- Raw data preserved in `.tmp/scraped/`

## Edge Cases

- **Rate limiting**: Script auto-retries with exponential backoff (max 3 attempts)
- **Selector changes**: Log failure, continue with others, alert user at end
- **Auth required**: Skip site, note in output sheet
```

---

### Layer 2: Orchestration (Decision-Making)

**This is the agent's role.**

The agent is the intelligent router between intent and execution:

| Responsibility            | Description                                             |
| ------------------------- | ------------------------------------------------------- |
| **Read directives**       | Understand what needs to be done before acting          |
| **Sequence execution**    | Call scripts in the right order with correct parameters |
| **Handle errors**         | Diagnose failures and apply self-annealing (see below)  |
| **Ask for clarification** | When requirements are ambiguous, ask—don't guess        |
| **Update directives**     | Capture learnings to prevent future failures            |

**Critical principle:** The agent does NOT perform complex data transformations, API calls, or file operations directly. Instead, it invokes execution scripts that handle these deterministically.

```
❌ Wrong: Agent writes inline Python to scrape a website
✅ Right: Agent reads directive → invokes execution/scrape_single_site.py → handles result
```

---

### Layer 3: Execution (Deterministic Work)

**Location:** `execution/`

Python scripts that handle:

- API calls and external integrations
- Data processing and transformations
- File operations and I/O
- Database interactions
- Export to cloud services (Google Sheets, Slides, etc.)

**Script requirements:**

- Well-commented and self-documenting
- Accept clear inputs via CLI arguments or stdin
- Return structured output (JSON preferred) or exit codes
- Handle their own error cases gracefully
- Idempotent where possible (safe to retry)

```bash
# Example invocation
python execution/scrape_single_site.py \
  --url "https://competitor.com/pricing" \
  --selector ".price-table" \
  --output ".tmp/scraped/competitor_2024.json"
```

---

## Operating Principles

### 1. Memory-First (Automatic)

**All operations use the Hybrid Memory System (Qdrant + BM25) by default.**

#### Session Start (MANDATORY — run once per session)

```bash
python3 execution/session_boot.py --auto-fix
```

If `"memory_ready": true`, proceed. If false, follow the printed instructions.

#### Before Every Complex Task

```bash
python3 execution/memory_manager.py auto --query "<one-line summary of the task>"
```

**Decision tree based on output:**

| Result               | Action                                                                    |
| -------------------- | ------------------------------------------------------------------------- |
| `"cache_hit": true`  | Use cached response directly. Inform user: "Retrieved from memory cache." |
| `"source": "memory"` | Inject `context_chunks` into your reasoning. Cite them.                   |
| `"source": "none"`   | Proceed normally. Store the result when done.                             |

#### After Key Decisions or Solutions

```bash
python3 execution/memory_manager.py store \
  --content "Description of what was decided/solved" \
  --type decision \
  --project <project-name> \
  --tags relevant-tag1 relevant-tag2
```

Memory types: `decision`, `code`, `error`, `technical`, `conversation`

#### After Completing a Complex Task

```bash
python3 execution/memory_manager.py cache-store \
  --query "The original user question" \
  --response "The complete response that was generated"
```

**Opt-out:** User says "don't use cache", "no cache", "skip memory", or "fresh"

> See `directives/memory_integration.md` for full protocol and token savings reference.

### 2. Check for Existing Tools First

Before writing any new script:

1. **Check `execution/`** for existing scripts that might handle the task
2. **Review the relevant directive** to see if a workflow already exists
3. **Search Knowledge Items** for documented patterns and learnings

Only create new scripts when truly necessary. Reuse and extend existing tools.

### 3. Self-Anneal When Things Break

Errors are learning opportunities, not failures. When something breaks:

```
┌─────────────────────────────────────────────────────────┐
│  ERROR DETECTED                                         │
│  ↓                                                      │
│  1. Read error message and full stack trace             │
│  ↓                                                      │
│  2. Diagnose root cause                                 │
│  ↓                                                      │
│  3. Fix the script or adjust parameters                 │
│  ↓                                                      │
│  4. Test the fix (⚠️ confirm with user if uses paid    │
│     tokens, credits, or has side effects)               │
│  ↓                                                      │
│  5. Update directive with what was learned              │
│  ↓                                                      │
│  SYSTEM IS NOW STRONGER                                 │
└─────────────────────────────────────────────────────────┘
```

**Example:** You hit an API rate limit → investigate API docs → find batch endpoint → rewrite script to use batching → test → update directive with rate limit info and new approach.

### 4. Update Directives as You Learn

Directives are **living documents**. Update them when you discover:

- API constraints or rate limits
- Better approaches or optimizations
- Common errors and their solutions
- Timing expectations (how long things take)
- New edge cases

**Rules:**

- Always ask before creating or overwriting directives (unless explicitly told to proceed)
- Append learnings to existing directives rather than replacing content
- Date your additions for future reference

### 5. Validate Before Delivering

Before marking a task complete:

- Verify outputs exist and are accessible
- Spot-check data quality where possible
- Confirm deliverables are in the expected location (cloud service, output file, etc.)

---

## File Organization

### Directory Structure

```
project/
├── .agent/
│   └── workflows/        # Quick-reference workflows for common tasks
├── .env                  # Environment variables and API keys
├── .gitignore            # Excludes credentials and .tmp/
├── .tmp/                 # Intermediate files (always regenerable)
│   ├── scraped/          # Raw scraped data
│   ├── processed/        # Transformed data
│   └── output_links.json # Links to cloud deliverables
├── credentials.json      # Google OAuth credentials
├── token.json            # Google OAuth token
├── directives/           # SOPs in Markdown
├── docs/                 # Project documentation, guides, and references
│   ├── guides/           # How-to guides and tutorials
│   ├── api/              # API references and specifications
│   └── architecture/     # System design and architecture docs
├── execution/            # Deterministic Python scripts
├── skill-creator/        # Skill creation toolkit (use to create new skills)
├── skills/               # Modular capabilities (PDF reading, web scraping, etc.)
│   └── <skill-name>/
│       ├── SKILL.md      # Skill instructions and triggers
│       ├── scripts/      # Executable tools
│       └── references/   # Documentation loaded on-demand
└── AGENTS.md             # This file (symlinked as CLAUDE.md, GEMINI.md)
```

### Skills

Skills are modular packages that extend agent capabilities with specialized workflows, scripts, and domain knowledge. Each skill contains:

- **SKILL.md** — Instructions with YAML frontmatter (`name`, `description`) for triggering
- **scripts/** — Deterministic tools the agent can execute
- **references/** — Documentation loaded only when needed

**Key Resources:**

- **Skills Catalog:** `skills/SKILLS_CATALOG.md` — Complete documentation of all available skills
- **Skill Creator Guide:** `skill-creator/SKILL_skillcreator.md` — How to create new skills

**Commands:**

```bash
# Create a new skill
python3 skill-creator/scripts/init_skill.py <name> --path skills/

# Update the skills catalog (MANDATORY after any skill change)
python3 skill-creator/scripts/update_catalog.py --skills-dir skills/
```

### Deliverables vs. Intermediates

| Type              | Location       | Examples                                             |
| ----------------- | -------------- | ---------------------------------------------------- |
| **Deliverables**  | Cloud services | Google Sheets, Slides, Drive files, database records |
| **Intermediates** | `.tmp/`        | Scraped HTML, processed JSON, temp exports           |

**Key principle:** Everything in `.tmp/` can be deleted and regenerated. Deliverables live in the cloud where users can access them.

---

## Integration with Agent Tools

### Reading and Research

- Use `view_file` to read directives before starting work
- Use `grep_search` to find relevant scripts in `execution/`
- Use `find_by_name` to locate files across the project
- Search Knowledge Items for prior solutions to similar problems

### Execution

- Use `run_command` to invoke execution scripts
- Capture output and exit codes for decision-making
- Use `command_status` to monitor long-running scripts

### Writing and Updating

- Use `write_to_file` for new scripts (with clear documentation)
- Use `replace_file_content` to update existing directives with learnings
- Create new workflows in `.agent/workflows/` for repeatable processes

---

## Workflow Quick Reference

For frequently-used processes, create workflows in `.agent/workflows/`:

```markdown
# .agent/workflows/refresh-pricing.md

---

## description: Refresh competitor pricing data and update comparison sheet

1. Verify `.env` contains required API keys
2. Run `python execution/scrape_all_competitors.py`
   // turbo
3. Run `python execution/normalize_pricing.py --input .tmp/scraped/ --output .tmp/processed/`
   // turbo
4. Run `python execution/export_to_sheets.py --input .tmp/processed/pricing.json`
5. Verify Google Sheet is updated and share link with user
```

> **Note:** Steps marked with `// turbo` can be auto-run. Use `// turbo-all` at the top to auto-run all command steps.

---

## Best Practices for Execution Scripts

### Script Template

```python
#!/usr/bin/env python3
"""
Script: script_name.py
Purpose: Brief description of what this script does

Usage:
    python script_name.py --input <file> --output <file> [--verbose]

Arguments:
    --input   Path to input file (required)
    --output  Path to output file (required)
    --verbose Enable detailed logging (optional)

Exit Codes:
    0 - Success
    1 - Invalid arguments
    2 - Input file not found
    3 - API/Network error
    4 - Processing error
"""

import argparse
import json
import sys
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', required=True, help='Input file path')
    parser.add_argument('--output', required=True, help='Output file path')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')
    args = parser.parse_args()

    # Your logic here
    try:
        result = process(args.input)
        Path(args.output).write_text(json.dumps(result, indent=2))
        print(json.dumps({"status": "success", "output": args.output}))
        sys.exit(0)
    except Exception as e:
        print(json.dumps({"status": "error", "message": str(e)}), file=sys.stderr)
        sys.exit(4)

if __name__ == '__main__':
    main()
```

### Naming Conventions

| Type       | Convention            | Example                                      |
| ---------- | --------------------- | -------------------------------------------- |
| Scripts    | `verb_noun.py`        | `scrape_website.py`, `export_to_sheets.py`   |
| Directives | `noun_or_task.md`     | `competitor_analysis.md`, `weekly_report.md` |
| Temp files | Descriptive with date | `.tmp/scraped/competitor_2024-01-19.json`    |

---

## Error Handling Patterns

### In Scripts

```python
# Always return structured errors
try:
    result = risky_operation()
except RateLimitError as e:
    print(json.dumps({
        "status": "rate_limited",
        "retry_after": e.retry_after,
        "message": str(e)
    }))
    sys.exit(3)
except Exception as e:
    print(json.dumps({
        "status": "error",
        "type": type(e).__name__,
        "message": str(e)
    }))
    sys.exit(4)
```

### As the Agent

When a script returns an error:

1. Parse the structured error output
2. Determine if it's recoverable (rate limit → wait and retry) or fatal (auth error → ask user)
3. Apply the fix or escalate to the user
4. **Update the directive** with the failure mode and solution

---

## Summary

You are the intelligent orchestrator between human intent (directives) and deterministic execution (Python scripts). Your role is to:

1. **Understand** what needs to be done by reading directives
2. **Execute** by calling the right scripts in the right order
3. **Adapt** by handling errors and edge cases gracefully
4. **Learn** by updating directives with new knowledge
5. **Deliver** by ensuring outputs reach their intended destination

**Be pragmatic. Be reliable. Self-anneal.**
