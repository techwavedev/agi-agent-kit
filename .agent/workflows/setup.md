---
description: Auto-detect platform and configure environment. One-shot setup wizard for Claude Code, Kiro, Gemini, or Opencode.
---

# Platform Setup Wizard

This workflow auto-detects your AI coding platform and configures the optimal environment in one step.

## Quick Start

// turbo

1. Run platform detection and setup:

```bash
python3 skills/plugin-discovery/scripts/platform_setup.py --project-dir .
```

## Options

### Dry Run (preview changes without applying)

```bash
python3 skills/plugin-discovery/scripts/platform_setup.py --project-dir . --dry-run
```

### Auto-Apply (no prompts)

```bash
python3 skills/plugin-discovery/scripts/platform_setup.py --project-dir . --auto
```

### JSON Output (for programmatic use)

```bash
python3 skills/plugin-discovery/scripts/platform_setup.py --project-dir . --json
```

## What It Detects

### Platforms

- **Claude Code**: Agent Teams, plugins, subagents, skills, MCP servers
- **Kiro IDE**: Powers, autonomous agent, hooks, MCP servers
- **Gemini / Antigravity**: Skills, execution scripts, agents, MCP servers
- **Opencode**: Skills, providers, MCP servers

### Project Stack

- Languages: JavaScript, TypeScript, Python, Go, Rust, Ruby
- Frameworks: Next.js, React, Vue, Express, Angular, Svelte, Astro, React Native
- Services: GitHub, GitLab, Docker, Vercel, Netlify, Stripe, Supabase, Firebase, Terraform

## What It Configures

### Auto-Applied (with confirmation)

- Claude Code: Agent Teams enable, `.claude/settings.json` updates, directory setup
- Kiro: Hook directories (`.kiro/hooks/`)
- Both: Skills/agents directory creation

### Manual Actions (shown as instructions)

- Claude Code: Plugin installs (requires `/plugin` command)
- Kiro: Power installs (requires Powers panel)
- Both: MCP server configuration

## Integration

After setup, the agent will proactively use detected capabilities:

- Claude Code + Agent Teams → parallel multi-agent orchestration
- Kiro + Powers → dynamic context loading per task
- Gemini/Opencode → sequential persona switching with full skill access
