---
name: microservices-patterns
description: Design microservices architectures with service boundaries, event-driven communication, and resilience patterns. Use when building distributed systems, decomposing monoliths, or implementing microservices.
---

# Microservices Patterns

Master microservices architecture patterns including service boundaries, inter-service communication, data management, and resilience patterns for building distributed systems.

## Use this skill when

- Decomposing monoliths into microservices
- Designing service boundaries and contracts
- Implementing inter-service communication
- Managing distributed data and transactions
- Building resilient distributed systems
- Implementing service discovery and load balancing
- Designing event-driven architectures

## Do not use this skill when

- The system is small enough for a modular monolith
- You need a quick prototype without distributed complexity
- There is no operational support for distributed systems

## Instructions

1. Identify domain boundaries and ownership for each service.
2. Define contracts, data ownership, and communication patterns.
3. Plan resilience, observability, and deployment strategy.
4. Provide migration steps and operational guardrails.

## Resources

- `resources/implementation-playbook.md` for detailed patterns and examples.


---

## 🧠 AGI Framework Integration

> **Adapted for [@techwavedev/agi-agent-kit](https://www.npmjs.com/package/@techwavedev/agi-agent-kit)**
> Original source: [antigravity-awesome-skills](https://github.com/sickn33/antigravity-awesome-skills)

### Hybrid Memory Integration (Qdrant + BM25)

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
  --tags microservices-patterns <relevant-tags>
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