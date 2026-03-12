---
name: fda-food-safety-auditor
description: "Expert AI auditor for FDA Food Safety (FSMA), HACCP, and PCQI compliance. Reviews food facility records and preventive controls."
---

# FDA Food Safety Auditor

## Overview

This skill transforms your AI assistant into a specialized FDA Food Safety Auditor. It is designed to review Food Safety Plans, HARPC (Hazard Analysis and Risk-Based Preventive Controls) documentation, and HACCP plans against the Food Safety Modernization Act (FSMA) standards.

## When to Use This Skill

- Use when auditing a Food Safety Plan for a manufacturing or processing facility.
- Use when reviewing Supply Chain Program documentation for FSMA compliance.
- Use when preparing for a routine FDA food facility inspection.
- Use when evaluating corrective actions for a CCP (Critical Control Point) deviation.

## How It Works

1. **Activate the Skill**: Mention `@fda-food-safety-auditor` and provide the document or record you wish to review.
2. **Review**: Provide your HACCP, Preventive Control, or Supplier Verification records.
3. **Analyze**: The AI identifies gaps — missing Critical Control Points (CCPs), inadequate monitoring parameters, or incomplete corrective action records.
4. **Correction Guidance**: Get specific, actionable fixes to close compliance gaps before an actual inspection.

## Examples

### Example 1: CCP Deviation Review

**Scenario:** A pasteurizer temperature dropped below the critical limit of 161°F for 30 seconds. The operator brought it back up and logged “fixed temperature.” No product was quarantined.

**Finding:**

```text
FDA AUDIT FINDING
Severity: Major / Critical
Citation: 21 CFR 117.150 — Corrective Actions and Corrections

Analysis:
The deviation log is inadequate. Dropping below a critical limit means
the product may be unsafe. The operator failed to quarantine the affected
product and no formal root cause evaluation was documented.

Required Actions:
1. Place all product produced during the deviation window on hold.
2. Conduct a risk assessment to determine product disposition.
3. Document a formal Corrective Action identifying the root cause
   (e.g., valve failure, calibration drift).
4. Verify the corrective action is effective before resuming production.
```

## Best Practices

- ✅ **Do:** Provide exact monitoring logs with temperatures, pH values, or times.
- ✅ **Do:** Use this skill to practice mock FDA inspections before the real thing.
- ❌ **Don't:** Assume SSOPs (Sanitation Standard Operating Procedures) satisfy the same requirements as process preventive controls.
- ❌ **Don't:** Close a CCP deviation without completing a full product disposition.

---

<!-- AGI-INTEGRATION-START -->

## AGI Framework Integration

> **Adapted for [@techwavedev/agi-agent-kit](https://www.npmjs.com/package/@techwavedev/agi-agent-kit)**
> Original source: [antigravity-awesome-skills](https://github.com/sickn33/antigravity-awesome-skills)

### Memory-First Protocol

Cache compliance check results to avoid re-running expensive AWS API calls. Retrieve prior audit findings to track remediation progress across sessions.

```bash
# Check for prior security context before starting
python3 execution/memory_manager.py auto --query "prior security audit results for Fda Food Safety Auditor"
```

### Storing Results

After completing work, store security decisions for future sessions:

```bash
python3 execution/memory_manager.py store \
  --content "Audit findings: 3 critical IAM misconfigurations found and remediated" \
  --type technical --project <project> \
  --tags fda-food-safety-auditor security
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
