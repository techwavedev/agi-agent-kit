---
name: plugin-discovery
description: Platform-adaptive plugin and extension auto-discovery. Detects the runtime environment (Claude Code, Gemini, Opencode, Kiro) and recommends or installs relevant plugins, extensions, MCP servers, and marketplace integrations. Use when setting up a project, onboarding, or when the user asks about available tools/plugins.
version: 1.0.0
---

# Plugin & Extension Auto-Discovery

> Detect the runtime platform and surface the best available extensions

## Overview

This skill provides platform-aware auto-discovery of plugins, extensions, MCP servers, and marketplace integrations. It detects which AI coding environment is active and recommends the most relevant tools for the current project.

## Supported Platforms

| Platform                 | Extension System                   | Discovery Mechanism                      |
| ------------------------ | ---------------------------------- | ---------------------------------------- |
| **Claude Code**          | Plugins + Skills + Subagents + MCP | `/plugin`, `/agents`, `marketplace.json` |
| **Gemini / Antigravity** | Skills + MCP                       | `skills/`, `GEMINI.md`, MCP config       |
| **Opencode**             | Skills + MCP                       | `skills/`, `OPENCODE.md`, MCP config     |
| **Kiro**                 | Powers + Hooks + Agents            | `powers/`, hooks system                  |
| **VS Code / Cursor**     | Extensions + MCP                   | Extension marketplace, MCP config        |

---

## Platform Detection

### How to Detect

| Signal                                               | Platform             |
| ---------------------------------------------------- | -------------------- |
| `Task` tool available, `/agents`, `/plugin` commands | **Claude Code**      |
| `GEMINI.md` loaded, Google model family              | **Gemini**           |
| `OPENCODE.md` loaded                                 | **Opencode**         |
| Kiro-specific context, `powers/` directory           | **Kiro**             |
| VS Code extension host, Cursor markers               | **VS Code / Cursor** |

### Detection Flow

```
1. Check for Claude Code signals (Task tool, /plugin command)
   → If found: Claude Code mode

2. Check for loaded memory files
   → GEMINI.md: Gemini mode
   → OPENCODE.md: Opencode mode

3. Check for Kiro signals
   → powers/ directory, kiro-specific context: Kiro mode

4. Fallback: Generic mode (skills-only)
```

---

## Claude Code: Plugin Discovery

### Official Marketplace

Claude Code provides an official marketplace with pre-built plugins. To set up:

```bash
# Add the official Anthropic marketplace
/plugin marketplace add anthropics/claude-code
```

### Recommended Plugins by Project Type

#### All Projects

| Plugin              | What It Does                      | Install                                                    |
| ------------------- | --------------------------------- | ---------------------------------------------------------- |
| `commit-commands`   | Git commit workflows, PR creation | `/plugin install commit-commands@anthropics-claude-code`   |
| `pr-review-toolkit` | Specialized PR review agents      | `/plugin install pr-review-toolkit@anthropics-claude-code` |

#### JavaScript / TypeScript Projects

| Plugin           | What It Does                         | Install                                                 |
| ---------------- | ------------------------------------ | ------------------------------------------------------- |
| `typescript-lsp` | Type errors, diagnostics, navigation | `/plugin install typescript-lsp@anthropics-claude-code` |

#### Python Projects

| Plugin        | What It Does                      | Install                                              |
| ------------- | --------------------------------- | ---------------------------------------------------- |
| `pyright-lsp` | Python type checking, diagnostics | `/plugin install pyright-lsp@anthropics-claude-code` |

#### Rust Projects

| Plugin              | What It Does                 | Install                                                    |
| ------------------- | ---------------------------- | ---------------------------------------------------------- |
| `rust-analyzer-lsp` | Rust diagnostics, navigation | `/plugin install rust-analyzer-lsp@anthropics-claude-code` |

#### Go Projects

| Plugin      | What It Does               | Install                                            |
| ----------- | -------------------------- | -------------------------------------------------- |
| `gopls-lsp` | Go diagnostics, navigation | `/plugin install gopls-lsp@anthropics-claude-code` |

#### With External Services

| Plugin      | What It Does              | Install                                            |
| ----------- | ------------------------- | -------------------------------------------------- |
| `github`    | GitHub issues, PRs, repos | `/plugin install github@anthropics-claude-code`    |
| `gitlab`    | GitLab integration        | `/plugin install gitlab@anthropics-claude-code`    |
| `atlassian` | Jira/Confluence           | `/plugin install atlassian@anthropics-claude-code` |
| `slack`     | Slack messaging           | `/plugin install slack@anthropics-claude-code`     |
| `sentry`    | Error monitoring          | `/plugin install sentry@anthropics-claude-code`    |
| `vercel`    | Deployment                | `/plugin install vercel@anthropics-claude-code`    |
| `firebase`  | Firebase services         | `/plugin install firebase@anthropics-claude-code`  |
| `figma`     | Design integration        | `/plugin install figma@anthropics-claude-code`     |

### Custom Marketplaces

Teams can create their own plugin marketplaces:

```bash
# Add from GitHub
/plugin marketplace add your-org/your-marketplace

# Add from other Git hosts
/plugin marketplace add https://gitlab.com/your-org/plugins.git

# Add from local path
/plugin marketplace add /path/to/marketplace
```

### Managing Plugins

```bash
# List installed plugins
/plugin

# Disable a plugin
/plugin disable plugin-name@marketplace-name

# Enable a plugin
/plugin enable plugin-name@marketplace-name

# Uninstall a plugin
/plugin uninstall plugin-name@marketplace-name

# Update all marketplaces
/plugin marketplace update
```

### Plugin Scopes

