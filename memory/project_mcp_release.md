---
name: MCP compatibility layer v1.6.3
description: MCP servers added to AGI framework, Kiro support, released to public repo
type: project
---
v1.6.3 released to techwavedev/agi-agent-kit on 2026-03-14. Two MCP servers added: execution/mcp_server.py (13 tools, agi-framework) and skills/qdrant-memory/mcp_server.py (6 tools). Kiro support via .kiro/steering/agents.md symlink. Last public release before this was v1.6.1 (v1.6.2 was on main but unreleased — both merged into v1.6.3).

**Why:** User wanted framework consumable by chat-interface MCP clients (Claude Desktop etc).
**How to apply:** MCP is additive only — coding agents (Antigravity, Kiro, Cursor etc) already work via AGENTS.md symlinks and direct bash. MCP only needed for chat-only clients.
