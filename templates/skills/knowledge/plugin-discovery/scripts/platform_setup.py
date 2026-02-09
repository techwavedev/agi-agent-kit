#!/usr/bin/env python3
"""
Script: platform_setup.py
Purpose: Auto-detect the AI coding platform and configure the environment
         for optimal use. One-step setup wizard.

Usage:
    python3 platform_setup.py [--project-dir <path>] [--auto] [--json]

Arguments:
    --project-dir   Path to the project root (default: current directory)
    --auto          Auto-apply all recommended settings without prompting
    --json          Output results as JSON (for agent consumption)
    --dry-run       Show what would be configured without making changes

Exit Codes:
    0 - Success
    1 - Invalid arguments
    2 - Project directory not found
    3 - Configuration error
"""

import argparse
import json
import os
import sys
import glob
import shutil
from pathlib import Path


# ── Platform Detection ──────────────────────────────────────────────


def detect_platform(project_dir: Path) -> dict:
    """Detect which AI coding platform is active and what features are available."""
    result = {
        "platform": "unknown",
        "features": {},
        "project_stack": {},
        "recommendations": [],
    }

    # Check for Claude Code signals
    claude_dir = project_dir / ".claude"
    claude_user_dir = Path.home() / ".claude"
    has_claude_settings = (claude_dir / "settings.json").exists()
    has_claude_user = claude_user_dir.exists()
    claude_md = project_dir / "CLAUDE.md"

    # Check for Kiro signals
    kiro_dir = project_dir / ".kiro"
    kiro_user_dir = Path.home() / ".kiro"
    has_kiro = kiro_dir.exists() or kiro_user_dir.exists()
    power_files = list(project_dir.glob("**/POWER.md"))

    # Check for Gemini signals
    gemini_md = project_dir / "GEMINI.md"
    has_gemini = gemini_md.exists()

    # Check for Opencode signals
    opencode_md = project_dir / "OPENCODE.md"
    has_opencode = opencode_md.exists()
    opencode_config = Path.home() / ".config" / "opencode" / "config.json"

    # Priority-based detection
    if has_claude_settings or has_claude_user:
        result["platform"] = "claude-code"
        result["features"] = detect_claude_features(project_dir, claude_dir, claude_user_dir)
    elif has_kiro or power_files:
        result["platform"] = "kiro"
        result["features"] = detect_kiro_features(project_dir, kiro_dir, kiro_user_dir)
    elif has_gemini:
        result["platform"] = "gemini"
        result["features"] = detect_gemini_features(project_dir)
    elif has_opencode or opencode_config.exists():
        result["platform"] = "opencode"
        result["features"] = detect_opencode_features(project_dir)
    else:
        # Fallback: check if any agent files exist (installed via agi-agent-kit)
        agents_md = project_dir / "AGENTS.md"
        if agents_md.exists() or gemini_md.exists() or claude_md.exists():
            result["platform"] = "gemini"  # Default to Gemini if AGENTS.md exists
            result["features"] = detect_gemini_features(project_dir)

    # Detect project tech stack
    result["project_stack"] = detect_project_stack(project_dir)

    # Generate recommendations
    result["recommendations"] = generate_recommendations(result)

    return result


def detect_claude_features(project_dir: Path, claude_dir: Path, claude_user_dir: Path) -> dict:
    """Detect Claude Code features and their current state."""
    features = {
        "agent_teams": {"enabled": False, "configurable": True},
        "plugins": {"installed": [], "marketplace_added": False},
        "subagents": {"project": [], "user": []},
        "skills": {"project": [], "user": []},
        "mcp_servers": {"configured": []},
        "hooks": {"configured": False},
    }

    # Check Agent Teams
    settings_file = claude_dir / "settings.json"
    if settings_file.exists():
        try:
            settings = json.loads(settings_file.read_text())
            env = settings.get("env", {})
            if env.get("CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS") == "1":
                features["agent_teams"]["enabled"] = True
        except (json.JSONDecodeError, KeyError):
            pass

    # Also check user-level settings
    user_settings = claude_user_dir / "settings.json"
    if user_settings.exists():
        try:
            settings = json.loads(user_settings.read_text())
            env = settings.get("env", {})
            if env.get("CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS") == "1":
                features["agent_teams"]["enabled"] = True
        except (json.JSONDecodeError, KeyError):
            pass

    # Check project-level agents
    agents_dir = claude_dir / "agents"
    if agents_dir.exists():
        features["subagents"]["project"] = [
            f.stem for f in agents_dir.glob("*.md")
        ]

    # Check user-level agents
    user_agents = claude_user_dir / "agents"
    if user_agents.exists():
        features["subagents"]["user"] = [
            f.stem for f in user_agents.glob("*.md")
        ]

    # Check project-level skills
    skills_dir = claude_dir / "skills"
    if skills_dir.exists():
        for skill_dir in skills_dir.iterdir():
            if skill_dir.is_dir() and (skill_dir / "SKILL.md").exists():
                features["skills"]["project"].append(skill_dir.name)

    # Also check Antigravity skills directory
    agi_skills = project_dir / "skills"
    if agi_skills.exists():
        for skill_dir in agi_skills.iterdir():
            if skill_dir.is_dir() and (skill_dir / "SKILL.md").exists():
                features["skills"]["project"].append(skill_dir.name)

    # Check MCP servers
    mcp_config = claude_dir / "mcp.json"
    if not mcp_config.exists():
        mcp_config = claude_dir / "settings.json"
    if mcp_config.exists():
        try:
            config = json.loads(mcp_config.read_text())
            servers = config.get("mcpServers", {})
            features["mcp_servers"]["configured"] = list(servers.keys())
        except (json.JSONDecodeError, KeyError):
            pass

    return features


