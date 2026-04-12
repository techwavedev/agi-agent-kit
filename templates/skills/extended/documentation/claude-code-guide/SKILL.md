---
name: claude-code-guide
description: "To provide a comprehensive reference for configuring and using Claude Code (the agentic coding tool) to its full potential. This skill synthesizes best practices, configuration templates, and advanced usage patterns."
risk: unknown
source: community
date_added: "2026-02-27"
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

## When to Use
This skill is applicable to execute the workflow or actions described in the overview.

---

<!-- AGI-INTEGRATION-START -->

## AGI Framework Integration

> **Adapted for [@techwavedev/agi-agent-kit](https://www.npmjs.com/package/@techwavedev/agi-agent-kit)**
> Original source: [antigravity-awesome-skills](https://github.com/sickn33/antigravity-awesome-skills)

### Memory-First Protocol

Retrieve prior documentation structure and content to maintain consistency. Cache generated docs to avoid regenerating unchanged sections.

```bash
# Check for prior documentation context before starting
python3 execution/memory_manager.py auto --query "documentation patterns and prior content for Claude Code Guide"
```

### Storing Results

After completing work, store documentation decisions for future sessions:

```bash
python3 execution/memory_manager.py store \
  --content "Documentation: API reference generated from OpenAPI spec, deployment guide updated with new env vars" \
  --type technical --project <project> \
  --tags claude-code-guide documentation
```

### Multi-Agent Collaboration

Share documentation changes with all agents so they reference the latest guides and APIs.

```bash
python3 execution/cross_agent_context.py store \
  --agent "<your-agent>" \
  --action "Documentation updated — API reference, deployment guide, and CHANGELOG all current" \
  --project <project>
```

### Agent Team: Documentation

This skill pairs with `documentation_team` — dispatched automatically after any code change to keep docs in sync.

<!-- AGI-INTEGRATION-END -->
