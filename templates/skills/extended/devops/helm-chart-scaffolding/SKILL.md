---
name: helm-chart-scaffolding
description: "Design, organize, and manage Helm charts for templating and packaging Kubernetes applications with reusable configurations. Use when creating Helm charts, packaging Kubernetes applications, or impl..."
risk: unknown
source: community
date_added: "2026-02-27"
---

# Helm Chart Scaffolding

Comprehensive guidance for creating, organizing, and managing Helm charts for packaging and deploying Kubernetes applications.

## Use this skill when

Use this skill when you need to:
- Create new Helm charts from scratch
- Package Kubernetes applications for distribution
- Manage multi-environment deployments with Helm
- Implement templating for reusable Kubernetes manifests
- Set up Helm chart repositories
- Follow Helm best practices and conventions

## Do not use this skill when

- The task is unrelated to helm chart scaffolding
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

Retrieve prior deployment configurations, rollback procedures, and incident post-mortems. Avoid re-discovering infrastructure patterns.

```bash
# Check for prior infrastructure context before starting
python3 execution/memory_manager.py auto --query "deployment configuration and patterns for Helm Chart Scaffolding"
```

### Storing Results

After completing work, store infrastructure decisions for future sessions:

```bash
python3 execution/memory_manager.py store \
  --content "Deployment pipeline: configured blue-green deployment with health checks on port 8080" \
  --type technical --project <project> \
  --tags helm-chart-scaffolding devops
```

### Multi-Agent Collaboration

Broadcast deployment changes so frontend and backend agents update their configurations accordingly.

```bash
python3 execution/cross_agent_context.py store \
  --agent "<your-agent>" \
  --action "Deployed infrastructure changes — updated CI/CD pipeline with new health check endpoints" \
  --project <project>
```

### Playbook Integration

Use the `ship-saas-mvp` or `full-stack-deploy` playbook to sequence this skill with testing, documentation, and deployment verification.

<!-- AGI-INTEGRATION-END -->