def detect_kiro_features(project_dir: Path, kiro_dir: Path, kiro_user_dir: Path) -> dict:
    """Detect Kiro features and their current state."""
    features = {
        "powers": {"installed": []},
        "autonomous_agent": {"available": True},
        "hooks": {"configured": []},
        "mcp_servers": {"configured": []},
    }

    # Check installed powers (user level)
    kiro_mcp = kiro_user_dir / "settings" / "mcp.json"
    if kiro_mcp.exists():
        try:
            config = json.loads(kiro_mcp.read_text())
            servers = config.get("mcpServers", {})
            # Powers are namespaced as power-<name>-<server>
            for name in servers:
                if name.startswith("power-"):
                    features["powers"]["installed"].append(name)
                features["mcp_servers"]["configured"].append(name)
        except (json.JSONDecodeError, KeyError):
            pass

    # Check hooks
    hooks_dir = kiro_dir / "hooks"
    if hooks_dir.exists():
        features["hooks"]["configured"] = [
            f.stem for f in hooks_dir.glob("*.kiro.hook")
        ]

    # Check for POWER.md files in project
    power_files = list(project_dir.glob("**/POWER.md"))
    for pf in power_files:
        features["powers"]["installed"].append(pf.parent.name)

    return features


def detect_gemini_features(project_dir: Path) -> dict:
    """Detect Gemini/Antigravity features."""
    features = {
        "skills": {"installed": []},
        "mcp_servers": {"configured": []},
        "execution_scripts": [],
        "agents": [],
    }

    # Check skills
    skills_dir = project_dir / "skills"
    if skills_dir.exists():
        for skill_dir in skills_dir.iterdir():
            if skill_dir.is_dir() and (skill_dir / "SKILL.md").exists():
                features["skills"]["installed"].append(skill_dir.name)

    # Check execution scripts
    exec_dir = project_dir / "execution"
    if exec_dir.exists():
        features["execution_scripts"] = [
            f.name for f in exec_dir.glob("*.py")
        ]

    # Check agents
    agents_dir = project_dir / ".agent" / "agents"
    if not agents_dir.exists():
        agents_dir = project_dir / ".agent"
    if agents_dir.exists():
        features["agents"] = [
            f.stem for f in agents_dir.glob("*.md")
            if f.name != "AGENTS.md"
        ]

    # Check MCP config
    for config_path in [
        project_dir / "mcp_config.json",
        Path.home() / ".config" / "claude" / "claude_desktop_config.json",
    ]:
        if config_path.exists():
            try:
                config = json.loads(config_path.read_text())
                servers = config.get("mcpServers", {})
                features["mcp_servers"]["configured"] = list(servers.keys())
                break
            except (json.JSONDecodeError, KeyError):
                pass

    return features


