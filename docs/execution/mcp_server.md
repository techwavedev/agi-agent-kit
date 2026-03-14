# execution/mcp_server.py

AGI Framework MCP Server. Exposes the execution layer as MCP tools for chat-interface clients (Claude Desktop, etc.) that cannot run bash directly.

> **Coding agents** (Antigravity, Claude Code, Kiro, Cursor, OpenCode) do not need this — they use `execution/` scripts directly via bash.

## Tools

### Memory (delegates to `memory_manager.py`)

| Tool | CLI equivalent |
|---|---|
| `memory_auto` | `memory_manager.py auto --query <q>` |
| `memory_store` | `memory_manager.py store --content <c> --type <t>` |
| `memory_retrieve` | `memory_manager.py retrieve --query <q>` |
| `memory_cache_store` | `memory_manager.py cache-store --query <q> --response <r>` |
| `memory_list` | `memory_manager.py list` |
| `memory_cache_clear` | `memory_manager.py cache-clear` |

### Cross-agent coordination (delegates to `cross_agent_context.py`)

| Tool | CLI equivalent |
|---|---|
| `agent_store` | `cross_agent_context.py store --agent <a> --action <x>` |
| `agent_sync` | `cross_agent_context.py sync --agent <a>` |
| `agent_status` | `cross_agent_context.py status` |
| `agent_handoff` | `cross_agent_context.py handoff --from <a> --to <b> --task <t>` |
| `agent_broadcast` | `cross_agent_context.py broadcast --agent <a> --message <m>` |
| `agent_pending` | `cross_agent_context.py pending --agent <a>` |

### System

| Tool | CLI equivalent |
|---|---|
| `session_health` | `session_boot.py --json` |

## Transport

JSON-RPC 2.0 over stdio. Methods handled: `initialize`, `tools/list`, `tools/call`.

## Usage

```bash
# Test locally
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' | python3 execution/mcp_server.py
```

## Environment variables

| Variable | Default |
|---|---|
| `QDRANT_URL` | `http://localhost:6333` |
| `EMBEDDING_PROVIDER` | `ollama` |
| `OLLAMA_URL` | `http://localhost:11434` |
| `MEMORY_COLLECTION` | `agent_memory` |
| `CACHE_COLLECTION` | `semantic_cache` |

## See also

- `docs/mcp-compatibility.md` — full client setup and compatibility matrix
- `skills/qdrant-memory/mcp_server.py` — skill-level MCP server (direct Qdrant ops)
