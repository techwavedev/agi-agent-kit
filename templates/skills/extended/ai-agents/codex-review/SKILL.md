---
name: codex-review
description: Professional code review with auto CHANGELOG generation, integrated with Codex AI
---

# codex-review

## Overview
Professional code review with auto CHANGELOG generation, integrated with Codex AI

## When to Use
- When you want professional code review before commits
- When you need automatic CHANGELOG generation
- When reviewing large-scale refactoring

## Installation
```bash
npx skills add -g BenedictKing/codex-review
```

## Step-by-Step Guide
1. Install the skill using the command above
2. Ensure Codex CLI is installed
3. Use `/codex-review` or natural language triggers

## Examples
See [GitHub Repository](https://github.com/BenedictKing/codex-review) for examples.

## Best Practices
- Keep CHANGELOG.md in your project root
- Use conventional commit messages

## Troubleshooting
See the GitHub repository for troubleshooting guides.

## Related Skills
- context7-auto-research, tavily-web, exa-search, firecrawl-scraper


---

## 🧠 AGI Framework Integration

> **Adapted for [@techwavedev/agi-agent-kit](https://www.npmjs.com/package/@techwavedev/agi-agent-kit)**
> Original source: [antigravity-awesome-skills](https://github.com/sickn33/antigravity-awesome-skills)

### Qdrant Memory Integration

Before executing complex tasks with this skill:
```bash
python3 execution/memory_manager.py auto --query "<task summary>"
```
- **Cache hit?** Use cached response directly — no need to re-process.
- **Memory match?** Inject `context_chunks` into your reasoning.
- **No match?** Proceed normally, then store results:
```bash
python3 execution/memory_manager.py store \
  --content "Description of what was decided/solved" \
  --type decision \
  --tags codex-review <relevant-tags>
```

### Agent Team Collaboration

- This skill can be invoked by the `orchestrator` agent via intelligent routing.
- In **Agent Teams mode**, results are shared via Qdrant shared memory for cross-agent context.
- In **Subagent mode**, this skill runs in isolation with its own memory namespace.

### Local LLM Support

When available, use local Ollama models for embedding and lightweight inference:
- Embeddings: `nomic-embed-text` via Qdrant memory system
- Lightweight analysis: Local models reduce API costs for repetitive patterns