def detect_opencode_features(project_dir: Path) -> dict:
    """Detect Opencode features."""
    features = {
        "skills": {"installed": []},
        "mcp_servers": {"configured": []},
        "providers": [],
    }

    # Check skills (same as Gemini)
    skills_dir = project_dir / "skills"
    if skills_dir.exists():
        for skill_dir in skills_dir.iterdir():
            if skill_dir.is_dir() and (skill_dir / "SKILL.md").exists():
                features["skills"]["installed"].append(skill_dir.name)

    # Check opencode config
    config_path = Path.home() / ".config" / "opencode" / "config.json"
    if config_path.exists():
        try:
            config = json.loads(config_path.read_text())
            features["providers"] = list(config.get("providers", {}).keys())
            features["mcp_servers"]["configured"] = list(
                config.get("mcpServers", {}).keys()
            )
        except (json.JSONDecodeError, KeyError):
            pass

    return features


# ── Project Stack Detection ─────────────────────────────────────────


def detect_project_stack(project_dir: Path) -> dict:
    """Detect the project's technology stack."""
    stack = {
        "languages": [],
        "frameworks": [],
        "services": [],
        "package_manager": None,
    }

    # Package managers
    if (project_dir / "package.json").exists():
        stack["package_manager"] = "npm"
        stack["languages"].append("javascript")

        try:
            pkg = json.loads((project_dir / "package.json").read_text())
            deps = {
                **pkg.get("dependencies", {}),
                **pkg.get("devDependencies", {}),
            }

            # Detect TypeScript
            if "typescript" in deps:
                stack["languages"].append("typescript")

            # Detect frameworks
            framework_map = {
                "next": "nextjs",
                "react": "react",
                "vue": "vue",
                "express": "express",
                "fastify": "fastify",
                "nestjs": "nestjs",
                "@angular/core": "angular",
                "svelte": "svelte",
                "astro": "astro",
                "react-native": "react-native",
                "expo": "expo",
            }
            for dep, fw in framework_map.items():
                if dep in deps:
                    stack["frameworks"].append(fw)

            # Detect services
            service_map = {
                "@supabase/supabase-js": "supabase",
                "stripe": "stripe",
                "firebase": "firebase",
                "@prisma/client": "prisma",
                "mongoose": "mongodb",
            }
            for dep, svc in service_map.items():
                if dep in deps:
                    stack["services"].append(svc)

        except (json.JSONDecodeError, KeyError):
            pass

    if (project_dir / "requirements.txt").exists() or (project_dir / "pyproject.toml").exists():
        stack["languages"].append("python")
        stack["package_manager"] = stack["package_manager"] or "pip"

    if (project_dir / "go.mod").exists():
        stack["languages"].append("go")

    if (project_dir / "Cargo.toml").exists():
        stack["languages"].append("rust")

    if (project_dir / "Gemfile").exists():
        stack["languages"].append("ruby")

    # Detect services from config files
    if (project_dir / ".github").exists():
        stack["services"].append("github")
    if (project_dir / ".gitlab-ci.yml").exists():
        stack["services"].append("gitlab")
    if (project_dir / "docker-compose.yml").exists() or (project_dir / "docker-compose.yaml").exists():
        stack["services"].append("docker")
    if (project_dir / "Dockerfile").exists():
        stack["services"].append("docker")
    if (project_dir / "vercel.json").exists():
        stack["services"].append("vercel")
    if (project_dir / "netlify.toml").exists():
        stack["services"].append("netlify")
    if (project_dir / "terraform").exists() or list(project_dir.glob("*.tf")):
        stack["services"].append("terraform")

    # Deduplicate
    stack["languages"] = list(dict.fromkeys(stack["languages"]))
    stack["frameworks"] = list(dict.fromkeys(stack["frameworks"]))
    stack["services"] = list(dict.fromkeys(stack["services"]))

    return stack


# ── Recommendations Engine ──────────────────────────────────────────


def generate_recommendations(detection: dict) -> list:
    """Generate platform-specific recommendations based on detection results."""
    recs = []
    platform = detection["platform"]
    features = detection["features"]
    stack = detection["project_stack"]

    if platform == "claude-code":
        recs.extend(generate_claude_recommendations(features, stack))
    elif platform == "kiro":
        recs.extend(generate_kiro_recommendations(features, stack))
    elif platform == "gemini":
        recs.extend(generate_gemini_recommendations(features, stack))
    elif platform == "opencode":
        recs.extend(generate_opencode_recommendations(features, stack))

    return recs