| Scope              | Who Sees It              | Where Stored            |
| ------------------ | ------------------------ | ----------------------- |
| **User** (default) | Only you, all projects   | `~/.claude/`            |
| **Project**        | All collaborators        | `.claude/settings.json` |
| **Local**          | Only you, this repo only | Local config            |

```bash
# Install for all collaborators
/plugin install commit-commands@anthropics-claude-code --scope project
```

---

## Claude Code: Subagent & Skill Discovery

### Discovering Available Subagents

```bash
# Open the subagent management UI
/agents
```

This shows:

- Built-in subagents (Explore, Plan, General-purpose)
- User-level agents (`~/.claude/agents/`)
- Project-level agents (`.claude/agents/`)
- Plugin-provided agents

### Discovering Available Skills

Skills are auto-discovered from:

- `~/.claude/skills/` — User-level skills
- `.claude/skills/` — Project-level skills
- Plugin skills — From installed plugins
- Nested directories — `packages/*/. claude/skills/`

### Claude Code Feature Checklist

When setting up a Claude Code project, recommend enabling:

```markdown
## Claude Code Setup Checklist

- [ ] **Marketplace**: `/plugin marketplace add anthropics/claude-code`
- [ ] **LSP Plugin**: Install language-specific LSP for auto-diagnostics
- [ ] **Agent Teams**: `{ "env": { "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1" } }`
- [ ] **MCP Servers**: Configure relevant MCP servers in `.claude/settings.json`
- [ ] **Project Skills**: Set up `.claude/skills/` for project-specific workflows
- [ ] **Hooks**: Configure quality gates (lint, test, security on file save)
```

---

## Gemini / Antigravity: Extension Discovery

### Available Extensions

On Gemini, extensions come from:

1. **Antigravity Skills** (`skills/`) — Project skills with `SKILL.md`
2. **MCP Servers** — Configured in project settings
3. **Execution Scripts** (`execution/`) — Python scripts for deterministic tasks

### Discovery Command

The user can discover available skills by:

```bash
# List all skills
python3 skill-creator/scripts/update_catalog.py --skills-dir skills/

# View the catalog
cat skills/SKILLS_CATALOG.md
```

### MCP Server Discovery

Check configured MCP servers:

```bash
# Gemini: check Claude desktop config
cat ~/.config/claude/claude_desktop_config.json 2>/dev/null

# Or project-level MCP config
cat mcp_config.json 2>/dev/null
```

---

## Opencode: Extension Discovery

### Available Extensions

On Opencode, extensions come from:

1. **Antigravity Skills** (`skills/`) — Same as Gemini
2. **MCP Servers** — Configured in opencode settings
3. **Providers** — Model providers configured in opencode

### Discovery

```bash
# opencode config
cat ~/.config/opencode/config.json 2>/dev/null
```

---

## Kiro: Powers Discovery

> **Note**: Kiro uses "Powers" instead of plugins/skills. This is a different system documented separately.

### What Kiro Powers Are

Powers are Kiro's way of extending agent capabilities. They integrate with Kiro's hook system and agent framework.

### How to Detect Kiro

Check for:

- `powers/` directory in project root
- Kiro-specific configuration files
- Kiro agent context markers

> **Full Kiro support**: See separate task/skill for complete Kiro Powers integration.

---

## Auto-Discovery Workflow

When this skill is activated (manually or via `/plugin-discovery`):

### Step 1: Detect Platform

```
Detecting runtime environment...
→ Platform: [Claude Code / Gemini / Opencode / Kiro / Other]
→ Features: [list available features]
```

### Step 2: Scan Project

```
Scanning project for technology stack...
→ Languages: [TypeScript, Python, etc.]
→ Frameworks: [Next.js, Express, etc.]
→ Services: [GitHub, Jira, etc.]
```

### Step 3: Recommend Extensions

Based on platform + project stack, recommend the most relevant extensions:

```markdown
## 📦 Recommended Extensions for Your Setup

### Must-Have

- [Extension 1]: [Why it helps for your project]
- [Extension 2]: [Why it helps for your project]

### Nice-to-Have

- [Extension 3]: [Benefit]
- [Extension 4]: [Benefit]

### Install Commands

[Platform-specific install commands]
```

### Step 4: Offer to Install

```
Would you like me to install the recommended extensions? (y/n)
```

---

## Cross-Platform Compatibility Map

| Feature                 | Claude Code          | Gemini        | Opencode      | Kiro          |
| ----------------------- | -------------------- | ------------- | ------------- | ------------- |
| **Plugins/Marketplace** | ✅ `/plugin`         | ❌            | ❌            | ❌ (Powers)   |
| **Skills**              | ✅ `.claude/skills/` | ✅ `skills/`  | ✅ `skills/`  | ❌ (Powers)   |
| **Subagents**           | ✅ `.claude/agents/` | ⚠️ Personas   | ⚠️ Personas   | ✅ Agents     |
| **Agent Teams**         | ✅ Experimental      | ❌            | ❌            | ❌            |
| **MCP Servers**         | ✅ Native            | ✅ Via config | ✅ Via config | ✅ Via config |
| **LSP Integration**     | ✅ Plugins           | ❌            | ❌            | ✅ Native     |
| **Hooks**               | ✅ Native            | ❌            | ❌            | ✅ Native     |
| **Persistent Memory**   | ✅ Agent memory      | ⚠️ KI system  | ⚠️ Limited    | ❌            |

---

## Best Practices

1. **Detect first, recommend second** — Always detect platform before suggesting extensions
2. **Project-aware recommendations** — Recommend based on the actual tech stack, not generic lists
3. **Don't over-install** — Recommend only what's relevant to the current project
4. **Respect scopes** — Use project scope for team tools, user scope for personal preferences
5. **Proactive but not pushy** — Suggest once per session, don't repeat
