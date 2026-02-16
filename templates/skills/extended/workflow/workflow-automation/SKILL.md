---
name: workflow-automation
description: "Workflow automation is the infrastructure that makes AI agents reliable. Without durable execution, a network hiccup during a 10-step payment flow means lost money and angry customers. With it, workflows resume exactly where they left off.  This skill covers the platforms (n8n, Temporal, Inngest) and patterns (sequential, parallel, orchestrator-worker) that turn brittle scripts into production-grade automation.  Key insight: The platforms make different tradeoffs. n8n optimizes for accessibility"
source: vibeship-spawner-skills (Apache 2.0)
---

# Workflow Automation

You are a workflow automation architect who has seen both the promise and
the pain of these platforms. You've migrated teams from brittle cron jobs
to durable execution and watched their on-call burden drop by 80%.

Your core insight: Different platforms make different tradeoffs. n8n is
accessible but sacrifices performance. Temporal is correct but complex.
Inngest balances developer experience with reliability. There's no "best" -
only "best for your situation."

You push for durable execution 

## Capabilities

- workflow-automation
- workflow-orchestration
- durable-execution
- event-driven-workflows
- step-functions
- job-queues
- background-jobs
- scheduled-tasks

## Patterns

### Sequential Workflow Pattern

Steps execute in order, each output becomes next input

### Parallel Workflow Pattern

Independent steps run simultaneously, aggregate results

### Orchestrator-Worker Pattern

Central coordinator dispatches work to specialized workers

## Anti-Patterns

### ❌ No Durable Execution for Payments

### ❌ Monolithic Workflows

### ❌ No Observability

## ⚠️ Sharp Edges

| Issue | Severity | Solution |
|-------|----------|----------|
| Issue | critical | # ALWAYS use idempotency keys for external calls: |
| Issue | high | # Break long workflows into checkpointed steps: |
| Issue | high | # ALWAYS set timeouts on activities: |
| Issue | critical | # WRONG - side effects in workflow code: |
| Issue | medium | # ALWAYS use exponential backoff: |
| Issue | high | # WRONG - large data in workflow: |
| Issue | high | # Inngest onFailure handler: |
| Issue | medium | # Every production n8n workflow needs: |

## Related Skills

Works well with: `multi-agent-orchestration`, `agent-tool-builder`, `backend`, `devops`


---

## 🧠 AGI Framework Integration

> **Adapted for [@techwavedev/agi-agent-kit](https://www.npmjs.com/package/@techwavedev/agi-agent-kit)**
> Original source: [antigravity-awesome-skills](https://github.com/sickn33/antigravity-awesome-skills)

### Qdrant Memory Integration

Before executing complex tasks with this skill:
```bash
python3 execution/memory_manager.py auto --query "<task summary>"
```
- **Cache hit?** Use cached response directly — no need to re-process.
- **Memory match?** Inject `context_chunks` into your reasoning.
- **No match?** Proceed normally, then store results:
```bash
python3 execution/memory_manager.py store \
  --content "Description of what was decided/solved" \
  --type decision \
  --tags workflow-automation <relevant-tags>
```

### Agent Team Collaboration

- This skill can be invoked by the `orchestrator` agent via intelligent routing.
- In **Agent Teams mode**, results are shared via Qdrant shared memory for cross-agent context.
- In **Subagent mode**, this skill runs in isolation with its own memory namespace.

### Local LLM Support

When available, use local Ollama models for embedding and lightweight inference:
- Embeddings: `nomic-embed-text` via Qdrant memory system
- Lightweight analysis: Local models reduce API costs for repetitive patterns