def generate_claude_recommendations(features: dict, stack: dict) -> list:
    recs = []

    # Agent Teams
    if not features.get("agent_teams", {}).get("enabled", False):
        recs.append({
            "id": "claude_agent_teams",
            "priority": "high",
            "category": "orchestration",
            "title": "Enable Agent Teams",
            "description": "True parallel multi-agent orchestration",
            "action": "add_settings_json",
            "config": {"env": {"CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"}},
            "target": ".claude/settings.json",
        })

    # LSP plugins based on stack
    lsp_map = {
        "typescript": ("typescript-lsp", "TypeScript type checking & diagnostics"),
        "javascript": ("typescript-lsp", "JavaScript/TypeScript diagnostics"),
        "python": ("pyright-lsp", "Python type checking & diagnostics"),
        "rust": ("rust-analyzer-lsp", "Rust diagnostics & navigation"),
        "go": ("gopls-lsp", "Go diagnostics & navigation"),
    }
    for lang in stack.get("languages", []):
        if lang in lsp_map:
            plugin_name, desc = lsp_map[lang]
            recs.append({
                "id": f"claude_lsp_{lang}",
                "priority": "high",
                "category": "plugins",
                "title": f"Install {plugin_name}",
                "description": desc,
                "action": "install_plugin",
                "command": f"/plugin install {plugin_name}@claude-plugins-official",
            })

    # Service integrations
    service_plugins = {
        "github": ("github", "GitHub issues, PRs, repos"),
        "gitlab": ("gitlab", "GitLab integration"),
        "vercel": ("vercel", "Deployment integration"),
        "firebase": ("firebase", "Firebase services"),
    }
    for svc in stack.get("services", []):
        if svc in service_plugins:
            plugin_name, desc = service_plugins[svc]
            recs.append({
                "id": f"claude_svc_{svc}",
                "priority": "medium",
                "category": "plugins",
                "title": f"Install {plugin_name} plugin",
                "description": desc,
                "action": "install_plugin",
                "command": f"/plugin install {plugin_name}@claude-plugins-official",
            })

    # Skills symlink
    skills_dir = Path(".claude/skills")
    if not skills_dir.exists():
        recs.append({
            "id": "claude_skills_dir",
            "priority": "medium",
            "category": "skills",
            "title": "Set up .claude/skills/ directory",
            "description": "Enable Claude Code to discover project skills",
            "action": "create_dir",
            "target": ".claude/skills",
        })

    return recs


def generate_kiro_recommendations(features: dict, stack: dict) -> list:
    recs = []

    # Power recommendations based on stack
    power_map = {
        "supabase": ("Supabase", "Database, auth, storage, realtime"),
        "stripe": ("Stripe", "Payment integration"),
        "firebase": ("Firebase", "Backend services"),
        "vercel": ("Vercel", "Not available as Power yet"),
        "netlify": ("Netlify", "Web app deployment"),
        "docker": ("Docker", "Not available as Power yet"),
        "terraform": ("Terraform", "Infrastructure as Code"),
    }
    installed = [p.lower() for p in features.get("powers", {}).get("installed", [])]
    for svc in stack.get("services", []):
        if svc in power_map and svc not in installed:
            name, desc = power_map[svc]
            recs.append({
                "id": f"kiro_power_{svc}",
                "priority": "high",
                "category": "powers",
                "title": f"Install {name} Power",
                "description": desc,
                "action": "install_power",
                "instruction": f"Open Powers panel → Install {name}",
            })

    # Framework-specific powers
    framework_powers = {
        "react": ("Figma", "Design to code with Figma"),
        "nextjs": ("Figma", "Design to code with Figma"),
    }
    for fw in stack.get("frameworks", []):
        if fw in framework_powers:
            name, desc = framework_powers[fw]
            if name.lower() not in installed:
                recs.append({
                    "id": f"kiro_power_{name.lower()}",
                    "priority": "medium",
                    "category": "powers",
                    "title": f"Install {name} Power",
                    "description": desc,
                    "action": "install_power",
                    "instruction": f"Open Powers panel → Install {name}",
                })

    # Hooks
    if not features.get("hooks", {}).get("configured", []):
        recs.append({
            "id": "kiro_hooks",
            "priority": "medium",
            "category": "hooks",
            "title": "Set up quality gate hooks",
            "description": "Automated checks in .kiro/hooks/",
            "action": "create_hooks",
            "target": ".kiro/hooks/",
        })

    return recs


def generate_gemini_recommendations(features: dict, stack: dict) -> list:
    recs = []

    # Skills catalog
    skills = features.get("skills", {}).get("installed", [])
    if not skills:
        recs.append({
            "id": "gemini_skills",
            "priority": "high",
            "category": "skills",
            "title": "Initialize skills",
            "description": "Run npx @techwavedev/agi-agent-kit init to install skills",
            "action": "run_command",
            "command": "npx -y @techwavedev/agi-agent-kit init",
        })

    return recs


