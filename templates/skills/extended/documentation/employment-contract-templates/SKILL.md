---
name: employment-contract-templates
description: "Create employment contracts, offer letters, and HR policy documents following legal best practices. Use when drafting employment agreements, creating HR policies, or standardizing employment docume..."
risk: unknown
source: community
date_added: "2026-02-27"
---

# Employment Contract Templates

Templates and patterns for creating legally sound employment documentation including contracts, offer letters, and HR policies.

## Use this skill when

- Drafting employment contracts
- Creating offer letters
- Writing employee handbooks
- Developing HR policies
- Standardizing employment documentation
- Preparing onboarding documentation

## Do not use this skill when

- You need jurisdiction-specific legal advice
- The task requires licensed counsel review
- The request is unrelated to employment documentation

## Instructions

- Confirm jurisdiction, employment type, and required clauses.
- Choose a document template and tailor role-specific terms.
- Validate compensation, benefits, and compliance requirements.
- Add signature, confidentiality, and IP assignment terms as needed.
- If detailed templates are required, open `resources/implementation-playbook.md`.

## Safety

- These templates are not legal advice; consult qualified counsel before use.

## Resources

- `resources/implementation-playbook.md` for detailed templates and checklists.

---

<!-- AGI-INTEGRATION-START -->

## AGI Framework Integration

> **Adapted for [@techwavedev/agi-agent-kit](https://www.npmjs.com/package/@techwavedev/agi-agent-kit)**
> Original source: [antigravity-awesome-skills](https://github.com/sickn33/antigravity-awesome-skills)

### Memory-First Protocol

Retrieve prior documentation structure and content to maintain consistency. Cache generated docs to avoid regenerating unchanged sections.

```bash
# Check for prior documentation context before starting
python3 execution/memory_manager.py auto --query "documentation patterns and prior content for Employment Contract Templates"
```

### Storing Results

After completing work, store documentation decisions for future sessions:

```bash
python3 execution/memory_manager.py store \
  --content "Documentation: API reference generated from OpenAPI spec, deployment guide updated with new env vars" \
  --type technical --project <project> \
  --tags employment-contract-templates documentation
```

### Multi-Agent Collaboration

Share documentation changes with all agents so they reference the latest guides and APIs.

```bash
python3 execution/cross_agent_context.py store \
  --agent "<your-agent>" \
  --action "Documentation updated — API reference, deployment guide, and CHANGELOG all current" \
  --project <project>
```

### Agent Team: Documentation

This skill pairs with `documentation_team` — dispatched automatically after any code change to keep docs in sync.

<!-- AGI-INTEGRATION-END -->
