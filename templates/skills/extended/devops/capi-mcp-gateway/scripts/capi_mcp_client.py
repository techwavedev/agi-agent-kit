#!/usr/bin/env python3
"""
Script: capi_mcp_client.py
Purpose: CLI client for interacting with CAPI MCP Gateway

Usage:
    python capi_mcp_client.py --url http://localhost:8383/mcp init
    python capi_mcp_client.py --url http://localhost:8383/mcp --session <id> list-tools
    python capi_mcp_client.py --url http://localhost:8383/mcp --session <id> call --tool orders.get --args '{"orderId":"123"}'
    python capi_mcp_client.py --url http://localhost:8383/mcp ping
    python capi_mcp_client.py --admin-url http://localhost:8381 status

Exit Codes:
    0 - Success
    1 - Invalid arguments
    2 - Connection error
    3 - MCP protocol error
    4 - Unexpected error
"""

import argparse
import json
import sys

try:
    import requests
except ImportError:
    print(json.dumps({
        "status": "error",
        "message": "Missing dependency: pip install requests"
    }), file=sys.stderr)
    sys.exit(1)


def jsonrpc_call(url, method, params=None, req_id=1, session_id=None, token=None):
    """Send a JSON-RPC 2.0 request to the CAPI MCP endpoint."""
    body = {"jsonrpc": "2.0", "method": method, "id": req_id}
    if params:
        body["params"] = params

    headers = {"Content-Type": "application/json"}
    if session_id:
        headers["Mcp-Session-Id"] = session_id
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        resp = requests.post(url, json=body, headers=headers, timeout=30)
        resp.raise_for_status()
    except requests.ConnectionError:
        print(json.dumps({
            "status": "error",
            "message": f"Cannot connect to {url}"
        }), file=sys.stderr)
        sys.exit(2)
    except requests.HTTPError as e:
        print(json.dumps({
            "status": "error",
            "message": f"HTTP {e.response.status_code}: {e.response.text}"
        }), file=sys.stderr)
        sys.exit(2)

    session = resp.headers.get("Mcp-Session-Id")
    data = resp.json()

    if "error" in data:
        print(json.dumps({
            "status": "mcp_error",
            "code": data["error"]["code"],
            "message": data["error"]["message"]
        }), file=sys.stderr)
        sys.exit(3)

    return data["result"], session


def cmd_init(args):
    """Initialize MCP session."""
    result, session_id = jsonrpc_call(
        args.url, "initialize", token=args.token
    )
    output = {
        "status": "success",
        "session_id": session_id,
        "server_info": result.get("serverInfo", {}),
        "capabilities": result.get("capabilities", {}),
        "protocol_version": result.get("protocolVersion", "")
    }
    print(json.dumps(output, indent=2))


def cmd_list_tools(args):
    """List available MCP tools."""
    if not args.session:
        print(json.dumps({
            "status": "error",
            "message": "Session ID required. Run 'init' first."
        }), file=sys.stderr)
        sys.exit(1)

    result, _ = jsonrpc_call(
        args.url, "tools/list", req_id=2,
        session_id=args.session, token=args.token
    )
    tools = result.get("tools", [])
    output = {
        "status": "success",
        "tool_count": len(tools),
        "tools": [{
            "name": t["name"],
            "description": t.get("description", ""),
            "input_schema": t.get("inputSchema", {})
        } for t in tools]
    }
    print(json.dumps(output, indent=2))


def cmd_call(args):
    """Call an MCP tool."""
    if not args.session:
        print(json.dumps({
            "status": "error",
            "message": "Session ID required. Run 'init' first."
        }), file=sys.stderr)
        sys.exit(1)
    if not args.tool:
        print(json.dumps({
            "status": "error",
            "message": "--tool is required for 'call' command"
        }), file=sys.stderr)
        sys.exit(1)

    arguments = {}
    if args.args:
        try:
            arguments = json.loads(args.args)
        except json.JSONDecodeError:
            print(json.dumps({
                "status": "error",
                "message": f"Invalid JSON in --args: {args.args}"
            }), file=sys.stderr)
            sys.exit(1)

    result, _ = jsonrpc_call(
        args.url, "tools/call", req_id=3,
        params={"name": args.tool, "arguments": arguments},
        session_id=args.session, token=args.token
    )
    content = result.get("content", [])
    output = {
        "status": "success",
        "tool": args.tool,
        "result": content[0]["text"] if content else None
    }
    print(json.dumps(output, indent=2))


def cmd_ping(args):
    """Ping the MCP endpoint."""
    result, _ = jsonrpc_call(args.url, "ping", token=args.token)
    print(json.dumps({"status": "success", "ping": "ok"}, indent=2))


def cmd_status(args):
    """Check MCP gateway status via Admin API."""
    admin_url = args.admin_url or "http://localhost:8381"
    try:
        # MCP info
        mcp_resp = requests.get(f"{admin_url}/info/mcp", timeout=10)
        mcp_data = mcp_resp.json() if mcp_resp.ok else {"error": mcp_resp.status_code}

        # Health
        health_resp = requests.get(f"{admin_url}/info/health", timeout=10)
        health_data = health_resp.json() if health_resp.ok else {"error": health_resp.status_code}

        output = {
            "status": "success",
            "health": health_data,
            "mcp": mcp_data
        }
        print(json.dumps(output, indent=2))
    except requests.ConnectionError:
        print(json.dumps({
            "status": "error",
            "message": f"Cannot connect to admin API at {admin_url}"
        }), file=sys.stderr)
        sys.exit(2)


def cmd_tools_admin(args):
    """List tools via Admin API (no session required)."""
    admin_url = args.admin_url or "http://localhost:8381"
    try:
        resp = requests.get(f"{admin_url}/info/mcp/tools", timeout=10)
        if resp.ok:
            print(json.dumps({
                "status": "success",
                "tools": resp.json()
            }, indent=2))
        else:
            print(json.dumps({
                "status": "error",
                "message": f"HTTP {resp.status_code}: {resp.text}"
            }), file=sys.stderr)
            sys.exit(2)
    except requests.ConnectionError:
        print(json.dumps({
            "status": "error",
            "message": f"Cannot connect to admin API at {admin_url}"
        }), file=sys.stderr)
        sys.exit(2)


def main():
    parser = argparse.ArgumentParser(
        description="CLI client for CAPI MCP Gateway"
    )
    parser.add_argument("--url", default="http://localhost:8383/mcp",
                        help="MCP endpoint URL")
    parser.add_argument("--admin-url", default="http://localhost:8381",
                        help="Admin API URL")
    parser.add_argument("--session", help="MCP session ID")
    parser.add_argument("--token", help="Bearer token for OAuth2")
    parser.add_argument("--tool", help="Tool name (for 'call' command)")
    parser.add_argument("--args", help="Tool arguments as JSON string")

    parser.add_argument("command",
                        choices=["init", "list-tools", "call", "ping",
                                 "status", "tools-admin"],
                        help="Command to execute")

    args = parser.parse_args()

    commands = {
        "init": cmd_init,
        "list-tools": cmd_list_tools,
        "call": cmd_call,
        "ping": cmd_ping,
        "status": cmd_status,
        "tools-admin": cmd_tools_admin,
    }

    try:
        commands[args.command](args)
    except Exception as e:
        print(json.dumps({
            "status": "error",
            "type": type(e).__name__,
            "message": str(e)
        }), file=sys.stderr)
        sys.exit(4)


if __name__ == "__main__":
    main()
