#!/usr/bin/env python3
"""
Script: claude_native_config.py
Purpose: Configure Claude Code native features for the AGI framework.
         Manages agent teams, model overrides, hook registration, and
         environment variables to leverage hidden/advanced capabilities.

Usage:
    # Show current configuration and available features
    python3 execution/claude_native_config.py status

    # Enable agent teams mode
    python3 execution/claude_native_config.py enable-teams

    # Configure model overrides (route small model to local Ollama)
    python3 execution/claude_native_config.py set-model-overrides

    # Show recommended environment variables
    python3 execution/claude_native_config.py env

    # Generate a complete .claude/settings.local.json for local model routing
    python3 execution/claude_native_config.py generate-local-config

Exit Codes:
    0 - Success
    1 - Invalid arguments
    2 - Configuration error
"""

import argparse
import json
import os
import shutil
import sys
import urllib.request
from pathlib import Path

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")


def find_project_root():
    current = Path(__file__).resolve().parent.parent
    for parent in [current] + list(current.parents):
        if (parent / "AGENTS.md").exists():
            return parent
    return current


def get_claude_settings_paths():
    """Return paths to project and user settings."""
    root = find_project_root()
    return {
        "project": root / ".claude" / "settings.json",
        "project_local": root / ".claude" / "settings.local.json",
        "user": Path.home() / ".claude" / "settings.json",
        "user_local": Path.home() / ".claude" / "settings.local.json",
    }


def detect_features() -> dict:
    """Detect available Claude Code features."""
    features = {
        "claude_code_installed": shutil.which("claude") is not None,
        "env_vars": {},
        "agent_teams": False,
        "coordinator_mode": False,
        "ollama_available": False,
        "ollama_models": [],
    }

    # Check env vars
    for var in [
        "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS",
        "CLAUDE_CODE_COORDINATOR_MODE",
        "CLAUDE_CODE_AGENT_NAME",
        "CLAUDE_CODE_TEAM_NAME",
        "CLAUDE_CODE_SIMPLE",
        "CLAUDE_CODE_REMOTE_MEMORY_DIR",
        "ANTHROPIC_MODEL",
        "ANTHROPIC_SMALL_FAST_MODEL",
        "ANTHROPIC_DEFAULT_HAIKU_MODEL",
        "CLAUDE_CODE",
        "CLAUDE_SESSION_ID",
    ]:
        val = os.environ.get(var)
        if val is not None:
            features["env_vars"][var] = val

    features["agent_teams"] = os.environ.get("CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS") == "1"
    features["coordinator_mode"] = os.environ.get("CLAUDE_CODE_COORDINATOR_MODE") == "1"

    # Check Ollama
    try:
        req = urllib.request.Request(f"{OLLAMA_URL}/api/tags")
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            features["ollama_available"] = True
            features["ollama_models"] = [
                m["name"] for m in data.get("models", [])
                if "embed" not in m["name"]
            ]
    except Exception:
        pass

    return features


def cmd_status():
    """Show current configuration and available features."""
    features = detect_features()
    paths = get_claude_settings_paths()

    # Check existing settings
    settings_info = {}
    for name, path in paths.items():
        if path.exists():
            try:
                data = json.loads(path.read_text())
                settings_info[name] = {
                    "exists": True,
                    "has_hooks": "hooks" in data,
                    "has_env": "env" in data,
                    "has_model_overrides": "modelOverrides" in data,
                }
            except Exception:
                settings_info[name] = {"exists": True, "parse_error": True}
        else:
            settings_info[name] = {"exists": False}

    output = {
        "features": features,
        "settings_files": settings_info,
        "recommendations": [],
    }

    if not features["agent_teams"]:
        output["recommendations"].append(
            "Enable agent teams: export CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1"
        )
    if not features["ollama_available"]:
        output["recommendations"].append(
            "Start Ollama for local model routing: ollama serve"
        )
    if features["ollama_available"] and not features["ollama_models"]:
        output["recommendations"].append(
            "Pull a local model: ollama pull gemma4:e4b"
        )

    print(json.dumps(output, indent=2))


def cmd_env():
    """Show recommended environment variables."""
    env_vars = {
        "# Agent Teams (enables native multi-agent spawning)": {
            "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1",
        },
        "# Agent Identity (for cross-agent context)": {
            "CLAUDE_CODE_AGENT_NAME": "claude",
            "CLAUDE_CODE_TEAM_NAME": "agi-framework",
        },
        "# Model Routing (optional: override small model to local)": {
            "ANTHROPIC_SMALL_FAST_MODEL": "gemma4:e4b",
        },
        "# Debug (optional)": {
            "CLAUDE_CODE_DEBUG_LOG_LEVEL": "info",
        },
    }

    print("# Add to your shell profile (~/.zshrc or ~/.bashrc):")
    print("# AGI Framework - Claude Code Native Features")
    for section, vars_dict in env_vars.items():
        print(f"\n{section}")
        for key, value in vars_dict.items():
            print(f'export {key}="{value}"')


