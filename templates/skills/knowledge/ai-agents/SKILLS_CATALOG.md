# Skills Catalog

> **Auto-generated Documentation** — Last updated: 2026-03-14 21:14
>
> This catalog is automatically maintained. Update it by running:
> ```bash
> python skill-creator/scripts/update_catalog.py --skills-dir skills/
> ```

This document provides comprehensive documentation on available skills, how to use them, and when each skill should be triggered.

---

## Table of Contents

- [What Are Skills?](#what-are-skills)
- [Available Skills](#available-skills)
  - [Agent Memory Systems](#agent-memory-systems)
  - [Agent Tool Builder](#agent-tool-builder)
  - [Ai Agents Architect](#ai-agents-architect)
  - [Ai Engineer](#ai-engineer)
  - [Autonomous Agent Patterns](#autonomous-agent-patterns)
  - [Debug Llm](#debug-llm)
  - [Mcp Builder](#mcp-builder)
  - [Notebooklm Rag](#notebooklm-rag)
  - [Parallel Agents](#parallel-agents)
  - [Prompt Engineering Patterns](#prompt-engineering-patterns)
- [Using Skills](#using-skills)
- [Creating New Skills](#creating-new-skills)
- [Maintenance](#maintenance)

---

## What Are Skills?

**Skills** are modular, self-contained packages that extend the AI agent's capabilities with specialized knowledge, workflows, and tools.

### Skill Structure

```
skill-name/
├── SKILL.md           # (required) Main instruction file
├── scripts/           # (optional) Executable scripts
├── references/        # (optional) Documentation
└── assets/            # (optional) Templates, images, etc.
```

---

## Available Skills

### Agent Memory Systems

| Property | Value |
| -------- | ----- |
| **Name** | `agent-memory-systems` |
| **Location** | `skills/agent-memory-systems/` |
| **Type** | Standalone |

**Description:** "Memory is the cornerstone of intelligent agents. Without it, every interaction starts from zero. This skill covers the architecture of agent memory: short-term (context window), long-term (vector stores), and the cognitive architectures that organize them.  Key insight: Memory isn't just storage - it's retrieval. A million stored facts mean nothing if you can't find the right one. Chunking, embedding, and retrieval strategies determine whether your agent remembers or forgets.  The field is fragm"

---

### Agent Tool Builder

| Property | Value |
| -------- | ----- |
| **Name** | `agent-tool-builder` |
| **Location** | `skills/agent-tool-builder/` |
| **Type** | Standalone |

**Description:** "Tools are how AI agents interact with the world. A well-designed tool is the difference between an agent that works and one that hallucinates, fails silently, or costs 10x more tokens than necessary.  This skill covers tool design from schema to error handling. JSON Schema best practices, description writing that actually helps the LLM, validation, and the emerging MCP standard that's becoming the lingua franca for AI tools.  Key insight: Tool descriptions are more important than tool implementa"

---

### Ai Agents Architect

| Property | Value |
| -------- | ----- |
| **Name** | `ai-agents-architect` |
| **Location** | `skills/ai-agents-architect/` |
| **Type** | Standalone |

**Description:** "Expert in designing and building autonomous AI agents. Masters tool use, memory systems, planning strategies, and multi-agent orchestration. Use when: build agent, AI agent, autonomous agent, tool use, function calling."

---

### Ai Engineer

| Property | Value |
| -------- | ----- |
| **Name** | `ai-engineer` |
| **Location** | `skills/ai-engineer/` |
| **Type** | Standalone |

**Description:** Build production-ready LLM applications, advanced RAG systems, and

---

### Autonomous Agent Patterns

| Property | Value |
| -------- | ----- |
| **Name** | `autonomous-agent-patterns` |
| **Location** | `skills/autonomous-agent-patterns/` |
| **Type** | Standalone |

**Description:** "Design patterns for building autonomous coding agents. Covers tool integration, permission systems, browser automation, and human-in-the-loop workflows. Use when building AI agents, designing tool APIs, implementing permission systems, or creating autonomous coding assistants."

---

### Debug Llm

| Property | Value |
| -------- | ----- |
| **Name** | `debug-llm` |
| **Location** | `skills/debug-llm/` |
| **MCP Server** | `mcp_server.py` |
| **Type** | Standalone |

**Description:** *[Description not yet provided]*

**References:**
- `references/api_reference.md`

---

### Mcp Builder

| Property | Value |
| -------- | ----- |
| **Name** | `mcp-builder` |
| **Location** | `skills/mcp-builder/` |
| **Type** | Standalone |

**Description:** Guide for creating high-quality MCP (Model Context Protocol) servers that enable LLMs to interact with external services through well-designed tools. Use when building MCP servers to integrate external APIs or services, whether in Python (FastMCP) or Node/TypeScript (MCP SDK).

---

### Notebooklm Rag

| Property | Value |
| -------- | ----- |
| **Name** | `notebooklm-rag` |
| **Location** | `skills/notebooklm-rag/` |
| **Type** | Standalone |

**Description:** "Deep RAG layer powered by Google NotebookLM + Gemini. The agent autonomously manages notebooks via MCP tools — authentication, library management, querying, follow-ups, and caching. Opt-in for users with a Google account. Default RAG is qdrant-memory. Triggers on: '@notebooklm', 'research my docs', 'deep search', 'query my notebook', 'check my notebooks'."

**Scripts:**

| Script | Purpose |
| ------ | ------- |
| `scripts/ask_question.py` | *[See script for details]* |
| `scripts/auth_manager.py` | *[See script for details]* |
| `scripts/browser_utils.py` | *[See script for details]* |
| `scripts/cleanup_manager.py` | *[See script for details]* |
| `scripts/config.py` | *[See script for details]* |
| `scripts/notebook_manager.py` | *[See script for details]* |
| `scripts/run.py` | *[See script for details]* |
| `scripts/setup_environment.py` | *[See script for details]* |

---

### Parallel Agents

| Property | Value |
| -------- | ----- |
| **Name** | `parallel-agents` |
| **Location** | `skills/parallel-agents/` |
| **Type** | Standalone |

**Description:** Platform-adaptive multi-agent orchestration. Uses Claude Code Agent Teams when available, subagents as fallback, and sequential persona switching on other platforms. Use when multiple independent tasks can run with different domain expertise or when comprehensive analysis requires multiple perspectives.

---

### Prompt Engineering Patterns

| Property | Value |
| -------- | ----- |
| **Name** | `prompt-engineering-patterns` |
| **Location** | `skills/prompt-engineering-patterns/` |
| **Type** | Standalone |

**Description:** Master advanced prompt engineering techniques to maximize LLM performance, reliability, and controllability in production. Use when optimizing prompts, improving LLM outputs, or designing production prompt templates.

**Scripts:**

| Script | Purpose |
| ------ | ------- |
| `scripts/optimize-prompt.py` | *[See script for details]* |

**References:**
- `references/chain-of-thought.md`
- `references/few-shot-learning.md`
- `references/prompt-optimization.md`
- `references/prompt-templates.md`
- `references/system-prompts.md`

---
## Using Skills

Skills are automatically triggered based on the user's request matching the skill description. You can also explicitly invoke a skill:

```
"Use the <skill-name> skill to <task>"
```

---

## Creating New Skills

```bash
# Initialize a new skill
python skill-creator/scripts/init_skill.py my-new-skill --path skills/

# Package the skill
python skill-creator/scripts/package_skill.py skills/my-new-skill
```

For detailed guidance, see: `skill-creator/SKILL_skillcreator.md`

---

## Maintenance

### Updating This Catalog

**IMPORTANT:** This catalog must be updated whenever skills are created, modified, or deleted.

```bash
python skill-creator/scripts/update_catalog.py --skills-dir skills/
```

---

*This catalog is part of the [3-Layer Architecture](../AGENTS.md) for reliable AI agent operations.*
