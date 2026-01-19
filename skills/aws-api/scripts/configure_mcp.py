#!/usr/bin/env python3
"""
Script: configure_mcp.py
Purpose: Configure MCP client with AWS API MCP Server

Usage:
    python configure_mcp.py [--client <client>] [--profile <profile>] [--region <region>] [--read-only]

Exit Codes: 0=success, 1=args, 2=config not found, 3=write error
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


MCP_CLIENTS = {
    "claude": {
        "name": "Claude Desktop",
        "paths": [
            Path.home() / "Library/Application Support/Claude/claude_desktop_config.json",
            Path.home() / "AppData/Roaming/Claude/claude_desktop_config.json",
            Path.home() / ".config/claude/claude_desktop_config.json",
        ]
    },
    "cursor": {
        "name": "Cursor IDE",
        "paths": [
            Path.home() / ".cursor/mcp.json",
            Path.cwd() / ".cursor/mcp.json",
        ]
    },
    "vscode": {
        "name": "VS Code (Continue)",
        "paths": [
            Path.home() / ".continue/config.json",
        ]
    }
}


def get_aws_region() -> str | None:
    region = os.environ.get("AWS_REGION") or os.environ.get("AWS_DEFAULT_REGION")
    if region:
        return region
    try:
        result = subprocess.run(["aws", "configure", "get", "region"], capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except FileNotFoundError:
        pass
    return None


def find_config_file(client: str) -> Path | None:
    if client not in MCP_CLIENTS:
        return None
    for path in MCP_CLIENTS[client]["paths"]:
        if path.exists():
            return path
    return MCP_CLIENTS[client]["paths"][0]


def detect_client() -> str | None:
    for client, info in MCP_CLIENTS.items():
        for path in info["paths"]:
            if path.exists():
                return client
    return None


def build_api_config(profile: str, region: str, read_only: bool, require_consent: bool) -> dict:
    env = {
        "AWS_PROFILE": profile,
        "AWS_REGION": region
    }
    if read_only:
        env["READ_OPERATIONS_ONLY"] = "true"
    if require_consent:
        env["REQUIRE_MUTATION_CONSENT"] = "true"
    
    return {
        "command": "uvx",
        "args": ["awslabs.aws-api-mcp-server@latest"],
        "env": env
    }


def update_config(config_path: Path, api_config: dict, client: str) -> dict:
    config = {}
    if config_path.exists():
        try:
            config = json.loads(config_path.read_text())
        except json.JSONDecodeError:
            config = {}
    
    if client == "vscode":
        if "mcpServers" not in config:
            config["mcpServers"] = []
        config["mcpServers"] = [s for s in config["mcpServers"] if s.get("name") != "aws-api"]
        config["mcpServers"].append({"name": "aws-api", **api_config})
    else:
        if "mcpServers" not in config:
            config["mcpServers"] = {}
        config["mcpServers"]["aws-api"] = api_config
    
    return config


def main():
    parser = argparse.ArgumentParser(description="Configure MCP client with AWS API server")
    parser.add_argument("-c", "--client", choices=["claude", "cursor", "vscode"])
    parser.add_argument("-p", "--profile", default="default", help="AWS profile")
    parser.add_argument("-r", "--region", help="AWS region")
    parser.add_argument("--read-only", action="store_true", help="Enable read-only mode")
    parser.add_argument("--require-consent", action="store_true", help="Require consent for mutations")
    parser.add_argument("--dry-run", action="store_true")
    
    args = parser.parse_args()
    
    client = args.client or detect_client()
    if not client:
        print("Error: Could not detect MCP client. Specify with --client", file=sys.stderr)
        sys.exit(2)
    
    region = args.region or get_aws_region()
    if not region:
        region = input("Enter AWS region (e.g., us-east-1, eu-west-1): ").strip()
        if not region:
            print("Error: Region is required", file=sys.stderr)
            sys.exit(1)
    
    config_path = find_config_file(client)
    if not config_path:
        print(f"Error: Could not find config path for {client}", file=sys.stderr)
        sys.exit(2)
    
    api_config = build_api_config(args.profile, region, args.read_only, args.require_consent)
    full_config = update_config(config_path, api_config, client)
    
    print(f"Client: {MCP_CLIENTS[client]['name']}")
    print(f"Config: {config_path}")
    print(f"Profile: {args.profile}")
    print(f"Region: {region}")
    print(f"Read-only: {args.read_only}")
    print(f"Require consent: {args.require_consent}")
    print()
    print("Configuration:")
    print(json.dumps({"mcpServers": {"aws-api": api_config}}, indent=2))
    
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
