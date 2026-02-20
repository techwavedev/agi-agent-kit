---
name: templates
description: Project scaffolding templates for new applications. Use when creating new projects from scratch. Contains 12 templates for various tech stacks.
allowed-tools: Read, Glob, Grep
---

# Project Templates

> Quick-start templates for scaffolding new projects.

---

## 🎯 Selective Reading Rule

**Read ONLY the template matching user's project type!**

| Template | Tech Stack | When to Use |
|----------|------------|-------------|
| [nextjs-fullstack](nextjs-fullstack/TEMPLATE.md) | Next.js + Prisma | Full-stack web app |
| [nextjs-saas](nextjs-saas/TEMPLATE.md) | Next.js + Stripe | SaaS product |
| [nextjs-static](nextjs-static/TEMPLATE.md) | Next.js + Framer | Landing page |
| [express-api](express-api/TEMPLATE.md) | Express + JWT | REST API |
| [python-fastapi](python-fastapi/TEMPLATE.md) | FastAPI | Python API |
| [react-native-app](react-native-app/TEMPLATE.md) | Expo + Zustand | Mobile app |
| [flutter-app](flutter-app/TEMPLATE.md) | Flutter + Riverpod | Cross-platform |
| [electron-desktop](electron-desktop/TEMPLATE.md) | Electron + React | Desktop app |
| [chrome-extension](chrome-extension/TEMPLATE.md) | Chrome MV3 | Browser extension |
| [cli-tool](cli-tool/TEMPLATE.md) | Node.js + Commander | CLI app |
| [monorepo-turborepo](monorepo-turborepo/TEMPLATE.md) | Turborepo + pnpm | Monorepo |
| [astro-static](astro-static/TEMPLATE.md) | Astro + MDX | Blog / Docs |

---

## Usage

1. User says "create [type] app"
2. Match to appropriate template
3. Read ONLY that template's TEMPLATE.md
4. Follow its tech stack and structure

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
  --tags templates <relevant-tags>
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
