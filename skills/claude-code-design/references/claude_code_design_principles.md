# Claude Code Design Principles (Distilled)

Curated from `CLAUDE.md` and `directives/` in this repo, plus publicly documented Anthropic Claude Code / Skills patterns. Use as a fallback when the Claude Code Design NotebookLM is unavailable.

> Sources: `CLAUDE.md`, `directives/framework_development.md`, `directives/skill_development.md`, `directives/memory_integration.md`, `skill-creator/SKILL_skillcreator.md`.

## 1. Determinism Over Probability

LLM calls are probabilistic; business logic is not. Push complex or repeatable logic into deterministic scripts and keep the agent as the intelligent router.

- 90% accuracy per step compounds to ~59% over 5 steps — so minimize probabilistic hops.
- Agent does NOT hand-roll scraping, data transforms, or API orchestration inline. It invokes `execution/*.py`.
- Scripts must be idempotent, CLI-driven, return structured JSON, and use explicit exit codes.

## 2. Three-Layer Architecture

```
Intent  (directives/*.md)    — what to do, edge cases, SOPs
Orchestration (the agent)    — read directive, sequence scripts, self-anneal
Execution (execution/*.py)   — deterministic work, APIs, I/O
```

Skills sit alongside as modular capabilities that wrap this pattern for a specific domain.

## 3. Skill Anatomy

Each skill lives under `skills/<name>/` with:

- `SKILL.md` — YAML frontmatter (`name`, `description`), trigger conditions, process routing. **Hard cap: 200 lines.**
- `scripts/` — deterministic executables (prefer `verb_noun.py`).
- `references/` — deep knowledge loaded on demand only.
- `eval/evals.json` — binary assertions for self-improvement.

Frontmatter `description` must encode trigger conditions clearly enough for the orchestrator to pick the skill without guessing.

## 4. Progressive Disclosure

SKILL.md is a process router, not an encyclopedia.

- Keep step-by-step routing and output format in `SKILL.md`.
- Push long examples, domain framework, and brand/context material into `references/`.
- Reference files are loaded only when `SKILL.md` explicitly tells the orchestrator to load them — then unloaded.
- If `SKILL.md` grows past ~1500 words / 200 lines, split it.

## 5. Memory-First Protocol

Every non-trivial task starts and ends in memory:

```
auto query  → inject context or use cached response
... work ...
store decision/technical/code/error
cache-store the final response for future lookups
```

Skipped memory = every query pays full token cost. Memory-first is mandatory, not advisory. Opt-out only when the user explicitly says "no cache" / "fresh".

## 6. Local-First Routing

| Route | When |
|-------|------|
| `local_required` | Secrets, `.env`, credentials — never leaves the machine |
| `local` | Simple deterministic tasks Gemma4 can handle without quality loss |
| `cloud` | Multi-file reasoning, architecture, refactors |

Rule: never sacrifice output quality for token savings. When in doubt, cloud for quality, local for security.

## 7. Self-Anneal on Failure

Errors are learning opportunities:

1. Read full error + stack.
2. Diagnose root cause.
3. Fix the script or parameters.
4. Test (confirm with user if the retry burns paid tokens or has side effects).
5. Update the directive with the new failure mode + solution.

The system strengthens each time it breaks and is repaired.

## 8. Karpathy Loop (Skill Self-Improvement)

Iterative cycle: test → edit SKILL.md → re-run eval → `git commit` if improved, `git reset` if not.

- Every skill ships `eval/evals.json` with purely **binary** assertions (`contains`, `max_lines`, `has_yaml_frontmatter`, ...).
- Never subjective judgments in evals.
- `execution/karpathy_loop.py` drives the loop; `execution/run_skill_eval.py` reports pass rate.

## 9. Sub-Agent Orchestration

Teams of sub-agents collaborate via manifests in `directives/teams/`.

- Simple sub-agent tasks → `local_micro_agent.py` on Ollama.
- Complex tasks → in-context delegation back to the active orchestrator session (no extra cloud spend).
- When a sub-agent returns `"status": "delegated_to_active_session"`, the orchestrator MUST open the delegation file and execute it as that persona.
- Handoff state between sub-agents is structured: `{ state, next_steps, validation_requirements }` and must be stored in Qdrant tagged with the team's run id.

## 10. Worktree Isolation for Parallel Work

When multiple sub-agents touch different files, each gets its own git worktree.

- `execution/worktree_isolator.py` handles create / merge / cleanup.
- File partitions must be validated to avoid overlap.
- Worktree branches are never pushed directly to main — always named branches + PRs.
- `.env` auto-copies into each worktree so memory/tooling keeps working.

## 11. Hooks (Context Mode)

Hooks wired in `.claude/settings.json` intercept tool output transparently:

| Hook | Event | Purpose |
|------|-------|---------|
| `context_session_start.py` | SessionStart | Initialize SQLite session |
| `context_filter.py` | PostToolUse | Sandbox-filter heavy outputs (> 8KB default) |
| `context_reinject.py` | PreCompact | Re-inject critical context before compaction |

Result: longer-lived sessions without blowing the context window.

## 12. Compaction Discipline

Before compacting or clearing context, write a pre-compaction summary to Qdrant (`type: conversation`). Context not stored is context lost.

## 13. Governance

- Feature branch + PR workflow is mandatory; no direct commits to `main` / `public`.
- Release Gate (`python3 .agent/scripts/release_gate.py`) runs before NPM publish — zero tolerance on bypass.
- Documentation team MUST be dispatched after any change to `execution/`, `skills/`, `templates/`, or `directives/`.

## 14. Cross-Agent Collaboration

All agents (Claude, Antigravity, Cursor, Copilot, ...) share one Qdrant memory. Use `cross_agent_context.py` for `sync`, `pending`, `store`, `handoff`, `broadcast`. Never work in a shared cwd with another live agent — always create a worktree.

## 15. Markdown Token Discipline

Markdown is loaded verbatim into the context window.

- Challenge every sentence.
- Prefer tables and examples over prose.
- Compress architecture descriptions to Mermaid diagrams.
- Split anything over ~1500 words.

## 16. Trigger-First Skill Design

A skill's frontmatter `description` is the only thing the orchestrator sees when deciding whether to activate it. Design it like an ad headline: trigger conditions first, capability second, constraints implied. Ambiguous descriptions cause mis-routing.
