#!/usr/bin/env python3
import sys
import json
import subprocess
import os
import time

def check_uv():
    try:
        subprocess.run(["uv", "--version"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def rpc_request(process, method, params=None, msg_id=None):
    req = {
        "jsonrpc": "2.0",
        "method": method,
    }
    if params is not None:
        req["params"] = params
    if msg_id is not None:
        req["id"] = msg_id
    
    line = json.dumps(req) + "\n"
    process.stdin.write(line.encode('utf-8'))
    process.stdin.flush()

def read_response(process):
    while True:
        line = process.stdout.readline()
        if not line:
            return None
        line_str = line.decode('utf-8').strip()
        if not line_str:
            continue
        try:
            return json.loads(line_str)
        except json.JSONDecodeError:
            # Ignore non-json lines (maybe uv output if somehow on stdout)
            pass

MESSAGE_ID = 1

def call_tool(process, name, arguments={}):
    global MESSAGE_ID
    msg_id = MESSAGE_ID
    MESSAGE_ID += 1
    
    rpc_request(process, "tools/call", {"name": name, "arguments": arguments}, msg_id)
    
    while True:
        resp = read_response(process)
        if not resp:
            break
        if resp.get("id") == msg_id:
            return resp

def main():
    if not check_uv():
        print("Error: 'uv' tool not found in PATH.")
        sys.exit(1)
        
    cmd = ["uv", "tool", "run", "--from", "notebooklm-mcp-server", "notebooklm-mcp"]
    
    print(f"Starting server: {' '.join(cmd)}")
    process = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=sys.stderr,
    )

    global MESSAGE_ID
    msg_id = MESSAGE_ID
    MESSAGE_ID += 1
    
    # Initialize
    rpc_request(process, "initialize", {
        "protocolVersion": "2024-11-05",
        "capabilities": {},
        "clientInfo": {"name": "antigravity-cli", "version": "1.0"}
    }, msg_id)
    
    while True:
        resp = read_response(process)
        if resp and resp.get("id") == msg_id:
            break
            
    rpc_request(process, "notifications/initialized")

    # List tools to verify name
    msg_id = MESSAGE_ID
    MESSAGE_ID += 1
    rpc_request(process, "tools/list", {}, msg_id)
    
    tool_name = "list_notebooks"
    
    while True:
        resp = read_response(process)
        if resp and resp.get("id") == msg_id:
            tools = resp.get("result", {}).get("tools", [])
            print(f"Available tools: {[t['name'] for t in tools]}")
            # Use exact match if available
            names = [t['name'] for t in tools]
            if "list_notebooks" in names:
                tool_name = "list_notebooks"
            elif "listNotebooks" in names:
                tool_name = "listNotebooks"
            elif "notebook_list" in names:
                tool_name = "notebook_list"
            break
            
    # Call list_notebooks
    print(f"Calling {tool_name}...")
    result = call_tool(process, tool_name)
    
    if result.get("error"):
        print("Error calling tool:")
        print(json.dumps(result["error"], indent=2))
        
        # If internal error, it might be auth
        if "Authentication" in str(result["error"]) or "cookie" in str(result["error"]):
            print("\nSUGGESTION: Please verify authentication.\nRun: python3 skills/notebooklm-mcp/scripts/auth_helper.py <cookies_file>")
    else:
        content = result.get("result", {}).get("content", [])
        if not content:
            print("No notebooks found.")
        for item in content:
            if item.get("type") == "text":
                print(item["text"])
            else:
                print(item)

    process.terminate()

if __name__ == "__main__":
    main()
