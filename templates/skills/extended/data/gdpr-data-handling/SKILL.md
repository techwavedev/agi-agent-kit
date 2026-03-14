---
name: gdpr-data-handling
description: "Implement GDPR-compliant data handling with consent management, data subject rights, and privacy by design. Use when building systems that process EU personal data, implementing privacy controls, o..."
risk: unknown
source: community
date_added: "2026-02-27"
---

# GDPR Data Handling

Practical implementation guide for GDPR-compliant data processing, consent management, and privacy controls.

## Use this skill when

- Building systems that process EU personal data
- Implementing consent management
- Handling data subject requests (DSRs)
- Conducting GDPR compliance reviews
- Designing privacy-first architectures
- Creating data processing agreements

## Do not use this skill when

- The task is unrelated to gdpr data handling
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

Cache data schemas, transformation rules, and query patterns. BM25 excels at finding specific column names, table references, and SQL patterns.

```bash
# Check for prior data engineering context before starting
python3 execution/memory_manager.py auto --query "data processing patterns and pipeline configurations for Gdpr Data Handling"
```

### Storing Results

After completing work, store data engineering decisions for future sessions:

```bash
python3 execution/memory_manager.py store \
  --content "Data pipeline: ETL from PostgreSQL to Qdrant, 50K records/batch, incremental sync via updated_at" \
  --type technical --project <project> \
  --tags gdpr-data-handling data
```

### Multi-Agent Collaboration

Share data schema changes with backend and frontend agents so they update their models accordingly.

```bash
python3 execution/cross_agent_context.py store \
  --agent "<your-agent>" \
  --action "Data pipeline implemented — ETL processing with validation, deduplication, and error recovery" \
  --project <project>
```

<!-- AGI-INTEGRATION-END -->
