---
name: hubspot-integration
description: "Authentication for single-account integrations"
risk: unknown
source: "vibeship-spawner-skills (Apache 2.0)"
date_added: "2026-02-27"
---

# HubSpot Integration

## Patterns

### OAuth 2.0 Authentication

Secure authentication for public apps

### Private App Token

Authentication for single-account integrations

### CRM Object CRUD Operations

Create, read, update, delete CRM records

## Anti-Patterns

### ❌ Using Deprecated API Keys

### ❌ Individual Requests Instead of Batch

### ❌ Polling Instead of Webhooks

## ⚠️ Sharp Edges

| Issue | Severity | Solution |
|-------|----------|----------|
| Issue | high | See docs |
| Issue | high | See docs |
| Issue | critical | See docs |
| Issue | high | See docs |
| Issue | critical | See docs |
| Issue | medium | See docs |
| Issue | high | See docs |
| Issue | medium | See docs |

## When to Use
This skill is applicable to execute the workflow or actions described in the overview.

---

<!-- AGI-INTEGRATION-START -->

## AGI Framework Integration

> **Adapted for [@techwavedev/agi-agent-kit](https://www.npmjs.com/package/@techwavedev/agi-agent-kit)**
> Original source: [antigravity-awesome-skills](https://github.com/sickn33/antigravity-awesome-skills)

### Memory-First Protocol

Retrieve prior API design decisions, database schema choices, and error handling patterns. Cache API response templates for consistent error formatting.

```bash
# Check for prior backend/API context before starting
python3 execution/memory_manager.py auto --query "API design patterns and architecture decisions for Hubspot Integration"
```

### Storing Results

After completing work, store backend/API decisions for future sessions:

```bash
python3 execution/memory_manager.py store \
  --content "API architecture: REST with HATEOAS, JWT auth, rate limiting at 100 req/min per tenant" \
  --type decision --project <project> \
  --tags hubspot-integration backend
```

### Multi-Agent Collaboration

Share API contract changes with frontend agents so they update their client code, and with QA agents for test coverage.

```bash
python3 execution/cross_agent_context.py store \
  --agent "<your-agent>" \
  --action "Implemented API endpoints — 5 new routes with OpenAPI spec and integration tests" \
  --project <project>
```

### Agent Team: Code Review

After implementation, dispatch `code_review_team` for two-stage review (spec compliance + code quality) before merging.

<!-- AGI-INTEGRATION-END -->
