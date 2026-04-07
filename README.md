# 🚀 AGI Agent Kit

🌐 _[Português (BR)](./README.pt-BR.md)_ | English

> **Stop hallucinating. Start executing.**

[![npm version](https://img.shields.io/npm/v/@techwavedev/agi-agent-kit.svg)](https://www.npmjs.com/package/@techwavedev/agi-agent-kit)
[![npm downloads](https://img.shields.io/npm/dw/@techwavedev/agi-agent-kit.svg)](https://www.npmjs.com/package/@techwavedev/agi-agent-kit)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-Anthropic-purple)](https://claude.ai)
[![Gemini CLI](https://img.shields.io/badge/Gemini%20CLI-Google-blue)](https://github.com/google-gemini/gemini-cli)
[![Codex CLI](https://img.shields.io/badge/Codex%20CLI-OpenAI-green)](https://github.com/openai/codex)
[![Cursor](https://img.shields.io/badge/Cursor-AI%20IDE-orange)](https://cursor.sh)
[![GitHub Copilot](https://img.shields.io/badge/GitHub%20Copilot-VSCode-lightblue)](https://github.com/features/copilot)
[![OpenCode](https://img.shields.io/badge/OpenCode-CLI-gray)](https://github.com/opencode-ai/opencode)
[![Antigravity IDE](https://img.shields.io/badge/Antigravity-DeepMind-red)](https://github.com/techwavedev/agi-agent-kit)
[![AdaL CLI](https://img.shields.io/badge/AdaL%20CLI-SylphAI-pink)](https://sylph.ai/)
[![OpenClaw](https://img.shields.io/badge/OpenClaw-CLI-teal)](https://github.com/openclaw/openclaw)
[![Kiro](https://img.shields.io/badge/Kiro-AWS-yellow)](https://kiro.dev)
[![MCP Compatible](https://img.shields.io/badge/MCP-Compatible-blueviolet)](https://modelcontextprotocol.io)
[![Buy me a coffee](https://img.shields.io/badge/Buy%20me%20a-coffee-d13610?logo=buymeacoffee&logoColor=white)](https://www.buymeacoffee.com/eltonmachado)

**AGI Agent Kit** is the enterprise-grade scaffolding that turns any AI coding assistant into a **deterministic production machine**. While LLMs are probabilistic (90% accuracy per step = 59% over 5 steps), this framework forces them through a **3-Layer Architecture** — Intent → Orchestration → Execution — where business logic lives in tested scripts, not hallucinated code.

## Why this exists

Most AI coding setups give you a prompt and hope for the best. AGI Agent Kit gives you:

- 🧠 **Hybrid Memory** — Qdrant vectors + BM25 keywords: semantic similarity for concepts, exact matching for error codes and IDs (90-100% token savings)
- 🎯 **19 Specialist Agents** — Domain-bounded experts (Frontend, Backend, Security, Mobile, Game Dev...) with enforced file ownership
- ⚡ **1,191 Curated Skills** — 4 core + 89 professional + 1,098 community skills across 16 domain categories
- 🔒 **Verification Gates** — No task completes without evidence. TDD enforcement. Two-stage code review.
- 🌐 **10 Platforms, One Config** — Write once, run on Claude Code, Gemini CLI, Codex CLI, Cursor, Copilot, OpenCode, AdaL CLI, Antigravity IDE, OpenClaw, Kiro
- 🔌 **MCP Compatible** — Exposes memory + cross-agent coordination as MCP tools for Claude Desktop and any chat-interface client

```bash
npx @techwavedev/agi-agent-kit init
```

If this project helps you, consider [supporting it here](https://www.buymeacoffee.com/eltonmachado) or simply ⭐ the repo.

---

## 🚀 Quick Start

Scaffold a new agent workspace in seconds:

```bash
npx @techwavedev/agi-agent-kit init

# Or install globally to ~/.agent to share skills across projects
npx @techwavedev/agi-agent-kit init --global
```

You'll be guided through an interactive wizard:

1. **Existing install check** — detects a prior install and offers Update / Reinstall / Cancel
2. **Install scope** — project-local (current dir) or global (`~/.agent` shared across projects)
3. **Smart backup** — scans files at risk and creates a timestamped backup before touching anything
4. **Pack selection** — choose skills to install:
   - **core** — 4 essential skills (webcrawler, pdf-reader, qdrant-memory, documentation)
   - **medium** — Core + 89 professional skills in 16 categories + `.agent/` structure
   - **full** — Everything: Medium + 1,098 community skills (1,191 total)
   - **custom** — Core + you pick specific domains (AI Agents, DevOps, Security, Frontend, etc.)
5. **Memory setup** — detects Ollama/Docker/Qdrant; if missing, asks whether to install locally or use a custom URL (supports Qdrant Cloud, remote servers)
6. **Agent Teams** — opt-in to parallel multi-agent execution (writes `.claude/settings.json`)
7. **Summary** — shows exactly what was configured vs what needs manual action

After installation the wizard shows your next steps, including:

```bash
# Boot the memory system (verifies Qdrant + Ollama, auto-fixes issues)
python3 execution/session_boot.py --auto-fix

# Run the platform setup wizard (auto-configures your AI platform)
python3 skills/plugin-discovery/scripts/platform_setup.py --project-dir .
```

---

## ✨ Key Features

| Feature                       | Description                                                                                   |
| ----------------------------- | --------------------------------------------------------------------------------------------- |
| **Deterministic Execution**   | Separates business logic (Python scripts) from AI reasoning (Directives)                      |
| **Modular Skill System**      | 1,191+ plug-and-play skills across 3 tiers, organized in 16 domain categories                 |
| **Memory Mode Tiers**         | Solo → Team → Pro: start simple, add multi-tenancy and auth as needed — no data migration     |
| **Distributed Agent Auth**    | HMAC-SHA256 signing, hash anchoring, project access control via shared Qdrant (Hyperledger Aries optional) |
| **Real-Time Agent Events**    | Apache Pulsar event bus for push notifications between agents — graceful degradation if unavailable |
| **Hybrid Memory**             | Qdrant vectors + BM25 keywords with weighted score merge (95% token savings)                  |
| **Platform-Adaptive**         | Auto-detects Claude Code, Gemini CLI, Codex CLI, Cursor, Copilot, OpenCode, AdaL, Antigravity, Kiro |
| **MCP Compatible**            | Memory + cross-agent coordination exposed as MCP tools (`execution/mcp_server.py`) for Claude Desktop and any MCP client |
| **Multi-Agent Orchestration** | Agent Teams, subagents, Powers, or sequential personas — adapts to platform                   |
| **Structured Plan Execution** | Batch or subagent-driven execution with two-stage review (spec + quality)                     |
| **TDD Enforcement**           | Iron-law RED-GREEN-REFACTOR cycle — no production code without failing test                   |
| **Verification Gates**        | Evidence before claims — no completion without fresh verification output                      |
| **Self-Healing Workflows**    | Agents read error logs, patch scripts, and update directives automatically                    |
| **Skill Self-Improvement**    | Karpathy Loop: autonomous test → improve → commit/reset cycle with 18 binary assertion types  |
| **One-Shot Setup**            | Platform detection + project stack scan + auto-configuration in one command                   |

---

## 🆚 How This Compares to Superpowers

The agi framework adopts all best patterns from [obra/superpowers](https://github.com/obra/superpowers) and extends them with capabilities superpowers does not have:

| Capability                   | obra/superpowers |         agi Framework          |
| ---------------------------- | :--------------: | :----------------------------: |
| TDD Enforcement              |        ✅        |           ✅ Adapted           |
| Plan Execution + Review      |        ✅        | ✅ Adapted + platform-adaptive |
| Systematic Debugging         |        ✅        | ✅ Adapted + `debugger` agent  |
| Verification Gates           |        ✅        | ✅ Adapted + 12 audit scripts  |
| Two-Stage Code Review        |        ✅        |  ✅ Adapted into orchestrator  |
| Multi-Platform Orchestration |  ❌ Claude only  |         ✅ 10 platforms        |
| Semantic Memory (Qdrant)     |        ❌        |    ✅ 90-100% token savings    |
| 19 Specialist Agents         |        ❌        |      ✅ Domain boundaries      |
| Agent Boundary Enforcement   |        ❌        |     ✅ File-type ownership     |
| Dynamic Question Generation  |        ❌        |   ✅ Trade-offs + priorities   |
| Memory-First Protocol        |        ❌        |       ✅ Auto cache-hit        |
| Skill Creator + Catalog      |        ❌        |  ✅ 1,191 composable skills   |
| Platform Setup Wizard        |        ❌        |       ✅ One-shot config       |
| Multi-Platform Symlinks      |  ❌ Claude only  |        ✅ 10 platforms         |
| MCP Server                   |        ❌        |   ✅ Memory + coordination     |

---

## 🆚 How This Compares to MemPalace

While traditional AI memory systems like MemPalace introduce clever textual compression techniques, they hit a fundamental scalability paradigm limit by treating memory like a localized SQLite filing cabinet. The **AGI Agent Kit** takes those theoretical leaps and deploys them onto an enterprise-grade infrastructure.

| Capability                     | MemPalace (SQLite/Chroma)                      | AGI Swarm (Qdrant + BM25)                                 |
| ------------------------------ | ---------------------------------------------- | --------------------------------------------------------- |
| **Data Architecture**          | Strict Relational Graph (SQLite)               | Distributed Hybrid Vector Cloud (Qdrant)                  |
| **Zero-Loss Compression**      | Requires secondary filesystem lookup ("Drawer")| Invisible JSON Payload ("Drawer" inside vector metadata)  |
| **Time-Stamped Self-Healing**  | Manual hard-coded invalidations                | Native Qdrant Range Filters (`valid_until < NOW()`)       |
| **Contradiction Resolution**   | Halts process, begs user                       | AI Ledger pre-store resolution via local LLM router       |
| **Scale Limits**               | Local-only, single MCP server                  | Massive, Cross-Agent Multi-LLM Orchestration              |

---

## 🧪 Real Benchmark: Subagents vs Agent Teams

The framework supports two orchestration modes. Here are **real test results** from `execution/benchmark_modes.py` running on local infrastructure (Qdrant + Ollama `nomic-embed-text`, zero cloud API calls):

```text
MODE A: SUBAGENTS — Independent, fire-and-forget
  📤 Explore Auth Patterns    → ✅ stored in cache + memory (127ms)
  📤 Query Performance        → ❌ FAILED (timeout — fault tolerant)
  📤 Scan CVEs                → ✅ stored in cache + memory (14ms)
  Summary: 2/3 completed, 1 failed, 0 cross-references

MODE B: AGENT TEAMS — Shared context, coordinated
  👤 Backend Specialist       → ✅ stored in shared memory (14ms)
  👤 Database Specialist      → ✅ stored in shared memory (13ms)
  👤 Frontend Specialist      → 🔗 Read Backend + Database output first
     ✅ Got context from team-backend: "API contract: POST /api/messages..."
     ✅ Got context from team-database: "Schema: users(id UUID PK, name..."
     → ✅ stored in shared memory (14ms)
  Summary: 3/3 completed, 0 failed, 2 cross-references
```

**2nd run (cache warm):** All queries hit cache at **score 1.000**, reducing total time from 314ms → 76ms (Subagents) and 292ms → 130ms (Agent Teams).

| Metric               | Subagents                            | Agent Teams                          |
| -------------------- | ------------------------------------ | ------------------------------------ |
| Execution model      | Fire-and-forget (isolated)           | Shared context (coordinated)         |
| Tasks completed      | 2/3 (fault tolerant)                 | 3/3                                  |
| Cross-references     | 0 (not supported)                    | 2 (peers read each other's work)     |
| Context sharing      | ❌ Each agent isolated               | ✅ Peer-to-peer via Qdrant           |
| Two-stage review     | ❌                                   | ✅ Spec + Quality                    |
| Cache hits (2nd run) | 5/5                                  | 5/5                                  |
| Embedding provider   | Ollama local (nomic-embed-text 137M) | Ollama local (nomic-embed-text 137M) |

**Try it yourself:**

```bash
# 1. Start infrastructure
docker run -d -p 6333:6333 -v qdrant_storage:/qdrant/storage qdrant/qdrant
ollama serve & ollama pull nomic-embed-text

# 2. Boot memory system
python3 execution/session_boot.py --auto-fix
# ✅ Memory system ready — 5 memories, 1 cached responses

# 3. Run the full benchmark (both modes)
python3 execution/benchmark_modes.py --verbose

# 4. Or test individual operations:

# Store a decision (embedding generated locally via Ollama)
python3 execution/memory_manager.py store \
  --content "Chose PostgreSQL for relational data" \
  --type decision --project myapp
# → {"status": "stored", "point_id": "...", "token_count": 5}

# Auto-query: checks cache first, then retrieves context
python3 execution/memory_manager.py auto \
  --query "what database did we choose?"
# → {"source": "memory", "cache_hit": false, "context_chunks": [...]}

# Cache an LLM response for future reuse
python3 execution/memory_manager.py cache-store \
  --query "how to set up auth?" \
  --response "Use JWT with 24h expiry, refresh tokens in httpOnly cookies"

# Re-query → instant cache hit (score 1.000, zero re-computation)
python3 execution/memory_manager.py auto \
  --query "how to set up auth?"
# → {"source": "cache", "cache_hit": true, "tokens_saved_estimate": 12}
```

## 🌐 Platform Support

The framework automatically detects your AI coding environment and activates the best available features.

Skills are installed to the canonical `skills/` directory and symlinked to each platform's expected path:

| Platform            | Skills Path       | Instruction File | Orchestration Strategy              |
| ------------------- | ----------------- | ---------------- | ----------------------------------- |
| **Claude Code**     | `.claude/skills/` | `CLAUDE.md`      | Agent Teams (parallel) or Subagents |
| **Gemini CLI**      | `.gemini/skills/` | `GEMINI.md`      | Sequential personas via `@agent`    |
| **Codex CLI**       | `.codex/skills/`  | `AGENTS.md`      | Sequential via prompts              |
| **Antigravity IDE** | `.agent/skills/`  | `AGENTS.md`      | Full agentic orchestration          |
| **Cursor**          | `.cursor/skills/` | `AGENTS.md`      | Chat-based via `@skill`             |
| **GitHub Copilot**  | N/A (paste)       | `COPILOT.md`     | Manual paste into context           |
| **OpenCode**        | `.agent/skills/`  | `OPENCODE.md`    | Sequential personas via `@agent`    |
| **AdaL CLI**        | `.adal/skills/`   | `AGENTS.md`      | Auto-load on demand                 |
| **Kiro (AWS)**      | `.kiro/skills/`   | `.kiro/steering/agents.md` | Full agentic orchestration   |

Run `/setup` to auto-detect and configure your platform, or use the setup script directly:

```bash
# Interactive (one Y/n question)
python3 skills/plugin-discovery/scripts/platform_setup.py --project-dir .

# Auto-apply everything
python3 skills/plugin-discovery/scripts/platform_setup.py --project-dir . --auto

# Preview without changes
python3 skills/plugin-discovery/scripts/platform_setup.py --project-dir . --dry-run
```

---

## 📦 What You Get

```text
your-project/
├── AGENTS.md              # Master instruction file
├── GEMINI.md → AGENTS.md  # Platform symlinks
├── CLAUDE.md → AGENTS.md
├── OPENCODE.md → AGENTS.md
├── COPILOT.md → AGENTS.md
├── skills/                # Up to 1,191 skills (depends on pack)
│   ├── webcrawler/        # Documentation harvesting
│   ├── qdrant-memory/     # Semantic caching & memory
│   └── ...                # 877 more skills in full pack
├── .claude/skills → skills/   # Platform-specific symlinks
├── .gemini/skills → skills/
├── .codex/skills → skills/
├── .cursor/skills → skills/
├── .adal/skills → skills/
├── directives/            # SOPs in Markdown
├── execution/             # Deterministic Python scripts
│   ├── session_boot.py    # Session startup (Qdrant + Ollama check)
│   └── memory_manager.py  # Store/retrieve/cache operations
├── skill-creator/         # Tools to create new skills
└── .agent/                # (medium/full) Agents, workflows, rules
    └── workflows/         # /setup, /deploy, /test, /debug, etc.
```

---

## 📖 Architecture

The system operates on three layers:

```text
┌─────────────────────────────────────────────────────────┐
│  Layer 1: DIRECTIVES (Intent)                           │
│  └─ SOPs written in Markdown (directives/)              │
├─────────────────────────────────────────────────────────┤
│  Layer 2: ORCHESTRATION (Agent)                         │
│  └─ LLM reads directive, decides which tool to call     │
│  └─ Platform-adaptive: Teams, Subagents, or Personas    │
├─────────────────────────────────────────────────────────┤
│  Layer 3: EXECUTION (Code)                              │
│  └─ Pure Python scripts (execution/) do the actual work │
└─────────────────────────────────────────────────────────┘
```

**Why?** LLMs are probabilistic. 90% accuracy per step = 59% success over 5 steps. By pushing complexity into deterministic scripts, we achieve reliable execution.

---

## 🔐 Distributed Agent System

The framework supports fully distributed agent deployments where multiple agents across different machines share context, authenticate writes, and receive real-time notifications — all through the shared Qdrant instance.

### Memory Mode Tiers

Set `MEMORY_MODE` in `.env` to choose your tier. All modes are backward-compatible — upgrade anytime without data migration.

| Mode | Use Case | Infrastructure | Key Feature |
|---|---|---|---|
| **Solo** | Single developer, one agent | Ollama + Qdrant | Full hybrid search, semantic cache |
| **Team** | Multiple agents sharing context | Same as Solo | Developer isolation + shared memories (`--shared`) |
| **Pro** | Enterprise / high-trust | Same + optional Aries | Signed writes, hash anchoring, access control, audit trail |

```bash
# Solo: just works
MEMORY_MODE=solo python3 execution/session_boot.py --auto-fix

# Team: agents share context, each has private + shared memories
MEMORY_MODE=team python3 execution/memory_manager.py store \
  --content "Use Redis for session cache" --type decision --project myapp --shared

# Pro: signed writes with tamper detection and access control
MEMORY_MODE=pro python3 execution/blockchain_auth.py init
python3 execution/blockchain_auth.py register --entity-type developer --entity-id you@co.com
python3 execution/blockchain_auth.py grant --entity-id you@co.com --project myapp --permissions read,write
python3 execution/memory_manager.py store --content "Decision" --type decision --project myapp --auth
# → {"status": "stored", "signature": "...", "blockchain_anchor": {"status": "anchored"}, "event": {"status": "published"}}
```

### Blockchain Authentication (Pro Mode)

Pro mode adds cryptographic verification to every write:

- **HMAC-SHA256 signing** — every memory gets a signature at write-time
- **Hash anchoring** — content hash stored in Qdrant `agent_auth` collection for tamper detection
- **Project access control** — grant read/write per entity per project
- **Audit trail** — who wrote what, when, with verification status
- **W3C DID identity** (optional) — via Hyperledger Aries ACA-Py 1.5.0 (Apache 2.0)

All auth data is stored in the shared Qdrant instance — no separate database needed. See [docs/blockchain-auth.md](./docs/blockchain-auth.md).

### Real-Time Agent Events (Apache Pulsar)

Optional add-on for team/pro modes. Without Pulsar, agents poll Qdrant on each query (~10ms). With Pulsar, events are pushed instantly.

```bash
# Start Pulsar (single container, ~256MB heap)
docker compose -f docker-compose.pulsar.yml up -d
pip install pulsar-client

# Events auto-publish on memory store
python3 execution/memory_manager.py store \
  --content "Switched to PostgreSQL" --type decision --project myapp
# → "event": {"status": "published", "topic": "persistent://agi/memory/myapp"}
```

If Pulsar is down, events are silently dropped — Qdrant stores always succeed. See [docs/agent-events.md](./docs/agent-events.md).

### Architecture (Distributed)

```text
┌─ Machine 1 ──────────────────┐    ┌─ Machine 2 ──────────────────┐
│  Agent A (Claude)            │    │  Agent B (Gemini)            │
│  └─ memory_manager.py        │    │  └─ memory_manager.py        │
│     ├─ Qdrant (shared) ──────┼────┼─── Qdrant (shared)          │
│     ├─ BM25 (auto-synced) ◄──┼────┼─── BM25 (auto-synced)       │
│     └─ Pulsar events ────────┼────┼──► Pulsar events             │
└──────────────────────────────┘    └──────────────────────────────┘
```

Every component is sourced from the shared Qdrant:
- **Memories & cache** — Qdrant `agent_memory` + `semantic_cache`
- **Auth data** — Qdrant `agent_auth` (pro mode)
- **BM25 keyword index** — local SQLite, auto-rebuilt from Qdrant on each `session_boot`
- **Events** — Apache Pulsar (optional, graceful degradation)

For full details: [docs/memory-modes.md](./docs/memory-modes.md) · [docs/blockchain-auth.md](./docs/blockchain-auth.md) · [docs/agent-events.md](./docs/agent-events.md)

---

## 🧠 Hybrid Memory (BM25 + Vector)

Dual-engine retrieval: Qdrant vector similarity for semantic concepts + SQLite FTS5 BM25 for exact keyword matching. Automatically merges results with configurable weights.

| Scenario              | Without Memory | With Memory | Savings  |
| --------------------- | -------------- | ----------- | -------- |
| Repeated question     | ~2000 tokens   | 0 tokens    | **100%** |
| Similar architecture  | ~5000 tokens   | ~500 tokens | **90%**  |
| Past error resolution | ~3000 tokens   | ~300 tokens | **90%**  |
| Exact ID/code lookup  | ~3000 tokens   | ~200 tokens | **93%**  |

**Setup** (requires [Qdrant](https://qdrant.tech/) + [Ollama](https://ollama.com/)):

```bash
# Start Qdrant
docker run -d -p 6333:6333 -v qdrant_storage:/qdrant/storage qdrant/qdrant

# Start Ollama + pull embedding model
ollama serve &
ollama pull nomic-embed-text

# Boot memory system (auto-creates collections)
python3 execution/session_boot.py --auto-fix
```

Agents automatically run `session_boot.py` at session start (first instruction in `AGENTS.md`). Memory operations:

```bash
# Auto-query (check cache + retrieve context)
python3 execution/memory_manager.py auto --query "your task summary"

# Store a decision (auto-indexes into BM25)
python3 execution/memory_manager.py store --content "what was decided" --type decision

# Health check (includes BM25 index status)
python3 execution/memory_manager.py health

# Rebuild BM25 index from existing Qdrant data
python3 execution/memory_manager.py bm25-sync
```

**Hybrid search modes** (via `hybrid_search.py`):

```bash
# True hybrid (default): vector + BM25 merged
python3 skills/qdrant-memory/scripts/hybrid_search.py --query "ImagePullBackOff error" --mode hybrid

# Vector only (pure semantic)
python3 skills/qdrant-memory/scripts/hybrid_search.py --query "database architecture" --mode vector

# Keyword only (exact BM25 match)
python3 skills/qdrant-memory/scripts/hybrid_search.py --query "sg-018f20ea63e82eeb5" --mode keyword
```

---

## ⚡ Prerequisites

The `npx init` command automatically creates a `.venv` and installs all dependencies. Just activate it:

```bash
source .venv/bin/activate   # macOS/Linux
# .venv\Scripts\activate    # Windows
```

If you need to reinstall or update dependencies:

```bash
.venv/bin/pip install -r requirements.txt
```

---

## 🔧 Commands

### Initialize a new project

```bash
npx @techwavedev/agi-agent-kit init --pack=full
# To install globally instead of per-project:
npx @techwavedev/agi-agent-kit init --pack=full --global
```

### Auto-detect platform and configure environment

```bash
python3 skills/plugin-discovery/scripts/platform_setup.py --project-dir .
```

### Update to latest version

```bash
npx @techwavedev/agi-agent-kit@latest init --pack=full
# or use the built-in skill:
python3 skills/self-update/scripts/update_kit.py
```

### Boot memory system

```bash
python3 execution/session_boot.py --auto-fix
```

### System health check

```bash
python3 execution/system_checkup.py --verbose
```

### Create a new skill

```bash
python3 skill-creator/scripts/init_skill.py my-skill --path skills/
```

### Update skills catalog

```bash
python3 skill-creator/scripts/update_catalog.py --skills-dir skills/
```

---

## 🎯 Activation Reference

Use these keywords, commands, and phrases to trigger specific capabilities:

### Slash Commands (Workflows)

| Command         | What It Does                                     |
| --------------- | ------------------------------------------------ |
| `/setup`        | Auto-detect platform and configure environment   |
| `/setup-memory` | Initialize Qdrant + Ollama memory system         |
| `/create`       | Start interactive app builder dialogue           |
| `/plan`         | Create a structured project plan (no code)       |
| `/enhance`      | Add or update features in existing app           |
| `/debug`        | Activate systematic debugging mode               |
| `/test`         | Generate and run tests                           |
| `/deploy`       | Pre-flight checks + deployment                   |
| `/orchestrate`  | Multi-agent coordination for complex tasks       |
| `/brainstorm`   | Structured brainstorming with multiple options   |
| `/preview`      | Start/stop local dev server                      |
| `/status`       | Show project progress and status board           |
| `/update`       | Update AGI Agent Kit to latest version           |
| `/checkup`      | Verify agents, workflows, skills, and core files |

### Agent Mentions (`@agent`)

| Mention                   | Specialist              | When To Use                                |
| ------------------------- | ----------------------- | ------------------------------------------ |
| `@orchestrator`           | Multi-agent coordinator | Complex multi-domain tasks                 |
| `@project-planner`        | Planning specialist     | Roadmaps, task breakdowns, phase planning  |
| `@frontend-specialist`    | UI/UX architect         | Web interfaces, React, Next.js             |
| `@backend-specialist`     | API/DB engineer         | Server-side, databases, APIs               |
| `@mobile-developer`       | Mobile specialist       | iOS, Android, React Native, Flutter        |
| `@security-auditor`       | Security expert         | Vulnerability scanning, audits, hardening  |
| `@debugger`               | Debug specialist        | Complex bug investigation                  |
| `@game-developer`         | Game dev specialist     | 2D/3D games, multiplayer, VR/AR            |
| `@devops-engineer`        | DevOps specialist       | CI/CD, containers, cloud infrastructure    |
| `@database-architect`     | Database specialist     | Schema design, migrations, optimization    |
| `@documentation-writer`   | Docs specialist         | Technical writing, API docs, READMEs       |
| `@test-engineer`          | Testing specialist      | Test strategy, automation, coverage        |
| `@qa-automation-engineer` | QA specialist           | E2E testing, regression, quality gates     |
| `@performance-optimizer`  | Performance specialist  | Profiling, bottlenecks, optimization       |
| `@seo-specialist`         | SEO specialist          | Search optimization, meta tags, rankings   |
| `@penetration-tester`     | Pen testing specialist  | Red team exercises, exploit verification   |
| `@product-manager`        | Product specialist      | Requirements, user stories, prioritization |
| `@code-archaeologist`     | Legacy code specialist  | Understanding old codebases, migrations    |
| `@explorer-agent`         | Discovery specialist    | Codebase exploration, dependency mapping   |

### Skill Trigger Keywords (Natural Language)

| Category           | Trigger Words / Phrases                                                | Skill Activated                       |
| ------------------ | ---------------------------------------------------------------------- | ------------------------------------- |
| **Memory**         | "don't use cache", "no cache", "skip memory", "fresh"                  | Memory opt-out                        |
| **Research**       | "research my docs", "check my notebooks", "deep search", "@notebooklm" | `notebooklm-rag`                      |
| **Documentation**  | "update docs", "regenerate catalog", "sync documentation"              | `documentation`                       |
| **Quality**        | "lint", "format", "check", "validate", "static analysis"               | `lint-and-validate`                   |
| **Testing**        | "write tests", "run tests", "TDD", "test coverage"                     | `testing-patterns` / `tdd-workflow`   |
| **TDD**            | "test first", "red green refactor", "failing test"                     | `test-driven-development`             |
| **Plan Execution** | "execute plan", "run the plan", "batch execution"                      | `executing-plans`                     |
| **Verification**   | "verify", "prove it works", "evidence", "show me the output"           | `verification-before-completion`      |
| **Debugging**      | "debug", "root cause", "investigate", "why is this failing"            | `systematic-debugging`                |
| **Architecture**   | "design system", "architecture decision", "ADR", "trade-off"           | `architecture`                        |
| **Security**       | "security scan", "vulnerability", "audit", "OWASP"                     | `red-team-tactics`                    |
| **Performance**    | "lighthouse", "bundle size", "core web vitals", "profiling"            | `performance-profiling`               |
| **Design**         | "design UI", "color scheme", "typography", "layout"                    | `frontend-design`                     |
| **Deployment**     | "deploy", "rollback", "release", "CI/CD"                               | `deployment-procedures`               |
| **API**            | "REST API", "GraphQL", "tRPC", "API design"                            | `api-patterns`                        |
| **Database**       | "schema design", "migration", "query optimization"                     | `database-design`                     |
| **Planning**       | "plan this", "break down", "task list", "requirements"                 | `plan-writing`                        |
| **Brainstorming**  | "explore options", "what are the approaches", "pros and cons"          | `brainstorming`                       |
| **Code Review**    | "review this", "code quality", "best practices"                        | `code-review-checklist`               |
| **i18n**           | "translate", "localization", "RTL", "locale"                           | `i18n-localization`                   |
| **AWS**            | "terraform", "EKS", "Lambda", "S3", "CloudFront"                       | `aws-skills` / `terraform-skill`      |
| **Infrastructure** | "service mesh", "Kubernetes", "Helm"                                   | `docker-expert` / `server-management` |

### Memory System Commands

| What You Want                | Command / Phrase                                                                 |
| ---------------------------- | -------------------------------------------------------------------------------- |
| **Boot memory**              | `python3 execution/session_boot.py --auto-fix`                                   |
| **Check before a task**      | `python3 execution/memory_manager.py auto --query "..."`                         |
| **Store a decision**         | `python3 execution/memory_manager.py store --content "..." --type decision`      |
| **Cache a response**         | `python3 execution/memory_manager.py cache-store --query "..." --response "..."` |
| **Health check**             | `python3 execution/memory_manager.py health`                                     |
| **Skip cache for this task** | Say "fresh", "no cache", or "skip memory" in your prompt                         |

---

## 📚 Documentation

- **[AGENTS.md](./AGENTS.md)** — Complete architecture and operating principles
- **[docs/memory-modes.md](./docs/memory-modes.md)** — Memory mode tiers (Solo / Team / Pro)
- **[docs/blockchain-auth.md](./docs/blockchain-auth.md)** — Distributed auth with Hyperledger Aries
- **[docs/agent-events.md](./docs/agent-events.md)** — Real-time events with Apache Pulsar
- **[skills/SKILLS_CATALOG.md](./skills/SKILLS_CATALOG.md)** — Skill catalog
- **[CHANGELOG.md](./CHANGELOG.md)** — Version history
- **[THIRD-PARTY-LICENSES.md](./THIRD-PARTY-LICENSES.md)** — Third-party attributions

---

## 🤝 Community Skills & Credits

The **Full** tier includes 774 community skills adapted from the [Antigravity Awesome Skills](https://github.com/sickn33/antigravity-awesome-skills) project (v5.4.0) by [@sickn33](https://github.com/sickn33), distributed under the MIT License.

This collection aggregates skills from 50+ open-source contributors and organizations including Anthropic, Microsoft, Vercel Labs, Supabase, Trail of Bits, Expo, Sentry, Neon, fal.ai, and many more. For the complete attribution ledger, see [SOURCES.md](https://github.com/sickn33/antigravity-awesome-skills/blob/main/docs/SOURCES.md).

Each community skill has been adapted for the AGI framework with:

- **Qdrant Memory Integration** — Semantic caching and context retrieval
- **Agent Team Collaboration** — Orchestrator-driven invocation and shared memory
- **Local LLM Support** — Ollama-based embeddings for local-first operation

If these community skills help you, consider [starring the original repo](https://github.com/sickn33/antigravity-awesome-skills) or [supporting the author](https://buymeacoffee.com/sickn33).

---

## 🗺️ Roadmap

| Feature                             | Status       | Description                                                                                                                                                                                                               |
| ----------------------------------- | ------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Federated Agent Memory**          | ✅ Shipped    | Cross-agent knowledge sharing via shared Qdrant. Multi-tenancy with developer isolation, `--shared` flag for team visibility. 15/15 tests. ([docs](./docs/memory-modes.md))                                               |
| **Blockchain Agent Trust & Tenancy** | ✅ Shipped   | HMAC-SHA256 signed writes, hash anchoring, project access control, audit trail — all via shared Qdrant `agent_auth` collection. Optional W3C DID via Hyperledger Aries ACA-Py 1.5.0. 36/36 tests. ([docs](./docs/blockchain-auth.md)) |
| **Event-Driven Agent Streaming**    | ✅ Shipped    | Apache Pulsar event bus with auto-publish on `memory_manager.py store`. Project-scoped topics, graceful degradation. 19/19 tests. ([docs](./docs/agent-events.md))                                                        |
| **Memory Mode Tiers**               | ✅ Shipped    | Solo → Team → Pro progression. Backward-compatible upgrades, no data migration. BM25 auto-synced from shared Qdrant on boot. ([docs](./docs/memory-modes.md))                                                            |
| **MCP Compatibility**               | ✅ Shipped    | Memory + cross-agent coordination exposed as MCP tools via `execution/mcp_server.py` (13 tools) and `skills/qdrant-memory/mcp_server.py` (6 tools). Pure chat clients (Claude Desktop) get full memory access. ([docs](./docs/mcp-compatibility.md)) |
| **Platform-Adaptive Orchestration** | ✅ Shipped    | 10 platforms share one `AGENTS.md` via symlinks (Claude Code, Gemini CLI, Codex CLI, Cursor, Copilot, OpenCode, AdaL, Antigravity, OpenClaw, Kiro). Each uses its native orchestration strategy automatically.           |
| **Workflow Engine**                 | ✅ Shipped    | `execution/workflow_engine.py` executes `data/workflows.json` playbooks as guided multi-skill sequences with progress tracking, skip/abort, and state persistence in `.tmp/playbook_state.json`.                         |
| **Skill Self-Improvement**          | ✅ Shipped    | Karpathy Loop: `run_skill_eval.py` (18 binary assertion types) + `karpathy_loop.py` (autonomous test/improve/commit/reset). Skills include `eval/evals.json` for objective quality measurement.                           |
| **Control Tower Orchestrator**      | 🚧 Active    | Basic dispatcher for agent registration and heartbeat via Qdrant (`control_tower.py`). Needs dedicated docs, test coverage, and integration with `session_boot`.                                                          |
| **Secrets Management (Vault)**      | 🔬 Design    | HashiCorp Vault integration for secure secret sharing. Agents authenticate via Ed25519 keypair, access tenant-scoped secrets. Zero long-lived credentials.                                                                |

---

## 🛡️ Security

This package includes a pre-flight security scanner that checks for private terms before publishing. All templates are sanitized for public use.

---

## ☕ Support

If the AGI Agent Kit helps you build better AI-powered workflows, consider supporting the project:

- ⭐ [Star on GitHub](https://github.com/techwavedev/agi-agent-kit)
- ☕ [Buy me a coffee](https://www.buymeacoffee.com/eltonmachado)

---

## 📄 License

Apache-2.0 © [Elton Machado@TechWaveDev](https://github.com/techwavedev)

Community skills in the Full tier are licensed under the MIT License. See [THIRD-PARTY-LICENSES.md](./THIRD-PARTY-LICENSES.md) for details.
