#!/usr/bin/env python3
"""
Script: configure_mcp.py
Purpose: Configure MCP client with AWS Knowledge MCP Server

Usage:
    python configure_mcp.py [--client <client>] [--use-proxy]

Arguments:
    --client, -c    MCP client: claude|cursor|vscode (default: auto-detect)
    --use-proxy     Use fastmcp proxy for stdio transport (for Claude Desktop)
    --dry-run       Show config without writing

Exit Codes: 0=success, 1=args, 2=config not found, 3=write error
"""

import argparse
import json
import sys
from pathlib import Path


# MCP client config file locations
MCP_CLIENTS = {
    "claude": {
        "name": "Claude Desktop",
        "paths": [
            Path.home() / "Library/Application Support/Claude/claude_desktop_config.json",
            Path.home() / "AppData/Roaming/Claude/claude_desktop_config.json",
            Path.home() / ".config/claude/claude_desktop_config.json",
        ],
        "supports_http": False  # Claude Desktop needs stdio proxy
    },
    "cursor": {
        "name": "Cursor IDE",
        "paths": [
            Path.home() / ".cursor/mcp.json",
            Path.cwd() / ".cursor/mcp.json",
        ],
        "supports_http": True
    },
    "vscode": {
        "name": "VS Code (Continue)",
        "paths": [
            Path.home() / ".continue/config.json",
        ],
        "supports_http": True
    }
}

KNOWLEDGE_URL = "https://knowledge-mcp.global.api.aws"


def find_config_file(client: str) -> Path | None:
    """Find existing config file for the specified client."""
    if client not in MCP_CLIENTS:
        return None
    
    for path in MCP_CLIENTS[client]["paths"]:
        if path.exists():
            return path
    
    return MCP_CLIENTS[client]["paths"][0]


def detect_client() -> str | None:
    """Auto-detect which MCP client is installed."""
    for client, info in MCP_CLIENTS.items():
        for path in info["paths"]:
            if path.exists():
                return client
    return None


def build_knowledge_config(use_proxy: bool) -> dict:
    """Build the AWS Knowledge MCP server configuration."""
    if use_proxy:
        return {
            "command": "uvx",
            "args": ["fastmcp", "run", KNOWLEDGE_URL]
        }
    else:
        return {
            "url": KNOWLEDGE_URL,
            "type": "http"
        }


def update_config(config_path: Path, knowledge_config: dict, client: str) -> dict:
    """Update or create config file with Knowledge server config."""
    config = {}
    
    if config_path.exists():
        try:
            config = json.loads(config_path.read_text())
        except json.JSONDecodeError:
            config = {}
    
    if client == "vscode":
        if "mcpServers" not in config:
            config["mcpServers"] = []
        config["mcpServers"] = [s for s in config["mcpServers"] if s.get("name") != "aws-knowledge"]
        config["mcpServers"].append({"name": "aws-knowledge", **knowledge_config})
    else:
        if "mcpServers" not in config:
            config["mcpServers"] = {}
        config["mcpServers"]["aws-knowledge"] = knowledge_config
    
    return config


def main():
    parser = argparse.ArgumentParser(description="Configure MCP client with AWS Knowledge server")
    parser.add_argument("-c", "--client", choices=["claude", "cursor", "vscode"])
    parser.add_argument("--use-proxy", action="store_true", 
                        help="Use fastmcp proxy (required for Claude Desktop)")
    parser.add_argument("--dry-run", action="store_true")
    
    args = parser.parse_args()
    
    client = args.client or detect_client()
    if not client:
        print("Error: Could not detect MCP client. Specify with --client", file=sys.stderr)
        sys.exit(2)
    
    # Determine if we need proxy
    use_proxy = args.use_proxy or not MCP_CLIENTS[client]["supports_http"]
    
    config_path = find_config_file(client)
    if not config_path:
        print(f"Error: Could not find config path for {client}", file=sys.stderr)
        sys.exit(2)
    
    knowledge_config = build_knowledge_config(use_proxy)
    full_config = update_config(config_path, knowledge_config, client)
    
    print(f"Client: {MCP_CLIENTS[client]['name']}")
    print(f"Config: {config_path}")
    print(f"Transport: {'stdio (fastmcp proxy)' if use_proxy else 'HTTP'}")
    print()
    print("Configuration:")
    print(json.dumps({"mcpServers": {"aws-knowledge": knowledge_config}}, indent=2))
    
    if args.dry_run:
        print("\n[Dry run - no changes made]")
        sys.exit(0)
    
    try:
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(json.dumps(full_config, indent=2))
        print(f"\n✅ Configuration written to {config_path}")
        print("\nRestart your MCP client to load the new configuration.")
    except Exception as e:
        print(f"\nError writing config: {e}", file=sys.stderr)
        sys.exit(3)


if __name__ == "__main__":
    main()
