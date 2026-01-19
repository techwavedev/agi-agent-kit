#!/usr/bin/env python3
"""
Script: configure_mcp.py
Purpose: Configure MCP client with AWS IaC servers (CDK, CloudFormation, Terraform)

Usage:
    python configure_mcp.py [--client <client>] [--cdk] [--cfn] [--terraform] [--all]

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
        "paths": [Path.home() / ".cursor/mcp.json", Path.cwd() / ".cursor/mcp.json"]
    },
    "vscode": {
        "name": "VS Code (Continue)",
        "paths": [Path.home() / ".continue/config.json"]
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
    return "eu-west-1"


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


def build_configs(cdk: bool, cfn: bool, terraform: bool, region: str, profile: str) -> dict:
    configs = {}
    
    if cdk:
        configs["cdk"] = {
            "command": "uvx",
            "args": ["awslabs.cdk-mcp-server@latest"],
            "env": {"FASTMCP_LOG_LEVEL": "ERROR"}
        }
    
    if cfn:
        configs["cloudformation"] = {
            "command": "uvx",
            "args": ["awslabs.cfn-mcp-server@latest"],
            "env": {"AWS_PROFILE": profile, "AWS_REGION": region}
        }
    
    if terraform:
        configs["terraform"] = {
            "command": "uvx",
            "args": ["awslabs.terraform-mcp-server@latest"],
            "env": {"FASTMCP_LOG_LEVEL": "ERROR"}
        }
    
    return configs


def update_config(config_path: Path, new_configs: dict, client: str) -> dict:
    config = {}
    if config_path.exists():
        try:
            config = json.loads(config_path.read_text())
        except json.JSONDecodeError:
            config = {}
    
    if "mcpServers" not in config:
        config["mcpServers"] = {} if client != "vscode" else []
    
    if client == "vscode":
        existing_names = {s.get("name") for s in config["mcpServers"]}
        for name, cfg in new_configs.items():
            if name not in existing_names:
                config["mcpServers"].append({"name": name, **cfg})
    else:
        config["mcpServers"].update(new_configs)
    
    return config


def main():
    parser = argparse.ArgumentParser(description="Configure MCP client with AWS IaC servers")
    parser.add_argument("-c", "--client", choices=["claude", "cursor", "vscode"])
    parser.add_argument("-p", "--profile", default="default")
    parser.add_argument("-r", "--region")
    parser.add_argument("--cdk", action="store_true", help="Add CDK server")
    parser.add_argument("--cfn", action="store_true", help="Add CloudFormation server")
    parser.add_argument("--terraform", action="store_true", help="Add Terraform server")
    parser.add_argument("--all", action="store_true", help="Add all IaC servers")
    parser.add_argument("--dry-run", action="store_true")
    
    args = parser.parse_args()
    
    client = args.client or detect_client()
    if not client:
        print("Error: Could not detect MCP client", file=sys.stderr)
        sys.exit(2)
    
    region = args.region or get_aws_region()
    
    # Default to all if nothing specified
    cdk = args.cdk or args.all
    cfn = args.cfn or args.all
    terraform = args.terraform or args.all
    
    if not (cdk or cfn or terraform):
        cdk = cfn = terraform = True  # Default all
    
    config_path = find_config_file(client)
    if not config_path:
        print(f"Error: Could not find config path for {client}", file=sys.stderr)
        sys.exit(2)
    
    new_configs = build_configs(cdk, cfn, terraform, region, args.profile)
    full_config = update_config(config_path, new_configs, client)
    
    print(f"Client: {MCP_CLIENTS[client]['name']}")
    print(f"Config: {config_path}")
    print(f"Servers: {', '.join(new_configs.keys())}")
    print()
    print("Configuration:")
    print(json.dumps({"mcpServers": new_configs}, indent=2))
    
    if args.dry_run:
        print("\n[Dry run - no changes made]")
        sys.exit(0)
    
    try:
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(json.dumps(full_config, indent=2))
        print(f"\n✅ Configuration written to {config_path}")
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        sys.exit(3)


if __name__ == "__main__":
    main()
