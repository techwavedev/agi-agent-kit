# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.0] - 2026-02-09

### Added

- **Platform-Adaptive Multi-Agent Orchestration** (`parallel-agents` v2.0):
  - **Strategy A: Claude Code Agent Teams** — True parallel multi-agent orchestration via tmux/in-process sessions. Requires `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`.
  - **Strategy B: Claude Code Subagents** — Background/foreground task orchestration via `Task()` tool with `context: fork`.
  - **Strategy C: Sequential Personas** — Universal fallback for Gemini, Opencode, and other platforms using `@agent` persona switching.
  - **Strategy D: Kiro Autonomous Agent** — Async parallel task execution in sandboxed environments with PR-based delivery and cross-repo coordination.
  - Automatic platform detection and strategy selection.
  - Subagent configuration reference (frontmatter, tools, permissions, model, memory).
  - Full Claude Code subagent lifecycle documentation (create, configure, invoke, manage).

- **Kiro IDE Powers & Autonomous Agent Support**:
  - Full Kiro Powers documentation: `POWER.md` anatomy, frontmatter keywords activation, onboarding sections, steering files, `mcp.json` configuration with auto-namespacing.
  - Kiro Hooks system (`.kiro/hooks/`) with JSON structure and automated behaviors.
  - Kiro Autonomous Agent: sandboxed execution, PR-based reviews, cross-repo coordination, learning from code reviews.
  - 12 curated launch partner Powers documented (Figma, Supabase, Stripe, Neon, Netlify, Postman, Strands, Datadog, Dynatrace, AWS CDK, Terraform, Aurora).
  - **Antigravity ↔ Kiro mapping guide**: Skill-to-Power conversion workflow, directory mapping, frontmatter translation.

- **Plugin & Extension Auto-Discovery** (`plugin-discovery` v1.1.0 — NEW SKILL):
  - Cross-platform extension auto-discovery for Claude Code, Kiro IDE, Gemini, and Opencode.
  - Claude Code: Plugin marketplace guide (official + custom), LSP plugins by language, service integrations, scopes, subagent/skill discovery.
  - Kiro: Full Powers discovery, installation guide (IDE, kiro.dev, GitHub, local path), setup checklist.
  - Gemini/Opencode: Skills catalog discovery, MCP server detection.
  - Cross-platform compatibility map (11 features × 4 platforms).

- **One-Shot Platform Setup Wizard** (`platform_setup.py`):
  - Auto-detects platform: Claude Code, Kiro IDE, Gemini, Opencode.
  - Scans project tech stack: languages (JS/TS/Python/Go/Rust/Ruby), frameworks (Next.js/React/Vue/Express/Angular/Svelte/Astro/React Native), services (GitHub/GitLab/Docker/Vercel/Netlify/Stripe/Supabase/Firebase/Terraform).
  - Generates prioritized recommendations with `🔴 High` / `🟡 Medium` / `🟢 Low` indicators.
  - Auto-applies configurable settings (Agent Teams, directory creation, hook setup) with single `Y/n` confirmation.
  - Shows manual instructions for platform-only actions (plugin installs, Power installs).
  - 4 modes: interactive, `--auto`, `--dry-run`, `--json`.
  - New `/setup` workflow with `// turbo` annotation for auto-run.

- **Intelligent Routing v2.0** (`intelligent-routing` v2.0):
  - Platform detection at session start (Claude Code, Kiro IDE, Gemini, Opencode).
  - Proactive capability announcements per platform.
  - Team Leader mode for Claude Code with Agent Teams enabled.
  - Powers-driven orchestration mode for Kiro IDE.
  - Proactive feature recommendations: suggests Agent Teams, plugins, Powers, Autonomous Agent when not enabled.
  - Multi-domain task routing adapts to best available parallelism strategy.

### Changed

- **`parallel-agents`**: Rewritten from v1.0 to v2.0 — now platform-adaptive with 4 orchestration strategies instead of 1.
- **`intelligent-routing`**: Rewritten from v1.0 to v2.0 — now includes platform detection, proactive recommendations, and Kiro support.
- **Cross-Platform Compatibility Map**: Updated with 2 new rows (Dynamic MCP Loading, Cross-Repo Tasks) and accurate Kiro feature coverage.
- **`package.json`**: Added `kiro`, `opencode`, and `platform-adaptive` keywords for NPM discoverability.
- **Templates**: All modified skills (`parallel-agents`, `intelligent-routing`, `plugin-discovery`) and scripts (`platform_setup.py`) synced to `templates/skills/knowledge/` for NPX distribution.
- **SKILLS_CATALOG.md**: Regenerated with 56 skills, including the new `plugin-discovery` skill.

