# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.6.3] - 2026-03-14

### Added

- **MCP Compatibility Layer** — The framework is now consumable as MCP servers by Claude Desktop, Antigravity, Cursor, Copilot, OpenCode, OpenClaw, and any MCP-compatible client. Two servers provided:
  - `execution/mcp_server.py` (`agi-framework`) — 13 tools covering the full execution layer: memory auto-query, store, retrieve, cache, list, cross-agent coordination (store/sync/status/handoff/broadcast/pending), and session health check.
  - `skills/qdrant-memory/mcp_server.py` (`qdrant-memory`) — 6 tools wrapping the skill's Python modules directly (no subprocess, no external package).
- **MCP Skill Scaffolding** — `init_skill.py` now auto-generates `mcp_server.py` + `mcp_tools.json` for every new skill. Template lives at `skill-creator/templates/mcp_server_template.py`.

- **Kiro (AWS) compatibility** — Added `.kiro/steering/agents.md` symlink → `AGENTS.md`. Kiro now loads the same agent instructions as Claude Code, Antigravity, and all other coding agents.

### Design Decision

MCP support is **purely additive** — no existing files modified, no validator changes. Rationale: `quick_validate.py` enforces an allowlist `{name, description, license, allowed-tools, metadata}`; adding new top-level SKILL.md keys would break all existing skills. MCP lives in separate files (`mcp_server.py`, `mcp_tools.json`) alongside the skill structure. The `metadata:` field (already allowed) is available for lightweight MCP hints.

**MCP scope clarification:** All coding agents with bash access (Antigravity, Claude Code, Kiro, Cursor, OpenCode, Copilot) were already fully compatible via the symlinked `AGENTS.md`. Agent teams, sub-agents, skills, and memory all work natively for these agents. MCP is only needed for pure chat interfaces (Claude Desktop, etc.) with no bash execution capability.

### Documentation

- **`docs/mcp-compatibility.md`** — New. Full MCP reference: tool catalog, client compatibility matrix, architecture decision rationale, setup for all agents.
- **`skills/qdrant-memory/SKILL.md`** — Updated MCP Quick Start section to reference `mcp_server.py` instead of the external `@qdrant/mcp-server-qdrant` package.
- **`AGENTS.md`** — Added MCP Servers table under Framework Self-Development → Key Scripts.
- **`docs/execution/mcp_server.md`** — New. Documents all 13 tools, transport protocol, environment variables.
- **`skills/SKILLS_CATALOG.md`** — Regenerated; `qdrant-memory` now shows `MCP Server: mcp_server.py` row.

## [1.6.2] - 2026-03-14

### Added

- **Contextual AGI Integration Blocks (1,200 Extended Skills)** — All 1,200 extended skills in `templates/skills/extended/` now include contextually adapted AGI Framework Integration blocks. Each block is domain-specific and provides: Memory-First Protocol (skill-specific Qdrant queries), Storing Results (concrete real-world examples), Multi-Agent Collaboration (skill-specific cross-agent sharing), and a 4th domain-specific section (e.g., Token Versioning for design-system, Brand Source of Truth for brand, Signed Audit Trail for security, Playbook Integration for devops, Asset Registry for banner design).

### Fixed

- **Python 3.11 f-string compatibility** — Resolved `SyntaxError` in `templates/skills/extended/frontend/ui-ux-pro-max/scripts/design_system.py`: backslash inside f-string expression extracted to intermediate variable.

## [1.6.1] - 2026-03-14

### Added

- **Distributed Agent Authentication** — Replaced local SQLite auth storage with shared Qdrant `agent_auth` collection. Identities, access grants, content hashes, and audit trails are now distributed across all agents sharing a Qdrant instance. 8 payload indexes for efficient filtering. Deterministic UUIDs for idempotent operations. (36/36 tests)
- **Hyperledger Aries Integration** — Replaced deprecated MultiChain with Hyperledger Aries ACA-Py 1.5.0 (OpenWallet Foundation). W3C DID identity, Ed25519 signing, official Docker image (`ghcr.io/openwallet-foundation/acapy-agent:1.5.0`). Optional add-on — HMAC-SHA256 works without Aries.
- **Memory Mode Tiers** — Three operational modes (`MEMORY_MODE`): Solo (single user), Team (multi-tenancy with developer isolation), Pro (blockchain auth + access control). All backward-compatible, no data migration needed.
- **Real-Time Agent Events** — Apache Pulsar event bus for push notifications between agents. Auto-publishes on `memory_manager.py store` (team/pro modes). 9 event types. Project-scoped topics (`persistent://agi/memory/<project>`). Graceful degradation when Pulsar unavailable. (19/19 tests)
- **BM25 Auto-Sync on Boot** — `session_boot.py` now automatically syncs the local BM25 keyword index from shared Qdrant data, ensuring every machine has consistent hybrid search results.
- **Docker Compose for Pulsar** — `docker-compose.pulsar.yml` with `apachepulsar/pulsar:4.1.3`, lightweight standalone mode (256-512MB heap), health checks.
- **Docker Compose for Aries** — `docker-compose.aries.yml` with official ACA-Py 1.5.0 image, wallet configuration.

