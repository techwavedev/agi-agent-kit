#!/usr/bin/env python3
"""
MCP Server for qdrant-memory skill.

Exposes long-term memory (Qdrant + Ollama) and semantic cache as MCP tools.
Zero changes to existing scripts — this is a pure wrapper over them.

Tools exposed:
  memory_store   - Store content with type/project/tags
  memory_search  - Semantic + keyword hybrid search
  memory_list    - Browse memories with filters
  cache_check    - Check semantic cache (100% token savings on hit)
  cache_store    - Cache a query-response pair
  cache_clear    - Remove old cache entries

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Claude Desktop setup (~/.claude/claude_desktop_config.json):

  {
    "mcpServers": {
      "qdrant-memory": {
        "command": "python3",
        "args": ["/absolute/path/to/skills/qdrant-memory/mcp_server.py"],
        "env": {
          "QDRANT_URL": "http://localhost:6333",
          "EMBEDDING_PROVIDER": "ollama",
          "OLLAMA_URL": "http://localhost:11434"
        }
      }
    }
  }

Environment variables (all optional — defaults shown):
  QDRANT_URL           http://localhost:6333
  EMBEDDING_PROVIDER   ollama   (or "openai" / "bedrock")
  OLLAMA_URL           http://localhost:11434
  OPENAI_API_KEY       (required if EMBEDDING_PROVIDER=openai)
  MEMORY_COLLECTION    agent_memory
  CACHE_COLLECTION     semantic_cache
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import json
import os
import sys

# Add the skill's scripts/ directory so we can import existing modules directly
_SCRIPTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scripts")
sys.path.insert(0, _SCRIPTS_DIR)

SERVER_NAME = "qdrant-memory"
SERVER_VERSION = "1.0.0"

TOOLS = [
    {
        "name": "memory_store",
        "description": (
            "Store a memory (decision, code pattern, error solution, conversation, "
            "or technical note) in long-term Qdrant storage with semantic + BM25 indexing."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "content": {
                    "type": "string",
                    "description": "The text content to store"
                },
                "type": {
                    "type": "string",
                    "enum": ["decision", "code", "error", "conversation", "technical"],
                    "description": "Memory category for filtering"
                },
                "project": {
                    "type": "string",
                    "description": "Project name for scoped filtering (optional)"
                },
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Tags for filtering (optional)"
                }
            },
            "required": ["content", "type"]
        }
    },
    {
        "name": "memory_search",
        "description": (
            "Search long-term memory using hybrid semantic + keyword matching. "
            "Returns the most relevant context chunks (80-95% token savings vs full history)."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Natural language search query"
                },
                "type": {
                    "type": "string",
                    "description": "Filter by memory type: decision, code, error, conversation, technical (optional)"
                },
                "project": {
                    "type": "string",
                    "description": "Filter by project name (optional)"
                },
                "top_k": {
                    "type": "integer",
                    "description": "Number of results to return (default: 5)",
                    "default": 5
                },
                "threshold": {
                    "type": "number",
                    "description": "Minimum similarity score 0.0–1.0 (default: 0.7)",
                    "default": 0.7
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "memory_list",
        "description": "List stored memories. Optionally filter by type and/or project.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "type": {
                    "type": "string",
                    "description": "Filter by memory type (optional)"
                },
                "project": {
                    "type": "string",
                    "description": "Filter by project name (optional)"
                },
                "limit": {
                    "type": "integer",
                    "description": "Max results (default: 20)",
                    "default": 20
                }
            }
        }
    },
    {
        "name": "cache_check",
        "description": (
            "Check if a semantically similar query has been cached. "
            "Returns the cached response on hit (100% token savings)."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The query to check"
                },
                "threshold": {
                    "type": "number",
                    "description": "Similarity threshold 0.0–1.0 (default: 0.92)",
                    "default": 0.92
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "cache_store",
        "description": "Store a query-response pair in the semantic cache for future reuse.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The original query"
                },
                "response": {
                    "type": "string",
                    "description": "The response to cache"
                },
                "project": {
                    "type": "string",
                    "description": "Project name (optional)"
                }
            },
            "required": ["query", "response"]
        }
    },
    {
        "name": "cache_clear",
        "description": "Remove semantic cache entries older than N days.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "older_than_days": {
                    "type": "integer",
                    "description": "Delete entries older than this many days (default: 7)",
                    "default": 7
                }
            }
        }
    }
]


def handle_tool_call(name: str, arguments: dict) -> dict:
    """Route MCP tool calls to the skill's existing Python modules."""
    try:
        if name == "memory_store":
            from memory_retrieval import store_memory
            metadata = {}
            if arguments.get("project"):
                metadata["project"] = arguments["project"]
            if arguments.get("tags"):
                metadata["tags"] = arguments["tags"]
            result = store_memory(arguments["content"], arguments["type"], metadata)
            return {"type": "text", "text": json.dumps(result, indent=2)}

        elif name == "memory_search":
            from memory_retrieval import retrieve_context, build_filter
            filters = build_filter(
                type_filter=arguments.get("type"),
                project=arguments.get("project")
            )
            result = retrieve_context(
                arguments["query"],
                filters={"must": filters["must"]} if filters else None,
                top_k=arguments.get("top_k", 5),
                score_threshold=arguments.get("threshold", 0.7)
            )
            return {"type": "text", "text": json.dumps(result, indent=2)}

        elif name == "memory_list":
            from memory_retrieval import list_memories, build_filter
            filters = build_filter(
                type_filter=arguments.get("type"),
                project=arguments.get("project")
            )
            result = list_memories(
                filters={"must": filters["must"]} if filters else None,
                limit=arguments.get("limit", 20)
            )
            return {"type": "text", "text": json.dumps(result, indent=2)}

        elif name == "cache_check":
            from semantic_cache import check_cache
            result = check_cache(arguments["query"], arguments.get("threshold", 0.92))
            if result is None:
                result = {"cache_hit": False, "query": arguments["query"]}
            return {"type": "text", "text": json.dumps(result, indent=2)}

        elif name == "cache_store":
            from semantic_cache import store_response
            metadata = {}
            if arguments.get("project"):
                metadata["project"] = arguments["project"]
            result = store_response(arguments["query"], arguments["response"], metadata)
            return {"type": "text", "text": json.dumps(result, indent=2)}

        elif name == "cache_clear":
            from semantic_cache import clear_cache
            result = clear_cache(arguments.get("older_than_days", 7))
            return {"type": "text", "text": json.dumps(result, indent=2)}

        else:
            return {"type": "text", "text": json.dumps({"error": f"Unknown tool: {name}"})}

    except Exception as e:
        return {
            "type": "text",
            "text": json.dumps({"error": type(e).__name__, "message": str(e)})
        }


def send(response: dict):
    """Write a JSON-RPC 2.0 response to stdout."""
    sys.stdout.write(json.dumps(response) + "\n")
    sys.stdout.flush()


def main():
    """JSON-RPC 2.0 loop over stdio — the MCP transport layer."""
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue

        try:
            request = json.loads(line)
        except json.JSONDecodeError:
            continue

        req_id = request.get("id")
        method = request.get("method", "")

        # Notifications have no id and require no response
        if req_id is None:
            continue

        if method == "initialize":
            send({
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION}
                }
            })

        elif method == "tools/list":
            send({
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {"tools": TOOLS}
            })

        elif method == "tools/call":
            params = request.get("params", {})
            content = handle_tool_call(
                params.get("name", ""),
                params.get("arguments", {})
            )
            send({
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {"content": [content]}
            })

        else:
            send({
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32601, "message": f"Method not found: {method}"}
            })


if __name__ == "__main__":
    main()