## [1.1.7] - 2026-02-07

### Added

- **NotebookLM RAG Skill** (EC Scoped): New `notebooklm-rag` skill providing deep-search RAG capabilities powered by Google NotebookLM + Gemini 2.5. Complementary to `qdrant-memory` for explicit, document-grounded research.
  - **B.L.A.S.T. Protocol**: Structured research workflow (Browse → Load → Ask → Synthesize → Transfer).
  - **4 Research Modes**: Quick (single query), Deep (3-5 iterative), Cross-Ref (multi-notebook), Plan (doc-grounded planning).
  - **Confidence Classification**: Automatic HIGH/MEDIUM/LOW categorization with source attribution.
  - `scripts/research_query.py` — Generates structured research questions by mode.
  - `scripts/research_report.py` — Formats findings into Markdown/JSON reports with confidence levels and knowledge gap analysis.
  - `scripts/preflight_check.py` — Pre-flight validation checklist for MCP server, auth, and library.
  - `references/research_patterns.md` — Workflow templates, query optimization, rate limit strategies.
- **Auto-Update in Skill Creator**: `init_skill.py` now auto-runs `update_catalog.py` and `sync_docs.py` after creating a new skill.
  - Default ON — use `--no-auto-update` to skip.
  - New `--skills-dir` flag for specifying catalog update target directory.
  - Non-fatal: graceful warnings if documentation skill is not installed.

### Changed

- **NotebookLM MCP Skill**: Migrated to `PleasePrompto/notebooklm-mcp` browser-automated implementation with full auth, library management, and stealth mode support.
- **Skill Creator Documentation** (`SKILL_skillcreator.md`):
  - Step 3: Documents new auto-update behavior and `--no-auto-update` / `--skills-dir` flags.
  - Step 6: Notes that manual catalog update is now only needed for modifications/deletions.
- **SKILLS_CATALOG.md**: Regenerated with 55 skills including `notebooklm-rag`.

### Fixed

- **`init_skill.py` argument parsing**: Migrated from fragile positional parsing (`sys.argv`) to robust `argparse` with proper help text and validation.
- **`sync_docs.py` invocation**: Fixed `--update-catalog` flag to pass `"true"` as required value (not just the bare flag).

## [1.1.6] - 2026-02-07

### Added

- **37 Knowledge Skills Promoted to Root**: All knowledge-pack skills now live at `skills/` root alongside core skills for unified access:
  - `api-patterns`, `app-builder`, `architecture`, `bash-linux`, `behavioral-modes`, `brainstorming`, `clean-code`, `code-review-checklist`, `database-design`, `deployment-procedures`, `documentation-templates`, `frontend-design`, `game-development`, `geo-fundamentals`, `i18n-localization`, `intelligent-routing`, `lint-and-validate`, `mcp-builder`, `mobile-design`, `nextjs-best-practices`, `nodejs-best-practices`, `parallel-agents`, `performance-profiling`, `plan-writing`, `powershell-windows`, `python-patterns`, `react-patterns`, `red-team-tactics`, `seo-fundamentals`, `server-management`, `systematic-debugging`, `tailwind-patterns`, `tdd-workflow`, `testing-patterns`, `vulnerability-scanner`, `webapp-testing`.
- **NotebookLM MCP Skill**: New `notebooklm-mcp` skill to interact with Google NotebookLM via Model Context Protocol, with documentation, example script, and reference assets.
- **Opencode Support**: Added `OPENCODE.md` configuration file for Opencode editor compatibility with `opencode-antigravity-auth` plugin.
- **Execution Scripts**: Two new deterministic execution scripts:
  - `memory_manager.py` — Centralized memory management for Qdrant operations.
  - `session_init.py` — Session initialization and context bootstrapping.
- **Stitch Skills in Templates**: `design-md`, `react-components`, and `stitch-loop` now included in knowledge templates (`templates/skills/knowledge/`) for NPX distribution.
- **Self-Update in Templates**: `self-update` skill with `update_kit.py` added to knowledge templates.
- **Knowledge SKILLS_CATALOG**: New comprehensive `SKILLS_CATALOG.md` inside `templates/skills/knowledge/` for template-level skill discovery.

### Changed