### Changed

- **`blockchain_auth.py`** — Complete rewrite: `QdrantAuthStore` replaces SQLite, `AriesClient` replaces MultiChain. All auth data stored in shared Qdrant collection.
- **`session_boot.py`** — Now reports Pulsar status, Aries status, and BM25 sync results. Auto-syncs BM25 from Qdrant on every boot.
- **`memory_manager.py`** — Auto-publishes Pulsar events on store (team/pro). Health check includes events status.
- **`session_init.py`** — Creates `agent_auth` Qdrant collection with 4-dimensional vectors and 8 payload indexes.

### Documentation

- **`docs/memory-modes.md`** — Complete rewrite. Why each mode, when to use, scenario comparisons, data storage table. Every feature verified with test evidence.
- **`docs/blockchain-auth.md`** — Complete rewrite. Technology comparison (MultiChain vs Ethereum vs Aries), Qdrant vs SQLite rationale, trust model diagram, all CLI commands verified.
- **`docs/agent-events.md`** — Complete rewrite. Pulsar vs Redis/RabbitMQ/Kafka comparison, verified capabilities table, corrected dependency requirements.

### Removed

- **MultiChain** — Deprecated (last commit 2023, no maintained Docker image). Replaced by Hyperledger Aries.
- **SQLite auth storage** — Replaced by shared Qdrant `agent_auth` collection for distributed consistency.

## [1.6.0] - 2026-03-12

### Added

- **Blockchain Agent Identity & Write Signing (Phase 1)** — Each agent gets an Ed25519 keypair on first boot (`~/.agi-agent-kit/identity/`). All Qdrant writes (memory + cache) are automatically signed with `_signature`, `_agent_id`, `_content_hash` fields. Zero performance impact on reads; signing adds <1ms to writes. Graceful degradation if `cryptography` package is not installed.
  - `execution/agent_identity.py` — keypair generation, signing, verification CLI
  - `execution/chain_anchor.py` — async MultiChain hash anchoring with local JSONL queue fallback
  - New dependency: `cryptography`

- **Control Tower Orchestrator** — Central dispatcher tracking all active agents, sub-agents, teams, and LLMs across machines. Commands: `register`, `heartbeat`, `status`, `assign`, `reassign`, `dashboard`. Auto-registers on `session_boot.py` startup.
  - `execution/control_tower.py`
  - `directives/control_tower.md`

- **Cross-Agent Collaboration** — Multi-LLM context sharing via Qdrant. Agents (Claude, Antigravity/Gemini, Cursor, Copilot, OpenCode, OpenClaw) share decisions, handoffs, and broadcasts through `execution/cross_agent_context.py`. Added `sync`, `pending`, `store`, `handoff`, `broadcast`, and `status` commands.

- **Framework Self-Development Infrastructure** — Full dogfooding layer for developing the public framework using its own 3-layer architecture:
  - Directives: `framework_development.md`, `template_sync.md`, `skill_development.md`, `multi_llm_collaboration.md`, `memory_integration.md`, `release_process.md`
  - Execution scripts: `sync_to_template.py` (drift detection + sync), `validate_template.py` (template integrity)
  - Agent Teams: `documentation_team`, `code_review_team`, `qa_team`, `build_deploy_team` with 8 sub-agent directives
  - Skill Creator toolkit: `init_skill.py`, `package_skill.py`, `quick_validate.py`, `update_catalog.py`

- **Upstream Sync Skill** — `skills/upstream-sync/` with `sync_upstream.py` and `upstream_registry.json` for pulling updates from forked skill sources

- **Upstream Sync: antigravity-awesome-skills** — Synced latest from `sickn33/antigravity-awesome-skills` via `skill-adapt` strategy. 406 new skills added, 756 updated with preserved AGI integration blocks. New skills include: `explain-like-socrates`, `ai-md`, `yes-md`, `local-llm-expert`, `keyword-extractor`, and 400+ more across all categories. Total extended skills: 1,181.

- **Upstream Sync: superpowers v5.0.1** — Synced 14 skills from `obra/superpowers` via `skill-diff` strategy: `brainstorming`, `dispatching-parallel-agents`, `executing-plans`, `finishing-a-development-branch`, `receiving-code-review`, `requesting-code-review`, `subagent-driven-development`, `systematic-debugging`, `test-driven-development`, `using-git-worktrees`, `using-superpowers`, `verification-before-completion`, `writing-plans`, `writing-skills`. All adapted with Qdrant hybrid memory integration.

