---
name: plugin-discovery
description: Platform-adaptive plugin and extension auto-discovery. Detects the runtime environment (Claude Code, Gemini, Opencode, Kiro) and recommends or installs relevant plugins, extensions, MCP servers, and marketplace integrations. Use when setting up a project, onboarding, or when the user asks about available tools/plugins.
version: 1.1.0
---

# Plugin & Extension Auto-Discovery

> Detect the runtime platform and surface the best available extensions

## Quick Start — One-Shot Setup

Run the setup wizard to auto-detect your platform and configure everything:

```bash
# Interactive (asks one confirmation question)
python3 skills/plugin-discovery/scripts/platform_setup.py --project-dir .

# Auto-apply everything
python3 skills/plugin-discovery/scripts/platform_setup.py --project-dir . --auto

# Preview without changes
python3 skills/plugin-discovery/scripts/platform_setup.py --project-dir . --dry-run

# JSON output (for agent consumption)
python3 skills/plugin-discovery/scripts/platform_setup.py --project-dir . --json
```

> **Trigger**: Also available via `/setup` workflow command.

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

| Plugin     | What It Does              | Install                                           |
| ---------- | ------------------------- | ------------------------------------------------- |
| `github`   | GitHub issues, PRs, repos | `/plugin install github@anthropics-claude-code`   |
| `linear`   | Issue tracking            | `/plugin install linear@anthropics-claude-code`   |
| `slack`    | Slack messaging           | `/plugin install slack@anthropics-claude-code`    |
| `sentry`   | Error monitoring          | `/plugin install sentry@anthropics-claude-code`   |
| `vercel`   | Deployment                | `/plugin install vercel@anthropics-claude-code`   |
| `firebase` | Firebase services         | `/plugin install firebase@anthropics-claude-code` |
| `figma`    | Design integration        | `/plugin install figma@anthropics-claude-code`    |

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

> Kiro uses **Powers** — unified bundles of MCP tools + steering knowledge + hooks that load dynamically based on context keywords. Available in Kiro IDE 0.7+.

### What Kiro Powers Are

Powers are Kiro's extension system. Unlike traditional MCP setups that load all tools upfront (causing context rot), Powers activate **on-demand** when the conversation mentions relevant keywords. A Power bundles:

1. **`POWER.md`** — Entry point with frontmatter (activation keywords) + onboarding steps + steering instructions
2. **`mcp.json`** — MCP server configuration for tool integrations (optional)
3. **`steering/`** — Workflow-specific guidance files loaded on-demand (optional)

### How to Detect Kiro

| Signal                               | Confidence |
| ------------------------------------ | ---------- |
| `.kiro/` directory in workspace      | ✅ High    |
| `POWER.md` files in project          | ✅ High    |
| Kiro-specific hooks (`.kiro/hooks/`) | ✅ High    |
| Kiro agent context markers           | ✅ High    |

### Power Structure

```
power-name/
├── POWER.md          # Metadata, onboarding, steering mappings (required)
├── mcp.json          # MCP server configuration (optional)
└── steering/         # Workflow-specific guidance (optional)
    ├── workflow-a.md
    ├── workflow-b.md
    └── patterns.md
```

### POWER.md Anatomy

The `POWER.md` has two parts: **frontmatter** (when to activate) and **body** (instructions).

#### Frontmatter: Keywords-Based Activation

```yaml
---
name: "supabase"
displayName: "Supabase with local CLI"
description: "Build fullstack applications with Supabase's Postgres database, auth, storage, and real-time subscriptions"
keywords:
  [
    "database",
    "postgres",
    "auth",
    "storage",
    "realtime",
    "backend",
    "supabase",
    "rls",
  ]
---
```

When someone says "Let's set up the database," Kiro detects "database" in the keywords and activates the Supabase power — loading its MCP tools and `POWER.md` steering into context. Other powers deactivate to save context.

#### Onboarding Section (runs once)

```markdown
# Onboarding

## Step 1: Validate tools work

- **Docker Desktop**: Verify with `docker --version`
- **Supabase CLI**: Verify with `supabase --version`

## Step 2: Add hooks

Add a hook to `.kiro/hooks/review-advisors.kiro.hook`
```

#### Steering Section (maps workflows to files)