def generate_opencode_recommendations(features: dict, stack: dict) -> list:
    recs = []

    skills = features.get("skills", {}).get("installed", [])
    if not skills:
        recs.append({
            "id": "opencode_skills",
            "priority": "high",
            "category": "skills",
            "title": "Initialize skills",
            "description": "Run npx @techwavedev/agi-agent-kit init to install skills",
            "action": "run_command",
            "command": "npx -y @techwavedev/agi-agent-kit init",
        })

    return recs


# ── Configuration Applier ───────────────────────────────────────────


def apply_recommendation(rec: dict, project_dir: Path, dry_run: bool = False) -> dict:
    """Apply a single recommendation."""
    result = {"id": rec["id"], "status": "skipped", "detail": ""}

    action = rec.get("action", "")

    if action == "add_settings_json":
        target = project_dir / rec["target"]
        config_to_add = rec["config"]

        if dry_run:
            result["status"] = "dry_run"
            result["detail"] = f"Would update {target} with {json.dumps(config_to_add)}"
            return result

        # Read existing or create new
        target.parent.mkdir(parents=True, exist_ok=True)
        existing = {}
        if target.exists():
            try:
                existing = json.loads(target.read_text())
            except json.JSONDecodeError:
                existing = {}

        # Deep merge
        for key, value in config_to_add.items():
            if isinstance(value, dict) and key in existing and isinstance(existing[key], dict):
                existing[key].update(value)
            else:
                existing[key] = value

        target.write_text(json.dumps(existing, indent=2) + "\n")
        result["status"] = "applied"
        result["detail"] = f"Updated {target}"

    elif action == "create_dir":
        target = project_dir / rec["target"]
        if dry_run:
            result["status"] = "dry_run"
            result["detail"] = f"Would create {target}"
        else:
            target.mkdir(parents=True, exist_ok=True)
            result["status"] = "applied"
            result["detail"] = f"Created {target}"

    elif action == "install_plugin":
        # Plugins require Claude Code CLI — output instruction
        result["status"] = "manual"
        result["detail"] = f"Run in Claude Code: {rec['command']}"

    elif action == "install_power":
        # Powers require Kiro IDE — output instruction
        result["status"] = "manual"
        result["detail"] = rec.get("instruction", "Open Powers panel to install")

    elif action == "run_command":
        if dry_run:
            result["status"] = "dry_run"
            result["detail"] = f"Would run: {rec['command']}"
        else:
            result["status"] = "manual"
            result["detail"] = f"Run: {rec['command']}"

    elif action == "create_hooks":
        target = project_dir / rec["target"]
        if dry_run:
            result["status"] = "dry_run"
            result["detail"] = f"Would create {target}"
        else:
            target.mkdir(parents=True, exist_ok=True)
            result["status"] = "applied"
            result["detail"] = f"Created {target}"

    return result


# ── Output Formatting ───────────────────────────────────────────────


PLATFORM_NAMES = {
    "claude-code": "Claude Code",
    "kiro": "Kiro IDE",
    "gemini": "Gemini / Antigravity",
    "opencode": "Opencode",
    "unknown": "Unknown",
}

PLATFORM_EMOJI = {
    "claude-code": "🤖",
    "kiro": "⚡",
    "gemini": "♊",
    "opencode": "💻",
    "unknown": "❓",
}


