---
name: server-management
description: Server management principles and decision-making. Process management, monitoring strategy, and scaling decisions. Teaches thinking, not commands.
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
---

# Server Management

> Server management principles for production operations.
> **Learn to THINK, not memorize commands.**

---

## 1. Process Management Principles

### Tool Selection

| Scenario | Tool |
|----------|------|
| **Node.js app** | PM2 (clustering, reload) |
| **Any app** | systemd (Linux native) |
| **Containers** | Docker/Podman |
| **Orchestration** | Kubernetes, Docker Swarm |

### Process Management Goals

| Goal | What It Means |
|------|---------------|
| **Restart on crash** | Auto-recovery |
| **Zero-downtime reload** | No service interruption |
| **Clustering** | Use all CPU cores |
| **Persistence** | Survive server reboot |

---

## 2. Monitoring Principles

### What to Monitor

| Category | Key Metrics |
|----------|-------------|
| **Availability** | Uptime, health checks |
| **Performance** | Response time, throughput |
| **Errors** | Error rate, types |
| **Resources** | CPU, memory, disk |

### Alert Severity Strategy

| Level | Response |
|-------|----------|
| **Critical** | Immediate action |
| **Warning** | Investigate soon |
| **Info** | Review daily |

### Monitoring Tool Selection

| Need | Options |
|------|---------|
| Simple/Free | PM2 metrics, htop |
| Full observability | Grafana, Datadog |
| Error tracking | Sentry |
| Uptime | UptimeRobot, Pingdom |

---

## 3. Log Management Principles

### Log Strategy

| Log Type | Purpose |
|----------|---------|
| **Application logs** | Debug, audit |
| **Access logs** | Traffic analysis |
| **Error logs** | Issue detection |

### Log Principles

1. **Rotate logs** to prevent disk fill
2. **Structured logging** (JSON) for parsing
3. **Appropriate levels** (error/warn/info/debug)
4. **No sensitive data** in logs

---

## 4. Scaling Decisions

### When to Scale

| Symptom | Solution |
|---------|----------|
| High CPU | Add instances (horizontal) |
| High memory | Increase RAM or fix leak |
| Slow response | Profile first, then scale |
| Traffic spikes | Auto-scaling |

### Scaling Strategy

| Type | When to Use |
|------|-------------|
| **Vertical** | Quick fix, single instance |
| **Horizontal** | Sustainable, distributed |
| **Auto** | Variable traffic |

---

## 5. Health Check Principles

### What Constitutes Healthy

| Check | Meaning |
|-------|---------|
| **HTTP 200** | Service responding |
| **Database connected** | Data accessible |
| **Dependencies OK** | External services reachable |
| **Resources OK** | CPU/memory not exhausted |

### Health Check Implementation

- Simple: Just return 200
- Deep: Check all dependencies
- Choose based on load balancer needs

---

## 6. Security Principles

| Area | Principle |
|------|-----------|
| **Access** | SSH keys only, no passwords |
| **Firewall** | Only needed ports open |
| **Updates** | Regular security patches |
| **Secrets** | Environment vars, not files |
| **Audit** | Log access and changes |

---

## 7. Troubleshooting Priority

When something's wrong:

1. **Check if running** (process status)
2. **Check logs** (error messages)
3. **Check resources** (disk, memory, CPU)
4. **Check network** (ports, DNS)
5. **Check dependencies** (database, APIs)

---

## 8. Anti-Patterns

| ❌ Don't | ✅ Do |
|----------|-------|
| Run as root | Use non-root user |
| Ignore logs | Set up log rotation |
| Skip monitoring | Monitor from day one |
| Manual restarts | Auto-restart config |
| No backups | Regular backup schedule |

---

> **Remember:** A well-managed server is boring. That's the goal.

## AGI Framework Integration

### Qdrant Memory Integration

Before executing complex tasks with this skill:
```bash
python3 execution/memory_manager.py auto --query "<task summary>"
```

**Decision Tree:**
- **Cache hit?** Use cached response directly — no need to re-process.
- **Memory match?** Inject `context_chunks` into your reasoning.
- **No match?** Proceed normally, then store results:

```bash
python3 execution/memory_manager.py store \
  --content "Description of what was decided/solved" \
  --type decision \
  --tags server-management <relevant-tags>
```

> **Note:** Storing automatically updates both Vector (Qdrant) and Keyword (BM25) indices.

### Agent Team Collaboration

- **Strategy**: This skill communicates via the shared memory system.
- **Orchestration**: Invoked by `orchestrator` via intelligent routing.
- **Context Sharing**: Always read previous agent outputs from memory before starting.

### Local LLM Support

When available, use local Ollama models for embedding and lightweight inference:
- Embeddings: `nomic-embed-text` via Qdrant memory system
- Lightweight analysis: Local models reduce API costs for repetitive patterns
