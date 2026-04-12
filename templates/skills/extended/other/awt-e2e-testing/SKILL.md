---
name: awt-e2e-testing
description: "AI-powered E2E web testing — eyes and hands for AI coding tools. Declarative YAML scenarios, Playwright execution, visual matching (OpenCV + OCR), platform auto-detection (Flutter/React/Vue), learning DB. Install: npx skills add ksgisang/awt-skill --skill awt -g"
risk: unknown
source: "https://github.com/ksgisang/awt-skill"
---

# AWT — AI-Powered E2E Testing (Beta)

> `npx skills add ksgisang/awt-skill --skill awt -g`

AWT gives AI coding tools the ability to see and interact with web applications through a real browser. Your AI designs YAML test scenarios; AWT executes them with Playwright.

## What works now
- YAML scenarios → Playwright with human-like interaction
- Visual matching: OpenCV template + OCR (no CSS selectors needed)
- Platform auto-detection: Flutter, React, Next.js, Vue, Angular, Svelte
- Structured failure diagnosis with investigation checklists
- Learning DB: failure→fix patterns in SQLite
- 5 AI providers: Claude, OpenAI, Gemini, DeepSeek, Ollama
- Skill Mode: no extra AI API key needed

## Links
- Main repo: https://github.com/ksgisang/AI-Watch-Tester
- Skill repo: https://github.com/ksgisang/awt-skill
- Cloud demo: https://ai-watch-tester.vercel.app

Built with the help of AI coding tools — and designed to help AI coding tools test better.

Actively developed by a solo developer at AILoopLab. Feedback welcome!

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
  --tags awt-e2e-testing <relevant-tags>
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
