#!/usr/bin/env python3
"""
AGI Framework MCP Server — Execution Layer.

Exposes the full execution layer (memory, cross-agent coordination, session health)
as MCP tools for use in Claude Desktop, Antigravity, Cursor, Copilot, and any
other MCP-compatible client.

Tools by category:
  ── Memory (memory_manager.py) ──────────────────────────────────────
  memory_auto          Auto-query: cache check → context retrieve → proceed
  memory_store         Store a memory (decision / code / error / technical / conversation)
  memory_retrieve      Retrieve relevant context chunks (semantic + BM25 hybrid)
  memory_cache_store   Cache a query-response pair (100% token savings on future hits)
  memory_list          List stored memories with optional filters
  memory_cache_clear   Remove old cache entries

  ── Cross-Agent Coordination (cross_agent_context.py) ────────────────
  agent_store          Publish your work so other agents (Antigravity, Cursor…) see it
  agent_sync           Pull what other agents have done recently
  agent_status         Team status — all agents, recent activity
  agent_handoff        Hand off a task to a specific agent
  agent_broadcast      Broadcast an update to ALL agents
  agent_pending        Check tasks that have been handed off to you

  ── GitHub / PR (gh CLI) ─────────────────────────────────────────────
  pr_status            PR state, mergeable flag, CI checks summary, draft flag, URL
  pr_diff              Unified diff for a PR (truncated to max_bytes)
  copilot_check_result Read a Copilot delegation result from .tmp/delegations/<run_id>.json

  ── System ───────────────────────────────────────────────────────────
  session_health       Full health check: Qdrant + Ollama + collections

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Claude Desktop setup (~/.claude/claude_desktop_config.json):

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

Works identically in Antigravity (GEMINI.md), Cursor (AGENTS.md), Copilot,
OpenCode, and OpenClaw — any client that supports MCP.

Environment variables (all optional — defaults shown):
  QDRANT_URL           http://localhost:6333
  EMBEDDING_PROVIDER   ollama   (or "openai" / "bedrock")
  OLLAMA_URL           http://localhost:11434
  OPENAI_API_KEY       (required if EMBEDDING_PROVIDER=openai)
  MEMORY_COLLECTION    agent_memory
  CACHE_COLLECTION     semantic_cache
  MEMORY_MODE          solo   (or "team" / "pro")
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import json
import os
import subprocess
import sys
from pathlib import Path

_EXECUTION_DIR = os.path.dirname(os.path.abspath(__file__))

SERVER_NAME = "agi-framework"
SERVER_VERSION = "1.0.0"

TOOLS = [
    # ── Memory ────────────────────────────────────────────────────────
    {
        "name": "memory_auto",
        "description": (
            "Auto-query the memory system: checks semantic cache first (100% token savings on hit), "
            "then retrieves relevant context chunks (80-95% token reduction). "
            "Run this before any complex task — it's the CLAUDE.md-mandated memory entry point."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "One-line summary of the task"},
                "project": {"type": "string", "description": "Filter by project name (optional)"},
                "top_k": {"type": "integer", "description": "Max context chunks to return (default: 5)", "default": 5}
            },
            "required": ["query"]
        }
    },
    {
        "name": "memory_store",
        "description": (
            "Store a decision, code pattern, error solution, conversation point, or technical note "
            "in long-term memory. Run this after completing any significant work."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "content": {"type": "string", "description": "What to store"},
                "type": {
                    "type": "string",
                    "enum": ["decision", "code", "error", "conversation", "technical"],
                    "description": "Memory category"
                },
                "project": {"type": "string", "description": "Project name (optional)"},
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
        "name": "memory_retrieve",
        "description": (
            "Retrieve relevant context chunks using semantic + BM25 hybrid search. "
            "Returns top-K most relevant memories (80-95% context reduction vs full history)."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Natural language search query"},
                "type": {"type": "string", "description": "Filter by memory type (optional)"},
                "project": {"type": "string", "description": "Filter by project (optional)"},
                "top_k": {"type": "integer", "description": "Number of results (default: 5)", "default": 5},
                "threshold": {"type": "number", "description": "Min score 0.0–1.0 (default: 0.7)", "default": 0.7}
            },
            "required": ["query"]
        }
    },
    {
        "name": "memory_cache_store",
        "description": "Cache a query-response pair so any agent gets it instantly on future similar queries.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The original question/task"},
                "response": {"type": "string", "description": "The complete response to cache"},
                "project": {"type": "string", "description": "Project name (optional)"}
            },
            "required": ["query", "response"]
        }
    },
    {
        "name": "memory_list",
        "description": "List stored memories. Filter by type and/or project.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "type": {"type": "string", "description": "Filter by memory type (optional)"},
                "project": {"type": "string", "description": "Filter by project (optional)"},
                "limit": {"type": "integer", "description": "Max results (default: 20)", "default": 20}
            }
        }
    },
    {
        "name": "memory_cache_clear",
        "description": "Remove old semantic cache entries.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "older_than_days": {
                    "type": "integer",
                    "description": "Delete entries older than N days (default: 7)",
                    "default": 7
                }
            }
        }
    },
    # ── Cross-Agent Coordination ───────────────────────────────────────
    {
        "name": "agent_store",
        "description": (
            "Publish your work to shared memory so other agents (Antigravity, Cursor, Copilot, etc.) "
            "can see what you've done. Call this after completing significant work."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "agent": {
                    "type": "string",
                    "description": "Your agent name",
                    "enum": ["claude", "antigravity", "gemini", "cursor", "copilot", "opencode", "openclaw"]
                },
                "action": {"type": "string", "description": "What you did or decided"},
                "project": {"type": "string", "description": "Project name (optional)"},
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Additional tags (optional)"
                }
            },
            "required": ["agent", "action"]
        }
    },
    {
        "name": "agent_sync",
        "description": (
            "Pull what other agents have done recently. "
            "Run at session start to see teammates' activity before starting work."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "agent": {
                    "type": "string",
                    "description": "Your agent name (your own entries are excluded from results)",
                    "enum": ["claude", "antigravity", "gemini", "cursor", "copilot", "opencode", "openclaw"]
                },
                "project": {"type": "string", "description": "Filter by project (optional)"},
                "hours": {"type": "integer", "description": "Look back N hours (default: 24)", "default": 24}
            },
            "required": ["agent"]
        }
    },
    {
        "name": "agent_status",
        "description": "Get team status overview — all agents, their recent activity, and active tasks.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project": {"type": "string", "description": "Filter by project (optional)"}
            }
        }
    },
    {
        "name": "agent_handoff",
        "description": (
            "Hand off a task to a specific agent. The target agent will see it when they run agent_pending."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "from_agent": {
                    "type": "string",
                    "description": "Your agent name",
                    "enum": ["claude", "antigravity", "gemini", "cursor", "copilot", "opencode", "openclaw"]
                },
                "to_agent": {
                    "type": "string",
                    "description": "Target agent name",
                    "enum": ["claude", "antigravity", "gemini", "cursor", "copilot", "opencode", "openclaw"]
                },
                "task": {"type": "string", "description": "Task description"},
                "context": {"type": "string", "description": "Additional context for the target agent (optional)"},
                "project": {"type": "string", "description": "Project name (optional)"}
            },
            "required": ["from_agent", "to_agent", "task"]
        }
    },
    {
        "name": "agent_broadcast",
        "description": "Broadcast an update to ALL agents — use for breaking changes or major decisions.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "agent": {
                    "type": "string",
                    "description": "Your agent name",
                    "enum": ["claude", "antigravity", "gemini", "cursor", "copilot", "opencode", "openclaw"]
                },
                "message": {"type": "string", "description": "The broadcast message"},
                "project": {"type": "string", "description": "Project name (optional)"},
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Tags e.g. ['breaking-change', 'release'] (optional)"
                }
            },
            "required": ["agent", "message"]
        }
    },
    {
        "name": "agent_pending",
        "description": "Check tasks that other agents have handed off to you. Run at session start.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "agent": {
                    "type": "string",
                    "description": "Your agent name",
                    "enum": ["claude", "antigravity", "gemini", "cursor", "copilot", "opencode", "openclaw"]
                },
                "project": {"type": "string", "description": "Filter by project (optional)"}
            },
            "required": ["agent"]
        }
    },
    # ── System ─────────────────────────────────────────────────────────
    {
        "name": "session_health",
        "description": (
            "Full health check: Qdrant availability, Ollama + embedding model status, "
            "and collection readiness. Run at session start. Returns memory_ready: true/false."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    },
    # ── GitHub / PR ────────────────────────────────────────────────────
    {
        "name": "pr_status",
        "description": (
            "Get the current status of a GitHub pull request: state (open/closed/merged), "
            "mergeable flag, draft flag, CI checks summary, and URL. "
            "Accepts a PR number (e.g. 42) or a full GitHub issue/PR URL."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "pr": {
                    "type": "string",
                    "description": "PR number (e.g. '42') or full GitHub PR/issue URL"
                },
                "repo": {
                    "type": "string",
                    "description": "owner/repo (e.g. 'octocat/hello-world'). Omit to use the repo detected by gh from the current directory."
                }
            },
            "required": ["pr"]
        }
    },
    {
        "name": "pr_diff",
        "description": (
            "Return the unified diff for a GitHub pull request, truncated to max_bytes. "
            "Useful for reviewing what changed without leaving the chat interface."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "pr": {
                    "type": "string",
                    "description": "PR number (e.g. '42') or full GitHub PR URL"
                },
                "repo": {
                    "type": "string",
                    "description": "owner/repo (e.g. 'octocat/hello-world'). Omit to use the repo detected by gh from the current directory."
                },
                "max_bytes": {
                    "type": "integer",
                    "description": "Maximum bytes of diff to return (default: 20000)",
                    "default": 20000
                }
            },
            "required": ["pr"]
        }
    },
    {
        "name": "copilot_check_result",
        "description": (
            "Read the result of a Copilot delegation run from .tmp/delegations/<run_id>.json. "
            "Written by the Copilot poller after a run completes. "
            "Returns the full JSON payload, or an error if the file does not exist yet."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "run_id": {
                    "type": "string",
                    "description": "The delegation run ID (filename stem, without .json extension)"
                }
            },
            "required": ["run_id"]
        }
    }
]


def run_script(script_name: str, args: list[str], timeout: int = 60) -> str:
    """Run an execution script and return its stdout (or stderr on failure)."""
    script_path = os.path.join(_EXECUTION_DIR, script_name)
    try:
        result = subprocess.run(
            [sys.executable, script_path] + args,
            capture_output=True,
            text=True,
            timeout=timeout,
            env={**os.environ}
        )
        output = result.stdout.strip()
        if not output and result.stderr.strip():
            output = result.stderr.strip()
        return output or json.dumps({"status": "ok", "exit_code": result.returncode})
    except subprocess.TimeoutExpired:
        return json.dumps({"error": "timeout", "script": script_name})
    except FileNotFoundError:
        return json.dumps({"error": f"Script not found: {script_path}"})
    except Exception as e:
        return json.dumps({"error": type(e).__name__, "message": str(e)})


def _run_gh(gh_args: list[str], timeout: int = 30) -> str:
    """Run a `gh` CLI command and return stdout as a string, or a JSON error."""
    try:
        result = subprocess.run(
            ["gh"] + gh_args,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if result.returncode != 0:
            return json.dumps({
                "error": "gh_cli_error",
                "exit_code": result.returncode,
                "stderr": result.stderr.strip()
            })
        return result.stdout.strip()
    except FileNotFoundError:
        return json.dumps({"error": "gh_not_found", "message": "gh CLI is not installed or not on PATH"})
    except subprocess.TimeoutExpired:
        return json.dumps({"error": "timeout", "command": "gh " + " ".join(gh_args)})
    except Exception as e:
        return json.dumps({"error": type(e).__name__, "message": str(e)})


def _parse_pr_ref(pr_arg: str) -> str:
    """Extract a bare PR number from either a plain number or a GitHub URL."""
    pr_arg = pr_arg.strip()
    # Accept full URLs like https://github.com/owner/repo/pull/42
    if pr_arg.startswith("http"):
        # The last path component is the number
        return pr_arg.rstrip("/").split("/")[-1]
    return pr_arg


def _gh_pr_status(args: dict) -> str:
    """Implement pr_status: return PR state, mergeable, draft, checks, url."""
    pr_ref = _parse_pr_ref(args["pr"])
    repo_flag = ["--repo", args["repo"]] if args.get("repo") else []

    fields = "number,title,state,isDraft,mergeable,url,headRefName,baseRefName,statusCheckRollup"
    raw = _run_gh(["pr", "view", pr_ref] + repo_flag + ["--json", fields])

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return json.dumps({"error": "invalid_json_from_gh", "raw": raw})

    if "error" in data:
        return raw  # propagate structured gh error

    checks_raw = data.get("statusCheckRollup") or []
    checks_summary: dict[str, int] = {}
    for check in checks_raw:
        state = (check.get("state") or check.get("conclusion") or "UNKNOWN").upper()
        checks_summary[state] = checks_summary.get(state, 0) + 1

    result = {
        "number": data.get("number"),
        "title": data.get("title"),
        "state": data.get("state"),
        "draft": data.get("isDraft"),
        "mergeable": data.get("mergeable"),
        "url": data.get("url"),
        "head": data.get("headRefName"),
        "base": data.get("baseRefName"),
        "checks": checks_summary,
        "checks_total": len(checks_raw)
    }
    return json.dumps(result)


def _gh_pr_diff(args: dict) -> str:
    """Implement pr_diff: return unified diff, truncated to max_bytes."""
    pr_ref = _parse_pr_ref(args["pr"])
    repo_flag = ["--repo", args["repo"]] if args.get("repo") else []
    max_bytes = int(args.get("max_bytes") or 20000)

    raw = _run_gh(["pr", "diff", pr_ref] + repo_flag)

    try:
        err = json.loads(raw)
        if "error" in err:
            return raw  # propagate structured error
    except (json.JSONDecodeError, TypeError):
        pass  # raw is the diff text — that's expected

    if len(raw) > max_bytes:
        truncated = raw[:max_bytes]
        return json.dumps({
            "diff": truncated,
            "truncated": True,
            "total_bytes": len(raw),
            "returned_bytes": max_bytes
        })
    return json.dumps({"diff": raw, "truncated": False, "total_bytes": len(raw)})


def _copilot_check_result(args: dict) -> str:
    """Implement copilot_check_result: read .tmp/delegations/<run_id>.json."""
    run_id = args.get("run_id", "").strip()
    if not run_id:
        return json.dumps({"error": "run_id is required"})

    # Security: reject run_ids that try to escape the delegations directory
    if "/" in run_id or "\\" in run_id or ".." in run_id:
        return json.dumps({"error": "invalid_run_id", "message": "run_id must not contain path separators"})

    project_root = os.path.dirname(_EXECUTION_DIR)
    delegation_path = os.path.join(project_root, ".tmp", "delegations", run_id + ".json")

    # Resolve and verify the path stays inside .tmp/delegations/
    resolved = Path(delegation_path).resolve()
    expected_dir = Path(project_root, ".tmp", "delegations").resolve()
    if not resolved.is_relative_to(expected_dir):
        return json.dumps({"error": "path_traversal_blocked"})

    if not resolved.exists():
        return json.dumps({
            "error": "not_found",
            "run_id": run_id,
            "message": "Delegation result file not found. The run may still be in progress."
        })

    try:
        with resolved.open("r", encoding="utf-8") as fh:
            payload = json.load(fh)
        return json.dumps(payload)
    except json.JSONDecodeError as exc:
        return json.dumps({"error": "invalid_json", "message": str(exc)})
    except OSError as exc:
        return json.dumps({"error": "read_error", "message": str(exc)})


def handle_tool_call(name: str, args: dict) -> dict:
    """Route MCP tool calls to the corresponding execution script."""

    # ── Memory ─────────────────────────────────────────────────────────
    if name == "memory_auto":
        cli = ["auto", "--query", args["query"]]
        if args.get("project"):
            cli += ["--project", args["project"]]
        if args.get("top_k"):
            cli += ["--top-k", str(args["top_k"])]
        return {"type": "text", "text": run_script("memory_manager.py", cli)}

    elif name == "memory_store":
        cli = ["store", "--content", args["content"], "--type", args["type"]]
        if args.get("project"):
            cli += ["--project", args["project"]]
        if args.get("tags"):
            cli += ["--tags"] + args["tags"]
        return {"type": "text", "text": run_script("memory_manager.py", cli)}

    elif name == "memory_retrieve":
        cli = ["retrieve", "--query", args["query"]]
        if args.get("type"):
            cli += ["--type", args["type"]]
        if args.get("project"):
            cli += ["--project", args["project"]]
        if args.get("top_k"):
            cli += ["--top-k", str(args["top_k"])]
        if args.get("threshold"):
            cli += ["--threshold", str(args["threshold"])]
        return {"type": "text", "text": run_script("memory_manager.py", cli)}

    elif name == "memory_cache_store":
        cli = ["cache-store", "--query", args["query"], "--response", args["response"]]
        if args.get("project"):
            cli += ["--project", args["project"]]
        return {"type": "text", "text": run_script("memory_manager.py", cli)}

    elif name == "memory_list":
        cli = ["list"]
        if args.get("type"):
            cli += ["--type", args["type"]]
        if args.get("project"):
            cli += ["--project", args["project"]]
        if args.get("limit"):
            cli += ["--limit", str(args["limit"])]
        return {"type": "text", "text": run_script("memory_manager.py", cli)}

    elif name == "memory_cache_clear":
        cli = ["cache-clear", "--older-than", str(args.get("older_than_days", 7))]
        return {"type": "text", "text": run_script("memory_manager.py", cli)}

    # ── Cross-Agent ─────────────────────────────────────────────────────
    elif name == "agent_store":
        cli = ["store", "--agent", args["agent"], "--action", args["action"]]
        if args.get("project"):
            cli += ["--project", args["project"]]
        if args.get("tags"):
            cli += ["--tags"] + args["tags"]
        return {"type": "text", "text": run_script("cross_agent_context.py", cli)}

    elif name == "agent_sync":
        cli = ["sync", "--agent", args["agent"]]
        if args.get("project"):
            cli += ["--project", args["project"]]
        if args.get("hours"):
            cli += ["--hours", str(args["hours"])]
        return {"type": "text", "text": run_script("cross_agent_context.py", cli)}

    elif name == "agent_status":
        cli = ["status"]
        if args.get("project"):
            cli += ["--project", args["project"]]
        return {"type": "text", "text": run_script("cross_agent_context.py", cli)}

    elif name == "agent_handoff":
        cli = [
            "handoff",
            "--from", args["from_agent"],
            "--to", args["to_agent"],
            "--task", args["task"]
        ]
        if args.get("context"):
            cli += ["--context", args["context"]]
        if args.get("project"):
            cli += ["--project", args["project"]]
        return {"type": "text", "text": run_script("cross_agent_context.py", cli)}

    elif name == "agent_broadcast":
        cli = ["broadcast", "--agent", args["agent"], "--message", args["message"]]
        if args.get("project"):
            cli += ["--project", args["project"]]
        if args.get("tags"):
            cli += ["--tags"] + args["tags"]
        return {"type": "text", "text": run_script("cross_agent_context.py", cli)}

    elif name == "agent_pending":
        cli = ["pending", "--agent", args["agent"]]
        if args.get("project"):
            cli += ["--project", args["project"]]
        return {"type": "text", "text": run_script("cross_agent_context.py", cli)}

    # ── System ──────────────────────────────────────────────────────────
    elif name == "session_health":
        return {"type": "text", "text": run_script("session_boot.py", ["--json"], timeout=30)}

    # ── GitHub / PR ──────────────────────────────────────────────────────
    elif name == "pr_status":
        return {"type": "text", "text": _gh_pr_status(args)}

    elif name == "pr_diff":
        return {"type": "text", "text": _gh_pr_diff(args)}

    elif name == "copilot_check_result":
        return {"type": "text", "text": _copilot_check_result(args)}

    else:
        return {"type": "text", "text": json.dumps({"error": f"Unknown tool: {name}"})}


def send(response: dict):
    sys.stdout.write(json.dumps(response) + "\n")
    sys.stdout.flush()


def main():
    """JSON-RPC 2.0 loop over stdio."""
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

        if req_id is None:  # notification — no response needed
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
            send({"jsonrpc": "2.0", "id": req_id, "result": {"tools": TOOLS}})

        elif method == "tools/call":
            params = request.get("params", {})
            content = handle_tool_call(params.get("name", ""), params.get("arguments", {}))
            send({"jsonrpc": "2.0", "id": req_id, "result": {"content": [content]}})

        else:
            send({
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32601, "message": f"Method not found: {method}"}
            })


if __name__ == "__main__":
    main()
