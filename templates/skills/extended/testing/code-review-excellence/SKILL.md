---
name: code-review-excellence
description: Master effective code review practices to provide constructive feedback, catch bugs early, and foster knowledge sharing while maintaining team morale. Use when reviewing pull requests, establishing review standards, or mentoring developers.
---

# Code Review Excellence

Transform code reviews from gatekeeping to knowledge sharing through constructive feedback, systematic analysis, and collaborative improvement.

## Use this skill when

- Reviewing pull requests and code changes
- Establishing code review standards
- Mentoring developers through review feedback
- Auditing for correctness, security, or performance

## Do not use this skill when

- There are no code changes to review
- The task is a design-only discussion without code
- You need to implement fixes instead of reviewing

## Instructions

- Read context, requirements, and test signals first.
- Review for correctness, security, performance, and maintainability.
- Provide actionable feedback with severity and rationale.
- Ask clarifying questions when intent is unclear.
- If detailed checklists are required, open `resources/implementation-playbook.md`.

## Output Format

- High-level summary of findings
- Issues grouped by severity (blocking, important, minor)
- Suggestions and questions
- Test and coverage notes

## Resources

- `resources/implementation-playbook.md` for detailed review patterns and templates.


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
  --tags code-review-excellence <relevant-tags>
```

### Agent Team Collaboration

- This skill can be invoked by the `orchestrator` agent via intelligent routing.
- In **Agent Teams mode**, results are shared via Qdrant shared memory for cross-agent context.
- In **Subagent mode**, this skill runs in isolation with its own memory namespace.

### Local LLM Support

When available, use local Ollama models for embedding and lightweight inference:
- Embeddings: `nomic-embed-text` via Qdrant memory system
- Lightweight analysis: Local models reduce API costs for repetitive patterns
