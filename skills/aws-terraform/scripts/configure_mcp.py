#!/usr/bin/env python3
"""Configure MCP client with AWS Terraform server."""

import argparse, json
from pathlib import Path

CLIENTS = {
    "claude": Path.home() / "Library/Application Support/Claude/claude_desktop_config.json",
    "cursor": Path.home() / ".cursor/mcp.json",
}

def main():
    p = argparse.ArgumentParser()
    p.add_argument("-c", "--client", choices=["claude", "cursor"], default="cursor")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()
    
    cfg_path = CLIENTS[args.client]
    config = {"command": "uvx", "args": ["awslabs.terraform-mcp-server@latest"],
              "env": {"FASTMCP_LOG_LEVEL": "ERROR"}}
    
    existing = json.loads(cfg_path.read_text()) if cfg_path.exists() else {}
    existing.setdefault("mcpServers", {})["terraform"] = config
    
    print(json.dumps({"mcpServers": {"terraform": config}}, indent=2))
    if not args.dry_run:
        cfg_path.parent.mkdir(parents=True, exist_ok=True)
        cfg_path.write_text(json.dumps(existing, indent=2))
        print(f"\n✅ Written to {cfg_path}")

if __name__ == "__main__": main()
