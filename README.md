# AGI Agent Kit

**Enterprise-Grade Agentic Framework & Scaffolding Tool**

[![npm version](https://img.shields.io/npm/v/@techwavedev/agi-agent-kit.svg)](https://www.npmjs.com/package/@techwavedev/agi-agent-kit)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

`@techwavedev/agi-agent-kit` is a modular, deterministic framework designed to bridge the gap between LLM reasoning and reliable production execution. It scaffolds a "3-Layer Architecture" (Intent → Orchestration → Execution) that forces agents to use tested scripts rather than hallucinating code.

**v1.2.0** — Now with platform-adaptive orchestration across Claude Code, Kiro IDE, Gemini, and Opencode.

---

## 🚀 Quick Start

Scaffold a new agent workspace in seconds:

```bash
npx @techwavedev/agi-agent-kit init
```

You'll be prompted to choose a pack:

- **core** - Essential skills (webcrawler, pdf-reader, qdrant-memory, documentation)
- **knowledge** - Core + 36 specialized skills (API, Security, Design, Architecture)
- **full** - Complete suite with `.agent/` structure (agents, workflows, rules)

After installation, run the **one-shot setup wizard** to auto-configure your environment:

```bash
python3 skills/plugin-discovery/scripts/platform_setup.py --project-dir .
```

This detects your platform, scans the project stack, and configures everything with a single confirmation.

Then **boot the memory system** for automatic token savings:

```bash
python3 execution/session_boot.py --auto-fix
```

This checks Qdrant, Ollama, embedding models, and collections — auto-fixing any issues.

---

## ✨ Key Features

| Feature                       | Description                                                                 |
| ----------------------------- | --------------------------------------------------------------------------- |
| **Deterministic Execution**   | Separates business logic (Python scripts) from AI reasoning (Directives)    |
| **Modular Skill System**      | 56 plug-and-play skills that can be added or removed instantly              |
| **Platform-Adaptive**         | Auto-detects and optimizes for Claude Code, Kiro IDE, Gemini, and Opencode  |
| **Multi-Agent Orchestration** | Agent Teams, subagents, Powers, or sequential personas — adapts to platform |
| **Semantic Memory**           | Built-in Qdrant-powered memory with 95% token savings via caching           |
| **Self-Healing Workflows**    | Agents read error logs, patch scripts, and update directives automatically  |
| **One-Shot Setup**            | Platform detection + project stack scan + auto-configuration in one command |

---

## 🌐 Platform Support

The framework automatically detects your AI coding environment and activates the best available features:

| Platform        | Orchestration Strategy              | Key Features                                 |
| --------------- | ----------------------------------- | -------------------------------------------- |
| **Claude Code** | Agent Teams (parallel) or Subagents | Plugins, marketplace, LSP, hooks             |
| **Kiro IDE**    | Powers + Autonomous Agent (async)   | Dynamic MCP loading, hooks, cross-repo tasks |
| **Gemini**      | Sequential personas via `@agent`    | Skills, MCP servers, execution scripts       |
| **Opencode**    | Sequential personas via `@agent`    | Skills, MCP servers, providers               |

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

```
your-project/
├── AGENTS.md              # Master instruction file (symlinked to GEMINI.md, CLAUDE.md)
├── skills/                # 56 pre-built tools
│   ├── webcrawler/        # Documentation harvesting
│   ├── pdf-reader/        # PDF text extraction
│   ├── qdrant-memory/     # Semantic caching & memory
│   ├── documentation/     # Auto-documentation maintenance
│   ├── plugin-discovery/  # Platform detection & setup wizard
│   ├── parallel-agents/   # Multi-agent orchestration
│   ├── intelligent-routing/ # Smart agent selection & routing
│   ├── self-update/       # Framework self-update capability
│   └── ...                # 48 more specialized skills
├── directives/            # SOPs in Markdown
│   └── memory_integration.md  # Memory protocol reference
├── execution/             # Deterministic Python scripts
│   ├── session_boot.py    # Session startup (Qdrant + Ollama check)
│   ├── session_init.py    # Collection initializer
│   └── memory_manager.py  # Store/retrieve/cache operations
├── skill-creator/         # Tools to create new skills
└── .agent/                # (full pack) Agents, workflows, rules
    └── workflows/         # /setup, /deploy, /test, /debug, etc.
```

---

## 📖 Architecture

The system operates on three layers:

```
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

## 🧠 Semantic Memory

Built-in Qdrant-powered memory with automatic token savings:

| Scenario              | Without Memory | With Memory | Savings  |
| --------------------- | -------------- | ----------- | -------- |
| Repeated question     | ~2000 tokens   | 0 tokens    | **100%** |
| Similar architecture  | ~5000 tokens   | ~500 tokens | **90%**  |
| Past error resolution | ~3000 tokens   | ~300 tokens | **90%**  |

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

# Store a decision
python3 execution/memory_manager.py store --content "what was decided" --type decision

# Health check
python3 execution/memory_manager.py health
```

---

## ⚡ Prerequisites

```bash
pip install requests beautifulsoup4 html2text lxml qdrant-client
```

Optional (for semantic memory with local embeddings):

```bash
pip install ollama sentence-transformers
```

---

## 🔧 Commands

### Initialize a new project

```bash
npx @techwavedev/agi-agent-kit init --pack=full
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

## 📚 Documentation

- **[AGENTS.md](./AGENTS.md)** - Complete architecture and operating principles
- **[skills/SKILLS_CATALOG.md](./skills/SKILLS_CATALOG.md)** - All 56 available skills
- **[CHANGELOG.md](./CHANGELOG.md)** - Version history

---

## 🛡️ Security

This package includes a pre-flight security scanner that checks for private terms before publishing. All templates are sanitized for public use.

---

## 📄 License

Apache-2.0 © [Elton Machado@TechWaveDev](https://github.com/techwavedev)
