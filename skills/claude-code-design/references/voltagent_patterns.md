# VoltAgent Cross-Framework Patterns

Distilled design signal from six VoltAgent repos (all MIT-licensed, fetched 2026-04-14).
Complements `claude_code_design_principles.md` by showing how a parallel TypeScript-first
ecosystem structures agents, skills, and multi-agent orchestration.

Sources cited inline as `[repo/path]`.

---

## 1. `voltagent/voltagent` — Core TypeScript Agent Framework

The flagship repo: a monorepo of `@voltagent/*` packages providing typed agents, tools,
memory, MCP, workflows, and observability.

### Key patterns

- **Config-first agent definition.** A VoltAgent agent is a single `new Agent({...})`
  object carrying `name`, `instructions`, `model`, `tools`, `memory`. No prompt-only
  agents; every capability is declared. [voltagent/README.md:86–112]
- **Separation of runtime concerns via packages.** `core` (orchestration/memory/tools),
  `server-hono` (HTTP), `logger`, `libsql`/`postgres` (memory storage), `mcp-server`
  (MCP exposure), `evals`, `scorers`, `guardrails`. [voltagent/docs/structure.md]
- **Typed tools via Zod + lifecycle hooks** — tools are first-class, with cancellation
  and MCP compatibility. Mirrors the AGI-Kit idea of "execution scripts as deterministic
  tools," but at runtime in the same process rather than subprocess shell-outs.
- **Supervisors & Sub-Agents** — a supervisor runtime routes tasks to specialized
  sub-agents and keeps state in sync. Analogous to our `dispatch_agent_team.py` /
  `worktree_isolator.py` pair, but without filesystem-level isolation.
- **Resumable streaming** as a first-class concept: clients reconnect to in-flight
  streams and continue receiving the same response. No parallel in AGI Kit.
- **VoltOps Console** for observability/evals/guardrails is a separate surface on top
  of the OSS runtime — same split as "framework + cloud ops" seen in LangGraph/LangSmith.
- **Gotchas as hard rules.** `voltagent/CLAUDE.md` notes `JSON.stringify` is banned
  in favor of `safeStringify` from `@voltagent/internal`. Worth mirroring in our
  CLAUDE.md: call out framework-wide hazards explicitly.

> "JSON.stringify SHOULD NEVER BE USED, used the `safeStringify` function instead,
> imported from `@voltagent/internal`" — [voltagent/CLAUDE.md:38]

### Contrasts vs AGI Agent Kit

| Dimension | VoltAgent | AGI Agent Kit |
|---|---|---|
| Language | TypeScript | Python + bash glue |
| Tool runtime | In-process (Zod-typed) | Subprocess (CLI scripts) |
| Memory | Pluggable adapters (LibSQL, Postgres, Supabase) | Qdrant + BM25 hybrid |
| Orchestration | Supervisor/sub-agent object graph | File-based directives + team manifests |
| Observability | VoltOps Console (SaaS) | Qdrant memory logs + proofs |

---

## 2. `awesome-design-md` — DESIGN.md as a Design SOP

Curates 66 `DESIGN.md` files (Google Stitch format) extracted from real sites.
Reinforces a clean taxonomy: some Markdown is **agent-readable configuration**, not
prose.

### Key patterns

- **Pairing `AGENTS.md` + `DESIGN.md`** — one directs build behavior, the other
  directs visual output. [awesome-design-md/README.md:37–41]

> "`AGENTS.md` — coding agents — how to build the project. `DESIGN.md` — design
> agents — how the project should look and feel." [awesome-design-md/README.md]

- **Fixed section shape** so an agent can reliably parse: Visual Theme, Color
  Palette, Typography, Components, Layout, Depth, Do/Don't, Responsive, Agent Prompt
  Guide. [awesome-design-md/README.md:152–162]
- **Preview HTML paired with each DESIGN.md** (`preview.html`, `preview-dark.html`)
  so a human can sanity-check without running the agent.
- **Applicability to our skill set:** any AGI Agent Kit skill that emits UI (web
  scraping reports, slides, dashboards) could adopt a DESIGN.md alongside SKILL.md
  to make visual output deterministic.

### License caveat

