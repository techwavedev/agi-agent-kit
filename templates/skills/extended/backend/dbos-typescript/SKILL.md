---
name: dbos-typescript
description: "Guide for building reliable, fault-tolerant TypeScript applications with DBOS durable workflows. Use when adding DBOS to existing TypeScript code, creating workflows and steps, or using queues for concurrency control."
risk: safe
source: "https://docs.dbos.dev/"
date_added: "2026-02-27"
---

# DBOS TypeScript Best Practices

Guide for building reliable, fault-tolerant TypeScript applications with DBOS durable workflows.

## When to Use
Reference these guidelines when:
- Adding DBOS to existing TypeScript code
- Creating workflows and steps
- Using queues for concurrency control
- Implementing workflow communication (events, messages, streams)
- Configuring and launching DBOS applications
- Using DBOSClient from external applications
- Testing DBOS applications

## Rule Categories by Priority

| Priority | Category | Impact | Prefix |
|----------|----------|--------|--------|
| 1 | Lifecycle | CRITICAL | `lifecycle-` |
| 2 | Workflow | CRITICAL | `workflow-` |
| 3 | Step | HIGH | `step-` |
| 4 | Queue | HIGH | `queue-` |
| 5 | Communication | MEDIUM | `comm-` |
| 6 | Pattern | MEDIUM | `pattern-` |
| 7 | Testing | LOW-MEDIUM | `test-` |
| 8 | Client | MEDIUM | `client-` |
| 9 | Advanced | LOW | `advanced-` |

## Critical Rules

### Installation

Always install the latest version of DBOS:

```bash
npm install @dbos-inc/dbos-sdk@latest
```

### DBOS Configuration and Launch

A DBOS application MUST configure and launch DBOS before running any workflows:

```typescript
import { DBOS } from "@dbos-inc/dbos-sdk";

async function main() {
  DBOS.setConfig({
    name: "my-app",
    systemDatabaseUrl: process.env.DBOS_SYSTEM_DATABASE_URL,
  });
  await DBOS.launch();
  await myWorkflow();
}

main().catch(console.log);
```

### Workflow and Step Structure

Workflows are comprised of steps. Any function performing complex operations or accessing external services must be run as a step using `DBOS.runStep`:

```typescript
import { DBOS } from "@dbos-inc/dbos-sdk";

async function fetchData() {
  return await fetch("https://api.example.com").then(r => r.json());
}

async function myWorkflowFn() {
  const result = await DBOS.runStep(fetchData, { name: "fetchData" });
  return result;
}
const myWorkflow = DBOS.registerWorkflow(myWorkflowFn);
```

### Key Constraints

- Do NOT call, start, or enqueue workflows from within steps
- Do NOT use threads or uncontrolled concurrency to start workflows - use `DBOS.startWorkflow` or queues
- Workflows MUST be deterministic - non-deterministic operations go in steps
- Do NOT modify global variables from workflows or steps

## How to Use

Read individual rule files for detailed explanations and examples:

```
references/lifecycle-config.md
references/workflow-determinism.md
references/queue-concurrency.md
```

## References

- https://docs.dbos.dev/
- https://github.com/dbos-inc/dbos-transact-ts

---

<!-- AGI-INTEGRATION-START -->

## AGI Framework Integration

> **Adapted for [@techwavedev/agi-agent-kit](https://www.npmjs.com/package/@techwavedev/agi-agent-kit)**
> Original source: [antigravity-awesome-skills](https://github.com/sickn33/antigravity-awesome-skills)

### Memory-First Protocol

Retrieve prior API design decisions, database schema choices, and error handling patterns. Cache API response templates for consistent error formatting.

```bash
# Check for prior backend/API context before starting
python3 execution/memory_manager.py auto --query "API design patterns and architecture decisions for Dbos Typescript"
```

### Storing Results

After completing work, store backend/API decisions for future sessions:

```bash
python3 execution/memory_manager.py store \
  --content "API architecture: REST with HATEOAS, JWT auth, rate limiting at 100 req/min per tenant" \
  --type decision --project <project> \
  --tags dbos-typescript backend
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
