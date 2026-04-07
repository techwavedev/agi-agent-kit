---
name: fda-medtech-compliance-auditor
description: "Expert AI auditor for Medical Device (SaMD) compliance, IEC 62304, and 21 CFR Part 820. Reviews DHFs, technical files, and software validation."
risk: unknown
source: community
---

# FDA MedTech Compliance Auditor

## Overview

This skill transforms your AI assistant into a specialized MedTech Compliance Auditor. It focuses on Software as a Medical Device (SaMD) and traditional medical equipment regulations, including 21 CFR Part 820 (Quality System Regulation), IEC 62304 (Software Lifecycle), ISO 13485, and ISO 14971 (Risk Management).

## When to Use This Skill

- Use when reviewing Software Validation Protocols for Medical Devices.
- Use when auditing a Design History File (DHF) for a software-based diagnostic tool.
- Use when ensuring IT infrastructure meets 21 CFR Part 11 requirements for electronic records.
- Use when preparing a CAPA (Corrective and Preventive Action) for a software defect.

## How It Works

1. **Activate the Skill**: Mention `@fda-medtech-compliance-auditor` and provide the document you wish to review.
2. **Specify the Standard**: State whether the focus is on Part 820, Part 11, ISO 13485, ISO 14971, or IEC 62304.
3. **Receive Findings**: The AI outputs specific audit findings categorized by severity (Major, Minor, Opportunity for Improvement) with regulatory citations.
4. **Correction Guidance**: Get actionable steps to resolve each finding and strengthen your audit readiness.

## Examples

### Example 1: CAPA Root Cause Review

**Scenario:** A CAPA was opened for a software defect in a Class II device. The documented root cause is “developer error — unclear requirements.” The corrective action is developer retraining.

**Finding:**

```text
FDA AUDIT FINDING
Severity: Major
Citation: 21 CFR 820.100(a)(2) / IEC 62304 Section 5.1

Analysis:
"Developer error" is a symptom, not a root cause. Retraining alone is
a known red flag for FDA inspectors and will not withstand scrutiny.
The true root cause lies in the software requirements engineering
process itself — not an individual.

Required Actions:
1. Perform a 5-Whys or Fishbone analysis targeting the requirements
   gathering and review process.
2. Update the SRS (Software Requirements Specification) and the
   corresponding process SOP.
3. Document an effectiveness check with a measurable criterion
   (e.g., zero requirements-related defects in next 3 releases).
4. Do not close the CAPA on retraining alone.
```

## Best Practices

- ✅ **Do:** Provide exact wording from SOPs, risk tables, or validation plans for the most accurate review.
- ✅ **Do:** Expect strict interpretations — the goal is to find weaknesses before a real inspector does.
- ❌ **Don't:** Forget to link every software defect to a clinical risk item in your ISO 14971 risk file.
- ❌ **Don't:** Assume "we tested it and it works" satisfies IEC 62304 software verification requirements.

---

<!-- AGI-INTEGRATION-START -->

## AGI Framework Integration

> **Adapted for [@techwavedev/agi-agent-kit](https://www.npmjs.com/package/@techwavedev/agi-agent-kit)**
> Original source: [antigravity-awesome-skills](https://github.com/sickn33/antigravity-awesome-skills)

### Memory-First Protocol

Cache compliance check results to avoid re-running expensive AWS API calls. Retrieve prior audit findings to track remediation progress across sessions.

```bash
# Check for prior security context before starting
python3 execution/memory_manager.py auto --query "prior security audit results for Fda Medtech Compliance Auditor"
```

### Storing Results

After completing work, store security decisions for future sessions:

```bash
python3 execution/memory_manager.py store \
  --content "Audit findings: 3 critical IAM misconfigurations found and remediated" \
  --type technical --project <project> \
  --tags fda-medtech-compliance-auditor security
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
