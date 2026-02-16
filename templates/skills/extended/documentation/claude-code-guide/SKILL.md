---
name: Claude Code Guide
description: Master guide for using Claude Code effectively. Includes configuration templates, prompting strategies "Thinking" keywords, debugging techniques, and best practices for interacting with the agent.
---

# Claude Code Guide

## Purpose

To provide a comprehensive reference for configuring and using Claude Code (the agentic coding tool) to its full potential. This skill synthesizes best practices, configuration templates, and advanced usage patterns.

## Configuration (`CLAUDE.md`)

When starting a new project, create a `CLAUDE.md` file in the root directory to guide the agent.

### Template (General)

```markdown
# Project Guidelines

## Commands

- Run app: `npm run dev`
- Test: `npm test`
- Build: `npm run build`

## Code Style

- Use TypeScript for all new code.
- Functional components with Hooks for React.
- Tailwind CSS for styling.
- Early returns for error handling.

## Workflow

- Read `README.md` first to understand project context.
- Before editing, read the file content.
- After editing, run tests to verify.
```

## Advanced Features

### Thinking Keywords

Use these keywords in your prompts to trigger deeper reasoning from the agent:

- "Think step-by-step"
- "Analyze the root cause"
- "Plan before executing"
- "Verify your assumptions"

### Debugging

If the agent is stuck or behaving unexpectedly:

1. **Clear Context**: Start a new session or ask the agent to "forget previous instructions" if confused.
2. **Explicit Instructions**: Be extremely specific about paths, filenames, and desired outcomes.
3. **Logs**: Ask the agent to "check the logs" or "run the command with verbose output".

## Best Practices

1. **Small Contexts**: Don't dump the entire codebase into the context. Use `grep` or `find` to locate relevant files first.
2. **Iterative Development**: Ask for small changes, verify, then proceed.
3. **Feedback Loop**: If the agent makes a mistake, correct it immediately and ask it to "add a lesson" to its memory (if supported) or `CLAUDE.md`.

## Reference

Based on [Claude Code Guide by zebbern](https://github.com/zebbern/claude-code-guide).


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
  --tags claude-code-guide <relevant-tags>
```

### Agent Team Collaboration

- This skill can be invoked by the `orchestrator` agent via intelligent routing.
- In **Agent Teams mode**, results are shared via Qdrant shared memory for cross-agent context.
- In **Subagent mode**, this skill runs in isolation with its own memory namespace.

### Local LLM Support

When available, use local Ollama models for embedding and lightweight inference:
- Embeddings: `nomic-embed-text` via Qdrant memory system
- Lightweight analysis: Local models reduce API costs for repetitive patterns
