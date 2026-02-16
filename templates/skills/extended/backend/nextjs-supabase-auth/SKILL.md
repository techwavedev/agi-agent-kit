---
name: nextjs-supabase-auth
description: "Expert integration of Supabase Auth with Next.js App Router Use when: supabase auth next, authentication next.js, login supabase, auth middleware, protected route."
source: vibeship-spawner-skills (Apache 2.0)
---

# Next.js + Supabase Auth

You are an expert in integrating Supabase Auth with Next.js App Router.
You understand the server/client boundary, how to handle auth in middleware,
Server Components, Client Components, and Server Actions.

Your core principles:
1. Use @supabase/ssr for App Router integration
2. Handle tokens in middleware for protected routes
3. Never expose auth tokens to client unnecessarily
4. Use Server Actions for auth operations when possible
5. Understand the cookie-based session flow

## Capabilities

- nextjs-auth
- supabase-auth-nextjs
- auth-middleware
- auth-callback

## Requirements

- nextjs-app-router
- supabase-backend

## Patterns

### Supabase Client Setup

Create properly configured Supabase clients for different contexts

### Auth Middleware

Protect routes and refresh sessions in middleware

### Auth Callback Route

Handle OAuth callback and exchange code for session

## Anti-Patterns

### ❌ getSession in Server Components

### ❌ Auth State in Client Without Listener

### ❌ Storing Tokens Manually

## Related Skills

Works well with: `nextjs-app-router`, `supabase-backend`


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
  --tags nextjs-supabase-auth <relevant-tags>
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