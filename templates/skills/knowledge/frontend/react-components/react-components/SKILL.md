---
name: react:components
description: Converts Stitch designs into modular Vite and React components using system-level networking and AST-based validation.
allowed-tools:
  - "stitch*:*"
  - "Bash"
  - "Read"
  - "Write"
  - "web_fetch"
  - "qdrant-memory"
---

# Stitch to React Components

You are a frontend engineer focused on transforming designs into clean React code. You follow a modular approach and use automated tools to ensure code quality.

## Retrieval and networking

1. **Namespace discovery**: Run `list_tools` to find the Stitch MCP prefix. Use this prefix (e.g., `stitch:`) for all subsequent calls.
2. **Metadata fetch**: Call `[prefix]:get_screen` to retrieve the design JSON.
3. **High-reliability download**: Internal AI fetch tools can fail on Google Cloud Storage domains.
   - Use the `Bash` tool to run: `bash scripts/fetch-stitch.sh "[htmlCode.downloadUrl]" "temp/source.html"`.
   - This script handles the necessary redirects and security handshakes.
4. **Visual audit**: Check `screenshot.downloadUrl` to confirm the design intent and layout details.

## Architectural rules

- **Modular components**: Break the design into independent files. Avoid large, single-file outputs.
- **Logic isolation**: Move event handlers and business logic into custom hooks in `src/hooks/`.
- **Data decoupling**: Move all static text, image URLs, and lists into `src/data/mockData.ts`.
- **Type safety**: Every component must include a `Readonly` TypeScript interface named `[ComponentName]Props`.
- **Project specific**: Focus on the target project's needs and constraints. Leave Google license headers out of the generated React components.
- **Style mapping**:
  - Extract the `tailwind.config` from the HTML `<head>`.
  - Sync these values with `resources/style-guide.json`.
  - Use theme-mapped Tailwind classes instead of arbitrary hex codes.

## Execution steps

1. **Environment setup**: If `node_modules` is missing, run `npm install` to enable the validation tools.
2. **Data layer**: Create `src/data/mockData.ts` based on the design content.
3. **Pattern Retrieval (Optional)**: If **qdrant-memory** is available, search for existing components (`type: "code"`) to reuse patterns or interfaces.
4. **Component drafting**: Use `resources/component-template.tsx` as a base. Find and replace all instances of `StitchComponent` with the actual name of the component you are creating.
5. **Application wiring**: Update the project entry point (like `App.tsx`) to render the new components.
6. **Quality check**:
   - Run `npm run validate <file_path>` for each component.
   - Verify the final output against the `resources/architecture-checklist.md`.
   - Start the dev server with `npm run dev` to verify the live result.

## Troubleshooting

- **Fetch errors**: Ensure the URL is quoted in the bash command to prevent shell errors.
- **Validation errors**: Review the AST report and fix any missing interfaces or hardcoded styles.

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
  --tags react-components <relevant-tags>
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
