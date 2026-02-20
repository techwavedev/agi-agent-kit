# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.5.0] - 2026-02-20

### Added

- **Smart Init Wizard** — Complete overhaul of `npx init` with a guided, step-by-step setup experience:
  - **Existing install detection** — Reads `.agi-version` stamp; offers `Update` (preserve `.env`), `Reinstall` (full overwrite), or `Cancel`. Shows installed vs incoming version with downgrade warning.
  - **Install scope prompt** — Choose between project-local (current dir) or global (`~/.agent` + platform symlinks) with a compatibility table and pitfalls disclaimer.
  - **Smart backup** — Scans files that would be overwritten before touching anything. For global installs, also detects real platform dirs that would be replaced by symlinks. Saves timestamped backup.
  - **Custom domain pack selection** — New `4. custom` option shows all 15 skill domains with ■ professional and ■ community skill counts, supports comma/range multi-select (`1,3,7-9`, `all`).
  - **Service-aware memory setup** — Detects Ollama, Docker, and Qdrant before asking. If a service is missing, asks whether it's not installed yet (shows install link) or running on a custom URL (prompts for URL + API key, verifies connectivity).
  - **Agent Teams prompt** — Explicit opt-in to `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` with explanation and safe merge into `.claude/settings.json`.
  - **Uninstall script** — Global installs generate `~/.agent/uninstall-agi.sh`, a ready-to-run script that removes all symlinks and the install directory.
  - **Version stamp** — Writes `.agi-version` after every install/update.
  - **Configurable final summary** — Shows exactly what was configured (memory, Agent Teams, MCP) and what manual steps remain (plugins, MCP servers).

### Changed

- **`verifyMemorySetup()`** — Now returns `true`/`false` so the final message correctly shows "Memory is READY" vs "start services" only when relevant.
- **`writeEnvFile()`** — Now writes the actual Qdrant URL, Ollama URL, and API key entered during setup instead of always defaulting to localhost.
- **`copySkills()`** — Refactored to share a helper. Custom pack installs core first then resolves each selected domain from both `knowledge/` and `extended/` tiers.
- **Platform setup** (`runPlatformSetup`) — Now runs _after_ the new `promptPlatformFeatures` step so user intent is captured before platform scripts apply settings.

### Fixed

- **Next steps message** — No longer suggests starting services when they were already verified during install.
- **`memoryVerified` bug** — Was referenced but never assigned; `verifyMemorySetup()` return value is now captured.

## [1.4.2]

