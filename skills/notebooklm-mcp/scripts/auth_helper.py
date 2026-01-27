#!/usr/bin/env python3
"""
Authentication helper for NotebookLM MCP.
Simulates calling `notebooklm-mcp-auth --file` but supports multiple input formats (Netscape, etc.)
and performs the format conversion automatically before saving.
"""

import json
import os
import sys
import re
from pathlib import Path

# Common cookie keys for Google
REQUIRED_COOKIES = ["SID", "HSID", "SSID", "APISID", "SAPISID"]

def parse_netscape_cookies(content: str) -> dict[str, str]:
    """Parse Netscape format (wget/curl/browser exports) cookies."""
    cookies = {}
    for line in content.splitlines():
        if line.startswith("#") or not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) >= 7:
            # domain, flag, path, secure, expiration, name, value
            key = parts[5].strip()
            value = parts[6].strip()
            cookies[key] = value
    return cookies

def parse_json_cookies(content: str) -> dict[str, str]:
    """Parse JSON format (EditThisCookie export)."""
    try:
        data = json.loads(content)
        if isinstance(data, list):
            cookies = {}
            for cookie in data:
                if isinstance(cookie, dict):
                    name = cookie.get("name")
                    value = cookie.get("value")
                    if name and value:
                        cookies[name] = value
            return cookies
        elif isinstance(data, dict):
            # Maybe simple key-value json
            return data
    except Exception:
        pass
    return {}

def parse_header_cookies(content: str) -> dict[str, str]:
    """Parse raw HTTP header format (key=value; key=value)."""
    cookies = {}
    # Remove 'Cookie:' prefix if present
    cleaned = re.sub(r'^(?i)cookie:\s*', '', content)
    for pair in cleaned.split(';'):
        if '=' in pair:
            key, value = pair.split('=', 1)
            cookies[key.strip()] = value.strip()
    return cookies

def detect_and_parse(content: str) -> dict[str, str]:
    """Detect format and return dictionary of cookies."""
    content = content.strip()
    
    # 1. Try JSON
    if content.startswith("[") or content.startswith("{"):
        cookies = parse_json_cookies(content)
        if cookies:
            return cookies

    # 2. Try Netscape (tab separated, typically starts with dot or domain)
    if "\t" in content and ("FALSE" in content or "TRUE" in content):
        cookies = parse_netscape_cookies(content)
        if cookies:
            return cookies

    # 3. Fallback to Header format
    return parse_header_cookies(content)

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 auth_helper.py <cookies_file_path>")
        sys.exit(1)

    file_path = Path(sys.argv[1]).expanduser()
    if not file_path.exists():
        print(f"Error: File not found: {file_path}")
        sys.exit(1)

    try:
        content = file_path.read_text("utf-8")
    except Exception as e:
        print(f"Error reading file: {e}")
        sys.exit(1)

    print(f"Parsing cookies from {file_path}...")
    cookies = detect_and_parse(content)

    if not cookies:
        print("Error: Could not parse any cookies from the file.")
        sys.exit(1)

    # Validate
    missing = [key for key in REQUIRED_COOKIES if key not in cookies]
    if missing:
        print(f"Warning: Missing standard Google auth cookies: {missing}")
        print("This might be okay if tokens are fresh, but often indicates incomplete export.")

    # Reconstruct valid header string
    header_string = "; ".join([f"{k}={v}" for k, v in cookies.items()])
    
    # Write to a temporary file that notebooklm-mcp-auth is guaranteed to accept
    temp_file = file_path.parent / "cookies_cleaned.txt"
    temp_file.write_text(header_string)

    print(f"Converted {len(cookies)} cookies to standard format.")
    print(f"Saving cleaned format to: {temp_file}")
    
    # Call the actual auth tool with the cleaned file
    print("Running notebooklm-mcp-auth...")
    
    # We use os.system for simplicity to pipe output directly
    ret = os.system(f"notebooklm-mcp-auth --file '{temp_file}'")
    
    # Cleanup (optional, maybe keep it in case it fails)
    # temp_file.unlink()
    
    if ret == 0:
        print("\n✅ Authentication setup complete!")
    else:
        print("\n❌ Authentication tool failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
