# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

- **Security**: Removed all references to private infrastructure (EC, Consul) from public templates.
- **Safety**: Added `verify_public_release.py` to prevent accidental publication of private secrets.
- **Menu**: Fixed `init` menu showing internal options.

## [0.1.0] - 2026-01-23

### Initial Release

- Core framework with `webcrawler`, `pdf-reader`, and `qdrant-memory`.
- CLI tool `agi-agent-kit` for scaffolding.
