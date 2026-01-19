#!/usr/bin/env python3
"""Configure MCP client with AWS CCAPI server."""

import argparse, json, os, subprocess, sys
from pathlib import Path

CLIENTS = {
    "claude": [Path.home() / "Library/Application Support/Claude/claude_desktop_config.json"],
    "cursor": [Path.home() / ".cursor/mcp.json"],
}

def get_region():
    r = os.environ.get("AWS_REGION")
    if r: return r
    try:
        result = subprocess.run(["aws", "configure", "get", "region"], capture_output=True, text=True)
        if result.returncode == 0: return result.stdout.strip()
    except: pass
    return "eu-west-1"

def main():
    p = argparse.ArgumentParser()
    p.add_argument("-c", "--client", choices=["claude", "cursor"], default="cursor")
    p.add_argument("-p", "--profile", default="default")
    p.add_argument("-r", "--region")
    p.add_argument("--no-security", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()
    
    region = args.region or get_region()
    cfg_path = CLIENTS[args.client][0]
    
    config = {"command": "uvx", "args": ["awslabs.ccapi-mcp-server@latest"],
              "env": {"AWS_PROFILE": args.profile, "AWS_REGION": region,
                      "SECURITY_SCANNING": "disabled" if args.no_security else "enabled"}}
    
    existing = json.loads(cfg_path.read_text()) if cfg_path.exists() else {}
    existing.setdefault("mcpServers", {})["ccapi"] = config
    
    print(json.dumps({"mcpServers": {"ccapi": config}}, indent=2))
    if not args.dry_run:
        cfg_path.parent.mkdir(parents=True, exist_ok=True)
        cfg_path.write_text(json.dumps(existing, indent=2))
        print(f"\n✅ Written to {cfg_path}")

if __name__ == "__main__": main()
