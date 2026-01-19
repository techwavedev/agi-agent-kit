#!/usr/bin/env python3
"""
Script: configure_mcp.py
Purpose: Configure MCP client (Claude Desktop, Cursor, etc.) with EKS MCP Server

Usage:
    python configure_mcp.py [--client <client>] [--region <region>] [--allow-write] [--allow-sensitive]

Arguments:
    --client, -c     MCP client: claude|cursor|vscode (default: auto-detect)
    --region, -r     AWS region (default: from AWS CLI config)
    --allow-write    Enable write operations (create/update/delete)
    --allow-sensitive Enable access to logs and secrets
    --profile        AWS profile name (default: default)
    --dry-run        Show config without writing

Exit Codes: 0=success, 1=args, 2=config not found, 3=write error
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


# MCP client config file locations
MCP_CLIENTS = {
    "claude": {
        "name": "Claude Desktop",
        "paths": [
            Path.home() / "Library/Application Support/Claude/claude_desktop_config.json",  # macOS
            Path.home() / "AppData/Roaming/Claude/claude_desktop_config.json",  # Windows
            Path.home() / ".config/claude/claude_desktop_config.json",  # Linux
        ]
    },
    "cursor": {
        "name": "Cursor IDE",
        "paths": [
            Path.home() / ".cursor/mcp.json",  # Global
            Path.cwd() / ".cursor/mcp.json",   # Project-level
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
    """Get default region from AWS CLI configuration."""
    # Try environment variable first
    region = os.environ.get("AWS_REGION") or os.environ.get("AWS_DEFAULT_REGION")
    if region:
        return region
    
    # Try AWS CLI config
    try:
        result = subprocess.run(
            ["aws", "configure", "get", "region"],
            capture_output=True, text=True
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except FileNotFoundError:
        pass
    
    return None


def get_aws_profile() -> str:
    """Get current AWS profile."""
    return os.environ.get("AWS_PROFILE", "default")


def find_config_file(client: str) -> Path | None:
    """Find existing config file for the specified client."""
    if client not in MCP_CLIENTS:
        return None
    
    for path in MCP_CLIENTS[client]["paths"]:
        if path.exists():
            return path
    
    # Return first path as default location
    return MCP_CLIENTS[client]["paths"][0]


def detect_client() -> str | None:
    """Auto-detect which MCP client is installed."""
    for client, info in MCP_CLIENTS.items():
        for path in info["paths"]:
            if path.exists():
                return client
    return None


def build_eks_config(region: str, profile: str, allow_write: bool, allow_sensitive: bool) -> dict:
    """Build the EKS MCP server configuration."""
    args = ["awslabs.eks-mcp-server@latest"]
    
    if allow_write:
        args.append("--allow-write")
    if allow_sensitive:
        args.append("--allow-sensitive-data-access")
    
    return {
        "command": "uvx",
        "args": args,
        "env": {
            "AWS_PROFILE": profile,
            "AWS_REGION": region
        }
    }


def update_config(config_path: Path, eks_config: dict, client: str) -> dict:
    """Update or create config file with EKS server config."""
    config = {}
    
    if config_path.exists():
        try:
            config = json.loads(config_path.read_text())
        except json.JSONDecodeError:
            print(f"Warning: Could not parse existing config at {config_path}", file=sys.stderr)
            config = {}
    
    # Different clients have different config structures
    if client == "vscode":
        # VS Code Continue uses array format
        if "mcpServers" not in config:
            config["mcpServers"] = []
        
        # Remove existing EKS config if present
        config["mcpServers"] = [s for s in config["mcpServers"] if s.get("name") != "eks"]
        
        # Add new config
        config["mcpServers"].append({
            "name": "eks",
            **eks_config
        })
    else:
        # Claude and Cursor use object format
        if "mcpServers" not in config:
            config["mcpServers"] = {}
        
        config["mcpServers"]["eks"] = eks_config
    
    return config


def main():
    parser = argparse.ArgumentParser(
        description="Configure MCP client with EKS MCP Server",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("-c", "--client", choices=["claude", "cursor", "vscode"],
                        help="MCP client to configure")
    parser.add_argument("-r", "--region", help="AWS region")
    parser.add_argument("--profile", default="default", help="AWS profile")
    parser.add_argument("--allow-write", action="store_true", 
                        help="Enable write operations")
    parser.add_argument("--allow-sensitive", action="store_true",
                        help="Enable access to logs and secrets")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show config without writing")
    
    args = parser.parse_args()
    
    # Detect or use specified client
    client = args.client or detect_client()
    if not client:
        print("Error: Could not detect MCP client. Specify with --client", file=sys.stderr)
        print(f"Supported clients: {', '.join(MCP_CLIENTS.keys())}", file=sys.stderr)
        sys.exit(2)
    
    # Get region
    region = args.region or get_aws_region()
    if not region:
        print("AWS region not found in CLI config.")
        region = input("Enter AWS region (e.g., us-east-1, eu-west-1): ").strip()
        if not region:
            print("Error: Region is required", file=sys.stderr)
            sys.exit(1)
    
    # Get profile
    profile = args.profile or get_aws_profile()
    
    # Find config file
    config_path = find_config_file(client)
    if not config_path:
        print(f"Error: Could not find config path for {client}", file=sys.stderr)
        sys.exit(2)
    
    # Build EKS config
    eks_config = build_eks_config(region, profile, args.allow_write, args.allow_sensitive)
    
    # Update config
    full_config = update_config(config_path, eks_config, client)
    
    # Output
    print(f"Client: {MCP_CLIENTS[client]['name']}")
    print(f"Config: {config_path}")
    print(f"Region: {region}")
    print(f"Profile: {profile}")
    print(f"Write ops: {'enabled' if args.allow_write else 'disabled'}")
    print(f"Sensitive access: {'enabled' if args.allow_sensitive else 'disabled'}")
    print()
    print("Configuration:")
    print(json.dumps({"mcpServers": {"eks": eks_config}}, indent=2))
    
    if args.dry_run:
        print("\n[Dry run - no changes made]")
        sys.exit(0)
    
    # Write config
    try:
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(json.dumps(full_config, indent=2))
        print(f"\n✅ Configuration written to {config_path}")
        print("\nRestart your MCP client to load the new configuration.")
    except Exception as e:
        print(f"\nError writing config: {e}", file=sys.stderr)
        sys.exit(3)
    
    sys.exit(0)


if __name__ == "__main__":
    main()
