# Implementation Plan: NotebookLM Concepts

This plan maps the concepts extracted from your NotebookLM link to the current state of our `techwavedev/agi` framework, identifying what we already do well and where we can improve.

## Analysis of Concepts vs Current Framework

| Concept from NotebookLM | Current AGI Framework Capability | Proposed Improvement |
| :--- | :--- | :--- |
| **Progressive Disclosure** | `SKILL.md` + `references/` directory pattern exists. | Update `skill_development.md` and `AGENTS.md` to strictly enforce < 200 lines for main `SKILL.md` files. |
| **Mermaid Context Compression** | Generic markdown rules apply. | Add specific rule to `AGENTS.md` advising agents to use Mermaid diagrams over long descriptive blocks for architecture to save tokens. |
| **Self-Correcting Memory** | Qdrant `memory_manager.py` captures learnings. | System is optimal; no structural changes needed. |
| **Heartbeats / Init** | `session_boot.py` exists (checks Qdrant, Ollama, etc). | System is optimal. |
| **Heartbeats / Wrap-up** | **None** | Add `execution/session_wrapup.py` to collect session feedback, perform cross-agent sync, and formally close the session context. Add to `AGENTS.md` as Session Close Protocol. |
| **Automated Evaluations** | Basic unit tests exist, but no formal AI evaluation loop for skills. | Create `skill-creator/scripts/evaluate_skill.py` OR an `autoresearch` skill to automatically run and evaluate skill outputs based on criteria. |

## User Review Required

Please review the proposed changes below. Let me know if you would like me to adjust any of these scopes or add other concepts (e.g. Cloud Tasks or Telegram bot integration)!

## Implemented Changes (2026-03-22)

### Core Execution Layer — DONE
Summary: Introduced the session wrap-up protocol to formally close sessions and commit learnings to shared memory.

#### [DONE] execution/session_wrapup.py
- Runs at the end of an agent session.
- Queries Qdrant for recent memories, verifies at least one was stored.
- Optionally broadcasts accomplishments via `cross_agent_context.py store` (`--auto-broadcast`).
- Scans `.tmp/` for stale files (>24h).
- Deregisters from Control Tower heartbeat.
- Exit codes: 0 (success), 1 (zero stores warning), 2 (Qdrant unreachable).
- Docs: `docs/execution/session_wrapup.md`

### Documentation Layer — DONE
Summary: Updated core directives and agent rules with token-saving best practices.

#### [DONE] AGENTS.md
- Added **Session Close Protocol** (mandatory `session_wrapup.py`).
- Added Mermaid Context Compression rule to Markdown best practices.
- Added Progressive Disclosure rule: `SKILL.md` must stay under 200 lines.
- Added `evaluate_skill.py` command reference under Skill Creator.

### Skill Creator Layer — DONE
Summary: Added autonomous skill evaluation loops.

#### [DONE] skill-creator/scripts/evaluate_skill.py
- Evaluates skills against binary criteria (structural checks + keyword heuristics).
- 8 built-in checks: SKILL.md exists, YAML frontmatter, required fields, line count, scripts dir, references dir, executability, naming convention.
- Stores results in Qdrant with historical trend comparison.
- Graceful degradation when Qdrant/Ollama unavailable.
- Docs: `docs/skill-creator/evaluate_skill.md`

## Verification Plan

### Automated Tests
- [ ] Run `python3 execution/session_wrapup.py` to ensure it successfully performs cleanup and syncs to memory.
- [ ] Run `python3 .agent/scripts/release_gate.py` and `python3 execution/validate_template.py` to ensure the AGENTS.md changes pass the framework release policies.
- [ ] Run `evaluate_skill.py` against a non-destructive skill (like `pdf-reader`) to verify the evaluation loop works.

### Templates Sync
- [ ] Run `python3 execution/sync_to_template.py --sync` to propagate all the root changes to `templates/base/` and `templates/skills/`.

### Documentation Team
- [x] doc-writer: Created `docs/execution/session_wrapup.md` and `docs/skill-creator/evaluate_skill.md` (2026-03-22)
- [x] doc-reviewer: Verified docs match source code (2026-03-22)
- [x] changelog-updater: Added entries under `[Unreleased]` in CHANGELOG.md (2026-03-22)
