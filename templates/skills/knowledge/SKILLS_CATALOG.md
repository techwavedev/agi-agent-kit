# Skills Catalog

> **Auto-generated Documentation** — Last updated: 2026-02-14 20:01
>
> This catalog is automatically maintained. Update it by running:
> ```bash
> python skill-creator/scripts/update_catalog.py --skills-dir skills/
> ```

This document provides comprehensive documentation on available skills, how to use them, and when each skill should be triggered.

---

## Table of Contents

- [What Are Skills?](#what-are-skills)
- [Available Skills](#available-skills)
  - [Api Patterns](#api-patterns)
  - [App Builder](#app-builder)
  - [Architecture](#architecture)
  - [Bash Linux](#bash-linux)
  - [Behavioral Modes](#behavioral-modes)
  - [Brainstorming](#brainstorming)
  - [Clean Code](#clean-code)
  - [Code Review Checklist](#code-review-checklist)
  - [Database Design](#database-design)
  - [Deployment Procedures](#deployment-procedures)
  - [Design Md](#design-md)
  - [Documentation Templates](#documentation-templates)
  - [Executing Plans](#executing-plans)
  - [Frontend Design](#frontend-design)
  - [Game Development](#game-development)
  - [Geo Fundamentals](#geo-fundamentals)
  - [I18N Localization](#i18n-localization)
  - [Intelligent Routing](#intelligent-routing)
  - [Lint And Validate](#lint-and-validate)
  - [Mcp Builder](#mcp-builder)
  - [Mobile Design](#mobile-design)
  - [Nextjs Best Practices](#nextjs-best-practices)
  - [Nodejs Best Practices](#nodejs-best-practices)
  - [Notebooklm Rag](#notebooklm-rag)
  - [Parallel Agents](#parallel-agents)
  - [Performance Profiling](#performance-profiling)
  - [Plan Writing](#plan-writing)
  - [Plugin Discovery](#plugin-discovery)
  - [Powershell Windows](#powershell-windows)
  - [Python Patterns](#python-patterns)
  - [React:Components](#react:components)
  - [React Patterns](#react-patterns)
  - [Red Team Tactics](#red-team-tactics)
  - [Self Update](#self-update)
  - [Seo Fundamentals](#seo-fundamentals)
  - [Server Management](#server-management)
  - [Stitch Loop](#stitch-loop)
  - [Systematic Debugging](#systematic-debugging)
  - [Tailwind Patterns](#tailwind-patterns)
  - [Tdd Workflow](#tdd-workflow)
  - [Test Driven Development](#test-driven-development)
  - [Testing Patterns](#testing-patterns)
  - [Verification Before Completion](#verification-before-completion)
  - [Vulnerability Scanner](#vulnerability-scanner)
  - [Webapp Testing](#webapp-testing)
- [Using Skills](#using-skills)
- [Creating New Skills](#creating-new-skills)
- [Maintenance](#maintenance)

---

## What Are Skills?

**Skills** are modular, self-contained packages that extend the AI agent's capabilities with specialized knowledge, workflows, and tools.

### Skill Structure

```
skill-name/
├── SKILL.md           # (required) Main instruction file
├── scripts/           # (optional) Executable scripts
├── references/        # (optional) Documentation
└── assets/            # (optional) Templates, images, etc.
```

---

## Available Skills

### Api Patterns

| Property | Value |
| -------- | ----- |
| **Name** | `api-patterns` |
| **Location** | `skills/api-patterns/` |
| **Type** | Standalone |

**Description:** API design principles and decision-making. REST vs GraphQL vs tRPC selection, response formats, versioning, pagination.

**Scripts:**

| Script | Purpose |
| ------ | ------- |
| `scripts/api_validator.py` | *[See script for details]* |

---

### App Builder

| Property | Value |
| -------- | ----- |
| **Name** | `app-builder` |
| **Location** | `skills/app-builder/` |
| **Type** | Standalone |

**Description:** Main application building orchestrator. Creates full-stack applications from natural language requests. Determines project type, selects tech stack, coordinates agents.

---

### Architecture

| Property | Value |
| -------- | ----- |
| **Name** | `architecture` |
| **Location** | `skills/architecture/` |
| **Type** | Standalone |

**Description:** Architectural decision-making framework. Requirements analysis, trade-off evaluation, ADR documentation. Use when making architecture decisions or analyzing system design.

---

### Bash Linux

| Property | Value |
| -------- | ----- |
| **Name** | `bash-linux` |
| **Location** | `skills/bash-linux/` |
| **Type** | Standalone |

**Description:** Bash/Linux terminal patterns. Critical commands, piping, error handling, scripting. Use when working on macOS or Linux systems.

---

### Behavioral Modes

| Property | Value |
| -------- | ----- |
| **Name** | `behavioral-modes` |
| **Location** | `skills/behavioral-modes/` |
| **Type** | Standalone |

**Description:** AI operational modes (brainstorm, implement, debug, review, teach, ship, orchestrate). Use to adapt behavior based on task type.

---

### Brainstorming

| Property | Value |
| -------- | ----- |
| **Name** | `brainstorming` |
| **Location** | `skills/brainstorming/` |
| **Type** | Standalone |

**Description:** Socratic questioning protocol + user communication. MANDATORY for complex requests, new features, or unclear requirements. Includes progress reporting and error handling.

---

### Clean Code

| Property | Value |
| -------- | ----- |
| **Name** | `clean-code` |
| **Location** | `skills/clean-code/` |
| **Type** | Standalone |

**Description:** Pragmatic coding standards - concise, direct, no over-engineering, no unnecessary comments

---

### Code Review Checklist

| Property | Value |
| -------- | ----- |
| **Name** | `code-review-checklist` |
| **Location** | `skills/code-review-checklist/` |
| **Type** | Standalone |

**Description:** Code review guidelines covering code quality, security, and best practices.

---

### Database Design

| Property | Value |
| -------- | ----- |
| **Name** | `database-design` |
| **Location** | `skills/database-design/` |
| **Type** | Standalone |

**Description:** Database design principles and decision-making. Schema design, indexing strategy, ORM selection, serverless databases.

**Scripts:**

| Script | Purpose |
| ------ | ------- |
| `scripts/schema_validator.py` | *[See script for details]* |

---

### Deployment Procedures

| Property | Value |
| -------- | ----- |
| **Name** | `deployment-procedures` |
| **Location** | `skills/deployment-procedures/` |
| **Type** | Standalone |

**Description:** Production deployment principles and decision-making. Safe deployment workflows, rollback strategies, and verification. Teaches thinking, not scripts.

---

### Design Md

| Property | Value |
| -------- | ----- |
| **Name** | `design-md` |
| **Location** | `skills/design-md/` |
| **Type** | Standalone |

**Description:** Analyze Stitch projects and synthesize a semantic design system into DESIGN.md files

---

### Documentation Templates

| Property | Value |
| -------- | ----- |
| **Name** | `documentation-templates` |
| **Location** | `skills/documentation-templates/` |
| **Type** | Standalone |

**Description:** Documentation templates and structure guidelines. README, API docs, code comments, and AI-friendly documentation.

---

### Executing Plans

| Property | Value |
| -------- | ----- |
| **Name** | `executing-plans` |
| **Location** | `skills/executing-plans/` |
| **Type** | Standalone |

**Description:** Structured plan execution with batch checkpoints or subagent-per-task with two-stage review. Use when you have a written implementation plan to execute methodically.

---

### Frontend Design

| Property | Value |
| -------- | ----- |
| **Name** | `frontend-design` |
| **Location** | `skills/frontend-design/` |
| **Type** | Standalone |

**Description:** Design thinking and decision-making for web UI. Use when designing components, layouts, color schemes, typography, or creating aesthetic interfaces. Teaches principles, not fixed values.

**Scripts:**

| Script | Purpose |
| ------ | ------- |
| `scripts/accessibility_checker.py` | *[See script for details]* |
| `scripts/ux_audit.py` | *[See script for details]* |

---

### Game Development

| Property | Value |
| -------- | ----- |
| **Name** | `game-development` |
| **Location** | `skills/game-development/` |
| **Type** | Standalone |

**Description:** Game development orchestrator. Routes to platform-specific skills based on project needs.

---

### Geo Fundamentals

| Property | Value |
| -------- | ----- |
| **Name** | `geo-fundamentals` |
| **Location** | `skills/geo-fundamentals/` |
| **Type** | Standalone |

**Description:** Generative Engine Optimization for AI search engines (ChatGPT, Claude, Perplexity).

**Scripts:**

| Script | Purpose |
| ------ | ------- |
| `scripts/geo_checker.py` | *[See script for details]* |

---

### I18N Localization

| Property | Value |
| -------- | ----- |
| **Name** | `i18n-localization` |
| **Location** | `skills/i18n-localization/` |
| **Type** | Standalone |

**Description:** Internationalization and localization patterns. Detecting hardcoded strings, managing translations, locale files, RTL support.

**Scripts:**

| Script | Purpose |
| ------ | ------- |
| `scripts/i18n_checker.py` | *[See script for details]* |

---

### Intelligent Routing

| Property | Value |
| -------- | ----- |
| **Name** | `intelligent-routing` |
| **Location** | `skills/intelligent-routing/` |
| **Type** | Standalone |

**Description:** Automatic agent selection, intelligent task routing, and platform-adaptive orchestration. Analyzes user requests and automatically selects the best specialist agent(s). Detects the runtime platform (Claude Code, Gemini, Opencode) and proactively recommends enabling platform-specific features like Agent Teams and Plugins.

---

### Lint And Validate

| Property | Value |
| -------- | ----- |
| **Name** | `lint-and-validate` |
| **Location** | `skills/lint-and-validate/` |
| **Type** | Standalone |

**Description:** Automatic quality control, linting, and static analysis procedures. Use after every code modification to ensure syntax correctness and project standards. Triggers onKeywords: lint, format, check, validate, types, static analysis.

**Scripts:**

| Script | Purpose |
| ------ | ------- |
| `scripts/lint_runner.py` | *[See script for details]* |
| `scripts/type_coverage.py` | *[See script for details]* |

---

### Mcp Builder

| Property | Value |
| -------- | ----- |
| **Name** | `mcp-builder` |
| **Location** | `skills/mcp-builder/` |
| **Type** | Standalone |

**Description:** MCP (Model Context Protocol) server building principles. Tool design, resource patterns, best practices.

---

### Mobile Design

| Property | Value |
| -------- | ----- |
| **Name** | `mobile-design` |
| **Location** | `skills/mobile-design/` |
| **Type** | Standalone |

**Description:** Mobile-first design thinking and decision-making for iOS and Android apps. Touch interaction, performance patterns, platform conventions. Teaches principles, not fixed values. Use when building React Native, Flutter, or native mobile apps.

**Scripts:**

| Script | Purpose |
| ------ | ------- |
| `scripts/mobile_audit.py` | *[See script for details]* |

---

### Nextjs Best Practices

| Property | Value |
| -------- | ----- |
| **Name** | `nextjs-best-practices` |
| **Location** | `skills/nextjs-best-practices/` |
| **Type** | Standalone |

**Description:** Next.js App Router principles. Server Components, data fetching, routing patterns.

---

### Nodejs Best Practices

| Property | Value |
| -------- | ----- |
| **Name** | `nodejs-best-practices` |
| **Location** | `skills/nodejs-best-practices/` |
| **Type** | Standalone |

**Description:** Node.js development principles and decision-making. Framework selection, async patterns, security, and architecture. Teaches thinking, not copying.

---

### Notebooklm Rag

| Property | Value |
| -------- | ----- |
| **Name** | `notebooklm-rag` |
| **Location** | `skills/notebooklm-rag/` |
| **Type** | Standalone |

**Description:** "Deep RAG layer powered by Google NotebookLM + Gemini. The agent autonomously manages notebooks via MCP tools — authentication, library management, querying, follow-ups, and caching. Opt-in for users with a Google account. Default RAG is qdrant-memory. Triggers on: '@notebooklm', 'research my docs', 'deep search', 'query my notebook', 'check my notebooks'."

**Scripts:**

| Script | Purpose |
| ------ | ------- |
| `scripts/ask_question.py` | *[See script for details]* |
| `scripts/auth_manager.py` | *[See script for details]* |
| `scripts/browser_utils.py` | *[See script for details]* |
| `scripts/cleanup_manager.py` | *[See script for details]* |
| `scripts/config.py` | *[See script for details]* |
| `scripts/notebook_manager.py` | *[See script for details]* |
| `scripts/run.py` | *[See script for details]* |
| `scripts/setup_environment.py` | *[See script for details]* |

---

### Parallel Agents

| Property | Value |
| -------- | ----- |
| **Name** | `parallel-agents` |
| **Location** | `skills/parallel-agents/` |
| **Type** | Standalone |

**Description:** Platform-adaptive multi-agent orchestration. Uses Claude Code Agent Teams when available, subagents as fallback, and sequential persona switching on other platforms. Use when multiple independent tasks can run with different domain expertise or when comprehensive analysis requires multiple perspectives.

---

### Performance Profiling

| Property | Value |
| -------- | ----- |
| **Name** | `performance-profiling` |
| **Location** | `skills/performance-profiling/` |
| **Type** | Standalone |

**Description:** Performance profiling principles. Measurement, analysis, and optimization techniques.

**Scripts:**

| Script | Purpose |
| ------ | ------- |
| `scripts/lighthouse_audit.py` | *[See script for details]* |

---

### Plan Writing

| Property | Value |
| -------- | ----- |
| **Name** | `plan-writing` |
| **Location** | `skills/plan-writing/` |
| **Type** | Standalone |

**Description:** Structured task planning with clear breakdowns, dependencies, and verification criteria. Use when implementing features, refactoring, or any multi-step work.

---

### Plugin Discovery

| Property | Value |
| -------- | ----- |
| **Name** | `plugin-discovery` |
| **Location** | `skills/plugin-discovery/` |
| **Type** | Standalone |

**Description:** Platform-adaptive plugin and extension auto-discovery. Detects the runtime environment (Claude Code, Gemini, Opencode, Kiro) and recommends or installs relevant plugins, extensions, MCP servers, and marketplace integrations. Use when setting up a project, onboarding, or when the user asks about available tools/plugins.

**Scripts:**

| Script | Purpose |
| ------ | ------- |
| `scripts/platform_setup.py` | *[See script for details]* |

---

### Powershell Windows

| Property | Value |
| -------- | ----- |
| **Name** | `powershell-windows` |
| **Location** | `skills/powershell-windows/` |
| **Type** | Standalone |

**Description:** PowerShell Windows patterns. Critical pitfalls, operator syntax, error handling.

---

### Python Patterns

| Property | Value |
| -------- | ----- |
| **Name** | `python-patterns` |
| **Location** | `skills/python-patterns/` |
| **Type** | Standalone |

**Description:** Python development principles and decision-making. Framework selection, async patterns, type hints, project structure. Teaches thinking, not copying.

---

### React Patterns

| Property | Value |
| -------- | ----- |
| **Name** | `react-patterns` |
| **Location** | `skills/react-patterns/` |
| **Type** | Standalone |

**Description:** Modern React patterns and principles. Hooks, composition, performance, TypeScript best practices.

---

### React:Components

| Property | Value |
| -------- | ----- |
| **Name** | `react:components` |
| **Location** | `skills/react-components/` |
| **Type** | Standalone |

**Description:** Converts Stitch designs into modular Vite and React components using system-level networking and AST-based validation.

---

### Red Team Tactics

| Property | Value |
| -------- | ----- |
| **Name** | `red-team-tactics` |
| **Location** | `skills/red-team-tactics/` |
| **Type** | Standalone |

**Description:** Red team tactics principles based on MITRE ATT&CK. Attack phases, detection evasion, reporting.

---

### Self Update

| Property | Value |
| -------- | ----- |
| **Name** | `self-update` |
| **Location** | `skills/self-update/` |
| **Type** | Standalone |

**Description:** Update the AGI Agent Kit to the latest version from NPM

**Scripts:**

| Script | Purpose |
| ------ | ------- |
| `scripts/update_kit.py` | *[See script for details]* |

---

### Seo Fundamentals

| Property | Value |
| -------- | ----- |
| **Name** | `seo-fundamentals` |
| **Location** | `skills/seo-fundamentals/` |
| **Type** | Standalone |

**Description:** SEO fundamentals, E-E-A-T, Core Web Vitals, and Google algorithm principles.

**Scripts:**

| Script | Purpose |
| ------ | ------- |
| `scripts/seo_checker.py` | *[See script for details]* |

---

### Server Management

| Property | Value |
| -------- | ----- |
| **Name** | `server-management` |
| **Location** | `skills/server-management/` |
| **Type** | Standalone |

**Description:** Server management principles and decision-making. Process management, monitoring strategy, and scaling decisions. Teaches thinking, not commands.

---

### Stitch Loop

| Property | Value |
| -------- | ----- |
| **Name** | `stitch-loop` |
| **Location** | `skills/stitch-loop/` |
| **Type** | Standalone |

**Description:** Teaches agents to iteratively build websites using Stitch with an autonomous baton-passing loop pattern

---

### Systematic Debugging

| Property | Value |
| -------- | ----- |
| **Name** | `systematic-debugging` |
| **Location** | `skills/systematic-debugging/` |
| **Type** | Standalone |

**Description:** 4-phase root cause debugging process. Use for ANY technical issue — test failures, bugs, unexpected behavior, performance problems. ALWAYS find root cause before attempting fixes.

---

### Tailwind Patterns

| Property | Value |
| -------- | ----- |
| **Name** | `tailwind-patterns` |
| **Location** | `skills/tailwind-patterns/` |
| **Type** | Standalone |

**Description:** Tailwind CSS v4 principles. CSS-first configuration, container queries, modern patterns, design token architecture.

---

### Tdd Workflow

| Property | Value |
| -------- | ----- |
| **Name** | `tdd-workflow` |
| **Location** | `skills/tdd-workflow/` |
| **Type** | Standalone |

**Description:** Test-Driven Development workflow principles. RED-GREEN-REFACTOR cycle.

---

### Test Driven Development

| Property | Value |
| -------- | ----- |
| **Name** | `test-driven-development` |
| **Location** | `skills/test-driven-development/` |
| **Type** | Standalone |

**Description:** RED-GREEN-REFACTOR enforcement. MANDATORY for new features, bug fixes, and behavior changes. Write the test first, watch it fail, then implement.

---

### Testing Patterns

| Property | Value |
| -------- | ----- |
| **Name** | `testing-patterns` |
| **Location** | `skills/testing-patterns/` |
| **Type** | Standalone |

**Description:** Testing patterns and principles. Unit, integration, mocking strategies.

**Scripts:**

| Script | Purpose |
| ------ | ------- |
| `scripts/test_runner.py` | *[See script for details]* |

---

### Verification Before Completion

| Property | Value |
| -------- | ----- |
| **Name** | `verification-before-completion` |
| **Location** | `skills/verification-before-completion/` |
| **Type** | Standalone |

**Description:** Universal verification gate. MANDATORY before any completion claim, success assertion, commit, or PR. Evidence before claims, always.

---

### Vulnerability Scanner

| Property | Value |
| -------- | ----- |
| **Name** | `vulnerability-scanner` |
| **Location** | `skills/vulnerability-scanner/` |
| **Type** | Standalone |

**Description:** Advanced vulnerability analysis principles. OWASP 2025, Supply Chain Security, attack surface mapping, risk prioritization.

**Scripts:**

| Script | Purpose |
| ------ | ------- |
| `scripts/security_scan.py` | *[See script for details]* |

---

### Webapp Testing

| Property | Value |
| -------- | ----- |
| **Name** | `webapp-testing` |
| **Location** | `skills/webapp-testing/` |
| **Type** | Standalone |

**Description:** Web application testing principles. E2E, Playwright, deep audit strategies.

**Scripts:**

| Script | Purpose |
| ------ | ------- |
| `scripts/playwright_runner.py` | *[See script for details]* |

---
## Using Skills

Skills are automatically triggered based on the user's request matching the skill description. You can also explicitly invoke a skill:

```
"Use the <skill-name> skill to <task>"
```

---

## Creating New Skills

```bash
# Initialize a new skill
python skill-creator/scripts/init_skill.py my-new-skill --path skills/

# Package the skill
python skill-creator/scripts/package_skill.py skills/my-new-skill
```

For detailed guidance, see: `skill-creator/SKILL_skillcreator.md`

---

## Maintenance

### Updating This Catalog

**IMPORTANT:** This catalog must be updated whenever skills are created, modified, or deleted.

```bash
python skill-creator/scripts/update_catalog.py --skills-dir skills/
```

---

*This catalog is part of the [3-Layer Architecture](../AGENTS.md) for reliable AI agent operations.*
