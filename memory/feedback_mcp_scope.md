---
name: MCP is only for chat interfaces, not coding agents
description: Coding agents with bash access don't need MCP — they use AGENTS.md symlinks directly
type: feedback
---
Don't suggest MCP as a compatibility solution for coding agents (Antigravity, Kiro, Cursor, Claude Code, OpenCode, Copilot). They already have full access via bash + AGENTS.md symlinks. MCP only adds value for pure chat UIs with no bash execution.

**Why:** User corrected this during the session — "antigravity and kiro and maybe others can run bash with it"
**How to apply:** When discussing tool compatibility with this project, distinguish between coding agents (already compatible) and chat interfaces (need MCP).
