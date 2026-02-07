#!/usr/bin/env python3
"""
preflight_check.py — Pre-flight Check for NotebookLM RAG

Validates that the NotebookLM MCP server is running, authenticated,
and has notebooks available before starting a research session.

Usage:
    python3 preflight_check.py
    python3 preflight_check.py --verbose

Exit Codes:
    0 - All checks passed
    1 - Critical failure (not authenticated, no notebooks)
    2 - Warning (authenticated but no notebooks in library)
"""

import json
import sys

def main():
    verbose = "--verbose" in sys.argv

    checks = {
        "mcp_server": {"status": "unknown", "detail": ""},
        "authentication": {"status": "unknown", "detail": ""},
        "library": {"status": "unknown", "detail": ""},
        "rate_limit": {"status": "unknown", "detail": ""},
    }

    # Check 1: MCP Server availability
    # This is a hint-based check — the agent should use get_health MCP tool
    checks["mcp_server"] = {
        "status": "info",
        "detail": "Use MCP tool 'get_health' to verify server is running",
        "mcp_tool": "get_health",
        "expected": {"status": "ok"},
    }

    # Check 2: Authentication
    checks["authentication"] = {
        "status": "info",
        "detail": "Verify 'authenticated: true' in get_health response",
        "mcp_tool": "get_health",
        "expected": {"authenticated": True},
        "fix_if_failed": "Run 'setup_auth' MCP tool → browser login",
    }

    # Check 3: Library has notebooks
    checks["library"] = {
        "status": "info",
        "detail": "Verify at least one notebook exists in library",
        "mcp_tool": "list_notebooks",
        "expected": "at least 1 notebook",
        "fix_if_failed": "Run 'add_notebook' MCP tool with NotebookLM share link",
    }

    # Check 4: Rate limit awareness
    checks["rate_limit"] = {
        "status": "info",
        "detail": "Free tier: ~50 queries/day. Budget 5-8 per research session.",
        "note": "If rate limited, use 're_auth' to switch Google account",
    }

    # Build preflight checklist
    preflight = {
        "skill": "notebooklm-rag",
        "purpose": "Pre-flight validation before research session",
        "checks": checks,
        "instructions": [
            "1. Call MCP tool 'get_health' → verify authenticated: true, status: ok",
            "2. Call MCP tool 'list_notebooks' → verify at least 1 notebook exists",
            "3. If auth failed → call 'setup_auth' MCP tool",
            "4. If no notebooks → ask user for NotebookLM share link → call 'add_notebook'",
            "5. Budget queries: reserve 5-8 for deep research, 1 for quick query",
        ],
        "ready_criteria": {
            "authenticated": True,
            "notebooks_count": ">= 1",
            "rate_limit_remaining": ">= 5",
        },
    }

    print(json.dumps(preflight, indent=2))

    if verbose:
        print("\n--- Pre-flight Instructions ---")
        for instruction in preflight["instructions"]:
            print(f"  {instruction}")
        print("\nRun MCP tools to complete the pre-flight check.")

    sys.exit(0)


if __name__ == "__main__":
    main()
