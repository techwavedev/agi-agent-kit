---
name: internal-comms-community
description: "To write internal communications, use this skill for:"
risk: unknown
source: community
date_added: "2026-02-27"
---

## When to use this skill
To write internal communications, use this skill for:
- 3P updates (Progress, Plans, Problems)
- Company newsletters
- FAQ responses
- Status reports
- Leadership updates
- Project updates
- Incident reports

## How to use this skill

To write any internal communication:

1. **Identify the communication type** from the request
2. **Load the appropriate guideline file** from the `examples/` directory:
    - `examples/3p-updates.md` - For Progress/Plans/Problems team updates
    - `examples/company-newsletter.md` - For company-wide newsletters
    - `examples/faq-answers.md` - For answering frequently asked questions
    - `examples/general-comms.md` - For anything else that doesn't explicitly match one of the above
3. **Follow the specific instructions** in that file for formatting, tone, and content gathering

If the communication type doesn't match any existing guideline, ask for clarification or more context about the desired format.

## Keywords
3P updates, company newsletter, company comms, weekly update, faqs, common questions, updates, internal comms

---

<!-- AGI-INTEGRATION-START -->

## AGI Framework Integration

> **Adapted for [@techwavedev/agi-agent-kit](https://www.npmjs.com/package/@techwavedev/agi-agent-kit)**
> Original source: [antigravity-awesome-skills](https://github.com/sickn33/antigravity-awesome-skills)

### Memory-First Protocol

Retrieve game design decisions, performance benchmarks, and engine configuration. Cache asset pipeline settings and build configurations.

```bash
# Check for prior game development context before starting
python3 execution/memory_manager.py auto --query "game architecture and engine patterns for Internal Comms Community"
```

### Storing Results

After completing work, store game development decisions for future sessions:

```bash
python3 execution/memory_manager.py store \
  --content "Game: ECS architecture with 60fps target, spatial partitioning for collision, asset pipeline with LOD" \
  --type technical --project <project> \
  --tags internal-comms-community gaming
```

### Multi-Agent Collaboration

Share engine decisions and performance budgets with art/design agents and QA agents.

```bash
python3 execution/cross_agent_context.py store \
  --agent "<your-agent>" \
  --action "Game feature implemented — performance profiled, asset pipeline updated, QA test plan created" \
  --project <project>
```

<!-- AGI-INTEGRATION-END -->
