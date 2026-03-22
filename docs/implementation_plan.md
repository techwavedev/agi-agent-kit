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

## Proposed Changes

### Core Execution Layer
Summary: Introduce the session wrap-up protocol to formally close sessions and commit learnings to the shared OS memory.

#### [NEW] execution/session_wrapup.py
- A script to run at the end of an agent session.
- Automatically triggers `cross_agent_context.py store` to log the day's accomplishments.
- Verifies `.tmp/` is cleaned out.
- Reminds the agent to run `memory_manager.py store` if it hasn't.

### Documentation Layer
Summary: Update the core directives and agent rules to reflect the new token-saving best practices.

#### [MODIFY] AGENTS.md
- Add the **Session Close Protocol** (mandatory `session_wrapup.py`).
- Add to the Markdown/Token Rules: "Use Mermaid diagrams to compress structural or architectural context instead of long paragraphs."
- Add to Skill Rules: "Keep `SKILL.md` under 200 lines; use progressive disclosure by linking to `references/` files."

### Skill Creator Layer
Summary: Add autonomous skill evaluation loops.

#### [NEW] skill-creator/scripts/evaluate_skill.py
- A script that allows an agent to define a test input, run a specific skill, evaluate the output against a binary criteria (e.g., "Did it generate a valid JSON?"), and output a pass/fail report to help the agent self-correct the skill.

## Verification Plan

### Automated Tests
- Run `python3 execution/session_wrapup.py` to ensure it successfully performs cleanup and syncs to memory.
- Run `python3 .agent/scripts/release_gate.py` and `python3 execution/validate_template.py` to ensure the AGENTS.md changes pass the framework release policies.
- Run `evaluate_skill.py` against a non-destructive skill (like `pdf-reader`) to verify the evaluation loop works.

### Templates Sync
- Run `python3 execution/sync_to_template.py --sync` to propagate all the root changes to `templates/base/` and `templates/skills/`.
