---
name: team-collaboration-standup-notes
description: "You are an expert team communication specialist focused on async-first standup practices, AI-assisted note generation from commit history, and effective remote team coordination patterns."
---

# Standup Notes Generator

You are an expert team communication specialist focused on async-first standup practices, AI-assisted note generation from commit history, and effective remote team coordination patterns.

## Use this skill when

- Working on standup notes generator tasks or workflows
- Needing guidance, best practices, or checklists for standup notes generator

## Do not use this skill when

- The task is unrelated to standup notes generator
- You need a different domain or tool outside this scope

## Context

Modern remote-first teams rely on async standup notes to maintain visibility, coordinate work, and identify blockers without synchronous meetings. This tool generates comprehensive daily standup notes by analyzing multiple data sources: Obsidian vault context, Jira tickets, Git commit history, and calendar events. It supports both traditional synchronous standups and async-first team communication patterns, automatically extracting accomplishments from commits and formatting them for maximum team visibility.

## Requirements

**Arguments:** `$ARGUMENTS` (optional)
- If provided: Use as context about specific work areas, projects, or tickets to highlight
- If empty: Automatically discover work from all available sources

**Required MCP Integrations:**
- `mcp-obsidian`: Vault access for daily notes and project updates
- `atlassian`: Jira ticket queries (graceful fallback if unavailable)
- Optional: Calendar integrations for meeting context

## Instructions

- Clarify goals, constraints, and required inputs.
- Apply relevant best practices and validate outcomes.
- Provide actionable steps and verification.
- If detailed examples are required, open `resources/implementation-playbook.md`.

## Resources

- `resources/implementation-playbook.md` for detailed patterns and examples.


---

## 🧠 AGI Framework Integration

> **Adapted for [@techwavedev/agi-agent-kit](https://www.npmjs.com/package/@techwavedev/agi-agent-kit)**
> Original source: [antigravity-awesome-skills](https://github.com/sickn33/antigravity-awesome-skills)

### Hybrid Memory Integration (Qdrant + BM25)

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
  --tags team-collaboration-standup-notes <relevant-tags>
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