#!/usr/bin/env python3
"""
MCP Server for __SKILL_NAME__ skill.

[TODO: Describe what memory/tools this server exposes]

Claude Desktop setup (~/.claude/claude_desktop_config.json):

  {
    "mcpServers": {
      "__SKILL_NAME__": {
        "command": "python3",
        "args": ["/absolute/path/to/skills/__SKILL_NAME__/mcp_server.py"],
        "env": {}
      }
    }
  }

Pattern A — import Python modules directly (preferred, faster):
  sys.path.insert(0, _SCRIPTS_DIR)
  from my_script import my_function

Pattern B — delegate to CLI scripts via subprocess (simpler):
  subprocess.run([sys.executable, script_path, "--arg", value], ...)
"""

import json
import os
import subprocess
import sys

_SKILL_DIR = os.path.dirname(os.path.abspath(__file__))
_SCRIPTS_DIR = os.path.join(_SKILL_DIR, "scripts")

# Add scripts/ to path if using Pattern A (direct imports)
sys.path.insert(0, _SCRIPTS_DIR)

SERVER_NAME = "__SKILL_NAME__"
SERVER_VERSION = "1.0.0"

# Load tool definitions from mcp_tools.json
_TOOLS_FILE = os.path.join(_SKILL_DIR, "mcp_tools.json")
try:
    with open(_TOOLS_FILE) as f:
        TOOLS = json.load(f).get("tools", [])
except (FileNotFoundError, json.JSONDecodeError):
    TOOLS = []


def handle_tool_call(name: str, arguments: dict) -> dict:
    """
    Route MCP tool calls to the appropriate implementation.

    Pattern A (direct import — recommended):
        from my_module import my_function
        result = my_function(**arguments)
        return {"type": "text", "text": json.dumps(result)}

    Pattern B (subprocess):
        result = subprocess.run(
            [sys.executable, os.path.join(_SCRIPTS_DIR, "my_script.py"),
             "--arg", arguments["arg"]],
            capture_output=True, text=True, timeout=60
        )
        return {"type": "text", "text": result.stdout or result.stderr}
    """
    # TODO: implement tool routing
    # Example:
    # if name == "my_tool":
    #     from my_module import do_thing
    #     result = do_thing(arguments["input"])
    #     return {"type": "text", "text": json.dumps(result)}

    return {"type": "text", "text": json.dumps({"error": f"Tool not implemented: {name}"})}


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
