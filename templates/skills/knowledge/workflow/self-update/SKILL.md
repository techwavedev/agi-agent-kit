---
name: self-update
description: Update the AGI Agent Kit to the latest version from NPM
version: 1.0.0
---

# Self-Update Skill

Updates the AGI Agent Kit framework components (skills, agents, workflows) to the latest published version.

## When to Use

- When a new version of `@techwavedev/agi-agent-kit` is available
- When you want to sync your local installation with the latest templates
- After the user asks to "update", "upgrade", or "get latest skills"

## How It Works

1. **Check Current Version**: Reads `.agi.json` for installed version (if present)
2. **Fetch Latest**: Runs `npm view @techwavedev/agi-agent-kit version`
3. **Update**: Re-runs init with `--pack=full` to overlay new templates

## Quick Commands

```bash
# Check installed version
cat .agi.json 2>/dev/null || echo "No version metadata found"

# Check latest NPM version
npm view @techwavedev/agi-agent-kit version

# Update to latest (re-init with full pack)
npx @techwavedev/agi-agent-kit@latest init --pack=full
```

## Update Script

Use the provided script for a guided update:

```bash
python3 skills/self-update/scripts/update_kit.py
```

## What Gets Updated

| Component         | Updated? | Notes                     |
| ----------------- | -------- | ------------------------- |
| Skills            | ✅ Yes   | All skills from templates |
| Agents            | ✅ Yes   | `.agent/` directory       |
| Workflows         | ✅ Yes   | `.agent/workflows/`       |
| Skill Creator     | ✅ Yes   | `skill-creator/`          |
| AGENTS.md         | ✅ Yes   | Overwrites with latest    |
| User's .env       | ❌ No    | Never touched             |
| User's directives | ❌ No    | Preserved                 |

## Notes

- The update process **overwrites** skill scripts. If you've customized them, back up first.
- Your `.env` and custom directives are always preserved.
- After updating, run `/checkup` to verify everything is working.

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
  --tags self-update <relevant-tags>
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
