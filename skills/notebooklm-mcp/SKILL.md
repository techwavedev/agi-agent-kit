---
name: notebooklm-mcp
description: "Connects to Google NotebookLM via Model Context Protocol (MCP) to access notebooks, sources, and query content. Triggers when the user asks to summarize, query, or interact with NotebookLM content."
---

# NotebookLM MCP Connector

## Overview

This skill allows the agent to interact with Google NotebookLM content through the `notebooklm-mcp-server`. It enables listing notebooks, retrieving sources, and querying the intelligent notebook interface.

## Capabilities

1.  **List Notebooks**: View all your NotebookLM notebooks.
2.  **Mange Sources**: Add or list sources within a notebook.
3.  **Query Content**: Ask questions about the documents in your notebooks.

## Setup & Configuration

### 1. Installation

The NotebookLM MCP server is installed via `uv`:

```bash
uv tool install notebooklm-mcp-server
```

### 2. Authentication

Authentication requires extracting cookies from a logged-in Chrome session.

**Recommended Method (File Mode):**

1.  Install a cookie exporter extension (e.g., [Get cookies.txt LOCALLY](https://chrome.google.com/webstore/detail/get-cookies-txt-locally/cclelndahbckbenkjhflccgombaodnld)).
2.  Log in to [NotebookLM](https://notebooklm.google.com/).
3.  Export cookies for `notebooklm.google.com` to a file (e.g., `~/cookies.txt`).
4.  Run the auth tool:
    ```bash
    notebooklm-mcp-auth --file ~/cookies.txt
    ```

**Auto Mode (Requires Chrome Debugging):**

If Chrome is running with `--remote-debugging-port=9222`, you can run:

```bash
notebooklm-mcp-auth
```

### 3. MCP Configuration

Add the following to your MCP client configuration (e.g., Claude Desktop or OpenCode):

```json
{
  "mcpServers": {
    "notebooklm-mcp-server": {
      "command": "uv",
      "args": ["tool", "run", "notebooklm-mcp-server"]
    }
  }
}
```

## Usage

Use the available MCP tools to interact with NotebookLM.

- `list_notebooks()`
- `get_notebook(notebook_id)`
- `query_notebook(notebook_id, query)`
