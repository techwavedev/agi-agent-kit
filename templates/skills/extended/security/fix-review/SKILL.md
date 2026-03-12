---
name: fix-review
description: "Verify fix commits address audit findings without new bugs"
risk: safe
source: "https://github.com/trailofbits/skills/tree/main/plugins/fix-review"
date_added: "2026-02-27"
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

<!-- AGI-INTEGRATION-START -->

## AGI Framework Integration

> **Adapted for [@techwavedev/agi-agent-kit](https://www.npmjs.com/package/@techwavedev/agi-agent-kit)**
> Original source: [antigravity-awesome-skills](https://github.com/sickn33/antigravity-awesome-skills)

### Memory-First Protocol

Cache compliance check results to avoid re-running expensive AWS API calls. Retrieve prior audit findings to track remediation progress across sessions.

```bash
# Check for prior security context before starting
python3 execution/memory_manager.py auto --query "prior security audit results for Fix Review"
```

### Storing Results

After completing work, store security decisions for future sessions:

```bash
python3 execution/memory_manager.py store \
  --content "Audit findings: 3 critical IAM misconfigurations found and remediated" \
  --type technical --project <project> \
  --tags fix-review security
```

### Multi-Agent Collaboration

Share security findings with other agents so they avoid introducing vulnerabilities in their code changes.

```bash
python3 execution/cross_agent_context.py store \
  --agent "<your-agent>" \
  --action "Completed security audit — 3 critical findings fixed, compliance score 94%" \
  --project <project>
```

### Signed Audit Trail

All security findings are cryptographically signed with the agent's Ed25519 identity, providing tamper-proof audit logs for compliance reporting.

### Semantic Cache for Compliance

Cache compliance check results (`semantic_cache.py`) to avoid redundant AWS API calls. Cache hit at similarity >0.92 returns prior results instantly.

<!-- AGI-INTEGRATION-END -->