def print_report(detection: dict, results: list = None):
    """Print a human-readable setup report."""
    platform = detection["platform"]
    emoji = PLATFORM_EMOJI.get(platform, "❓")
    name = PLATFORM_NAMES.get(platform, "Unknown")
    features = detection["features"]
    stack = detection["project_stack"]
    recs = detection["recommendations"]

    print(f"\n{'='*60}")
    print(f"  {emoji}  Platform Setup Report — {name}")
    print(f"{'='*60}\n")

    # Tech Stack
    if stack.get("languages") or stack.get("frameworks"):
        print("📦 Project Stack:")
        if stack["languages"]:
            print(f"   Languages:  {', '.join(stack['languages'])}")
        if stack["frameworks"]:
            print(f"   Frameworks: {', '.join(stack['frameworks'])}")
        if stack["services"]:
            print(f"   Services:   {', '.join(stack['services'])}")
        print()

    # Current Features
    print("🔍 Detected Features:")
    if platform == "claude-code":
        at = features.get("agent_teams", {})
        print(f"   Agent Teams:  {'✅ Enabled' if at.get('enabled') else '❌ Not enabled'}")
        agents = features.get("subagents", {})
        total_agents = len(agents.get("project", [])) + len(agents.get("user", []))
        print(f"   Subagents:    {total_agents} configured")
        skills = features.get("skills", {})
        total_skills = len(set(skills.get("project", [])))
        print(f"   Skills:       {total_skills} discovered")
        mcp = features.get("mcp_servers", {})
        print(f"   MCP Servers:  {len(mcp.get('configured', []))} configured")

    elif platform == "kiro":
        powers = features.get("powers", {})
        print(f"   Powers:       {len(powers.get('installed', []))} installed")
        hooks = features.get("hooks", {})
        print(f"   Hooks:        {len(hooks.get('configured', []))} configured")
        mcp = features.get("mcp_servers", {})
        print(f"   MCP Servers:  {len(mcp.get('configured', []))} configured")
        print(f"   Autonomous:   ✅ Available")

    elif platform in ("gemini", "opencode"):
        skills = features.get("skills", {})
        print(f"   Skills:       {len(skills.get('installed', []))} installed")
        agents = features.get("agents", [])
        if agents:
            print(f"   Agents:       {len(agents)} configured")
        mcp = features.get("mcp_servers", {})
        print(f"   MCP Servers:  {len(mcp.get('configured', []))} configured")

    print()

    # Recommendations
    if recs:
        print(f"💡 Recommendations ({len(recs)}):")
        for i, rec in enumerate(recs, 1):
            priority_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(rec["priority"], "⚪")
            print(f"   {i}. {priority_icon} [{rec['category']}] {rec['title']}")
            print(f"      {rec['description']}")
        print()
    else:
        print("✅ No recommendations — everything looks configured!\n")

    # Results
    if results:
        print("📋 Applied Changes:")
        for r in results:
            status_icon = {
                "applied": "✅",
                "manual": "👉",
                "skipped": "⏭️",
                "dry_run": "🔍",
                "error": "❌",
            }.get(r["status"], "❓")
            print(f"   {status_icon} {r['detail']}")
        print()

    print(f"{'='*60}\n")


# ── Main ────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description="Auto-detect AI platform and configure environment"
    )
    parser.add_argument(
        "--project-dir",
        default=".",
        help="Path to the project root (default: current directory)",
    )
    parser.add_argument(
        "--auto",
        action="store_true",
        help="Auto-apply all recommended settings without prompting",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Output results as JSON",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be configured without making changes",
    )
    args = parser.parse_args()

    project_dir = Path(args.project_dir).resolve()
    if not project_dir.exists():
        print(json.dumps({"status": "error", "message": f"Directory not found: {project_dir}"}))
        sys.exit(2)

    # Detect
    detection = detect_platform(project_dir)

    # JSON output mode (for agent consumption)
    if args.json_output:
        print(json.dumps(detection, indent=2))
        sys.exit(0)

    # Interactive / auto mode
    print_report(detection)

    recs = detection["recommendations"]
    if not recs:
        sys.exit(0)

    # Filter to auto-applicable recommendations
    auto_applicable = [r for r in recs if r["action"] in ("add_settings_json", "create_dir", "create_hooks")]
    manual_only = [r for r in recs if r["action"] not in ("add_settings_json", "create_dir", "create_hooks")]

    if auto_applicable:
        if args.auto or args.dry_run:
            confirm = True
        else:
            print(f"🔧 {len(auto_applicable)} setting(s) can be auto-configured.")
            if manual_only:
                print(f"👉 {len(manual_only)} require manual action (plugin/power installs).")
            try:
                answer = input("\nApply recommended settings? [Y/n] ").strip().lower()
                confirm = answer in ("", "y", "yes")
            except (EOFError, KeyboardInterrupt):
                confirm = False

        results = []
        if confirm:
            for rec in auto_applicable:
                result = apply_recommendation(rec, project_dir, dry_run=args.dry_run)
                results.append(result)

        # Always show manual actions
        for rec in manual_only:
            result = apply_recommendation(rec, project_dir, dry_run=args.dry_run)
            results.append(result)

        print_report(detection, results)
    else:
        # Only manual recommendations
        results = []
        for rec in manual_only:
            result = apply_recommendation(rec, project_dir, dry_run=args.dry_run)
            results.append(result)
        if results:
            print("👉 Manual actions required:")
            for r in results:
                print(f"   • {r['detail']}")
            print()

    sys.exit(0)


if __name__ == "__main__":
    main()
