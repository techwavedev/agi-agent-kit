---
name: notebooklm-mcp
description: "Connects to Google NotebookLM via MCP using PleasePrompto/notebooklm-mcp. Browser-automated auth, zero-hallucination research, smart library management. Triggers when user asks to research docs, query NotebookLM, or manage notebook libraries."
---

# NotebookLM MCP Connector

## Overview

This skill integrates [PleasePrompto/notebooklm-mcp](https://github.com/PleasePrompto/notebooklm-mcp) — a Node.js MCP server that lets AI agents research documentation directly through Google NotebookLM with **zero hallucinations**, powered by Gemini 2.5.

### Why NotebookLM over local RAG?

| Feature              | Local RAG                     | NotebookLM MCP                  |
| -------------------- | ----------------------------- | ------------------------------- |
| **Accuracy**         | Keyword-based, misses context | Gemini-powered synthesis        |
| **Hallucinations**   | Invents when unsure           | Refuses if not in docs          |
| **Cost**             | Massive token consumption     | Minimal — offloads to Google    |
| **Setup**            | Embedding pipelines, chunking | Upload docs, query              |
| **Cross-references** | Limited                       | Intelligent multi-doc synthesis |

### Architecture

```
Your Task → Agent → MCP Server → Chrome Automation (Patchright) → NotebookLM → Gemini 2.5 → Your Docs → Accurate Code
```

---

## Setup & Configuration

### 1. Installation

The server runs via NPX — no global install required:

```bash
npx -y notebooklm-mcp@latest
```

### 2. Authentication (One-Time)

Authentication uses **browser-based Google login** via Patchright (Playwright fork). No cookies to extract manually.

**First-time setup:**

1. Say in your chat: `"Log me in to NotebookLM"`
2. A Chrome window opens → log in with your Google account
3. The session persists in `~/Library/Application Support/notebooklm-mcp/chrome_profile/`

**Re-authenticate (rate limit or account switch):**

Say: `"Re-authenticate NotebookLM"` — this closes all sessions, clears auth, and opens a fresh login.

### 3. MCP Client Configuration

**Claude Desktop** (`~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "notebooklm": {
      "command": "/opt/homebrew/bin/npx",
      "args": ["-y", "notebooklm-mcp@latest"]
    }
  }
}
```

**Claude Code:**

```bash
claude mcp add notebooklm npx notebooklm-mcp@latest
```

**Opencode / Generic MCP:**

```json
{
  "mcpServers": {
    "notebooklm": {
      "command": "npx",
      "args": ["notebooklm-mcp@latest"]
    }
  }
}
```

---

## Available Tools

### Core Tools

| Tool            | Description                                                                                                                  |
| --------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| `ask_question`  | Query NotebookLM with a question. Params: `question` (required), `session_id`, `notebook_id`, `notebook_url`, `show_browser` |
| `setup_auth`    | Opens Chrome profile for manual Google login                                                                                 |
| `re_auth`       | Switch account or re-authenticate (clears all sessions)                                                                      |
| `get_health`    | Check auth status, active sessions, configuration                                                                            |
| `list_sessions` | Inspect active browser sessions                                                                                              |
| `close_session` | Close a specific session                                                                                                     |
| `reset_session` | Reset a specific session                                                                                                     |

### Library Management Tools

| Tool                | Description                                                         |
| ------------------- | ------------------------------------------------------------------- |
| `add_notebook`      | Add a notebook to library (conversational, confirms before writing) |
| `list_notebooks`    | List all notebooks with id, name, topics, URL, metadata             |
| `get_notebook`      | Fetch a single notebook by id                                       |
| `select_notebook`   | Set the active default notebook for queries                         |
| `update_notebook`   | Modify notebook metadata fields                                     |
| `remove_notebook`   | Remove from library (doesn't delete from NotebookLM)                |
| `search_notebooks`  | Search across name/description/topics/tags                          |
| `get_library_stats` | Aggregate statistics (total notebooks, usage counts)                |

### Resources

| Resource URI                | Description                                               |
| --------------------------- | --------------------------------------------------------- |
| `notebooklm://library`      | Full library JSON (active notebook, stats, all notebooks) |
| `notebooklm://library/{id}` | Metadata for a specific notebook                          |

---

## Usage Patterns

### Basic Research

```
"I'm building with Next.js 15. Here's my NotebookLM: [link]"
```

The agent automatically:

1. Adds the notebook to library
2. Asks iterative follow-up questions
3. Builds deep understanding before writing code

### Deep Research Workflow

```
"Research the authentication patterns in my docs, ask at least 5 questions"
```

The agent performs autonomous iterative research — each answer triggers deeper questions.

### Library Management

```
"Add [link] to library tagged 'frontend, react, components'"
"What notebooks do I have about backend APIs?"
"Switch to my infrastructure notebook"
```

### Show the Browser

```
"Research this and show me the browser"
```

Sets `show_browser: true` so you can watch the live NotebookLM conversation.

---

## Stealth & Humanization

The server includes built-in humanization to avoid detection:

| Feature         | Default    | Purpose                           |
| --------------- | ---------- | --------------------------------- |
| Random delays   | ✅ Enabled | 100-400ms between actions         |
| Human typing    | ✅ Enabled | 160-240 WPM with natural variance |
| Mouse movements | ✅ Enabled | Realistic cursor paths            |
| Headless mode   | ✅ Enabled | No visible browser window         |

Configurable via environment variables (`STEALTH_ENABLED`, `TYPING_WPM_MIN`, etc.) or runtime `browser_options` parameter.

---

## Tool Profiles

Reduce token usage by loading only the tools you need:

| Profile    | Tools Loaded                | Best For               |
| ---------- | --------------------------- | ---------------------- |
| `full`     | All tools                   | Complete control       |
| `research` | ask_question, library tools | Documentation research |
| `library`  | Library management only     | Organizing notebooks   |

Configure via CLI: `npx notebooklm-mcp@latest --profile research`

---

## Storage

| Path                                                           | Content                                      |
| -------------------------------------------------------------- | -------------------------------------------- |
| `~/Library/Application Support/notebooklm-mcp/chrome_profile/` | Persistent Chrome profile with login session |
| `~/Library/Application Support/notebooklm-mcp/browser_state/`  | Browser context state and cookies            |
| `~/Library/Application Support/notebooklm-mcp/library.json`    | Notebook library with metadata               |

---

## Troubleshooting

| Issue                       | Solution                                                                               |
| --------------------------- | -------------------------------------------------------------------------------------- |
| Rate limit (50 queries/day) | Say "Re-authenticate NotebookLM" to switch Google account                              |
| Auth expired                | Say "Log me in to NotebookLM" to re-login                                              |
| Browser won't open          | Ensure Chrome/Chromium is installed                                                    |
| Stale sessions              | Use `reset_session` or `close_session` tools                                           |
| Disk bloat                  | Auto-cleanup runs on startup/shutdown (configurable via `NOTEBOOK_CLEANUP_ON_STARTUP`) |

---

## Important Notes

- **Free tier limit**: ~50 queries/day per Google account. Quick account switching supported.
- **Security**: Chrome runs locally. Credentials never leave your machine.
- **Disclaimer**: Uses browser automation. Consider using a dedicated Google account.
- **Source**: [PleasePrompto/notebooklm-mcp](https://github.com/PleasePrompto/notebooklm-mcp) (MIT License)
