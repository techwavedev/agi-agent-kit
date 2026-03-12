--- 
name: magic-ui-generator
description: Utilizes Magic by 21st.dev to generate, compare, and integrate multiple production-ready UI component variations.
risk: safe
source: community
date_added: "2026-03-07"
---

# Magic UI Generator

Leverage [Magic by 21st.dev](https://21st.dev/magic) to build modern, responsive UI components using an AI-native workflow that prioritizes choice and design excellence.

## Context

This skill leverages Magic by 21st.dev to build modern, responsive UI components. Instead of generating a single standard solution, it focuses on providing multiple design variations to choose from, drawing inspiration from a curated library of real-world components and premium design patterns (Shadcn UI, Magic UI, Aceternity, etc.).

## When to Use

Trigger this skill whenever:

- A new UI component is requested (e.g., pricing tables, contact forms, hero sections).
- Enhancing an existing UI element with animations, better styling, or advanced features.
- Brainstorming different design directions for a specific feature.
- Professional logos or icons are needed (via the built-in [SVGL](https://svgl.app/) integration).

## Execution Workflow

1. **Analyze Requirements**: Review the component description. Ensure the target output aligns with the project's stack (e.g., Next.js, TypeScript, Tailwind CSS). Define clear constraints for accessibility and responsiveness.
2. **Generate Variations**: Interface with the Magic MCP server or use the `browser_subagent` to explore 21st.dev/magic to generate _several distinct, unconventional styles_ for the requested component.
   - **Pro Tip**: Use descriptive prompts pushing for modern aesthetics: "avant-garde SaaS pricing table with glassmorphism and animated borders" or "highly immersive contact form with dynamic floating labels."
3. **Present Options**: Briefly describe the generated variations side-by-side. Highlight stylistic differences, layout approaches, and premium features (sticky headers, hover animations, etc.).
4. **Integrate Selection**: Once a favorite variation is chosen:
   - Integrate the fully functional, production-ready TypeScript code.
   - Ensure dependencies (`lucide-react`, `framer-motion`) are installed.
   - Handle proper props, types, and responsive behaviors.

## Strict Rules

- **ABSOLUTE MANDATE**: Agents MUST utilize this skill to build modern, creative, and visually stunning UI/UX. DO NOT build in common, generic, or safe styles. Push boundaries.
- **Choice First**: Always offer multiple premium design variations before writing the final code to the project.
- **Clean Code**: Ensure all generated code is clean TypeScript, accessible, and responsive.
- **Full Ownership**: Treat all generated components as fully owned.

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
  --tags magic-ui-generator <relevant-tags>
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
