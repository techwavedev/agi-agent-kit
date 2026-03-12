---
name: ddd-context-mapping
description: "Map relationships between bounded contexts and define integration contracts using DDD context mapping patterns."
risk: safe
source: self
tags: "[ddd, context-map, anti-corruption-layer, integration]"
date_added: "2026-02-27"
---

# DDD Context Mapping

## Use this skill when

- Defining integration patterns between bounded contexts.
- Preventing domain leakage across service boundaries.
- Planning anti-corruption layers during migration.
- Clarifying upstream and downstream ownership for contracts.

## Do not use this skill when

- You have a single-context system with no integrations.
- You only need internal class design.
- You are selecting cloud infrastructure tooling.

## Instructions

1. List all context pairs and dependency direction.
2. Choose relationship patterns per pair.
3. Define translation rules and ownership boundaries.
4. Add failure modes, fallback behavior, and versioning policy.

If detailed mapping structures are needed, open `references/context-map-patterns.md`.

## Output requirements

- Relationship map for all context pairs
- Contract ownership matrix
- Translation and anti-corruption decisions
- Known coupling risks and mitigation plan

## Examples

```text
Use @ddd-context-mapping to define how Checkout integrates with Billing,
Inventory, and Fraud contexts, including ACL and contract ownership.
```

## Limitations

- This skill does not replace API-level schema design.
- It does not guarantee organizational alignment by itself.
- It should be revisited when team ownership changes.

---

<!-- AGI-INTEGRATION-START -->

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
python3 execution/memory_manager.py store \\
  --content "Description of what was decided/solved" \\
  --type decision \\
  --tags ddd-context-mapping <relevant-tags>
```

### Agent Team Collaboration

- This skill can be invoked by the `orchestrator` agent via intelligent routing.
- In **Agent Teams mode**, results are shared via Qdrant shared memory for cross-agent context.
- In **Subagent mode**, this skill runs in isolation with its own memory namespace.

### Local LLM Support

When available, use local Ollama models for embedding and lightweight inference:
- Embeddings: `nomic-embed-text` via Qdrant memory system
- Lightweight analysis: Local models reduce API costs for repetitive patterns

<!-- AGI-INTEGRATION-END -->
