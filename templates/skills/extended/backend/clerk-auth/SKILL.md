---
name: clerk-auth
description: "Expert patterns for Clerk auth implementation, middleware, organizations, webhooks, and user sync Use when: adding authentication, clerk auth, user authentication, sign in, sign up."
source: vibeship-spawner-skills (Apache 2.0)
---

# Clerk Authentication

## Patterns

### Next.js App Router Setup

Complete Clerk setup for Next.js 14/15 App Router.

Includes ClerkProvider, environment variables, and basic
sign-in/sign-up components.

Key components:
- ClerkProvider: Wraps app for auth context
- <SignIn />, <SignUp />: Pre-built auth forms
- <UserButton />: User menu with session management


### Middleware Route Protection

Protect routes using clerkMiddleware and createRouteMatcher.

Best practices:
- Single middleware.ts file at project root
- Use createRouteMatcher for route groups
- auth.protect() for explicit protection
- Centralize all auth logic in middleware


### Server Component Authentication

Access auth state in Server Components using auth() and currentUser().

Key functions:
- auth(): Returns userId, sessionId, orgId, claims
- currentUser(): Returns full User object
- Both require clerkMiddleware to be configured


## ⚠️ Sharp Edges

| Issue | Severity | Solution |
|-------|----------|----------|
| Issue | critical | See docs |
| Issue | high | See docs |
| Issue | high | See docs |
| Issue | high | See docs |
| Issue | medium | See docs |
| Issue | medium | See docs |
| Issue | medium | See docs |
| Issue | medium | See docs |


---

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
python3 execution/memory_manager.py store \
  --content "Description of what was decided/solved" \
  --type decision \
  --tags clerk-auth <relevant-tags>
```

### Agent Team Collaboration

- This skill can be invoked by the `orchestrator` agent via intelligent routing.
- In **Agent Teams mode**, results are shared via Qdrant shared memory for cross-agent context.
- In **Subagent mode**, this skill runs in isolation with its own memory namespace.

### Local LLM Support

When available, use local Ollama models for embedding and lightweight inference:
- Embeddings: `nomic-embed-text` via Qdrant memory system
- Lightweight analysis: Local models reduce API costs for repetitive patterns
