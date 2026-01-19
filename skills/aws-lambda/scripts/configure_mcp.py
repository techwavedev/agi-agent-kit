#!/usr/bin/env python3
"""Configure MCP client with AWS Lambda Tool server."""

import argparse, json, os, subprocess
from pathlib import Path

CLIENTS = {
    "claude": Path.home() / "Library/Application Support/Claude/claude_desktop_config.json",
    "cursor": Path.home() / ".cursor/mcp.json",
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
    p.add_argument("--prefix", help="Function name prefix")
    p.add_argument("--functions", help="Comma-separated function names")
    p.add_argument("--tag-key", help="Filter tag key")
    p.add_argument("--tag-value", help="Filter tag value")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()
    
    region = args.region or get_region()
    cfg_path = CLIENTS[args.client]
    
    env = {"AWS_PROFILE": args.profile, "AWS_REGION": region}
    if args.prefix: env["FUNCTION_PREFIX"] = args.prefix
    if args.functions: env["FUNCTION_LIST"] = args.functions
    if args.tag_key: env["FUNCTION_TAG_KEY"] = args.tag_key
    if args.tag_value: env["FUNCTION_TAG_VALUE"] = args.tag_value
    
    config = {"command": "uvx", "args": ["awslabs.lambda-tool-mcp-server@latest"], "env": env}
    
    existing = json.loads(cfg_path.read_text()) if cfg_path.exists() else {}
    existing.setdefault("mcpServers", {})["lambda"] = config
    
    print(json.dumps({"mcpServers": {"lambda": config}}, indent=2))
    if not args.dry_run:
        cfg_path.parent.mkdir(parents=True, exist_ok=True)
        cfg_path.write_text(json.dumps(existing, indent=2))
        print(f"\n✅ Written to {cfg_path}")

if __name__ == "__main__": main()
