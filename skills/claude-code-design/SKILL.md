---
name: claude-code-design
description: "Answer questions about Claude Code / Anthropic agent design patterns (CLAUDE.md layering, skills anatomy, progressive disclosure, memory-first, orchestration, sub-agents, worktree isolation, Karpathy loop). Primary backend is a NotebookLM RAG over Anthropic design notebooks; falls back to bundled references when the notebook is not registered."
risk: low
source: internal
date_added: "2026-04-14"
---

# Claude Code Design Skill

Source-grounded answers about how Claude Code and adjacent Anthropic agent systems are designed. Pulls from a NotebookLM RAG (Claude Code Design notebook) when available, and from curated local references otherwise.

## When to Use

Trigger when user asks about:
- Claude Code architecture, orchestration, or sub-agents
- Agent skill anatomy (SKILL.md, references, eval)
- Progressive disclosure, 200-line SKILL cap, hooks, worktree isolation
- Memory-first / determinism-over-probability patterns
- Karpathy self-improvement loop for skills
- CLAUDE.md layering (directives / orchestration / execution)

Do NOT trigger for generic LLM design questions unrelated to Claude Code / Anthropic agent patterns.

## Retrieval Order (Do Not Skip)

1. Check the notebooklm library for an active "Claude Code Design" notebook:

   ```bash
   python skills/notebooklm/scripts/run.py notebook_manager.py search --query "claude code design"
   ```

2. If a matching notebook exists, query it via the wrapper:

   ```bash
   python skills/notebooklm/scripts/run.py ask_question.py \
     --question "<user question>" \
     --notebook-id <id>
   ```

   Or, with a direct URL:

   ```bash
   python skills/notebooklm/scripts/run.py ask_question.py \
     --question "<user question>" \
     --notebook-url "<URL>"
   ```

3. If no matching notebook is registered, fall back to:
   - `references/claude_code_design_principles.md`
   - `references/usage_patterns.md`

   Then surface a one-line note to the user: "Answer from local references; no Claude Code Design NotebookLM is registered yet."

## One-shot Wrapper

For quick terminal use:

```bash
bash skills/claude-code-design/scripts/ask_design.sh "How should a SKILL.md handle progressive disclosure?"
```

The wrapper forwards the question to `skills/notebooklm/scripts/run.py ask_question.py` using the active notebook. It is a convenience; always prefer the explicit commands above when you need to control which notebook is queried.

## TODO: Register the NotebookLM Source

The Claude Code Design notebook is NOT yet in the local notebooklm library. User action required:

```bash
python skills/notebooklm/scripts/run.py notebook_manager.py add \
  --url "<CLAUDE_CODE_DESIGN_NOTEBOOK_URL>" \
  --name "Claude Code Design" \
  --description "Anthropic notebooks on Claude Code architecture, skills, orchestration, agent patterns" \
  --topics "claude-code,design,agents,skills,orchestration"
```

Until this is done, answers fall back to bundled references only.

## Answer Protocol

1. Retrieve via NotebookLM (preferred) or local references (fallback).
2. Cite the source explicitly:
   - `[NotebookLM: Claude Code Design]` for RAG answers
   - `[local: references/claude_code_design_principles.md]` for fallback
3. If the NotebookLM answer ends with "Is that ALL you need to know?", follow the notebooklm skill's Follow-Up Protocol before responding to the user.
4. Prefer short, structured answers. Examples beat prose.
5. For multi-part design questions, split into sub-queries and synthesize.

## Memory-First Protocol

Before answering a non-trivial design question:

```bash
python3 execution/memory_manager.py auto --query "claude-code-design: <topic>"
```

After answering (especially if you synthesized multiple sources):

```bash
python3 execution/memory_manager.py store \
  --content "claude-code-design: <distilled answer>" \
  --type technical \
  --project agi-agent-kit \
  --tags claude-code-design skill agent-patterns
```

## References

- [references/claude_code_design_principles.md](references/claude_code_design_principles.md) — core design patterns distilled from CLAUDE.md and framework directives
- [references/usage_patterns.md](references/usage_patterns.md) — example queries and routing patterns
- [references/voltagent_patterns.md](references/voltagent_patterns.md) — cross-framework patterns from VoltAgent org (TS core, DESIGN.md, subagent format, awesome-skills quality bar, 2026 agent papers)

## Related Skills

- `notebooklm` — query backend (browser automation)
- `qdrant-memory` — memory store used by memory-first protocol
- `documentation` — sister skill for producing Anthropic-style docs
