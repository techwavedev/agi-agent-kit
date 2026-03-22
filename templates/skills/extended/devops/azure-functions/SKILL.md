---
name: azure-functions
description: "Expert patterns for Azure Functions development including isolated worker model, Durable Functions orchestration, cold start optimization, and production patterns. Covers .NET, Python, and Node.js ..."
risk: unknown
source: "vibeship-spawner-skills (Apache 2.0)"
date_added: "2026-02-27"
---

# Azure Functions

## Patterns

### Isolated Worker Model (.NET)

Modern .NET execution model with process isolation

### Node.js v4 Programming Model

Modern code-centric approach for TypeScript/JavaScript

### Python v2 Programming Model

Decorator-based approach for Python functions

## Anti-Patterns

### ❌ Blocking Async Calls

### ❌ New HttpClient Per Request

### ❌ In-Process Model for New Projects

## ⚠️ Sharp Edges

| Issue | Severity | Solution |
|-------|----------|----------|
| Issue | high | ## Use async pattern with Durable Functions |
| Issue | high | ## Use IHttpClientFactory (Recommended) |
| Issue | high | ## Always use async/await |
| Issue | medium | ## Configure maximum timeout (Consumption) |
| Issue | high | ## Use isolated worker for new projects |
| Issue | medium | ## Configure Application Insights properly |
| Issue | medium | ## Check extension bundle (most common) |
| Issue | medium | ## Add warmup trigger to initialize your code |

## When to Use
This skill is applicable to execute the workflow or actions described in the overview.

---

<!-- AGI-INTEGRATION-START -->

## AGI Framework Integration

> **Adapted for [@techwavedev/agi-agent-kit](https://www.npmjs.com/package/@techwavedev/agi-agent-kit)**
> Original source: [antigravity-awesome-skills](https://github.com/sickn33/antigravity-awesome-skills)

### Memory-First Protocol

Retrieve prior deployment configurations, rollback procedures, and incident post-mortems. Avoid re-discovering infrastructure patterns.

```bash
# Check for prior infrastructure context before starting
python3 execution/memory_manager.py auto --query "deployment configuration and patterns for Azure Functions"
```

### Storing Results

After completing work, store infrastructure decisions for future sessions:

```bash
python3 execution/memory_manager.py store \
  --content "Deployment pipeline: configured blue-green deployment with health checks on port 8080" \
  --type technical --project <project> \
  --tags azure-functions devops
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
