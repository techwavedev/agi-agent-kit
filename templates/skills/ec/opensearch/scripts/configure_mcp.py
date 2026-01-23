#!/usr/bin/env python3
"""
Script: configure_mcp.py
Purpose: Configure the OpenSearch MCP server for the current environment

Usage:
    python configure_mcp.py [--url URL] [--username USER] [--password PASS] [--config-path PATH]

Arguments:
    --url         OpenSearch URL (default: https://localhost:9200)
    --username    OpenSearch username (default: admin)
    --password    OpenSearch password (from env OPENSEARCH_PASSWORD if not specified)
    --config-path Path to MCP config file (auto-detected if not specified)

Exit Codes:
    0 - Success
    1 - Invalid arguments
    2 - Config file not found
    3 - JSON parse error
    4 - Write error
"""

import argparse
import json
import os
import sys
from pathlib import Path


def get_default_config_path() -> Path:
    """Get the default MCP configuration path based on the environment."""
    home = Path.home()
    
    candidates = [
        home / ".gemini" / "settings.json",
        home / ".kiro" / "settings" / "mcp.json",
        home / ".cursor" / "mcp.json",
        home / ".vscode" / "mcp.json",
        home / ".config" / "mcp" / "settings.json",
    ]
    
    for path in candidates:
        if path.exists():
            return path
    
    return home / ".gemini" / "settings.json"


def create_opensearch_mcp_config(url: str, username: str, password: str) -> dict:
    """Create the OpenSearch MCP server configuration."""
    return {
        "opensearch-mcp": {
            "command": "npx",
            "args": ["-y", "opensearch-mcp-server"],
            "env": {
                "OPENSEARCH_URL": url,
                "OPENSEARCH_USERNAME": username,
                "OPENSEARCH_PASSWORD": password if password else "${OPENSEARCH_PASSWORD}",
                "OPENSEARCH_SSL_VERIFY": "false"
            },
            "disabled": False,
            "autoApprove": []
        }
    }


def main():
    parser = argparse.ArgumentParser(
        description="Configure the OpenSearch MCP server"
    )
    parser.add_argument(
        "--url",
        default="https://localhost:9200",
        help="OpenSearch URL (default: https://localhost:9200)"
    )
    parser.add_argument(
        "--username",
        default="admin",
        help="OpenSearch username (default: admin)"
    )
    parser.add_argument(
        "--password",
        default=os.environ.get("OPENSEARCH_PASSWORD", ""),
        help="OpenSearch password (default: from OPENSEARCH_PASSWORD env)"
    )
    parser.add_argument(
        "--config-path",
        type=Path,
        help="Path to MCP config file (auto-detected if not specified)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print configuration without writing"
    )
    args = parser.parse_args()

    config_path = args.config_path or get_default_config_path()
    new_server_config = create_opensearch_mcp_config(args.url, args.username, args.password)
    
    if args.dry_run:
        print(f"Config path: {config_path}")
        print("\nOpenSearch MCP Server configuration:")
        print(json.dumps(new_server_config, indent=2))
        sys.exit(0)
    
    if config_path.exists():
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
        except json.JSONDecodeError as e:
            print(json.dumps({
                "status": "error",
                "message": f"Failed to parse config: {e}"
            }), file=sys.stderr)
            sys.exit(3)
    else:
        config = {}
        config_path.parent.mkdir(parents=True, exist_ok=True)
    
    if "mcpServers" not in config:
        config["mcpServers"] = {}
    
    config["mcpServers"].update(new_server_config)
    
    try:
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        print(json.dumps({
            "status": "success",
            "config_path": str(config_path),
            "server": "opensearch-mcp",
            "url": args.url,
            "username": args.username
        }, indent=2))
        sys.exit(0)
        
    except IOError as e:
        print(json.dumps({
            "status": "error",
            "message": f"Failed to write config: {e}"
        }), file=sys.stderr)
        sys.exit(4)


if __name__ == "__main__":
    main()
