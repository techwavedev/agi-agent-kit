---
description: Core system rules and behavior requirements for all AI agents
---

# 🤖 Agent Core Rules (MANDATORY)

You are operating within the `AGI Agent Kit` deterministic framework.

## 1. Zero Tolerance Probabilistic Execution

- Do NOT perform complex, multi-step data transformations using inline code snippets if an `execution/` script exists for it.
- **You are the orchestrator.** Rely on the `execution/` scripts to handle logic, files, and queries deterministically.

## 2. Memory is Mandatory (Qdrant & Ollama)

You are REQUIRED to actively use Qdrant Semantic Memory during EVERY task.
Failure to call these scripts is strictly considered a bug.

### Before Beginning A Complex Task

You MUST retrieve context to save tokens and reuse past logic:

```bash
python3 execution/memory_manager.py auto --query "<summary of user request>"
```

- If it returns `cache_hit: true`, use the cache.
- If it returns `source: memory`, inject those context chunks securely into your answer.

### After Delivering A Task or Making a Decision (REQUIRED)

You MUST store key learnings for future sessions:

```bash
python3 execution/memory_manager.py store \
  --content "<what was decided, patterned, or solved>" \
  --type decision \
  --project "<project-name>" \
  --tags <relevant-tags>
```

**Types:** `decision`, `code`, `error`, `technical`, `conversation`

## 3. Self-Annealing Pattern

If a script fails with an error:

1. Do NOT crash or immediately give up.
2. Read the script output (which contains structured JSON error messages).
3. Attempt to fix parameters, read the docs, and try again.
4. If it's a new failure mode you figured out, **store it in memory** using `memory_manager.py` so you remember next time.

## 4. Workflows and Playbooks

- You can execute multi-step playbooks using the workflow engine:
  ```bash
  python3 execution/workflow_engine.py status
  ```
- Before suggesting complex pipelines, check `.agent/workflows/` or the Workflow Engine for pre-existing playbooks.

## 5. Prove Your Work

The user expects you to leave an auditable trail of memory usage.

```bash
python3 execution/memory_usage_proof.py --check --since 60
```

Run this to ensure your `store` command actually succeeded!
