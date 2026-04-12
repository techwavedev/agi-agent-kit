# Phase-Reset Architecture (SOP 002)

## Background

When autonomous agents process long, multi-step workflows (like "Discovery → Investigation → Design → Build"), their context window accumulates immense "drift." The LLM memory becomes cluttered with past loops, previous false-starts, and stale code. 

**This results in agents looping infinitely, ignoring recent instructions, and inflating cloud token costs.**

To solve this, AGI Agent Kit natively implements the **Phase-Reset Pattern** adopted from OpenSquad.

## Core Directives

1. **Clean Context Boundaries**: Each discrete phase of a playbook or workflow MUST run in a completely fresh context execution.
2. **Disk-First Handoffs**: Phases may NEVER pass conversation history to the next phase. They must communicate exclusively by writing strictly-typed output files (e.g., `.tmp/phase-1-discovery.md`).
3. **Validation Gates**: Output files must be deterministically checked (via `#32 Output Gates`) before the orchestrator launches the next phase.

## Workflow Engine Integration

When defining a playbook in `data/workflows.json`, you must append `"phase_boundary": true` to steps that represent major phase shifts.

```json
{
  "step": 3,
  "action": "Investigate source references",
  "phase_boundary": true
}
```

When the `workflow_engine.py` orchestrator hits a flag set to `true`:
1. It immediately terminates the current CLI session/execution subshell.
2. It invokes a *fresh* memory injection reading only the outputs from the designated `<step_id>.yaml` artifact.
3. It initializes the next team/agent with a brand-new context window.

## Cost Savings

Enforcing Phase-Resets provides a linear `O(n)` reduction in token costs (where `n` is the number of phases), compared to an exponentially accumulating cost of `O(n^2)` for a continuous chat session.
