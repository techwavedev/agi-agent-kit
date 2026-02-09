---
name: notebooklm-rag
description: "Deep RAG layer powered by Google NotebookLM + Gemini. The agent autonomously manages notebooks via MCP tools — authentication, library management, querying, follow-ups, and caching. Opt-in for users with a Google account. Default RAG is qdrant-memory. Triggers on: '@notebooklm', 'research my docs', 'deep search', 'query my notebook', 'check my notebooks'."
---

# NotebookLM Deep RAG

> **This is a Deep RAG tool.** The agent uses NotebookLM as an autonomous knowledge backend via MCP tools. It handles auth, notebooks, queries, follow-ups, and caching — fully hands-free.
>
> **Opt-in:** Requires a Google account with NotebookLM. Default RAG uses `qdrant-memory` (local, offline, no account needed).

## Architecture

```
User question
    ↓
Agent checks Qdrant cache → hit? → return cached answer (0 cost)
    ↓ miss
Agent checks NotebookLM auth → not authenticated? → setup_auth (opens browser)
    ↓ authenticated
Agent resolves notebook → list_notebooks / search_notebooks / select_notebook
    ↓
Agent asks question → ask_question (browser automation, Gemini-grounded answer)
    ↓
Agent evaluates answer → gaps? → ask follow-up automatically
    ↓ complete
Agent stores in Qdrant → cache for future use
    ↓
Agent responds to user with synthesized answer
```

## MCP Tools Reference

The agent has direct access to these tools. Use them autonomously.

### Authentication

| Tool         | When                                          |
| ------------ | --------------------------------------------- |
| `get_health` | First — always check auth status              |
| `setup_auth` | One-time Google login (opens visible browser) |
| `re_auth`    | Switch account or fix expired session         |

### Library Management

| Tool                | When                                                              |
| ------------------- | ----------------------------------------------------------------- |
| `list_notebooks`    | See all registered notebooks                                      |
| `add_notebook`      | Register a new notebook (url, name, description, topics required) |
| `remove_notebook`   | Remove a notebook from library                                    |
| `update_notebook`   | Update notebook metadata                                          |
| `search_notebooks`  | Find notebooks by topic/keyword                                   |
| `select_notebook`   | Set active notebook (used as default for queries)                 |
| `get_notebook`      | Get details of a specific notebook                                |
| `get_library_stats` | Library overview                                                  |

### Querying

| Tool            | When                                  |
| --------------- | ------------------------------------- |
| `ask_question`  | Query a notebook — core research tool |
| `list_sessions` | Check active browser sessions         |
| `close_session` | Close a session when done             |
| `reset_session` | Clear session history                 |

### Maintenance

| Tool           | When                           |
| -------------- | ------------------------------ |
| `cleanup_data` | Clean browser data, fix issues |

## Autonomous Workflow

### On Any Research Request:

1. **Check Qdrant first** — `memory_manager.py auto --query "..."`. If cache hit, return immediately.

2. **Check auth** — `get_health`. If not authenticated, run `setup_auth` and tell user a browser will open.

3. **Resolve notebook** — `list_notebooks`. If user mentions a topic, `search_notebooks`. If no notebooks exist, ask user for a NotebookLM URL and `add_notebook`.

4. **Ask the question** — `ask_question` with the resolved notebook. Can pass `notebook_id` (from library) or `notebook_url` (direct URL).

5. **Follow up** — Every answer ends with "Is that ALL you need to know?" The agent MUST:
   - Compare answer to original request
   - Identify gaps
   - Ask follow-up questions automatically (include full context — each question is a new browser session)
   - Repeat until information is complete

6. **Cache in Qdrant** — Store result with `memory_manager.py store` and `cache-store`.

7. **Respond** — Synthesize all answers into a cohesive response.

### On "Add a notebook":

**Smart Add** — If user provides a URL but no details:

1. `ask_question` with `notebook_url` and question: "What is the content of this notebook? What topics are covered? Provide a brief overview."
2. Use the answer to fill in `name`, `description`, `topics`
3. `add_notebook` with discovered metadata

**Manual Add** — If user provides all details directly, just `add_notebook`.

### On Notebook Management:

- "List my notebooks" → `list_notebooks`
- "Remove X" → Confirm with user → `remove_notebook`
- "Switch to X" → `select_notebook`
- "Update X description" → `update_notebook`
- "Search for X" → `search_notebooks`

## Qdrant Integration (Context Keeping)

NotebookLM answers are cached in Qdrant. Prior research is recalled automatically.

### Before Query

```bash
python3 execution/memory_manager.py auto --query "<research question>"
```

- `cache_hit: true` → Skip browser, return cached answer
- `source: memory` → Inject prior context into the question
- `source: none` → Proceed with NotebookLM query

### After Query

```bash
python3 execution/memory_manager.py store \
  --content "Q: [question] A: [answer]" \
  --type technical \
  --project notebooklm-research \
  --tags notebooklm [notebook-name] [topic]

python3 execution/memory_manager.py cache-store \
  --query "[question]" \
  --response "[synthesized answer]"
```

### Context Keeping

- Prior research on same topic is auto-recalled
- Previous findings enrich follow-up questions
- Each session builds compound knowledge

## MCP Server Setup

The NotebookLM MCP server must be configured in the AI host:

### Claude Desktop / Claude Code

```json
{
  "mcpServers": {
    "notebooklm": {
      "command": "npx",
      "args": ["-y", "@anthropic/notebooklm-mcp"]
    }
  }
}
```

### Opencode

```json
{
  "mcpServers": {
    "notebooklm": {
      "command": "npx",
      "args": ["-y", "@anthropic/notebooklm-mcp"]
    }
  }
}
```

If MCP is not configured, fall back to the Python scripts in `scripts/` (see Fallback section below).

## Fallback: Python Scripts

When MCP is not available, use the bundled scripts via `run.py`:

```bash
python scripts/run.py auth_manager.py status          # Check auth
python scripts/run.py auth_manager.py setup            # Authenticate
python scripts/run.py notebook_manager.py list         # List notebooks
python scripts/run.py notebook_manager.py add --url URL --name NAME --description DESC --topics TOPICS
python scripts/run.py ask_question.py --question "..." # Query
python scripts/run.py ask_question.py --question "..." --notebook-url "https://..."
python scripts/run.py cleanup_manager.py --confirm     # Cleanup
```

The `run.py` wrapper auto-creates `.venv`, installs dependencies (patchright, python-dotenv), and installs Chrome.

## Troubleshooting

| Problem                  | Solution                                                |
| ------------------------ | ------------------------------------------------------- |
| Not authenticated        | `setup_auth` (browser opens for Google login)           |
| Rate limit (50/day free) | Wait 24h or `re_auth` with different Google account     |
| Browser crashes          | `cleanup_data(preserve_library=true)` then `setup_auth` |
| Stale cached answer      | Re-query or clear Qdrant cache                          |
| Notebook not found       | `list_notebooks`, then `add_notebook` if missing        |
| MCP not available        | Use fallback Python scripts via `run.py`                |

## Limitations

- Rate limits: 50 queries/day (free), 250/day (Google AI Pro)
- Manual upload: User must add documents to NotebookLM first
- Browser overhead: Few seconds per query
- No live notebook discovery: User must provide URLs to register notebooks

## Credits

MCP server: [PleasePrompto/notebooklm-mcp](https://github.com/PleasePrompto/notebooklm-mcp)
Browser automation: [PleasePrompto/notebooklm-skill](https://github.com/PleasePrompto/notebooklm-skill) (MIT License)
Adapted for the Agi Agent Framework with Qdrant memory integration.
