# Usage Patterns — claude-code-design

Short, concrete examples for routing design questions to the NotebookLM RAG backend. Assumes the Claude Code Design notebook is already registered in the notebooklm library.

## 1. Direct question (active notebook)

```bash
python skills/notebooklm/scripts/run.py ask_question.py \
  --question "Why is SKILL.md capped at 200 lines?"
```

Use when one notebook is activated and the question is self-contained.

## 2. Pin the notebook explicitly

```bash
python skills/notebooklm/scripts/run.py ask_question.py \
  --question "How do sub-agents hand off state in Claude Code teams?" \
  --notebook-id claude-code-design
```

Use when multiple notebooks are registered and you need the correct source.

## 3. Direct URL (no library entry)

```bash
python skills/notebooklm/scripts/run.py ask_question.py \
  --question "What triggers PreCompact hooks?" \
  --notebook-url "https://notebooklm.google.com/notebook/<id>"
```

Use for one-off queries against a notebook you do not want to persist.

## 4. Multi-part synthesis

Split the question, query each part, then combine.

```bash
python skills/notebooklm/scripts/run.py ask_question.py \
  --question "What is progressive disclosure in skills?"

python skills/notebooklm/scripts/run.py ask_question.py \
  --question "How does the Karpathy loop improve a skill?"
```

Synthesize locally before responding to the user.

## 5. One-shot wrapper (convenience)

```bash
bash skills/claude-code-design/scripts/ask_design.sh \
  "How should directives coordinate with execution scripts?"
```

The wrapper is equivalent to option 1 but shorter to type.

## 6. Fallback when notebook is missing

If `notebook_manager.py search --query "claude code design"` returns no match:

1. Read `references/claude_code_design_principles.md` directly.
2. Cite as `[local: references/claude_code_design_principles.md]`.
3. Note to the user that the NotebookLM source is not yet registered and include the registration command from `SKILL.md`.

## 7. Memory integration

Cache-store a good synthesized answer so the next identical question is free:

```bash
python3 execution/memory_manager.py cache-store \
  --query "How does the Karpathy loop work?" \
  --response "<final synthesized answer>"
```

## 8. Common design questions (routing hints)

| Question topic | Primary source |
|----------------|----------------|
| SKILL.md structure / 200-line cap | NotebookLM + principles doc §3, §4 |
| Memory-first protocol | principles doc §5 |
| Karpathy loop mechanics | principles doc §8 |
| Sub-agent handoff JSON shape | principles doc §9 |
| Worktree isolation rules | principles doc §10 |
| Hooks and context mode | principles doc §11 |
| Progressive disclosure | principles doc §4 |