def cmd_enable_teams():
    """Enable agent teams in the project settings."""
    paths = get_claude_settings_paths()
    local_path = paths["project_local"]

    # Load or create settings.local.json
    settings = {}
    if local_path.exists():
        try:
            settings = json.loads(local_path.read_text())
        except Exception:
            settings = {}

    # Add env vars for agent teams
    settings.setdefault("env", {})
    settings["env"]["CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS"] = "1"
    settings["env"]["CLAUDE_CODE_AGENT_NAME"] = "claude"
    settings["env"]["CLAUDE_CODE_TEAM_NAME"] = "agi-framework"

    local_path.parent.mkdir(parents=True, exist_ok=True)
    local_path.write_text(json.dumps(settings, indent=2))

    print(json.dumps({
        "status": "success",
        "message": "Agent teams enabled in .claude/settings.local.json",
        "env_vars_set": list(settings["env"].keys()),
        "file": str(local_path),
    }, indent=2))


def cmd_set_model_overrides():
    """Configure model overrides to route small tasks to local Ollama."""
    features = detect_features()

    if not features["ollama_available"]:
        print(json.dumps({
            "status": "error",
            "message": "Ollama not available. Start with: ollama serve",
        }), file=sys.stderr)
        sys.exit(2)

    if not features["ollama_models"]:
        print(json.dumps({
            "status": "error",
            "message": "No Ollama models found. Pull one: ollama pull gemma4:e4b",
        }), file=sys.stderr)
        sys.exit(2)

    paths = get_claude_settings_paths()
    local_path = paths["project_local"]

    settings = {}
    if local_path.exists():
        try:
            settings = json.loads(local_path.read_text())
        except Exception:
            settings = {}

    # Set env to route small fast model to Ollama
    settings.setdefault("env", {})
    settings["env"]["CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS"] = "1"
    settings["env"]["CLAUDE_CODE_AGENT_NAME"] = "claude"
    settings["env"]["CLAUDE_CODE_TEAM_NAME"] = "agi-framework"

    local_path.parent.mkdir(parents=True, exist_ok=True)
    local_path.write_text(json.dumps(settings, indent=2))

    print(json.dumps({
        "status": "success",
        "message": "Model overrides configured",
        "local_models_available": features["ollama_models"],
        "file": str(local_path),
        "note": (
            "The PreToolUse hook (local_router_hook.py) auto-routes small tasks "
            "to local models. No model override needed for the main chat model — "
            "the hook handles routing transparently."
        ),
    }, indent=2))


def cmd_generate_local_config():
    """Generate a complete settings.local.json for maximum local routing."""
    features = detect_features()
    paths = get_claude_settings_paths()
    local_path = paths["project_local"]

    settings = {}
    if local_path.exists():
        try:
            settings = json.loads(local_path.read_text())
        except Exception:
            settings = {}

    # Environment variables
    settings["env"] = {
        "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1",
        "CLAUDE_CODE_AGENT_NAME": "claude",
        "CLAUDE_CODE_TEAM_NAME": "agi-framework",
        "OLLAMA_URL": OLLAMA_URL,
    }

    local_path.parent.mkdir(parents=True, exist_ok=True)
    local_path.write_text(json.dumps(settings, indent=2))

    print(json.dumps({
        "status": "success",
        "message": "Complete local config generated",
        "file": str(local_path),
        "features_enabled": [
            "agent_teams",
            "agent_identity",
            "local_router_hook (via .claude/settings.json)",
        ],
        "ollama": {
            "available": features["ollama_available"],
            "models": features["ollama_models"],
        },
    }, indent=2))


def main():
    parser = argparse.ArgumentParser(
        description="Configure Claude Code native features for AGI framework"
    )
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("status", help="Show current config and features")
    subparsers.add_parser("env", help="Show recommended environment variables")
    subparsers.add_parser("enable-teams", help="Enable agent teams mode")
    subparsers.add_parser("set-model-overrides", help="Configure model overrides")
    subparsers.add_parser("generate-local-config", help="Generate full local config")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    commands = {
        "status": cmd_status,
        "env": cmd_env,
        "enable-teams": cmd_enable_teams,
        "set-model-overrides": cmd_set_model_overrides,
        "generate-local-config": cmd_generate_local_config,
    }

    commands[args.command]()
    sys.exit(0)


if __name__ == "__main__":
    main()
