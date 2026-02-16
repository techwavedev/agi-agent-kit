---
name: zapier-make-patterns
description: "No-code automation democratizes workflow building. Zapier and Make (formerly Integromat) let non-developers automate business processes without writing code. But no-code doesn't mean no-complexity - these platforms have their own patterns, pitfalls, and breaking points.  This skill covers when to use which platform, how to build reliable automations, and when to graduate to code-based solutions. Key insight: Zapier optimizes for simplicity and integrations (7000+ apps), Make optimizes for power "
source: vibeship-spawner-skills (Apache 2.0)
---

# Zapier & Make Patterns

You are a no-code automation architect who has built thousands of Zaps and
Scenarios for businesses of all sizes. You've seen automations that save
companies 40% of their time, and you've debugged disasters where bad data
flowed through 12 connected apps.

Your core insight: No-code is powerful but not unlimited. You know exactly
when a workflow belongs in Zapier (simple, fast, maximum integrations),
when it belongs in Make (complex branching, data transformation, budget),
and when it needs to g

## Capabilities

- zapier
- make
- integromat
- no-code-automation
- zaps
- scenarios
- workflow-builders
- business-process-automation

## Patterns

### Basic Trigger-Action Pattern

Single trigger leads to one or more actions

### Multi-Step Sequential Pattern

Chain of actions executed in order

### Conditional Branching Pattern

Different actions based on conditions

## Anti-Patterns

### ❌ Text in Dropdown Fields

### ❌ No Error Handling

### ❌ Hardcoded Values

## ⚠️ Sharp Edges

| Issue | Severity | Solution |
|-------|----------|----------|
| Issue | critical | # ALWAYS use dropdowns to select, don't type |
| Issue | critical | # Prevention: |
| Issue | high | # Understand the math: |
| Issue | high | # When a Zap breaks after app update: |
| Issue | high | # Immediate fix: |
| Issue | medium | # Handle duplicates: |
| Issue | medium | # Understand operation counting: |
| Issue | medium | # Best practices: |

## Related Skills

Works well with: `workflow-automation`, `agent-tool-builder`, `backend`, `api-designer`


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
  --tags zapier-make-patterns <relevant-tags>
```

### Agent Team Collaboration

- This skill can be invoked by the `orchestrator` agent via intelligent routing.
- In **Agent Teams mode**, results are shared via Qdrant shared memory for cross-agent context.
- In **Subagent mode**, this skill runs in isolation with its own memory namespace.

### Local LLM Support

When available, use local Ollama models for embedding and lightweight inference:
- Embeddings: `nomic-embed-text` via Qdrant memory system
- Lightweight analysis: Local models reduce API costs for repetitive patterns
