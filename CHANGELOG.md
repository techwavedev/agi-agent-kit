# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
