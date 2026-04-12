#!/usr/bin/env python3
"""
Script: sandbox_manager.py
Purpose: Code Submission Sandbox Executor.
         Executes LLM-generated Python snippets in a secure, isolated manner.
         Provides access to the FastAPI host bridge for native framework tools.
         Supports Docker container pooling or isolated subprocess execution.

Usage:
    python3 execution/sandbox_manager.py execute --code "./script.py"

Exit Codes:
    0 - Execution success
    1 - Syntax error or invalid input
    2 - Security violation
    3 - Execution error (returns structured RFC 9457 JSON)
"""

import argparse
import json
import os
import sys
import subprocess
import tempfile
import textwrap
from pathlib import Path

# Load bridge token if available
BRIDGE_TOKEN = os.environ.get("SANDBOX_BRIDGE_TOKEN", "dev-secure-bridge-token-999")
FASTAPI_PORT = os.environ.get("FASTAPI_BRIDGE_PORT", "8000")

def format_rfc9457_error(title: str, detail: str, type_err: str, status: int = 400) -> str:
    """Formats standard RFC 9457 error payload to save tokens for LLM parsing."""
    return json.dumps({
        "type": f"https://agent-framework.internal/errors/{type_err}",
        "title": title,
        "detail": detail,
        "status": status,
        "instance": "sandbox_manager.py"
    })

def inject_bridge_client(raw_code: str) -> str:
    """
    Prepends a lightweight HTTP client to the LLM's code so it can trigger 
    framework tools via the FastAPI bridge instead of using raw raw keys.
    """
    bridge_client = textwrap.dedent(f"""\
        import urllib.request
        import json
        import os
        import sys

        class AGIBridge:
            def __init__(self):
                self.url = "http://127.0.0.1:{FASTAPI_PORT}/api/v1/execute"
                self.headers = {{
                    "Content-Type": "application/json",
                    "x-sandbox-token": "{BRIDGE_TOKEN}"
                }}

            def execute(self, tool_name, arguments):
                req = urllib.request.Request(
                    self.url,
                    data=json.dumps({{"tool_name": tool_name, "arguments": arguments}}).encode(),
                    headers=self.headers,
                    method="POST"
                )
                try:
                    with urllib.request.urlopen(req, timeout=15) as response:
                        return json.loads(response.read().decode())
                except urllib.error.HTTPError as e:
                    print(f"Bridge Execution Error: {{e.read().decode()}}", file=sys.stderr)
                    sys.exit(3)
                except Exception as e:
                    print(f"Bridge Connection Error: {{e}}", file=sys.stderr)
                    sys.exit(3)

        agent = AGIBridge()
        
    """)
    return bridge_client + raw_code


def execute_in_sandbox(code_path: str, mode: str = "subprocess"):
    """
    Executes the code securely. 
    mode="docker" will use a pre-warmed container if available.
    mode="subprocess" will use native python isolated tempfiles.
    """
    path = Path(code_path)
    if not path.exists():
        print(format_rfc9457_error("File not found", f"The code file {code_path} does not exist.", "file-not-found"), file=sys.stderr)
        sys.exit(1)

    raw_code = path.read_text(encoding="utf-8")
    
    # Very basic static analysis security check
    if "import os" in raw_code or "import subprocess" in raw_code:
        if mode == "subprocess":
             print(format_rfc9457_error(
                "Security Violation", 
                "os/subprocess imports are blocked in subprocess sandbox mode. Please use agent.execute() via the FastAPI bridge.", 
                "security-violation"
             ), file=sys.stderr)
             sys.exit(2)
             
    # Inject the AGI bridge into the sandbox context
    executable_code = inject_bridge_client(raw_code)

    if mode == "subprocess":
        # Execute using a temporary isolated file
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode="w", encoding="utf-8") as tf:
            tf.write(executable_code)
            temp_path = tf.name

        try:
            # Drop environment variables to isolate
            clean_env = {
                "PATH": os.environ.get("PATH", ""),
                "LANG": os.environ.get("LANG", "en_US.UTF-8")
            }
            res = subprocess.run(
                ["python3", temp_path],
                capture_output=True,
                text=True,
                timeout=30,
                env=clean_env
            )
            
            if res.returncode == 0:
                print(json.dumps({"status": "success", "stdout": res.stdout}))
                sys.exit(0)
            else:
                # RFC 9457 Output formatting
                print(format_rfc9457_error(
                    "Execution Failed",
                    f"The scripted code threw an error.\n{res.stderr}",
                    "execution-error"
                ), file=sys.stderr)
                sys.exit(3)
        finally:
            os.remove(temp_path)
            
    elif mode == "docker":
        # Roadmap: Integrate llm-sandbox Docker container pooling here
        print(format_rfc9457_error("Not Implemented", "Docker container pooling is roadmap feature. Use mode=subprocess.", "not-implemented"), file=sys.stderr)
        sys.exit(3)

def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    subparsers = parser.add_subparsers(dest="action", required=True)
    
    exec_p = subparsers.add_parser("execute", help="Execute generated python code")
    exec_p.add_argument("--code", required=True, help="Path to python file created by LLM")
    exec_p.add_argument("--mode", choices=["subprocess", "docker"], default="subprocess", help="Isolation backend")
    
    args = parser.parse_args()
    
    if args.action == "execute":
        execute_in_sandbox(args.code, args.mode)

if __name__ == "__main__":
    main()
