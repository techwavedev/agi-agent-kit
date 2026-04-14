# MCP Compatibility

> **Decision (2026-03-14):** MCP compatibility is implemented as a purely additive layer.
> No existing files were modified. All MCP files are optional alongside the existing skill structure.

## When MCP is and isn't needed

**Coding agents with bash access** (Antigravity, Claude Code, Kiro, Cursor, OpenCode, Copilot) already have full access to everything — agent teams, sub-agents, skills, memory — because they run bash commands directly and read their instruction file (all symlinked to `AGENTS.md`). MCP adds nothing for them.

**MCP is only needed for pure chat interfaces** with no bash execution: Claude Desktop, or any client that speaks MCP but can't run terminal commands. These clients can't call `dispatch_agent_team.py` themselves, so MCP gives them a limited window into the memory and coordination layer.

## What MCP exposes

The AGI framework exposes its memory and cross-agent coordination layer as [MCP (Model Context Protocol)](https://modelcontextprotocol.io) servers for chat-interface clients.

Two servers are provided:

| Server | File | Tools | Use when |
|---|---|---|---|
| `agi-framework` | `execution/mcp_server.py` | 16 | Daily use — memory + cross-agent + GitHub PR + health |
| `qdrant-memory` | `skills/qdrant-memory/mcp_server.py` | 6 | Direct Qdrant access (low-level ops) |

---

## Quick Setup

Add to your MCP client config (Claude Desktop: `~/.claude/claude_desktop_config.json`, Antigravity: equivalent config):

```json
{
  "mcpServers": {
    "agi-framework": {
      "command": "python3",
      "args": ["/absolute/path/to/execution/mcp_server.py"],
      "env": {
        "QDRANT_URL": "http://localhost:6333",
        "EMBEDDING_PROVIDER": "ollama",
        "OLLAMA_URL": "http://localhost:11434"
      }
    }
  }
}
```

> **Prerequisites:** Qdrant running on port 6333, Ollama running with `nomic-embed-text` pulled.
> Use `python3 execution/session_boot.py --auto-fix` to verify and repair.

---

## `agi-framework` — Execution Layer Server

**File:** `execution/mcp_server.py`

### Memory tools

| Tool | What it does |
|---|---|
| `memory_auto` | Cache check → context retrieve → proceed (the CLAUDE.md-mandated entry point) |
| `memory_store` | Store decision / code / error / conversation / technical note |
| `memory_retrieve` | Hybrid semantic + BM25 search, returns top-K chunks |
| `memory_cache_store` | Cache a query-response pair for any agent to reuse |
| `memory_list` | Browse stored memories with type/project filters |
| `memory_cache_clear` | Remove old cache entries |

### Cross-agent coordination tools

All agents share the same Qdrant instance. These tools wire them together.

| Tool | What it does |
|---|---|
| `agent_store` | Publish your work so Antigravity, Cursor, etc. can see it |
| `agent_sync` | Pull what other agents have done recently (run at session start) |
| `agent_status` | Full team view — all agents, recent activity |
| `agent_handoff` | Delegate a task to a specific agent |
| `agent_broadcast` | Team-wide announcement (breaking changes, releases) |
| `agent_pending` | Check tasks handed off to you (run at session start) |

### System tool

| Tool | What it does |
|---|---|
| `session_health` | Qdrant + Ollama + collections health check. Returns `memory_ready: true/false` |

### GitHub / PR tools

| Tool | What it does |
|---|---|
| `pr_status` | PR state, mergeable flag, draft flag, CI checks summary, URL. Accepts PR number or full URL. |
| `pr_diff` | Unified diff for a PR, truncated to `max_bytes` (default 20 000). |
| `copilot_check_result` | Read a Copilot delegation result from `.tmp/delegations/<run_id>.json`. |

> **Prerequisites for GitHub tools:** `gh` CLI must be installed and authenticated (`gh auth login`).

---

## `qdrant-memory` — Skill-Level Server

**File:** `skills/qdrant-memory/mcp_server.py`

Wraps the skill's existing Python modules directly (no subprocess). Use this when you need direct control over Qdrant operations.

| Tool | Wraps |
|---|---|
| `memory_store` | `memory_retrieval.store_memory()` |
| `memory_search` | `memory_retrieval.retrieve_context()` |
| `memory_list` | `memory_retrieval.list_memories()` |
| `cache_check` | `semantic_cache.check_cache()` |
| `cache_store` | `semantic_cache.store_response()` |
| `cache_clear` | `semantic_cache.clear_cache()` |

---

## Compatibility Matrix

| Client | Instructions file | Agent teams | Skills | MCP needed? |
|---|---|---|---|---|
| Claude Code | `CLAUDE.md` → `AGENTS.md` | ✅ | ✅ | No |
| Antigravity / Gemini | `GEMINI.md` → `AGENTS.md` | ✅ | ✅ | No |
| Kiro (AWS) | `.kiro/steering/agents.md` → `AGENTS.md` | ✅ | ✅ | No |
| Cursor | `AGENTS.md` directly | ✅ | ✅ | No |
| OpenCode | `AGENTS.md` directly | ✅ | ✅ | No |
| Copilot | `AGENTS.md` directly | ✅ | ✅ | No |
| Claude Desktop | — (chat only) | ✗ | ✗ | **Yes** |
| Any pure chat MCP client | — (chat only) | ✗ | ✗ | **Yes** |

All coding agents share the same `AGENTS.md` instructions and write to the **same Qdrant instance**. The symlink pattern is what makes cross-agent compatibility work — not MCP.

---

## MCP Support in New Skills

Skills created with `init_skill.py` are automatically scaffolded with:

- `mcp_server.py` — stub MCP server using the generic template
- `mcp_tools.json` — tool definitions placeholder

**Template location:** `skill-creator/templates/mcp_server_template.py`

To implement: fill in `handle_tool_call()` in `mcp_server.py` and define tools in `mcp_tools.json`.

---

## Architecture Decision: Why Additive

**Problem:** Adding MCP fields to `SKILL.md` frontmatter would break `quick_validate.py`, which enforces an allowlist: `{name, description, license, allowed-tools, metadata}`.

**Decision:** Keep MCP as separate files (`mcp_server.py`, `mcp_tools.json`) alongside the existing skill structure. No changes to validator, no changes to `update_catalog.py`, no changes to any existing SKILL.md.

The `metadata:` field is available for lightweight MCP hints (version, category) since it is already in the validator allowlist.

**Result:** Existing skills work exactly as before. MCP is opt-in per skill.