The `design-md/<site>/` subfolders in the repo are mostly *pointers* (a single
`README.md` redirect to getdesign.md) rather than the full DESIGN.md content. To
mirror a DESIGN.md verbatim, fetch from getdesign.md directly and verify its
per-site license terms — the repo's MIT only covers the curation, not the underlying
visual tokens.

---

## 3. `awesome-agent-skills` — Official Skills Collection (1184+)

A directory of published Agent Skills from Anthropic, Google, Vercel, Stripe,
Cloudflare, etc. The most useful content is the **Quality Standards** section.

### Skill quality criteria (directly applicable to our `skills/`)

| Area | Rule |
|------|------|
| Description | Third person, state *what* + *when*; specific keywords agents can match on |
| Progressive disclosure | Top-level metadata < ~100 tokens; skill body < 500 lines; load resources on demand |
| No absolute paths | Use relative paths or `$HOME` / `$PROJECT_ROOT` |
| Scoped tools | Declare explicit tool list; avoid `"tools": ["*"]` |

[awesome-agent-skills/README.md:1429–1437]

### Divergences vs AGI Agent Kit SKILL.md rules

- VoltAgent says skill body "below 500 lines"; AGI-Kit is stricter at **200 lines**
  (SKILL.md only) with references for the rest. Our rule is the more defensible one
  for context-window economy.
- VoltAgent calls out **third-person descriptions** as a separate criterion — we
  should add this to `skill-creator/` eval assertions. It materially improves
  auto-selection by the harness.
- "Avoid `tools: ['*']`" is good advice we under-emphasize. See the Claude Code
  Subagents repo below for a concrete tool-assignment matrix by role.

---

## 4. `awesome-openclaw-skills` — OpenClaw Skill Registry

Curates 5,198 skills from ClawHub. Mostly interesting for its **filtering discipline**
and **security stance** rather than content.

### Key patterns

- **Explicit spam/dup/malicious filter pipeline:** 7,215 skills excluded out of
  13,729 (52%). Categories: bulk/bot accounts, duplicates, low-quality, crypto-spam,
  security-flagged. [awesome-openclaw-skills/README.md:79–88]
- **Security notice is first-class**, not a footnote: prompt-injection, tool
  poisoning, hidden malware payloads, unsafe data handling. Recommends Snyk Skill
  Security Scanner and Agent Trust Hub. [awesome-openclaw-skills/README.md:158–169]
- **Priority order** for installed skills: `Workspace > Local > Bundled` — matches
  Claude Code's project-over-global precedence.
- **Takeaway for AGI Agent Kit:** when we eventually publish a community skill
  registry, bake in the "curated not audited" disclaimer and a VirusTotal-style
  scan hook. Our `dependency_tracker.py` is the natural home for this.

---

## 5. `awesome-claude-code-subagents` — 130+ Subagent Definitions

This is the highest-signal repo for Claude Code specifically, because it shows the
**subagent file format** and a **tool-assignment matrix** that we should adopt.

### Subagent file template

```yaml
---
name: agent-name
description: When this agent should be invoked (used by Claude Code for auto-selection)
tools: Read, Write, Edit, Bash, Glob, Grep  # Comma-separated tool permissions
---

You are a [role description]...

[Agent-specific checklists, patterns, guidelines]

## Communication Protocol
[Inter-agent communication specs]

## Development Workflow
[Structured implementation phases]
```

[awesome-claude-code-subagents/CLAUDE.md:28–45]

### Tool assignment matrix (adopt in our `directives/subagents/`)

| Role type | Tools |
|---|---|
| Read-only (reviewers, auditors) | `Read, Grep, Glob` |
| Research (analysts) | `Read, Grep, Glob, WebFetch, WebSearch` |
| Code writers (developers) | `Read, Write, Edit, Bash, Glob, Grep` |
| Documentation | `Read, Write, Edit, Glob, Grep, WebFetch, WebSearch` |

[awesome-claude-code-subagents/CLAUDE.md:47–52]

### Storage precedence

| Type | Path | Scope |
|---|---|---|
| Project | `.claude/agents/` | Current project only |
| Global | `~/.claude/agents/` | All projects |

Project subagents override global ones with the same name.
[awesome-claude-code-subagents/CLAUDE.md:64–71]

### Plugin-based distribution

VoltAgent packages subagents as Claude Code **plugins** distributed via a marketplace:

