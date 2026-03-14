---
name: debugging-strategies
description: "Master systematic debugging techniques, profiling tools, and root cause analysis to efficiently track down bugs across any codebase or technology stack. Use when investigating bugs, performance iss..."
risk: unknown
source: community
date_added: "2026-02-27"
---

# Debugging Strategies

Transform debugging from frustrating guesswork into systematic problem-solving with proven strategies, powerful tools, and methodical approaches.

## Use this skill when

- Tracking down elusive bugs
- Investigating performance issues
- Debugging production incidents
- Analyzing crash dumps or stack traces
- Debugging distributed systems

## Do not use this skill when

- There is no reproducible issue or observable symptom
- The task is purely feature development
- You cannot access logs, traces, or runtime signals

## Instructions

- Reproduce the issue and capture logs, traces, and environment details.
- Form hypotheses and design controlled experiments.
- Narrow scope with binary search and targeted instrumentation.
- Document findings and verify the fix.
- If detailed playbooks are required, open `resources/implementation-playbook.md`.

## Resources

- `resources/implementation-playbook.md` for detailed debugging patterns and checklists.

---

<!-- AGI-INTEGRATION-START -->

## AGI Framework Integration

> **Adapted for [@techwavedev/agi-agent-kit](https://www.npmjs.com/package/@techwavedev/agi-agent-kit)**
> Original source: [antigravity-awesome-skills](https://github.com/sickn33/antigravity-awesome-skills)

### Memory-First Protocol

Retrieve prior error resolutions and debugging strategies. The hybrid search excels here — BM25 finds exact error codes/stack traces while vectors find semantically similar past issues.

```bash
# Check for prior debugging/diagnostics context before starting
python3 execution/memory_manager.py auto --query "error patterns and debugging solutions for Debugging Strategies"
```

### Storing Results

After completing work, store debugging/diagnostics decisions for future sessions:

```bash
python3 execution/memory_manager.py store \
  --content "Root cause: memory leak from unclosed DB connections in pool — fixed with context manager" \
  --type error --project <project> \
  --tags debugging-strategies debugging
```

### Multi-Agent Collaboration

Store error resolutions so any agent encountering the same issue retrieves the fix instantly instead of re-debugging.

```bash
python3 execution/cross_agent_context.py store \
  --agent "<your-agent>" \
  --action "Debugged and resolved critical issue — root cause documented for future reference" \
  --project <project>
```

### Self-Annealing Loop

When this skill resolves an error, store the fix in memory AND update the relevant directive. The system gets stronger with each resolved issue.

### BM25 Exact Match

Error codes, stack traces, and log messages are best found via BM25 keyword search. The hybrid system automatically uses exact matching for these patterns.

<!-- AGI-INTEGRATION-END -->
