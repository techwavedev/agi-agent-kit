---
name: notebooklm-rag
description: "Optional deep document research using Google NotebookLM as a RAG backend with browser automation. Default RAG uses Qdrant + local embeddings (see qdrant-memory skill). NotebookLM is opt-in for users with a Google account. Triggers on: 'research my docs', 'check my notebooks', 'deep search', '@notebooklm', 'query my notebook'."
---

# NotebookLM RAG — Deep Document Research (Opt-In)

> **Default RAG**: The Agi framework uses **Qdrant + local embeddings** (`qdrant-memory` skill) as the default RAG system. It works offline, requires no accounts, and provides semantic caching with 80-100% token savings.
>
> **This skill is optional**: NotebookLM RAG is for users who have a Google account and want to leverage NotebookLM's Gemini-powered, source-grounded answers from their uploaded documents. It complements — not replaces — the default Qdrant memory system.

## How It Works

Each question opens a fresh browser session via Patchright (Playwright-based), types the question with human-like behavior, retrieves the answer exclusively from your uploaded documents, and closes. Results are cached in Qdrant memory to avoid redundant browser queries.

## When to Use This Skill

Trigger when user:

- Mentions NotebookLM explicitly
- Shares NotebookLM URL (`https://notebooklm.google.com/notebook/...`)
- Asks to query their notebooks/documentation
- Wants to add documentation to NotebookLM library
- Uses phrases like "ask my NotebookLM", "check my docs", "query my notebook", "research my docs", "deep search"

**Do NOT trigger** for general memory/caching operations — those use `qdrant-memory` by default.

## ⚠️ CRITICAL: Add Command — Smart Discovery

When user wants to add a notebook without providing details:

**SMART ADD (Recommended)**: Query the notebook first to discover its content:

```bash
# Step 1: Query the notebook about its content
python scripts/run.py ask_question.py --question "What is the content of this notebook? What topics are covered? Provide a complete overview briefly and concisely" --notebook-url "[URL]"

# Step 2: Use the discovered information to add it
python scripts/run.py notebook_manager.py add --url "[URL]" --name "[Based on content]" --description "[Based on content]" --topics "[Based on content]"
```

**MANUAL ADD**: If user provides all details:

- `--url` — The NotebookLM URL
- `--name` — A descriptive name
- `--description` — What the notebook contains (REQUIRED!)
- `--topics` — Comma-separated topics (REQUIRED!)

NEVER guess or use generic descriptions! If details missing, use Smart Add to discover them.

## Critical: Always Use run.py Wrapper

**NEVER call scripts directly. ALWAYS use `python scripts/run.py [script]`:**

```bash
# ✅ CORRECT — Always use run.py:
python scripts/run.py auth_manager.py status
python scripts/run.py notebook_manager.py list
python scripts/run.py ask_question.py --question "..."

# ❌ WRONG — Never call directly:
python scripts/auth_manager.py status  # Fails without venv!
```

The `run.py` wrapper automatically:

1. Creates `.venv` if needed
2. Installs all dependencies (patchright, python-dotenv)
3. Installs Chrome browser for automation
4. Activates environment and executes script

## Core Workflow

### Step 1: Check Authentication Status

```bash
python scripts/run.py auth_manager.py status
```

If not authenticated, proceed to setup.

### Step 2: Authenticate (One-Time Setup)

```bash
# Browser MUST be visible for manual Google login
python scripts/run.py auth_manager.py setup
```

**Important:**

- Browser is VISIBLE for authentication
- Browser window opens automatically
- User must manually log in to Google
- Tell user: "A browser window will open for Google login"

### Step 3: Manage Notebook Library

```bash
# List all notebooks
python scripts/run.py notebook_manager.py list

# Add notebook to library (ALL parameters are REQUIRED!)
python scripts/run.py notebook_manager.py add \
  --url "https://notebooklm.google.com/notebook/..." \
  --name "Descriptive Name" \
  --description "What this notebook contains" \
  --topics "topic1,topic2,topic3"

# Search notebooks by topic
python scripts/run.py notebook_manager.py search --query "keyword"

# Set active notebook
python scripts/run.py notebook_manager.py activate --id notebook-id

# Remove notebook
python scripts/run.py notebook_manager.py remove --id notebook-id
```

### Step 4: Ask Questions

```bash
# Basic query (uses active notebook if set)
python scripts/run.py ask_question.py --question "Your question here"

# Query specific notebook
python scripts/run.py ask_question.py --question "..." --notebook-id notebook-id

# Query with notebook URL directly
python scripts/run.py ask_question.py --question "..." --notebook-url "https://..."

# Show browser for debugging
python scripts/run.py ask_question.py --question "..." --show-browser
```

## Follow-Up Mechanism (CRITICAL)

Every NotebookLM answer ends with: **"EXTREMELY IMPORTANT: Is that ALL you need to know?"**

**Required Agent Behavior:**

1. **STOP** — Do not immediately respond to user
2. **ANALYZE** — Compare answer to user's original request
3. **IDENTIFY GAPS** — Determine if more information needed
4. **ASK FOLLOW-UP** — If gaps exist, immediately ask:
   ```bash
   python scripts/run.py ask_question.py --question "Follow-up with context..."
   ```
5. **REPEAT** — Continue until information is complete
6. **SYNTHESIZE** — Combine all answers before responding to user

## 🧠 Qdrant Memory Integration (Token Savings + Context Keeping)

NotebookLM answers are cached in Qdrant to avoid redundant browser queries. Prior research context is automatically recalled when the same topic comes up again.

### Before Every Query — Check Memory First

