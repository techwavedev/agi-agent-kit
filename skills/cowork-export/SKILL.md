---
name: cowork-export
description: "Export current session context as a portable briefing document for Claude on claude.ai (Cowork). Use when the user wants to delegate tasks to Claude web, schedule work in Cowork, or hand off context to a remote Claude instance. Triggers on: 'export to cowork', 'cowork briefing', 'send to claude.ai', 'schedule in cowork', 'remote agent context'."
---

# Cowork Export Skill

Packages your local session context (git state, Qdrant memory, decisions, code changes) into a clipboard-ready briefing document that Claude on claude.ai can consume as a remote sub-agent.

## Quick Start

```bash
# Full export: git state + Qdrant memory + task brief
python3 skills/cowork-export/scripts/export_context.py \
  --project <project-name> \
  --task "What the remote agent should do" \
  --output .tmp/cowork_briefing.md

# Minimal: git state only (no Qdrant dependency)
python3 skills/cowork-export/scripts/export_context.py \
  --git-only \
  --task "Review these changes and suggest improvements" \
  --output .tmp/cowork_briefing.md

# Include specific files as inline context
python3 skills/cowork-export/scripts/export_context.py \
  --project agi-agent-kit \
  --task "Refactor this module for clarity" \
  --include-files execution/memory_manager.py execution/session_boot.py \
  --output .tmp/cowork_briefing.md

# Copy to clipboard directly (macOS)
python3 skills/cowork-export/scripts/export_context.py \
  --project agi-agent-kit \
  --task "Write tests for the new feature" \
  --clipboard
```

## How It Works

```
┌─────────────────────────────────────────────┐
│  1. Gather Context                          │
│     ├─ git branch, diff, recent commits     │
│     ├─ Qdrant: recent decisions & learnings │
│     └─ Specified files (inline snippets)    │
│                                             │
│  2. Build Briefing Document                 │
│     ├─ Project summary                      │
│     ├─ Current state (what was done)        │
│     ├─ Task assignment (what to do next)    │
│     └─ Constraints & guidelines             │
│                                             │
│  3. Export                                  │
│     ├─ .tmp/cowork_briefing.md (file)       │
│     ├─ --clipboard (macOS pbcopy)           │
│     └─ stdout (pipe-friendly)               │
└─────────────────────────────────────────────┘
```

## Output Sections

The exported briefing contains:

| Section | Content | Source |
|---------|---------|--------|
| **Project Context** | Repo name, branch, description | git remote + branch |
| **Recent Work** | Last 5 commits + changed files | git log + git diff --stat |
| **Decisions & Learnings** | Key context from session | Qdrant memory |
| **Code Context** | Inline file contents | `--include-files` |
| **Task Assignment** | What the remote agent should do | `--task` flag |
| **Constraints** | Guidelines, style, boundaries | `--constraints` flag |

## Agent Protocol

When the user asks to export context to Cowork:

1. **Ask what task** the remote agent should perform (if not specified)
2. **Ask which files** to include inline (if the task requires code context)
3. **Run the export script** with appropriate flags
4. **Read the output file** to verify it looks correct
5. **Copy to clipboard** or show the user where the file is

When the user says "schedule" or "delegate" — add time-awareness:

```bash
python3 skills/cowork-export/scripts/export_context.py \
  --project myapp \
  --task "Run the full test suite and report failures" \
  --deadline "2026-03-23" \
  --priority high \
  --output .tmp/cowork_briefing.md
```

## Project Bootstrap Pattern

When the user wants Cowork to create a **full new project** (not just review existing code):

1. **Ask for project specs** — Name, purpose, tech stack, automation goals
2. **Export a bootstrap briefing** with framework structure embedded:

```bash
python3 skills/cowork-export/scripts/export_context.py \
  --project new-project-name \
  --task "Create a complete Python automation project with these specifications: [specs]. Use the AGI Agent Kit structure: directives/ for SOPs, execution/ for scripts, skills/ for modular capabilities. Include a CLAUDE.md with agent instructions, a session_boot.py, and a memory_manager.py integration." \
  --include-files CLAUDE.md execution/session_boot.py \
  --constraints "Follow the 3-layer architecture: directives (intent), orchestration (agent), execution (scripts). All scripts must accept CLI args and return JSON." \
  --priority high \
  --clipboard
```

3. **Paste into Cowork** (claude.ai or Desktop) → Cowork builds the full project
4. **Pull results back** → Copy from Cowork's folder into your repo
5. **Record the handoff** so local agents know

### Full Project Ideas via Cowork

Common automation projects to delegate:
- Email automation pipeline (Gmail MCP → classify → respond/archive)
- Competitor monitoring dashboard (scrape → compare → HTML report)
- Social media content scheduler (draft → review → post via API)
- Data pipeline (ingest → transform → export to Google Sheets)
- Internal tool (Slack bot → process requests → update database)

## Cross-Agent Integration

After exporting, store a handoff record so local agents know work was delegated:

```bash
python3 execution/cross_agent_context.py handoff \
  --from "claude" --to "cowork" \
  --task "<task description>" \
  --project <project-name>
```

## Flags Reference

| Flag | Description | Default |
|------|-------------|---------|
| `--project` | Project name for Qdrant query | auto-detect from git |
| `--task` | Task assignment for remote agent | required |
| `--output` | Output file path | stdout |
| `--clipboard` | Copy to macOS clipboard | false |
| `--git-only` | Skip Qdrant, git context only | false |
| `--include-files` | Files to embed inline | none |
| `--since` | Qdrant lookback in minutes | 120 |
| `--max-memory` | Max Qdrant chunks to include | 10 |
| `--deadline` | Deadline for the task | none |
| `--priority` | Priority level (low/medium/high) | medium |
| `--constraints` | Additional constraints text | none |
| `--compact` | Shorter output, less verbose | false |