- **Fixed README links** — ./skills/SKILLS_CATALOG.md updated to ./templates/skills/SKILLS_CATALOG.md (closes #15)
- **Removed Stitch Nested Duplicates** — Removed nested design-md/design-md, react-components/react-components, stitch-loop/stitch-loop (closes #16) - 2026-02-20

### Added

- **Workflow Engine** — `execution/workflow_engine.py` — executes multi-skill playbooks from `data/workflows.json` with state persistence, progress tracking, and branching logic (closes #13)
- **Playbook Protocol in AGENTS.md** — Agents now know how to discover, start, and step through playbooks via the `/playbook` command
- **4 Missing Slash Commands** — Created `setup.md`, `setup-memory.md`, `update.md`, `checkup.md` workflow files (closes #8)
- **All 19 Agent Personas Documented** — README now lists all 19 agents instead of only 8 (closes #9)

### Fixed

- **README Skill Counts** — 853→878 (was stale since v1.3.7); breakdown: 4 core + 89 knowledge + 785 extended (closes #6)
- **README Platform Counts** — Fixed inconsistencies (4/8/9) to consistent 9 platforms everywhere (closes #10)
- **README Trigger Keywords** — Fixed ghost skill names (`aws`→`aws-skills`, `aws-terraform`→`terraform-skill`, removed `consul`/`opensearch` EC-scoped refs) (closes #11)
- **10 Skills Missing AGI Framework Integration** — Added `🧠 AGI Framework Integration` section to 10 knowledge skills that lacked it (closes #7)
- **init.js Skill Counts** — Updated 793→785 to match actual after removals
- **SKILLS_CATALOG.md Header** — Updated 886→878 to match actual

### Removed

- **8 Duplicate Skills** — Finally removed 8 skills that v1.3.7 CHANGELOG claimed were removed but still existed (closes #12):
  - `pptx-official`, `docx-official` (duplicates of `pptx`, `docx`)
  - `brand-guidelines-community`, `brand-guidelines-anthropic` (merged into `brand-guidelines`)
  - `internal-comms-community`, `internal-comms-anthropic` (merged into `internal-comms`)
  - `mcp-builder-ms`, `skill-creator-ms` (merged into `mcp-builder`, `skill-creator`)
- **Skill Count** — 886→878 (net -8 duplicates)

## [1.4.1] - 2026-02-20

### Added

- **11 New Upstream Skills** — Imported and adapted from `antigravity-awesome-skills` latest:
  - `crypto-bd-agent` — Autonomous crypto business development patterns
  - `dbos-golang`, `dbos-python`, `dbos-typescript` — DBOS durable workflow SDKs
  - `ddd-context-mapping`, `ddd-strategic-design`, `ddd-tactical-patterns`, `domain-driven-design` — Domain-Driven Design suite
  - `laravel-expert`, `laravel-security-audit` — Laravel development and security
  - `react-flow-architect` — ReactFlow interactive graph applications
- **Release Gate UX** — Added progress indicators to secret scanning and syntax checking

### Fixed

- **Skill Count Update** — Total skills 875→886, Extended 782→793

## [1.4.0] - 2026-02-20

### Added

- **Workflows Metadata** — Added `data/workflows.json` with 4 guided multi-skill playbooks:
  - `ship-saas-mvp` — 5-step SaaS delivery
  - `security-audit-web-app` — 4-step AppSec review
  - `build-ai-agent-system` — 4-step AI agent design
  - `qa-browser-automation` — 3-step E2E testing

### Fixed

- **Skill Count Correction** — Updated SKILLS_CATALOG.md and init.js from stale 862/76 to actual 875/89. Core: 4, Knowledge (Medium): 89, Extended (Full): 782.

## [1.3.8] - 2026-02-20

### Fixed

- **Memory System Path Resolution** — Fixed `ModuleNotFoundError` for `embedding_utils` in `memory_manager.py` and `session_init.py` by implementing an adaptive multi-candidate path approach. This ensures correct script initialization inside natively customized workspaces and `npx`-bootstrapped agent projects.

## [1.3.7] - 2026-02-17

### Fixed

- **Skill Conflict Resolution** — Resolved 8 conflicting skill pairs detected in Gemini CLI:
  - **6 duplicates removed**: `xlsx-official`, `pdf-official`, `pptx-official`, `docx-official`, `brand-guidelines-community`, `internal-comms-community` (identical SKILL.md content, only `__pycache__` differed)
  - **2 MS-specialized skills merged**: `mcp-builder-ms` → `mcp-builder` (added C#/.NET SDK, Azure MCP ecosystem, Foundry remote MCP), `skill-creator-ms` → `skill-creator` (added Azure SDK Appendix with auth patterns, verb patterns, product categories)
  - **2 skills renamed**: `brand-guidelines-anthropic` → `brand-guidelines`, `internal-comms-anthropic` → `internal-comms`

### Changed

- **Skill count**: 861 → 853 (8 redundant skill directories removed, 0 content lost)
- **`mcp-builder`**: Now includes Microsoft MCP ecosystem section (Azure MCP Server, Foundry MCP, Fabric MCP), C#/.NET language support, and transport selection tables
- **`skill-creator`**: Now includes Azure SDK Skill Patterns appendix with DefaultAzureCredential patterns, standard verb patterns, and product area categories

## [1.3.6] - 2026-02-16

### Security

- **Backend Template Hardening** — Resolved 5 high-severity vulnerabilities in `loki-mode` backend example by upgrading dependencies.

### Added

- **OpenClaw Platform Support** — Complete integration with auto-detection and instruction symlinks.
  - **Badge**: Added OpenClaw badge to README
  - **Ecosystem**: Now supporting 9 major AI coding platforms

- **Hybrid BM25+Vector Memory Search** — True hybrid retrieval combining Qdrant vector similarity with SQLite FTS5 keyword search:
  - **BM25 Index** (`bm25_index.py`): SQLite FTS5 sidecar for exact keyword matching (error codes, IDs, env vars)
  - **Weighted Score Merge**: `finalScore = 0.7 × vectorScore + 0.3 × textScore` (configurable)
  - **3 Search Modes**: `hybrid` (default), `vector`, `keyword`
  - **Auto-indexing**: Every `store_memory()` call automatically indexes into BM25
  - **`bm25-sync` command**: Rebuild keyword index from existing Qdrant collection
  - **Graceful fallback**: Falls back to vector-only if BM25 unavailable
  - **FTS5 query sanitization**: Handles special characters (hyphens, dots) in search terms
  - **16/16 tests passing**: 4 new BM25 tests (index, hybrid, score merge, fallback)

## [1.3.5] - 2026-02-16

### Added

- **Extended Skills Tier: 861 Total Skills** — Integrated 782 community skills from [antigravity-awesome-skills](https://github.com/sickn33/antigravity-awesome-skills) (v5.4.0). Restructured skill tiers:
  - **Core** (4 skills): webcrawler, pdf-reader, qdrant-memory, documentation
  - **Medium** (75 skills): Core + specialized skills across 16 categories
  - **Full** (861 skills): Medium + 782 community skills, all adapted for AGI framework

- **Categorized Skill Organization** — All skills organized into 16 domain categories:
  `frontend/`, `backend/`, `ai-agents/`, `devops/`, `testing/`, `security/`, `architecture/`, `mobile/`, `debugging/`, `documentation/`, `workflow/`, `content/`, `data/`, `gaming/`, `blockchain/`, `other/`

- **8-Platform Support** — Claude Code, Gemini CLI, Codex CLI, Antigravity IDE, Cursor, GitHub Copilot, OpenCode, AdaL CLI

- **AGI Framework Adaptation** — All 782 community skills adapted with:
  - Qdrant Memory Integration (semantic caching)
  - Agent Team Collaboration (orchestrator-driven invocation)
  - Local LLM Support (Ollama embeddings)

- **Automated NPM Publishing** — GitHub Actions workflow: create a release → NPM publishes automatically via OIDC Trusted Publisher

### Credits

This release includes skills aggregated from 50+ open-source contributors including Anthropic, Microsoft, Vercel Labs, Supabase, Trail of Bits, and many more. See [SOURCES.md](https://github.com/sickn33/antigravity-awesome-skills/blob/main/docs/SOURCES.md) for the full attribution ledger.

## [1.2.8] - 2026-02-14

### Added

- **Superpowers Adaptation** — Adapted best patterns from [obra/superpowers](https://github.com/obra/superpowers):
  - **`executing-plans`**: Structured plan execution with Batch or Subagent-Driven modes + two-stage review
  - **`test-driven-development`**: Iron-law TDD enforcement with RED-GREEN-REFACTOR cycle
  - **`verification-before-completion`**: No completion claims without fresh verification output
  - **`systematic-debugging`**: Comprehensive 4-phase methodology (Root Cause → Pattern Analysis → Hypothesis → Implementation)

## [1.2.7] - 2026-02-11

### Security & Maintenance

- Repository sanitization: removed all internal development configurations from public repository
- Workflow hardening: enforced fork-and-PR workflow
- Added issue templates and PR templates

## [1.2.6] - 2026-02-10

### Added

- **NotebookLM RAG Skill**: Deep-search RAG powered by Google NotebookLM + Gemini. MCP-first autonomous knowledge backend with Qdrant caching for token savings.

## [1.2.3] - 2026-02-09

### Added

- **Auto Python Virtual Environment**: `npx init` now auto-creates `.venv/` and installs all dependencies
- **Auto Platform Setup**: `npx init` runs `platform_setup.py --auto` after venv creation
- **Activation Reference Table**: 14 slash commands, 8 `@agent` mentions, 18 trigger keyword categories, 6 memory commands
- **Platform-Adaptive Multi-Agent Orchestration**: 4 strategies (Agent Teams, Subagents, Sequential Personas, Kiro Autonomous Agent)
- **Plugin & Extension Auto-Discovery**: Cross-platform extension discovery for Claude Code, Kiro IDE, Gemini, and Opencode
- **One-Shot Platform Setup Wizard**: Auto-detects platform, scans project stack, generates recommendations, auto-applies settings
- **Memory System Integration**: `session_boot.py` — single entry point for Qdrant + Ollama initialization

## [1.1.7] - 2026-02-07

### Added

- **NotebookLM MCP Skill**: Interact with Google NotebookLM via Model Context Protocol
- **37 Knowledge Skills Promoted**: All knowledge-pack skills now live at `skills/` root for unified access
- **Opencode Support**: Added `OPENCODE.md` configuration

## [1.1.5] - 2026-01-27

### Added

- **Stitch Skills Suite**: `design-md`, `react-components`, `stitch-loop` with Qdrant memory integration

## [1.1.0] - 2026-01-23

### Added

- **Knowledge Pack**: 36+ new skills from `agents-web` (API patterns, frontend design, security, mobile)
- **Agent Roles**: `project-planner`, `orchestrator`, `security-auditor`
- **Clean-code** and **deployment** global standards

## [0.1.0] - 2026-01-23

### Initial Release

- Core framework with `webcrawler`, `pdf-reader`, and `qdrant-memory`
- CLI tool `agi-agent-kit` for scaffolding
