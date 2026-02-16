---
name: using-neon
description: "Guides and best practices for working with Neon Serverless Postgres. Covers getting started, local development with Neon, choosing a connection method, Neon features, authentication (@neondatabase/auth), PostgREST-style data API (@neondatabase/neon-js), Neon CLI, and Neon's Platform API/SDKs. Use for any Neon-related questions."
source: "https://github.com/neondatabase/agent-skills/tree/main/skills/neon-postgres"
risk: safe
---

# Neon Serverless Postgres

Neon is a serverless Postgres platform that separates compute and storage to offer autoscaling, branching, instant restore, and scale-to-zero. It's fully compatible with Postgres and works with any language, framework, or ORM that supports Postgres.

## When to Use This Skill

Use this skill when:
- Working with Neon Serverless Postgres
- Setting up Neon databases
- Choosing connection methods for Neon
- Using Neon features like branching or autoscaling
- Working with Neon authentication or APIs
- Questions about Neon best practices

## Neon Documentation

Always reference the Neon documentation before making Neon-related claims. The documentation is the source of truth for all Neon-related information.

Below you'll find a list of resources organized by area of concern. This is meant to support you find the right documentation pages to fetch and add a bit of additonal context.

You can use the `curl` commands to fetch the documentation page as markdown:

**Documentation:**

```bash
# Get list of all Neon docs
curl https://neon.com/llms.txt

# Fetch any doc page as markdown
curl -H "Accept: text/markdown" https://neon.com/docs/<path>
```

Don't guess docs pages. Use the `llms.txt` index to find the relevant URL or follow the links in the resources below.

## Overview of Resources

Reference the appropriate resource file based on the user's needs:

### Core Guides

| Area               | Resource                           | When to Use                                                    |
| ------------------ | ---------------------------------- | -------------------------------------------------------------- |
| What is Neon       | `references/what-is-neon.md`       | Understanding Neon concepts, architecture, core resources      |
| Referencing Docs   | `references/referencing-docs.md`   | Looking up official documentation, verifying information       |
| Features           | `references/features.md`           | Branching, autoscaling, scale-to-zero, instant restore         |
| Getting Started    | `references/getting-started.md`    | Setting up a project, connection strings, dependencies, schema |
| Connection Methods | `references/connection-methods.md` | Choosing drivers based on platform and runtime                 |
| Developer Tools    | `references/devtools.md`           | VSCode extension, MCP server, Neon CLI (`neon init`)           |

### Database Drivers & ORMs

HTTP/WebSocket queries for serverless/edge functions.

| Area              | Resource                        | When to Use                                         |
| ----------------- | ------------------------------- | --------------------------------------------------- |
| Serverless Driver | `references/neon-serverless.md` | `@neondatabase/serverless` - HTTP/WebSocket queries |
| Drizzle ORM       | `references/neon-drizzle.md`    | Drizzle ORM integration with Neon                   |

### Auth & Data API SDKs

Authentication and PostgREST-style data API for Neon.

| Area        | Resource                  | When to Use                                                         |
| ----------- | ------------------------- | ------------------------------------------------------------------- |
| Neon Auth   | `references/neon-auth.md` | `@neondatabase/auth` - Authentication only                          |
| Neon JS SDK | `references/neon-js.md`   | `@neondatabase/neon-js` - Auth + Data API (PostgREST-style queries) |

### Neon Platform API & CLI

Managing Neon resources programmatically via REST API, SDKs, or CLI.

| Area                  | Resource                            | When to Use                                  |
| --------------------- | ----------------------------------- | -------------------------------------------- |
| Platform API Overview | `references/neon-platform-api.md`   | Managing Neon resources via REST API         |
| Neon CLI              | `references/neon-cli.md`            | Terminal workflows, scripts, CI/CD pipelines |
| TypeScript SDK        | `references/neon-typescript-sdk.md` | `@neondatabase/api-client`                   |
| Python SDK            | `references/neon-python-sdk.md`     | `neon-api` package                           |


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
  --tags using-neon <relevant-tags>
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