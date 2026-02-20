# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
