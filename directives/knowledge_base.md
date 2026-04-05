# Knowledge Base Pattern

This document describes the hybrid knowledge-base system used across all agent sessions in this framework.

## Overview

The knowledge base follows a **hybrid pattern**: a small always-loaded core plus semantic retrieval from Qdrant for the rest. This keeps initialization token costs low while retaining full context when needed.

```
knowledge/
├── core.md          ← always injected (≤500 tokens)
├── voice.md         ← writing style & tone
├── preferences.md   ← development conventions
├── prohibitions.md  ← things to never do
├── technical.md     ← architecture & env vars
└── project-facts.md ← team, timeline, decisions log
```

## Two Layers

### Layer 1 — Always Loaded (`core.md`)

`knowledge/core.md` is injected into every agent dispatch, regardless of Qdrant availability. Keep it under ~500 tokens. It should contain only:

- Project name and primary tech stack
- Non-negotiable rules (security, testing, style)

### Layer 2 — Semantically Retrieved (Qdrant, all other files)

All `knowledge/*.md` files except `core.md` are synced to Qdrant (type `knowledge`). At dispatch time the orchestrator retrieves only the chunks relevant to the current task, reducing token overhead by 80–95%.

**Fallback:** when Qdrant is unreachable, all `knowledge/*.md` files are loaded directly into the payload (Option A degraded mode — functional but burns more tokens).

## Setup

### 1. Fill in your knowledge files

Edit the files in `knowledge/` with project-specific information.

### 2. Sync to Qdrant

```bash
# Sync once (re-runnable — uses deterministic IDs so no duplicates)
python3 execution/memory_manager.py knowledge-sync --project <your-project>

# Optionally specify a custom knowledge directory
python3 execution/memory_manager.py knowledge-sync --project <your-project> --dir path/to/knowledge
```

### 3. Wire into agent dispatches

`dispatch_agent_team.py` auto-injects knowledge context whenever it builds a manifest. No extra configuration is needed after the sync.

## How Injection Works

`dispatch_agent_team.py` calls `load_knowledge_context(root, task_summary, project)`:

1. Reads `knowledge/core.md` — always included.
2. Queries Qdrant for chunks with `type=knowledge, project=<project>` ranked by similarity to the task summary.
3. Returns `{"core": "...", "retrieved": [...chunks...], "source": "qdrant"}`.
4. On Qdrant error: loads all `knowledge/*.md` and returns `{"source": "fallback_markdown"}`.

The result is added to the manifest under the key `knowledge_context`.

## Updating the Knowledge Base

Edit the markdown files and re-run the sync command:

```bash
python3 execution/memory_manager.py knowledge-sync --project <your-project>
```

The sync is idempotent — it uses a deterministic UUID based on `project:filename:section`, so re-running upserts rather than duplicates.

## Silent Schema Migration

If section names change (e.g. renaming `## Voice` → `## Tone`), re-run the sync. Old chunks with the previous section name remain in Qdrant until they age out of relevance, but new queries will prefer the updated chunks. For a hard reset:

```bash
# Delete all knowledge chunks for the project and re-sync
python3 execution/memory_manager.py knowledge-sync --project <your-project> --reset
```

## Token Budget Reference

| Mode | Tokens injected | When |
|---|---|---|
| Core only | ~500 | Qdrant unavailable, task unrelated to KB |
| Core + retrieved | ~500 + 3×~200 = ~1100 | Normal operation |
| Full fallback | Sum of all knowledge/*.md | Qdrant unreachable |

## Related

- `execution/memory_manager.py` — `knowledge-sync` and `knowledge-query` commands
- `execution/dispatch_agent_team.py` — `load_knowledge_context()` injection
- `directives/memory_integration.md` — general memory system guide
