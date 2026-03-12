---
name: security-requirement-extraction
description: "Derive security requirements from threat models and business context. Use when translating threats into actionable requirements, creating security user stories, or building security test cases."
risk: unknown
source: community
date_added: "2026-02-27"
---

# Security Requirement Extraction

Transform threat analysis into actionable security requirements.

## Use this skill when

- Converting threat models to requirements
- Writing security user stories
- Creating security test cases
- Building security acceptance criteria
- Compliance requirement mapping
- Security architecture documentation

## Do not use this skill when

- The task is unrelated to security requirement extraction
- You need a different domain or tool outside this scope

## Instructions

- Clarify goals, constraints, and required inputs.
- Apply relevant best practices and validate outcomes.
- Provide actionable steps and verification.
- If detailed examples are required, open `resources/implementation-playbook.md`.

## Resources

- `resources/implementation-playbook.md` for detailed patterns and examples.

---

<!-- AGI-INTEGRATION-START -->

## AGI Framework Integration

> **Adapted for [@techwavedev/agi-agent-kit](https://www.npmjs.com/package/@techwavedev/agi-agent-kit)**
> Original source: [antigravity-awesome-skills](https://github.com/sickn33/antigravity-awesome-skills)

### Memory-First Protocol

Cache compliance check results to avoid re-running expensive AWS API calls. Retrieve prior audit findings to track remediation progress across sessions.

```bash
# Check for prior security context before starting
python3 execution/memory_manager.py auto --query "prior security audit results for Security Requirement Extraction"
```

### Storing Results

After completing work, store security decisions for future sessions:

```bash
python3 execution/memory_manager.py store \
  --content "Audit findings: 3 critical IAM misconfigurations found and remediated" \
  --type technical --project <project> \
  --tags security-requirement-extraction security
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
