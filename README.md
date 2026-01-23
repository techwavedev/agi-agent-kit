# AGI Agent Kit

**Enterprise-Grade Agentic Framework & Scaffolding Tool**

[![npm version](https://img.shields.io/npm/v/@techwavedev/agi-agent-kit.svg)](https://www.npmjs.com/package/@techwavedev/agi-agent-kit)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

`@techwavedev/agi-agent-kit` is a modular, deterministic framework designed to bridge the gap between LLM reasoning and reliable production execution. It scaffolds a "3-Layer Architecture" (Intent → Orchestration → Execution) that forces agents to use tested scripts rather than hallucinating code.

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

---

## ✨ Key Features

| Feature                     | Description                                                                |
| --------------------------- | -------------------------------------------------------------------------- |
| **Deterministic Execution** | Separates business logic (Python scripts) from AI reasoning (Directives)   |
| **Modular Skill System**    | Plug-and-play capabilities that can be added or removed instantly          |
| **Semantic Memory**         | Built-in Qdrant-powered memory with 95% token savings via caching          |
| **Universal Compatibility** | Works with Claude, Gemini, and OpenAI via standardized context files       |
| **Self-Healing Workflows**  | Agents read error logs, patch scripts, and update directives automatically |
| **Self-Update**             | Update to the latest version with a single command                         |

---

## 📦 What You Get

```
your-project/
├── AGENTS.md              # Master instruction file (symlinked to GEMINI.md, CLAUDE.md)
├── skills/                # Pre-built tools
│   ├── webcrawler/        # Documentation harvesting
│   ├── pdf-reader/        # PDF text extraction
│   ├── qdrant-memory/     # Semantic caching & memory
│   ├── documentation/     # Auto-documentation maintenance
│   └── self-update/       # Framework self-update capability
├── directives/            # SOPs in Markdown
├── execution/             # Deterministic Python scripts
├── skill-creator/         # Tools to create new skills
└── .agent/                # (full pack) Agents, workflows, rules
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
├─────────────────────────────────────────────────────────┤
│  Layer 3: EXECUTION (Code)                              │
│  └─ Pure Python scripts (execution/) do the actual work │
└─────────────────────────────────────────────────────────┘
```

**Why?** LLMs are probabilistic. 90% accuracy per step = 59% success over 5 steps. By pushing complexity into deterministic scripts, we achieve reliable execution.

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

### Update to latest version

```bash
npx @techwavedev/agi-agent-kit@latest init --pack=full
# or use the built-in skill:
python3 skills/self-update/scripts/update_kit.py
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
- **[skills/SKILLS_CATALOG.md](./skills/SKILLS_CATALOG.md)** - All available skills
- **[CHANGELOG.md](./CHANGELOG.md)** - Version history

---

## 🛡️ Security

This package includes a pre-flight security scanner (`verify_public_release.py`) that checks for private terms before publishing. All templates are sanitized for public use.

---

## 📄 License

Apache-2.0 © [Elton Machado@TechWaveDev](https://github.com/techwavedev)