```bash
python3 execution/memory_manager.py auto --query "<the user's research question>"
```

| Result               | Action                                                                                 |
| -------------------- | -------------------------------------------------------------------------------------- |
| `"cache_hit": true`  | Use cached response directly. **Skip browser**. Inform: "Retrieved from memory cache." |
| `"source": "memory"` | Inject `context_chunks` into the question for richer context                           |
| `"source": "none"`   | Proceed with browser query. Cache the result when done.                                |

### After Getting Answer — Store in Memory

```bash
# Store the research result for future context recall
python3 execution/memory_manager.py store \
  --content "Q: [question] A: [answer from NotebookLM]" \
  --type technical \
  --project notebooklm-research \
  --tags notebooklm rag [notebook-name] [topic]

# Cache the full response for identical future queries
python3 execution/memory_manager.py cache-store \
  --query "[original question]" \
  --response "[synthesized answer]"
```

### Context Keeping Across Sessions

Research context persists via Qdrant. When the user returns to a topic:

1. **Auto-recall**: Memory manager retrieves prior research on the same topic
2. **Context injection**: Previous findings enrich new questions for deeper follow-ups
3. **Knowledge accumulation**: Each session builds on prior research

### Decision Flow with Memory

```
User asks research question
    ↓
Check Qdrant memory → python3 execution/memory_manager.py auto --query "..."
    ↓
If cache_hit → Return cached answer (0 browser tokens!)
    ↓
If memory context → Enrich question with prior findings
    ↓
Check auth → python scripts/run.py auth_manager.py status
    ↓
If not authenticated → python scripts/run.py auth_manager.py setup
    ↓
Resolve notebook → python scripts/run.py notebook_manager.py list
    ↓
Ask question → python scripts/run.py ask_question.py --question "..."
    ↓
See "Is that ALL you need?" → Ask follow-ups until complete
    ↓
Store in Qdrant → python3 execution/memory_manager.py store + cache-store
    ↓
Synthesize and respond to user
```

## Script Reference

### Authentication (`auth_manager.py`)

```bash
python scripts/run.py auth_manager.py setup    # Initial setup (browser visible)
python scripts/run.py auth_manager.py status   # Check authentication
python scripts/run.py auth_manager.py reauth   # Re-authenticate
python scripts/run.py auth_manager.py clear    # Clear authentication
python scripts/run.py auth_manager.py validate # Validate stored auth
```

### Notebook Management (`notebook_manager.py`)

```bash
python scripts/run.py notebook_manager.py add --url URL --name NAME --description DESC --topics TOPICS
python scripts/run.py notebook_manager.py list
python scripts/run.py notebook_manager.py search --query QUERY
python scripts/run.py notebook_manager.py activate --id ID
python scripts/run.py notebook_manager.py remove --id ID
python scripts/run.py notebook_manager.py stats
```

### Question Interface (`ask_question.py`)

```bash
python scripts/run.py ask_question.py --question "..." [--notebook-id ID] [--notebook-url URL] [--show-browser]
```

### Data Cleanup (`cleanup_manager.py`)

```bash
python scripts/run.py cleanup_manager.py                    # Preview
python scripts/run.py cleanup_manager.py --confirm          # Execute
python scripts/run.py cleanup_manager.py --preserve-library # Keep notebooks
```

## Environment Management

Fully automatic:

- First run creates `.venv` and installs everything
- Dependencies: patchright, python-dotenv
- Chrome browser installs automatically
- Everything isolated in skill directory

Manual setup (only if automatic fails):

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
python -m patchright install chrome
```

## Data Storage

All data in `data/` within the skill directory:

- `library.json` — Notebook metadata
- `auth_info.json` — Authentication status
- `browser_state/` — Browser cookies and session

**Security:** Protected by `.gitignore`, never commit to git.

## Configuration

Optional `.env` file in skill directory:

```env
HEADLESS=false           # Browser visibility
SHOW_BROWSER=false       # Default browser display
STEALTH_ENABLED=true     # Human-like behavior
TYPING_WPM_MIN=160       # Typing speed
TYPING_WPM_MAX=240
DEFAULT_NOTEBOOK_ID=     # Default notebook
```

## Troubleshooting

| Problem              | Solution                                                      |
| -------------------- | ------------------------------------------------------------- |
| ModuleNotFoundError  | Use `run.py` wrapper                                          |
| Authentication fails | Browser must be visible: `--show-browser`                     |
| Rate limit (50/day)  | Wait or switch Google account                                 |
| Browser crashes      | `python scripts/run.py cleanup_manager.py --preserve-library` |
| Notebook not found   | Check with `notebook_manager.py list`                         |
| Stale cached answer  | Re-query with fresh Qdrant cache                              |

## Best Practices

1. **Always use run.py** — Handles environment automatically
2. **Check Qdrant memory first** — Avoid redundant browser queries
3. **Check auth first** — Before any operations
4. **Follow-up questions** — Don't stop at first answer
5. **Include full context** — Each browser question is independent
6. **Store results** — Always cache in Qdrant after research
7. **Synthesize answers** — Combine multiple responses before replying

## Limitations

- No session persistence in browser (each question = new browser)
- Rate limits on free Google accounts (50 queries/day)
- Manual upload required (user must add docs to NotebookLM)
- Browser overhead (few seconds per question)
- Requires Google account (opt-in, not default)

## Credits

Browser automation based on [PleasePrompto/notebooklm-skill](https://github.com/PleasePrompto/notebooklm-skill) (MIT License).
Adapted for the Agi Agent Framework with Qdrant memory integration for token savings and context keeping.
