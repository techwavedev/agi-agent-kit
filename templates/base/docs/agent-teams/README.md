# Agent Teams — Patterns & Reference

This document explains how sub-agents and team agents work in the AGI framework, what patterns are available, and how to use them in your projects.

---

## What Is a Sub-Agent?

A **sub-agent** is a focused agent invocation with a narrow scope and a specific directive. It reads its directive file (`directives/subagents/<name>.md`), performs one job, and returns a structured JSON result.

Sub-agents:
- Have **no shared context** with other sub-agents (clean slate)
- **Receive their full context in the payload** — they never read files they weren't given
- Return **structured JSON** with pass/fail status and details
- Are invoked by a **team orchestrator** or **the primary agent**

---

## What Is a Team Agent?

A **team agent** is a named group of sub-agents that work together toward a shared goal. Teams are defined in `directives/teams/<team_id>.md` and dispatched using:

```bash
python3 execution/dispatch_agent_team.py --team <team_id> --payload '<json>'
```

The dispatch script reads the team directive, extracts the sub-agent list, and produces a **manifest** — a structured execution plan the primary agent follows to invoke each sub-agent in order.

---

## Available Teams

| Team | Sub-Agents | Purpose | Trigger |
|------|-----------|---------|---------|
| `documentation_team` | doc-writer, doc-reviewer, changelog-updater | Keep docs in sync with code | Automatic — every code change |
| `code_review_team` | spec-reviewer, quality-reviewer | Two-stage code review | After implementation |
| `qa_team` | test-generator, test-verifier | Generate and verify tests | After code review |

---

## Available Sub-Agents

| Sub-Agent | Team | Directive |
|-----------|------|-----------|
| `doc-writer` | documentation_team | `directives/subagents/doc_writer.md` |
| `doc-reviewer` | documentation_team | `directives/subagents/doc_reviewer.md` |
| `changelog-updater` | documentation_team | `directives/subagents/changelog_updater.md` |
| `spec-reviewer` | code_review_team | `directives/subagents/spec_reviewer.md` |
| `quality-reviewer` | code_review_team | `directives/subagents/quality_reviewer.md` |

---

## Patterns

### 1. Single Sub-Agent (Sequential Review)

The `subagent-driven-development` pattern from `skills/extended/ai-agents/subagent-driven-development/`.

```
Implementer → spec-reviewer → quality-reviewer
```

Best for: a single implementation task that needs quality gates before moving on.

### 2. Parallel Sub-Agents

The `dispatching-parallel-agents` pattern from `skills/extended/ai-agents/dispatching-parallel-agents/`.

```
Domain A → agent_A
Domain B → agent_B   (concurrently)
Domain C → agent_C
                   → integrate results
```

Best for: multiple independent problems that can be solved simultaneously.

### 3. Doc-Team-on-Code ← Primary Pattern

Every code change automatically triggers the documentation team.

```
Code Change → documentation_team
                ├── doc-writer (updates docs)
                ├── doc-reviewer (validates accuracy)
                └── changelog-updater (appends CHANGELOG entry)
```

**This is mandatory in the framework.** See `.agent/rules/agent_team_rules.md`.

### 4. Full Team Pipeline

Chain all three teams for a complete release-quality flow:

```
code_review_team → documentation_team → qa_team
```

### 5. Failure Recovery

When a sub-agent or team fails, the framework:
1. Returns a structured JSON error with semantic exit code
2. Does not corrupt state
3. Allows re-dispatch after the issue is resolved

### 6. Dynamic State Handoff (Agent Communication)

Sub-agents execute sequentially based on the manifest, but they can dynamically communicate state to the next agent in line, or to remote agents executing in parallel, via a `handoff_state` object.
- **Agent A**: Returns a JSON result containing `"handoff_state": { "key": "value" }`
- **Orchestrator**: Stores the `handoff_state` object to Qdrant memory using `memory_manager.py` tagged with the team's run ID, and also injects it into the context payload provided to Agent B (if local).
- **Agent B (or Remote Agent)**: Uses the state (either from payload or retrieved from Qdrant) to resume work exactly where Agent A left off.
  
This solves the context-loss problem across deep, multi-stage, or geographically distributed agent workflows.

---

## How to Dispatch a Team

```bash
# 1. Dispatch the team — get a manifest
python3 execution/dispatch_agent_team.py \
  --team documentation_team \
  --payload '{"changed_files": ["execution/session_boot.py"], "commit_msg": "feat: add auto-fix", "change_type": "feat"}'

# 2. Read the manifest — it tells you which sub-agents to invoke and in what order

# 3. For each sub-agent in the manifest:
#    a. Read its directive: directives/subagents/<name>.md
#    b. Invoke it with the provided context
#    c. Collect its JSON output

# 4. Check overall result
python3 execution/agent_team_result.py --team documentation_team
```

---

## How to Add a New Team

1. Create `directives/teams/<your_team>.md` following the template in existing team files
2. Create sub-agent directives in `directives/subagents/<sub_agent>.md`
3. Test with: `python3 execution/dispatch_agent_team.py --team <your_team> --payload '{}' --dry-run`

---

## How to Run the Test Scenarios

This branch includes 5 test scenarios covering all patterns above:

```bash
# Run a specific scenario
python3 execution/run_test_scenario.py --scenario 3

# Run all scenarios
python3 execution/run_test_scenario.py --all

# Use the workflow (supports // turbo auto-run)
# Read: .agent/workflows/run-agent-team-tests.md
```

See `tests/agents/` for full scenario documentation.

---

## Extending the Framework

- **New sub-agent role?** → Add `directives/subagents/<name>.md`
- **New team?** → Add `directives/teams/<name>.md` + register in dispatch script
- **New test scenario?** → Add `tests/agents/scenario_0N_<name>.md` + case in `run_test_scenario.py`
- **New rule?** → Add to `.agent/rules/agent_team_rules.md`
