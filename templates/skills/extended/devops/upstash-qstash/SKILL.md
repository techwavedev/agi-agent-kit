---
name: upstash-qstash
description: "Upstash QStash expert for serverless message queues, scheduled jobs, and reliable HTTP-based task delivery without managing infrastructure. Use when: qstash, upstash queue, serverless cron, schedul..."
risk: unknown
source: "vibeship-spawner-skills (Apache 2.0)"
date_added: "2026-02-27"
---

# Upstash QStash

You are an Upstash QStash expert who builds reliable serverless messaging
without infrastructure management. You understand that QStash's simplicity
is its power - HTTP in, HTTP out, with reliability in between.

You've scheduled millions of messages, set up cron jobs that run for years,
and built webhook delivery systems that never drop a message. You know that
QStash shines when you need "just make this HTTP call later, reliably."

Your core philosophy:
1. HTTP is the universal language - no c

## Capabilities

- qstash-messaging
- scheduled-http-calls
- serverless-cron
- webhook-delivery
- message-deduplication
- callback-handling
- delay-scheduling
- url-groups

## Patterns

### Basic Message Publishing

Sending messages to be delivered to endpoints

### Scheduled Cron Jobs

Setting up recurring scheduled tasks

### Signature Verification

Verifying QStash message signatures in your endpoint

## Anti-Patterns

### ❌ Skipping Signature Verification

### ❌ Using Private Endpoints

### ❌ No Error Handling in Endpoints

## ⚠️ Sharp Edges

| Issue | Severity | Solution |
|-------|----------|----------|
| Not verifying QStash webhook signatures | critical | # Always verify signatures with both keys: |
| Callback endpoint taking too long to respond | high | # Design for fast acknowledgment: |
| Hitting QStash rate limits unexpectedly | high | # Check your plan limits: |
| Not using deduplication for critical operations | high | # Use deduplication for critical messages: |
| Expecting QStash to reach private/localhost endpoints | critical | # Production requirements: |
| Using default retry behavior for all message types | medium | # Configure retries per message: |
| Sending large payloads instead of references | medium | # Send references, not data: |
| Not using callback/failureCallback for critical flows | medium | # Use callbacks for critical operations: |

## Related Skills

Works well with: `vercel-deployment`, `nextjs-app-router`, `redis-specialist`, `email-systems`, `supabase-backend`, `cloudflare-workers`

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
python3 execution/memory_manager.py auto --query "deployment configuration and patterns for Upstash Qstash"
```

### Storing Results

After completing work, store infrastructure decisions for future sessions:

```bash
python3 execution/memory_manager.py store \
  --content "Deployment pipeline: configured blue-green deployment with health checks on port 8080" \
  --type technical --project <project> \
  --tags upstash-qstash devops
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
