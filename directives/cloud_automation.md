# Cloud Automation Directive

## Goal

Enable the AGI Agent Kit to integrate with Claude's cloud-native features: **Cowork** (desktop VM agent), **Cloud Tasks** (24/7 scheduled runs), **Channels** (Telegram/Discord remote control), and **Scheduled Tasks** (local cron). This provides full automation without human interaction after one-time setup.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   Automation Tiers                       │
├──────────────┬──────────────┬──────────────┬────────────┤
│ Local Agent  │ Cowork       │ Cloud Tasks  │ Channels   │
│ (CLI/IDE)    │ (Desktop VM) │ (24/7 cloud) │ (Telegram) │
├──────────────┼──────────────┼──────────────┼────────────┤
│ You control  │ Runs skills  │ Runs on      │ Remote     │
│ the terminal │ in isolated  │ Anthropic    │ trigger    │
│              │ VM, reads    │ servers,     │ via phone  │
│              │ local files  │ never fails  │ to desktop │
├──────────────┼──────────────┼──────────────┼────────────┤
│ Worktrees +  │ Dispatch via │ Setup via    │ /plugin    │
│ Qdrant       │ mobile app   │ claude.ai    │ install    │
│ memory       │ or schedule  │ /code web UI │ telegram   │
└──────────────┴──────────────┴──────────────┴────────────┘
         ↕ All tiers share Qdrant memory ↕
```

## Tier 1: Local Agent Automation

What the framework already provides. Run in terminal, fully autonomous.

```bash
# Autonomous loop (runs every 10 minutes, expires after 3 days)
/loop 10m Check for new PRs on main branch and review them

# Scheduled local task (daily/weekly via Claude desktop app)
# Created via: Claude Desktop → Scheduled tab → New Task
```

**Integration:** Use `execution/worktree_isolator.py` for parallel agent isolation. Use `execution/dispatch_agent_team.py --parallel` for team dispatch.

## Tier 2: Cowork (Desktop VM Agent)

Cowork runs skills in an isolated VM on your desktop. It can read/write local files, connect to Gmail/Slack/Calendar via MCP connectors.

### Export context to Cowork

```bash
# Full export: git + Qdrant memory + files
python3 skills/cowork-export/scripts/export_context.py \
  --project agi-agent-kit \
  --task "Implement the new feature described in the briefing" \
  --include-files execution/worktree_isolator.py \
  --clipboard

# Project bootstrap: export full project scaffold for Cowork to build
python3 skills/cowork-export/scripts/export_context.py \
  --project new-automation-project \
  --task "Create a full Python automation project with these specs: [description]" \
  --include-files CLAUDE.md execution/session_boot.py \
  --constraints "Use the AGI Agent Kit structure: directives/, execution/, skills/" \
  --clipboard
```

### Cowork Scheduled Tasks

Set up via Claude Desktop app:
1. Open Claude Desktop → Scheduled tab → New Task
2. Name: "Daily framework check"
3. Prompt: "Run session_boot.py, check for pending handoffs, process any automated tasks"
4. Frequency: Daily at 7:00 AM
5. Model: Claude Sonnet (cost-effective for routine work)

### Cowork Dispatch (Mobile → Desktop)

Trigger from your phone while away:
1. Open Claude mobile app → Dispatch button
2. Type command matching an installed skill (e.g., "review inbox", "scan receipts")
3. Cowork runs on your desktop, saves results locally
4. You get a summary on your phone

### Handoff tracking

After exporting to Cowork, record the handoff:

```bash
python3 execution/cross_agent_context.py handoff \
  --from "claude" --to "cowork" \
  --task "Implement auth module" \
  --project agi-agent-kit
```

## Tier 3: Cloud Tasks (24/7 Reliability)

Run on Anthropic servers. Never fail. Setup via `claude.ai/code` web UI only.

### When to use Cloud Tasks vs. Local

| Scenario | Use |
|----------|-----|
| Critical daily checks (security scans, deploys) | Cloud Tasks |
| Quick local file operations | Local Scheduled |
| Needs local file access | Cowork Scheduled |
| Must run even if laptop is closed | Cloud Tasks |
| Needs GPU/heavy processing | Cloud Tasks |

### Setup (one-time, manual via web UI)

1. Navigate to `claude.ai/code` → Scheduled Tasks
2. Select repository, frequency, connectors
3. Paste detailed prompt with skill instructions
4. Create task

### Framework integration

Cloud Tasks results can be pushed to Qdrant via webhook or manual sync:

```bash
# After Cloud Task completes, store result
python3 execution/memory_manager.py store \
  --content "Cloud Task result: [summary]" \
  --type decision \
  --project agi-agent-kit \
  --tags cloud-task automated
```

## Tier 4: Channels (Telegram/Discord Remote Control)

Control your local Claude Code instance from your phone via Telegram bot.

### One-time setup

```bash
# 1. Install telegram plugin
/plugin install telegram

# 2. Create bot via @BotFather on Telegram → /newbot → get token

# 3. Configure token
/telegram configure <bot_token>

# 4. Reload plugins
/reload plugins

# 5. Get your Telegram user ID from @userinfobot
/telegram access allow <your_user_id>

# 6. Prevent Mac sleep (keep channel alive)
caffeinate -d  # in separate terminal
```

### Remote usage

Text your Telegram bot: "Create a new directive for email automation"
Claude Code executes locally and responds via Telegram.

## Full Automation Patterns

### Pattern 1: Hands-Free Development Cycle

```
Cloud Task (daily 2am) → Run tests, security scan → Push results to Qdrant
  ↓ (morning)
Cowork Scheduled (7am) → Read Qdrant → Generate daily briefing
  ↓ (on-demand)
Local Agent → Read briefing → Implement fixes with worktree isolation
  ↓ (after implementation)
Cowork Export → Delegate code review to Cowork web instance
```

### Pattern 2: Mobile-First Automation

```
You (phone) → Dispatch to Cowork → "Scan inbox, draft responses"
Cowork (desktop) → Reads Gmail via MCP → Drafts in local folder
Cowork (desktop) → Stores decisions in Qdrant
Next session → Local agent reads Qdrant → Continues work
```

### Pattern 3: Project Bootstrap via Cowork

```
Local Agent → Export project spec + CLAUDE.md template → Clipboard
You → Paste into claude.ai Cowork → "Build this project"
Cowork → Creates full project structure in its VM folder
You → Copy project to your repo → Local agent takes over
```

## Edge Cases

- **Cowork VM not running**: Dispatch fails silently. Check Claude Desktop is open.
- **Cloud Task repo access**: Must grant GitHub access via claude.ai settings.
- **Telegram bot offline**: Terminal must stay open. Use `caffeinate -d`.
- **Qdrant unreachable from Cowork**: Cowork works local-only; sync context manually.
- **Rate limits**: Cloud Tasks share your plan's rate limit (Pro/Max).