```bash
claude plugin marketplace add VoltAgent/awesome-claude-code-subagents
claude plugin install voltagent-lang
```

[awesome-claude-code-subagents/README.md:53–64]

Our equivalent is `npx @techwavedev/agi-agent-kit init` — a scaffolding install
rather than per-skill. Both models are valid; the plugin model is better for
selective adoption, the scaffold model is better for tightly-coupled skill sets.

### Meta-orchestration as a category

The `09-meta-orchestration/` category defines purpose-built coordinator subagents:
`multi-agent-coordinator`, `context-manager`, `task-distributor`, `workflow-orchestrator`,
`error-coordinator`, `knowledge-synthesizer`, `agent-organizer`, `performance-monitor`,
`agent-installer`. Each is a plain Markdown file with the frontmatter above.

Example coordinator structure:

> "When invoked: 1) Query context manager for workflow requirements and agent
> states; 2) Review communication patterns, dependencies, and resource constraints;
> 3) Analyze coordination bottlenecks, deadlock risks…; 4) Implement robust
> multi-agent coordination strategies."
> — [awesome-claude-code-subagents/categories/09-meta-orchestration/multi-agent-coordinator.md:11–15]

AGI Agent Kit's closest analog is `directives/teams/` + `dispatch_agent_team.py`;
the VoltAgent version is a richer set of *named personas* rather than team
manifests. Worth considering as an additional layer.

---

## 6. `awesome-ai-agent-papers` — 2026 Research Index

363+ arXiv papers grouped into: Multi-Agent (51), Memory & RAG (56), Eval &
Observability (79), Agent Tooling (95), AI Agent Security (82).

### Design-relevant threads (sampled from titles + abstracts)

- **Deterministic orchestration:** "ORCH: many analyses, one merge — a deterministic
  multi-agent orchestrator" validates our determinism-first philosophy in literature.
  [ai-agent-papers/README.md, arXiv 2602.01797]
- **Topology matters:** DyTopo, TopoDIM, CTHA all argue that *dynamic* inter-agent
  topology beats fixed pipelines. Our current team manifests are static; worth
  re-reading our `dispatch_agent_team.py` design against this.
- **Single-agent-with-skills vs multi-agent:** "When Single-Agent with Skills Replace
  Multi-Agent Systems and When They Fail" (arXiv 2601.04748) — directly relevant;
  our skill-rich single-orchestrator pattern sits exactly on this axis.
- **Budget-tier memory routing:** "BudgetMem: Learning Query-Aware Budget-Tier
  Routing for Runtime Agent Memory" maps onto our local-vs-cloud router philosophy
  applied to memory retrieval tiers.
- **Long-context via agent roles:** "LSTM-MAS" (worker/filter/judge/manager) is a
  clean analog for our doc-writer → doc-reviewer → changelog-updater chain.
- **Memory & RAG themes** reinforce: selective memory sharing between parallel
  agents, atomic QA decomposition for multi-hop (CompactRAG), query-aware routing.

### How to use this

Treat this repo as a **weekly reading feed**, not a dump. When designing a new
orchestration pattern in AGI Kit, search the Multi-Agent and Agent Tooling sections
first for prior art.

---

## Synthesis — What to Pull Into AGI Agent Kit

1. **Third-person descriptions + explicit trigger keywords** in every SKILL.md
   frontmatter. Add as eval assertion.
2. **Tool-scope matrix** for `directives/subagents/*` — adopt the four-role table
   from awesome-claude-code-subagents verbatim.
3. **DESIGN.md companion** for any skill that emits UI; pair with AGENTS.md/CLAUDE.md
   the same way VoltAgent pairs them.
4. **Security stance first** in any future community-skills registry: explicit
   "curated not audited" plus a dependency/skill scanner hook.
5. **Named meta-orchestrator personas** (context-manager, task-distributor,
   error-coordinator) as a richer layer on top of existing team manifests.
6. **Resumable streaming** — open question whether our sub-agent delegation
   protocol should survive an orchestrator restart. VoltAgent says yes.

All six repos are MIT-licensed, so short quoted excerpts above are permitted with
attribution. Longer mirroring of any `DESIGN.md` tokens from getdesign.md should be
verified against the source site's own terms.
