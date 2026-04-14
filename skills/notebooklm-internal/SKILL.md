---
name: notebooklm-internal
description: "INTERNAL ONLY. Forked write-capable variant of the public notebooklm skill. Adds programmatic source ingestion (add_source) for the X/YouTube → NotebookLM pipeline (#119). Headless, non-interactive, cron-driven. NEVER ship publicly."
risk: high
source: internal-fork
forked_from: skills/notebooklm
internal: true
public: false
non_interactive: true
date_added: "2026-04-13"
---

# NotebookLM Internal (Write-Capable) Skill

> **⚠️ INTERNAL USE ONLY** — excluded from public release via `.private`. This fork adds programmatic source ingestion (issues #126 ensure_notebook, #127 add_source) for the X/YouTube → NotebookLM pipeline. All browser automation runs **headless** by default and is designed to execute under cron with **zero human interaction**. The first-time `auth_manager.py setup` is the only step that can open a visible browser; everything else (queries, source ingestion, notebook resolution) is fully non-interactive.

## Original Skill Documentation (forked from `skills/notebooklm/`)

Query Google NotebookLM for source-grounded answers from your uploaded documents. Each question opens a fresh browser session, retrieves the answer, and closes.

## When to Use

Trigger when user:
- Mentions NotebookLM or shares a NotebookLM URL
- Asks to query their notebooks/documentation
- Uses phrases like "ask my NotebookLM", "check my docs", "query my notebook"

## Critical: Always Use run.py Wrapper

**NEVER call scripts directly. ALWAYS use `python scripts/run.py [script]`:**

```bash
# ✅ CORRECT:
python scripts/run.py auth_manager.py status
python scripts/run.py notebook_manager.py list

# ❌ WRONG (fails without venv):
python scripts/auth_manager.py status
```

The wrapper auto-creates `.venv`, installs deps, and activates the environment.

## Core Workflow

### 1. Check Auth
```bash
python scripts/run.py auth_manager.py status
```
If not authenticated → `python scripts/run.py auth_manager.py setup` (browser opens for Google login).

### 2. Manage Notebooks
```bash
python scripts/run.py notebook_manager.py list
python scripts/run.py notebook_manager.py add --url URL --name NAME --description DESC --topics TOPICS
python scripts/run.py notebook_manager.py search --query QUERY
python scripts/run.py notebook_manager.py activate --id ID
python scripts/run.py notebook_manager.py remove --id ID
```

### 3. Smart Add (when user doesn't provide details)

Query the notebook first to discover its content, then add with accurate metadata:
```bash
# Step 1: Discover content
python scripts/run.py ask_question.py --question "What is the content of this notebook? What topics are covered?" --notebook-url "[URL]"

# Step 2: Add with discovered info
python scripts/run.py notebook_manager.py add --url "[URL]" --name "[discovered]" --description "[discovered]" --topics "[discovered]"
```

NEVER guess descriptions — use Smart Add or ask the user.

### 4. Ask Questions
```bash
python scripts/run.py ask_question.py --question "Your question" [--notebook-id ID] [--notebook-url URL] [--show-browser]
```

## Follow-Up Protocol

Every NotebookLM answer ends with: **"Is that ALL you need to know?"**

1. **STOP** — Don't immediately respond to user
2. **ANALYZE** — Compare answer to user's original request
3. **IDENTIFY GAPS** — Determine if more information needed
4. **ASK FOLLOW-UP** — If gaps exist, query again with context
5. **SYNTHESIZE** — Combine all answers before responding to user

## Decision Flow

```
User mentions NotebookLM
  → Check auth (auth_manager.py status)
  → If not auth'd → setup (browser visible)
  → Check/Add notebook (notebook_manager.py list/add)
  → Activate notebook (notebook_manager.py activate --id ID)
  → Ask question (ask_question.py --question "...")
  → Follow-up until complete
  → Synthesize and respond
```

## Data Storage

All data stored locally in `data/` within the skill directory:
- `library.json` — Notebook metadata
- `auth_info.json` — Authentication status
- `browser_state/` — Browser cookies and session

Protected by `.gitignore` — never committed to git.

## Limitations

- No session persistence (each question = new browser session)
- Rate limits on free Google accounts (~50 queries/day)
- Manual upload required (user adds docs to NotebookLM web UI)
- Browser overhead (few seconds per question)

## References

For detailed information, see:
- [references/api_reference.md](references/api_reference.md) — Full script API, arguments, and examples
- [references/troubleshooting.md](references/troubleshooting.md) — Common issues and solutions
- [references/usage_patterns.md](references/usage_patterns.md) — Best practices and workflow patterns
- [references/configuration.md](references/configuration.md) — Environment variables and .env setup

---

<!-- AGI-INTEGRATION-START -->

## AGI Framework Integration

> **Adapted for [@techwavedev/agi-agent-kit](https://www.npmjs.com/package/@techwavedev/agi-agent-kit)**

### Memory-First Protocol

```bash
python3 execution/memory_manager.py auto --query "NotebookLM patterns and prior queries"
```

### Storing Results

```bash
python3 execution/memory_manager.py store \
  --content "NotebookLM: <what was queried/decided>" \
  --type technical --project <project> \
  --tags notebooklm documentation
```

### Multi-Agent Collaboration

```bash
python3 execution/cross_agent_context.py store \
  --agent "<your-agent>" \
  --action "NotebookLM query completed — <summary>" \
  --project <project>
```

<!-- AGI-INTEGRATION-END -->