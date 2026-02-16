---
name: fix-review
description: "Verify fix commits address audit findings without new bugs"
source: "https://github.com/trailofbits/skills/tree/main/plugins/fix-review"
risk: safe
---

# Fix Review

## Overview

Verify that fix commits properly address audit findings without introducing new bugs or security vulnerabilities.

## When to Use This Skill

Use this skill when you need to verify fix commits address audit findings without new bugs.

Use this skill when:
- Reviewing commits that address security audit findings
- Verifying that fixes don't introduce new vulnerabilities
- Ensuring code changes properly resolve identified issues
- Validating that remediation efforts are complete and correct

## Instructions

This skill helps verify that fix commits properly address audit findings:

1. **Review Fix Commits**: Analyze commits that claim to fix audit findings
2. **Verify Resolution**: Ensure the original issue is properly addressed
3. **Check for Regressions**: Verify no new bugs or vulnerabilities are introduced
4. **Validate Completeness**: Ensure all aspects of the finding are resolved

## Review Process

When reviewing fix commits:

1. Compare the fix against the original audit finding
2. Verify the fix addresses the root cause, not just symptoms
3. Check for potential side effects or new issues
4. Validate that tests cover the fixed scenario
5. Ensure no similar vulnerabilities exist elsewhere

## Best Practices

- Review fixes in context of the full codebase
- Verify test coverage for the fixed issue
- Check for similar patterns that might need fixing
- Ensure fixes follow security best practices
- Document the resolution approach

## Resources

For more information, see the [source repository](https://github.com/trailofbits/skills/tree/main/plugins/fix-review).


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
  --tags fix-review <relevant-tags>
```

### Agent Team Collaboration

- This skill can be invoked by the `orchestrator` agent via intelligent routing.
- In **Agent Teams mode**, results are shared via Qdrant shared memory for cross-agent context.
- In **Subagent mode**, this skill runs in isolation with its own memory namespace.

### Local LLM Support

When available, use local Ollama models for embedding and lightweight inference:
- Embeddings: `nomic-embed-text` via Qdrant memory system
- Lightweight analysis: Local models reduce API costs for repetitive patterns
