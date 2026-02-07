# NotebookLM MCP — API & Tool Reference

## Source

[PleasePrompto/notebooklm-mcp](https://github.com/PleasePrompto/notebooklm-mcp) v1.2.1+

## Core Tools

### `ask_question`

Primary research tool — queries NotebookLM for grounded answers.

**Parameters:**

| Param             | Type    | Required | Description                           |
| ----------------- | ------- | -------- | ------------------------------------- |
| `question`        | string  | ✅       | The question to ask                   |
| `session_id`      | string  | ❌       | Reuse an existing session             |
| `notebook_id`     | string  | ❌       | Target specific notebook from library |
| `notebook_url`    | string  | ❌       | Direct NotebookLM URL                 |
| `show_browser`    | boolean | ❌       | Show Chrome window during query       |
| `browser_options` | object  | ❌       | Override stealth/viewport settings    |

**Returns:** NotebookLM's answer + follow-up reminder for iterative research.

**Notes:**

- Every response ends with a follow-up reminder to encourage deeper research
- Supports `browser_options.stealth` for humanization overrides
- Rate limit: ~50 queries/day per Google account

### `setup_auth`

Opens persistent Chrome profile for manual Google login. One-time setup.

### `re_auth`

Re-authenticate or switch Google accounts. Clears all sessions and auth data.

### `get_health`

Returns auth status, active sessions, and configuration summary.

### `list_sessions` / `close_session` / `reset_session`

Inspect and manage active browser sessions.

---

## Library Management Tools

### `add_notebook`

Conversational add — expects confirmation before writing.

**Parameters:** `name`, `url`, `description`, `topics`, `tags`

### `list_notebooks`

Returns all notebooks with: `id`, `name`, `topics`, `url`, `metadata`.

### `get_notebook`

Fetch single notebook by `id`.

### `select_notebook`

Set the active default notebook for subsequent `ask_question` calls.

### `update_notebook`

Modify metadata fields (`name`, `description`, `topics`, `tags`).

### `remove_notebook`

Removes from local library only (does NOT delete from NotebookLM).

### `search_notebooks`

Simple query across `name`, `description`, `topics`, `tags`.

### `get_library_stats`

Aggregate statistics: total notebooks, usage counts, last accessed.

---

## Resources (MCP Resource Protocol)

| URI                         | Description                |
| --------------------------- | -------------------------- |
| `notebooklm://library`      | Full library as JSON       |
| `notebooklm://library/{id}` | Specific notebook metadata |

---

## Browser Options Schema

Passed via `browser_options` parameter in `ask_question`, `setup_auth`, `re_auth`:

```typescript
{
  show: boolean,              // Show browser window (default: false)
  headless: boolean,          // Headless mode (default: true)
  timeout_ms: number,         // Browser timeout (default: 30000)
  stealth: {
    enabled: boolean,         // Master switch (default: true)
    random_delays: boolean,   // Random delays (default: true)
    human_typing: boolean,    // Human-like typing (default: true)
    mouse_movements: boolean, // Mouse movements (default: true)
    typing_wpm_min: number,   // Min WPM (default: 160)
    typing_wpm_max: number,   // Max WPM (default: 240)
    delay_min_ms: number,     // Min delay (default: 100)
    delay_max_ms: number,     // Max delay (default: 400)
  },
  viewport: {
    width: number,            // Default: 1024
    height: number,           // Default: 768
  }
}
```

---

## Environment Variables

All optional — sensible defaults work out of the box.

| Variable                      | Default | Description                 |
| ----------------------------- | ------- | --------------------------- |
| `AUTO_LOGIN_ENABLED`          | `false` | Enable auto-login           |
| `LOGIN_EMAIL`                 | —       | For auto-login              |
| `LOGIN_PASSWORD`              | —       | For auto-login              |
| `STEALTH_ENABLED`             | `true`  | Master humanization switch  |
| `HEADLESS`                    | `true`  | Hide browser                |
| `BROWSER_TIMEOUT`             | `30000` | Browser timeout (ms)        |
| `MAX_SESSIONS`                | `10`    | Max concurrent sessions     |
| `SESSION_TIMEOUT`             | `900`   | Session timeout (seconds)   |
| `NOTEBOOK_PROFILE_STRATEGY`   | `auto`  | `auto\|single\|isolated`    |
| `NOTEBOOK_CLEANUP_ON_STARTUP` | `true`  | Clean old profiles on start |
| `NOTEBOOK_INSTANCE_TTL_HOURS` | `72`    | Profile TTL                 |
| `NOTEBOOK_INSTANCE_MAX_COUNT` | `20`    | Max profile instances       |
