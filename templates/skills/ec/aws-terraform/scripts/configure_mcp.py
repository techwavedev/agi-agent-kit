#!/usr/bin/env python3
"""
Script: configure_mcp.py
Purpose: Configure the Terraform MCP server for the current environment

Usage:
    python configure_mcp.py [--profile PROFILE] [--region REGION] [--config-path PATH]

Arguments:
    --profile   AWS profile to use (default: "default")
    --region    AWS region (default: "eu-west-1")
    --config-path  Path to MCP config file (auto-detected if not specified)

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
    # Check common MCP client config locations
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
    
    # Default to Gemini settings if none found
    return home / ".gemini" / "settings.json"


def create_terraform_mcp_config(profile: str, region: str) -> dict:
    """Create the Terraform MCP server configuration."""
    return {
        "awslabs.terraform-mcp-server": {
            "command": "uvx",
            "args": ["awslabs.terraform-mcp-server@latest"],
            "env": {
                "FASTMCP_LOG_LEVEL": "ERROR",
                "AWS_PROFILE": profile,
                "AWS_REGION": region
            },
            "disabled": False,
            "autoApprove": []
        }
    }


def main():
    parser = argparse.ArgumentParser(
        description="Configure the Terraform MCP server for AWS deployments"
    )
    parser.add_argument(
        "--profile",
        default="default",
        help="AWS profile to use (default: default)"
    )
    parser.add_argument(
        "--region",
        default="eu-west-1",
        help="AWS region (default: eu-west-1)"
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

    # Determine config path
    config_path = args.config_path or get_default_config_path()
    
    # Create the new server config
    new_server_config = create_terraform_mcp_config(args.profile, args.region)
    
    if args.dry_run:
        print(f"Config path: {config_path}")
        print("\nTerraform MCP Server configuration:")
        print(json.dumps(new_server_config, indent=2))
        sys.exit(0)
    
    # Load existing config or create new
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
    
    # Ensure mcpServers key exists
    if "mcpServers" not in config:
        config["mcpServers"] = {}
    
    # Add/update the Terraform server
    config["mcpServers"].update(new_server_config)
    
    # Write updated config
    try:
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        print(json.dumps({
            "status": "success",
            "config_path": str(config_path),
            "server": "awslabs.terraform-mcp-server",
            "profile": args.profile,
            "region": args.region
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
