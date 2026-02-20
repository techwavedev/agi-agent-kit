---
description: Verify and enforce Qdrant/Ollama memory usage during real agent sessions
---

# Memory Usage Workflow

This workflow ensures the agent ACTUALLY uses Qdrant and Ollama during real work,
not just during benchmarks or tests.

## When to Use

- At the start of every session
- After completing a significant task
- When auditing agent behavior

## Steps

### 1. Boot Memory System

// turbo

```bash
python3 execution/session_boot.py --auto-fix
```

### 2. Query Memory BEFORE Starting Work

// turbo

```bash
python3 execution/memory_manager.py auto --query "<summary of user's request>"
```

Use the result:

- `cache_hit: true` → Use cached response, tell user
- `source: memory` → Inject context into reasoning
- `source: none` → Proceed normally

### 3. Store Results AFTER Completing Work

```bash
python3 execution/memory_manager.py store \
  --content "<what was decided or solved>" \
  --type decision \
  --project <project-name> \
  --tags <relevant-tags>
```

### 4. Verify Usage With Proof

// turbo

```bash
python3 execution/memory_usage_proof.py --check
```

This shows actual Qdrant point counts and timestamps to PROVE the agent stored something.

### 5. Audit Report (Optional)

// turbo

```bash
python3 execution/memory_usage_proof.py --report
```

Full report of all memories with timestamps, types, and projects.
