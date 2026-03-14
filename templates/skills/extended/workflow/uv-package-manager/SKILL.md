---
name: uv-package-manager
description: "Master the uv package manager for fast Python dependency management, virtual environments, and modern Python project workflows. Use when setting up Python projects, managing dependencies, or optimi..."
risk: unknown
source: community
date_added: "2026-02-27"
---

# UV Package Manager

Comprehensive guide to using uv, an extremely fast Python package installer and resolver written in Rust, for modern Python project management and dependency workflows.

## Use this skill when

- Setting up new Python projects quickly
- Managing Python dependencies faster than pip
- Creating and managing virtual environments
- Installing Python interpreters
- Resolving dependency conflicts efficiently
- Migrating from pip/pip-tools/poetry
- Speeding up CI/CD pipelines
- Managing monorepo Python projects
- Working with lockfiles for reproducible builds
- Optimizing Docker builds with Python dependencies

## Do not use this skill when

- The task is unrelated to uv package manager
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

Cache workflow configurations and automation patterns. Retrieve prior pipeline designs to avoid re-building similar flows from scratch.

```bash
# Check for prior workflow/automation context before starting
python3 execution/memory_manager.py auto --query "automation patterns and workflow configurations for Uv Package Manager"
```

### Storing Results

After completing work, store workflow/automation decisions for future sessions:

```bash
python3 execution/memory_manager.py store \
  --content "Workflow: automated data pipeline with retry logic, dead-letter queue, and Slack alerts on failure" \
  --type technical --project <project> \
  --tags uv-package-manager workflow
```

### Multi-Agent Collaboration

Share workflow state with other agents so they can trigger, monitor, or extend the automation.

```bash
python3 execution/cross_agent_context.py store \
  --agent "<your-agent>" \
  --action "Workflow automation deployed — pipeline processing 1000+ events/day with 99.9% success rate" \
  --project <project>
```

### Playbook Engine

Combine this skill with others using the Playbook Engine (`execution/workflow_engine.py`) for guided multi-step automation with progress tracking.

<!-- AGI-INTEGRATION-END -->