- **Upstream Sync: ui-ux-pro-max** — Full-replace sync from `nextlevelbuilder/ui-ux-pro-max-skill`. 319 files synced including new `slides` skill (HTML presentations with Chart.js), `banner-design` skill (22 styles, multi-platform), `logo` generation (55 styles, Gemini AI), `icon` design (15 styles, SVG), `social-photos` (HTML-to-screenshot), corporate identity program (CIP), and expanded Google Fonts collection with Chinese-to-English translations.

- **Upstream Sync: Yuan3.0** — Reference-only inspection of `Yuan-lab-LLM/Yuan3.0` (8,804 files). Yuan3.0 MoE 40B model with RAPO reinforcement learning. No direct skill mapping — used as research reference for MoE/RAPO patterns.

- **Skills Catalog** — `skills/SKILLS_CATALOG.md` — complete auto-generated catalog of all installed skills

- **Workflow Playbooks Data** — `data/workflows.json` with guided multi-skill sequences

- **Contextual AGI Integration Blocks** — Replaced generic copy-paste AGI blocks across all 1,184 extended skills with domain-specific content. 16 category templates (security, architecture, testing, debugging, AI agents, DevOps, frontend, backend, workflow, documentation, data, content, mobile, blockchain, gaming, default) each showing real framework features relevant to that skill's domain — signed audit trails for security, TDD enforcement for testing, BM25 exact match for debugging, Control Tower for architecture, etc. Added `scripts/contextualize_agi_blocks.py` for future upstream sync re-runs.

### Changed

- **Session Boot** — Now checks/generates agent identity (Step 2.5) and auto-registers with Control Tower (Step 4). Reports `agent_id` in summary output.
- **Memory Writes** — `store_memory()` and `store_response()` return `signed` and `agent_id` fields indicating cryptographic signing status.
- **AGENTS.md** — Added cross-agent collaboration section and framework self-development documentation. Symlinked as `CLAUDE.md` and `GEMINI.md` for cross-agent instruction sharing.
- **Roadmap** — Added: Blockchain Agent Trust & Tenancy (design), Apache Pulsar streaming (design), Control Tower Orchestrator (active), Secrets Management via Vault (design).
- **Upstream Sync Script** — Fixed `PROJECT_ROOT` resolution in `sync_upstream.py` (was resolving to `skills/` instead of repo root, causing `adapt_script_missing` errors).

### Security

- **CodeQL CWE-20 Fix** — Replaced URL substring checks with `urlparse` hostname comparison to prevent incomplete URL sanitization (`46739fc`)
- **Workflow Permissions** — Added explicit least-privilege permissions to `publish.yml` and `virustotal.yml` workflows (`70715d4`)
- **CVE-2026-27606** — Updated rollup in todo app example to resolve dependency vulnerability (`34b28d1`)
- **VirusTotal Action** — Bumped `crazy-max/ghaction-virustotal` from v4 to v5

## [1.5.3] - 2026-02-22

### Fixed

- **`system_checkup.py` missing after full install** — The script was accidentally removed during the v1.2.7 repository sanitization (`c564459`). Restored `system_checkup.py` to `templates/base/execution/` so `npx init` correctly copies it into new projects. Running `python3 execution/system_checkup.py --verbose` now works as documented.
- **`hybrid_search.py` incorrect path in documentation** — README, README.pt-BR, `directives/memory_integration.md`, and `qdrant-memory/references/complete_guide.md` all referenced `scripts/hybrid_search.py`, which does not exist. Corrected all 6 occurrences to the actual path: `skills/qdrant-memory/scripts/hybrid_search.py`.

## [1.5.2] - 2026-02-21

### Added

- **Portuguese Localization** — Added `README.pt-BR.md` to support Brazilian Portuguese speakers.
- **UI UX Pro Max Prompts** — Expanded the `ui-ux-pro-max` skill with proven structural and stylistic prompt examples (SaaS, Educational, Pet Grooming, AI Chatbot).

## [1.5.1] - 2026-02-21

### Changed

- **UI UX Pro Max v2.0** — Upgraded design intelligence skill with major enhancements:
  - **Design System Generator** — AI-powered reasoning engine that analyzes project requirements and generates complete, tailored design systems (pattern, style, colors, typography, effects, anti-patterns)
  - **100 Industry-Specific Reasoning Rules** — Automated style/color/typography selection based on product type and industry
  - **Expanded Data** — 67 UI styles (was 50), 96 color palettes (was 21), 57 font pairings (was 50), 25 chart types (was 20), 13 tech stacks (was 9), 99 UX guidelines
  - **Persist Design System** — Master + Overrides pattern for hierarchical retrieval across sessions (`--persist` flag)
  - **Qdrant Memory Integration** — Design decisions automatically stored and retrieved for project continuity
  - **SKILLS_CATALOG.md** — Updated `ui-ux-pro-max` description to reflect v2.0 capabilities

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