- **AGENTS.md**: Added "Getting Started" section with installation, dependency, and update instructions.
- **Memory Integration Directive**: Complete rewrite of `directives/memory_integration.md` — simplified from 211 lines to 95 lines with clearer goal/inputs/execution structure and Ollama embedding documentation.
- **Skill Creator**: Updated `SKILL_skillcreator.md` with refined skill creation guidelines.
- **SKILLS_CATALOG.md**: Expanded with 560+ lines of new skill entries covering all promoted knowledge skills.
- **Documentation Skill**: Updated `skills/documentation/SKILL.md` with improved detection and sync logic.
- **Template Hierarchy Restructured**: Shifted standalone template skills (`design-md`, `react-components`, `stitch-loop`) into `templates/skills/knowledge/` for consistent NPX packaging.

### Improved

- **Core Skill Definitions**: Refined SKILL.md files across `pdf-reader`, `qdrant-memory`, and `webcrawler` with updated descriptions, triggers, and references.
- **Qdrant Memory Scripts**: Updated all 7 scripts (`benchmark_token_savings.py`, `embedding_utils.py`, `hybrid_search.py`, `init_collection.py`, `memory_retrieval.py`, `semantic_cache.py`, `test_skill.py`) with improved patterns.
- **Knowledge Skill Documentation**: Mass update of SKILL.md definitions across 36+ knowledge skills with enhanced frontmatter, triggers, and reference content in templates.
- **Audit Scripts**: Updated `ux_audit.py`, `security_scan.py`, `lighthouse_audit.py`, `test_runner.py`, `playwright_runner.py`, and `seo_checker.py` in templates.

### Fixed

- **Version Bump**: Package version correctly set to `1.1.6` in `package.json`.
- **Template Cleanup**: Removed duplicate standalone Stitch skill templates (`templates/skills/design-md/`, `templates/skills/react-components/`, `templates/skills/stitch-loop/`), consolidated into `templates/skills/knowledge/`.
- **Removed `verify_public_release.py`**: Deprecated top-level verification script removed (functionality integrated into CI/CD pipeline).

## [1.1.5] - 2026-01-27

### Added

- **Stitch Skills Suite**: Added three new skills from Google Stitch:
  - `design-md`: Analyzes Stitch projects to synthesize semantic `DESIGN.md` systems.
  - `react-components`: Converts Stitch screens into modular, validating React components.
  - `stitch-loop`: Orchestrates autonomous iterative website building loops.
- **Memory Integration**: Integrated `qdrant-memory` into the Stitch skills suite for:
  - Storing design systems for future retrieval (`design-md`).
  - Retrieving code patterns and interfaces (`react-components`).
  - Leveraging past decisions and project context (`stitch-loop`).

## [1.1.2] - 2026-01-23

### Added

- **Self-Update Skill**: New `self-update` skill with `update_kit.py` script for easy framework updates.
- **System Checkup**: New `system_checkup.py` execution script to verify agents, skills, workflows, and scripts.
- **Workflows**: Added `/checkup` and `/update` workflows for quick access.

### Changed

- Updated `README.md` with comprehensive Quick Start, Commands, and Architecture sections.
- Updated `SKILLS_CATALOG.md` to include self-update skill.

## [1.1.01] - 2026-01-23

### Fixed

- Stabilized Full Suite activation.
- Micro-bump for polish releases.

## [1.1.0] - 2026-01-23

### Added

- **Knowledge Pack**: Imported 36+ new skills from `agents-web` including:
  - `api-patterns`: Best practices for REST/GraphQL/tRPC.
  - `frontend-design`: UX/UI principles and audit tools.
  - `security-auditor`: Vulnerability scanning and red-team tactics.
  - `mobile-design`: iOS/Android development patterns.
- **Agent Roles**: Added `project-planner`, `orchestrator`, and `security-auditor` agent personas.
- **Rules**: Added global `deployment_policy` and `clean-code` standards.

### Changed

- Refactored `init` command to support `knowledge` pack.
- Enhanced `AGENTS.md` with new agent capabilities.
- Updated `SKILLS_CATALOG.md` with full list of new skills.

## [1.0.1] - 2026-01-23

### Fixed

- **Security**: Removed all references to private infrastructure from public templates.
- **Safety**: Added `verify_public_release.py` to prevent accidental publication of private secrets.
- **Menu**: Fixed `init` menu showing internal options.

## [0.1.0] - 2026-01-23

### Initial Release

- Core framework with `webcrawler`, `pdf-reader`, and `qdrant-memory`.
- CLI tool `agi-agent-kit` for scaffolding.