**Simple approach** — all guidance in `POWER.md`:

```markdown
# Best Practices

## Database Schema Design

- Use UUIDs for primary keys
- Always add timestamps
- Enable RLS on all tables with user data
```

**Advanced approach** — separate steering files:

```markdown
# When to Load Steering Files

- Setting up a database → `database-setup-workflow.md`
- Creating RLS policies → `supabase-database-rls-policies.md`
- Creating PostgreSQL functions → `supabase-database-functions.md`
- Working with Edge Functions → `supabase-edge-functions.md`
```

### MCP Server Configuration (mcp.json)

```json
{
  "mcpServers": {
    "supabase-local": {
      "command": "npx",
      "args": ["-y", "@supabase/mcp-server-supabase"],
      "env": {
        "SUPABASE_URL": "${SUPABASE_URL}",
        "SUPABASE_ANON_KEY": "${SUPABASE_ANON_KEY}"
      }
    }
  }
}
```

Kiro auto-namespaces server names to avoid conflicts (e.g., `supabase-local` → `power-supabase-supabase-local`).

### Kiro Hooks System

Powers can install hooks into `.kiro/hooks/`. Hooks are JSON files that define automated behaviors:

```json
{
  "enabled": true,
  "name": "Review Database Performance & Security",
  "description": "Verify database follows performance/security best practices",
  "version": "1",
  "when": { "type": "userTriggered" },
  "then": {
    "type": "askAgent",
    "prompt": "Execute `get_advisors` via MCP to check for performance and security concerns"
  }
}
```

### Kiro Autonomous Agent

Kiro also has an **autonomous agent** that works at the team level:

- **Runs in isolated sandbox environments** — opens PRs for review
- **Maintains context** across tasks, repos, and pull requests
- **Learns from code reviews** — adapts to team patterns over time
- **Works across repos** — coordinates multi-repo changes into related PRs
- **Protects focus time** — handles routine fixes, follow-ups, status updates

> The autonomous agent is complementary to Powers. Powers provide the expertise, the autonomous agent provides the execution.

### Available Kiro Powers (Curated Partners)

| Power         | Category       | What It Does                      |
| ------------- | -------------- | --------------------------------- |
| **Figma**     | Design         | Design to code                    |
| **Supabase**  | Backend        | Database, auth, storage, realtime |
| **Stripe**    | Payments       | Payment integration               |
| **Neon**      | Database       | Serverless Postgres               |
| **Netlify**   | Deployment     | Web app deployment                |
| **Postman**   | API Testing    | API testing and docs              |
| **Strands**   | Agent Dev      | Build agents                      |
| **Datadog**   | Observability  | Monitoring & observability        |
| **Dynatrace** | Observability  | APM & monitoring                  |
| **AWS CDK**   | Infrastructure | AWS IaC with CDK/CloudFormation   |
| **Terraform** | Infrastructure | Multi-cloud IaC                   |
| **Aurora**    | Database       | AWS Aurora PostgreSQL/DSQL        |

### Installing Powers

```
# From the Kiro IDE Powers panel:
1. Open Powers panel → Browse curated powers
2. Click "Install" on any power

# From GitHub:
1. Powers panel → "Add power from GitHub"
2. Enter repository URL

# From local directory:
1. Powers panel → "Add power from Local Path"
2. Select your power directory
```

### Kiro Setup Checklist

```markdown
## Kiro Setup Checklist

- [ ] **Install essential Powers**: Figma, Supabase/Neon, deployment tool
- [ ] **Configure hooks**: Quality gates in `.kiro/hooks/`
- [ ] **Set up autonomous agent**: For team-level async task execution
- [ ] **Create project-specific powers**: Package team patterns as Powers
- [ ] **Share powers**: Push to GitHub for team-wide access
```

---

## Antigravity ↔ Kiro Powers: Mapping Guide

Our Antigravity skills can be adapted to Kiro Powers with minimal changes:

| Antigravity          | Kiro Powers                             | Mapping Notes                                               |
| -------------------- | --------------------------------------- | ----------------------------------------------------------- |
| `SKILL.md`           | `POWER.md`                              | Rename + adjust frontmatter (add `keywords`, `displayName`) |
| `skills/skill-name/` | `power-name/`                           | Same directory structure                                    |
| `references/`        | `steering/`                             | Rename directory                                            |
| `scripts/`           | Keep as `scripts/` or integrate via MCP | Scripts stay or wrap in MCP                                 |
| `SKILLS_CATALOG.md`  | Kiro Powers panel                       | Kiro handles discovery natively                             |
| `.agent/agents/`     | Kiro agents                             | Different agent system                                      |
| `execution/`         | Wrap as MCP tools                       | Kiro prefers MCP for tool access                            |
| `GEMINI.md` rules    | `.kiro/settings` + hooks                | Different configuration approach                            |

### Converting a Skill to a Power

```bash
# Example: Convert webcrawler skill to Kiro Power
mkdir power-webcrawler
cp skills/webcrawler/SKILL.md power-webcrawler/POWER.md
# Edit POWER.md frontmatter:
#   Add: keywords: ["scrape", "crawl", "website", "docs", "harvest"]
#   Add: displayName: "Web Crawler"
# Move references/ → steering/
cp -r skills/webcrawler/references/ power-webcrawler/steering/ 2>/dev/null
# If skill uses MCP, create mcp.json
```

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
→ Services: [GitHub, Linear, etc.]
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

| Feature                 | Claude Code          | Gemini         | Opencode       | Kiro                        |
| ----------------------- | -------------------- | -------------- | -------------- | --------------------------- |
| **Plugins/Marketplace** | ✅ `/plugin`         | ❌             | ❌             | ✅ Powers panel             |
| **Skills/Powers**       | ✅ `.claude/skills/` | ✅ `skills/`   | ✅ `skills/`   | ✅ `POWER.md`               |
| **Subagents**           | ✅ `.claude/agents/` | ⚠️ Personas    | ⚠️ Personas    | ✅ Agents                   |
| **Agent Teams**         | ✅ Experimental      | ❌             | ❌             | ✅ Autonomous Agent (async) |
| **MCP Servers**         | ✅ Native            | ✅ Via config  | ✅ Via config  | ✅ Dynamic via Powers       |
| **Dynamic MCP Loading** | ❌ All upfront       | ❌ All upfront | ❌ All upfront | ✅ On-demand per Power      |
| **LSP Integration**     | ✅ Plugins           | ❌             | ❌             | ✅ Native                   |
| **Hooks**               | ✅ Native            | ❌             | ❌             | ✅ `.kiro/hooks/`           |
| **Persistent Memory**   | ✅ Agent memory      | ⚠️ KI system   | ⚠️ Limited     | ✅ Cross-task learning      |
| **Cross-Repo Tasks**    | ❌                   | ❌             | ❌             | ✅ Autonomous Agent         |

---

## Best Practices

1. **Detect first, recommend second** — Always detect platform before suggesting extensions
2. **Project-aware recommendations** — Recommend based on the actual tech stack, not generic lists
3. **Don't over-install** — Recommend only what's relevant to the current project
4. **Respect scopes** — Use project scope for team tools, user scope for personal preferences
5. **Proactive but not pushy** — Suggest once per session, don't repeat
6. **Cross-platform awareness** — When a skill exists as both Antigravity SKILL.md and Kiro POWER.md, use the native format for the detected platform

## AGI Framework Integration

### Qdrant Memory Integration

Before executing complex tasks with this skill:
```bash
python3 execution/memory_manager.py auto --query "<task summary>"
```

**Decision Tree:**
- **Cache hit?** Use cached response directly — no need to re-process.
- **Memory match?** Inject `context_chunks` into your reasoning.
- **No match?** Proceed normally, then store results:

```bash
python3 execution/memory_manager.py store \
  --content "Description of what was decided/solved" \
  --type decision \
  --tags plugin-discovery <relevant-tags>
```

> **Note:** Storing automatically updates both Vector (Qdrant) and Keyword (BM25) indices.

### Agent Team Collaboration

- **Strategy**: This skill communicates via the shared memory system.
- **Orchestration**: Invoked by `orchestrator` via intelligent routing.
- **Context Sharing**: Always read previous agent outputs from memory before starting.

### Local LLM Support

When available, use local Ollama models for embedding and lightweight inference:
- Embeddings: `nomic-embed-text` via Qdrant memory system
- Lightweight analysis: Local models reduce API costs for repetitive patterns
