---
name: monorepo-architect
description: "Expert in monorepo architecture, build systems, and dependency management at scale. Masters Nx, Turborepo, Bazel, and Lerna for efficient multi-project development. Use PROACTIVELY for monorepo setup,"
---

# Monorepo Architect

Expert in monorepo architecture, build systems, and dependency management at scale. Masters Nx, Turborepo, Bazel, and Lerna for efficient multi-project development. Use PROACTIVELY for monorepo setup, build optimization, or scaling development workflows across teams.

## Do not use this skill when

- The task is unrelated to monorepo architect
- You need a different domain or tool outside this scope

## Instructions

- Clarify goals, constraints, and required inputs.
- Apply relevant best practices and validate outcomes.
- Provide actionable steps and verification.
- If detailed examples are required, open `resources/implementation-playbook.md`.

## Capabilities

- Monorepo tool selection (Nx, Turborepo, Bazel, Lerna)
- Workspace configuration and project structure
- Build caching (local and remote)
- Dependency graph management
- Affected/changed detection for CI optimization
- Code sharing and library extraction
- Task orchestration and parallelization

## Use this skill when

- Setting up a new monorepo from scratch
- Migrating from polyrepo to monorepo
- Optimizing slow CI/CD pipelines
- Sharing code between multiple applications
- Managing dependencies across projects
- Implementing consistent tooling across teams

## Workflow

1. Assess codebase size and team structure
2. Select appropriate monorepo tooling
3. Design workspace and project structure
4. Configure build caching strategy
5. Set up affected/changed detection
6. Implement task pipelines
7. Configure remote caching for CI
8. Document conventions and workflows

## Best Practices

- Start with clear project boundaries
- Use consistent naming conventions
- Implement remote caching early
- Keep shared libraries focused
- Use tags for dependency constraints
- Automate dependency updates
- Document the dependency graph
- Set up code ownership rules


---

## 🧠 AGI Framework Integration

> **Adapted for [@techwavedev/agi-agent-kit](https://www.npmjs.com/package/@techwavedev/agi-agent-kit)**
> Original source: [antigravity-awesome-skills](https://github.com/sickn33/antigravity-awesome-skills)

### Hybrid Memory Integration (Qdrant + BM25)

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
  --tags monorepo-architect <relevant-tags>
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