---
name: makepad-reference
description: |
  CRITICAL: Use for Makepad troubleshooting and reference. Triggers on:
  troubleshoot, error, debug, fix, problem, issue,
  no matching field, parse error, widget not found, UI not updating,
  code quality, refactor, responsive layout, adaptive,
  api docs, reference,...
---

# Makepad Reference

This category provides reference materials for debugging, code quality, and advanced layout patterns.

## Quick Navigation

| Topic | File | Use When |
|-------|------|----------|
| API Documentation | Official docs index, quick API reference | Finding detailed API info |
| Troubleshooting | Common errors and fixes | Build fails, runtime errors |
| Code Quality | Makepad-aware refactoring | Simplifying code safely |
| Adaptive Layout | Desktop/mobile responsive | Cross-platform layouts |

## Common Issues Quick Reference

| Error | Quick Fix |
|-------|-----------|
| `no matching field: font` | Use `text_style: <THEME_FONT_*>{}` |
| Color parse error (ends in `e`) | Change last digit (e.g., `#14141e` → `#14141f`) |
| `set_text` missing argument | Add `cx` as first argument |
| UI not updating | Call `redraw(cx)` after changes |
| Widget not found | Check ID spelling, use `ids!()` for paths |

## Debug Tips

```bash
# Run with line info for better error messages
MAKEPAD=lines cargo +nightly run
```

```rust
// Add logging
log!("Value: {:?}", my_value);
log!("State: {} / {}", self.counter, self.is_loading);
```

## Resources

- [Makepad Official Docs](https://publish.obsidian.md/makepad-docs/) - Obsidian-based documentation
- [Makepad Repository](https://github.com/makepad/makepad)
- [Robrix](https://github.com/project-robius/robrix) - Production reference
- [Moly](https://github.com/moxin-org/moly) - Production reference

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
  --tags makepad-reference <relevant-tags>
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
