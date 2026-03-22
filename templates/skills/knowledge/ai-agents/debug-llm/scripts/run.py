#!/usr/bin/env python3
"""
Script: run.py
Purpose: Manage the local Langfuse Docker Compose stack for the debug-llm skill.

Usage:
    python scripts/run.py {start|stop|status}

Arguments:
    start   - Starts the Langfuse infrastructure via docker-compose
    stop    - Stops the Langfuse infrastructure
    status  - Checks the status of the containers
"""

import os
import sys
import subprocess
from pathlib import Path

def get_compose_file():
    # assumes this is executed from root or correctly mapped
    # script path: ai-agents/debug-llm/scripts/run.py
    script_dir = Path(__file__).resolve().parent
    return script_dir.parent / "docker-compose.yml"

def run_compose(command):
    compose_file = get_compose_file()
    if not compose_file.exists():
        print(f"Error: {compose_file} not found.", file=sys.stderr)
        sys.exit(1)

    cmd = ["docker", "compose", "-f", str(compose_file)] + command
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Command failed with exit code {e.returncode}", file=sys.stderr)
        sys.exit(e.returncode)
    except FileNotFoundError:
        print("Error: 'docker' or 'docker-compose' command not found. Please ensure Docker is installed.", file=sys.stderr)
        sys.exit(1)

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    action = sys.argv[1].lower()

    if action == "start":
        print("Starting Langfuse locally...")
        run_compose(["up", "-d"])
        print("\nLangfuse is starting. It may take a minute for the DB to initialize.")
        print("Once healthy, visit: http://localhost:3000")
        print("You will need to create a new admin account on the first run.")

    elif action == "stop":
        print("Stopping Langfuse...")
        run_compose(["down"])

    elif action == "status":
        print("Checking Langfuse status...")
        run_compose(["ps"])

    else:
        print(f"Unknown action: {action}", file=sys.stderr)
        print(__doc__)
        sys.exit(1)

if __name__ == "__main__":
    main()
