# AGI Agent Kit

**Enterprise-Grade Agentic Framework & Scaffolding Tool**

`@techwavedev/agi-agent-kit` is a modular, deterministic framework designed to bridge the gap between LLM reasoning and reliable production execution. It scaffolds a "3-Layer Architecture" (Intent -> Orchestration -> Execution) that forces agents to use tested snippets rather than hallucinating code.

## 🚀 Key Features

- **Deterministic Execution Layer**: Separates business logic (Python scripts) from AI reasoning (Directives).
- **Modular Skill System**: Plug-and-play capabilities (Webcrawler, PDF Analysis, Memory) that can be added or removed instantly.
- **Semantic Memory (Qdrant)**: Built-in short-term and long-term memory with 95% token savings via semantic caching.
- **Universal Compatibility**: Works out-of-the-box with Claude (Anthropic), Gemini (Google), and OpenAI models via standardized context files.
- **Self-Healing Workflows**: Agents are trained to read error logs, patch their own scripts, and update their directives automatically.

## 📦 Quick Start

Scaffold a new agent workspace in seconds:

```bash
npx @techwavedev/agi-agent-kit init
```

### What You Get

- **`/skills`**: Pre-built tools for common tasks (Docs, Web, Memory).
- **`AGENTS.md`**: The master instruction file that "installs" the OS into your LLM.
- **Structure**: A production-ready folder hierarchy (`directives/`, `execution/`, `.tmp/`).

## ⚡ Prerequisites

This kit relies on robust Python tooling for its execution layer:

```bash
pip install requests beautifulsoup4 html2text lxml qdrant-client
```

## 📖 Architecture

The system operates on three layers:

1.  **Directives (Intent)**: SOPs written in simple Markdown (`directives/`).
2.  **Orchestration (Agent)**: The LLM reads the directive and decides which tool to call.
3.  **Execution (Code)**: Pure, reliable Python scripts (`execution/`) handle the actual work.

---

_Built by [TechWaveDev](https://github.com/techwavedev)_
