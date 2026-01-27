# Contributing to Agi Agent Kit

Thank you for your interest in contributing to `@techwavedev/agi-agent-kit`! This framework is designed to bring deterministic reliability to AI agents, and your contributions help make that mission a reality.

## Core Philosophy

Before contributing, please understand the **3-Layer Architecture**:

1.  **Directives (Intent)**: Markdown SOPs in `directives/`.
2.  **Orchestration (Agent)**: The LLM reads directives and decides actions.
3.  **Execution (Code)**: Deterministic Python scripts in `execution/`.

**Golden Rule:** We push complexity into deterministic scripts. Agents act as routers, not code generators for business logic.

## How to Contribute

### 1. Reporting Bugs

- Ensure the bug was not already reported by searching on GitHub under [Issues](https://github.com/techwavedev/agi-agent-kit/issues).
- Use a clear and descriptive title.
- Describe the exact steps to reproduce the issue.

### 2. Proposing Changes

- **Discuss First:** Open an issue to discuss significant changes before writing code.
- **Fork & Branch:** Fork the repository and create a branch for your feature (`git checkout -b feature/amazing-skill`).

### 3. Adding New Skills

Skills live in `templates/base/skills/`. To add a skill:

1.  Run `python3 skill-creator/scripts/init_skill.py <skill-name>`.
2.  Ensure it includes a `SKILL.md` and a `scripts/` directory.
3.  Scripts must be deterministic and error-resilient.

### 4. Code Style

- **Python:** Follow PEP 8.
- **Markdown:** Use standard GitHub Flavored Markdown.
- **Directives:** Follow the format in `templates/base/directives/template.md`.

### 5. Testing

- Run system checkups before submitting:
  ```bash
  python3 execution/system_checkup.py
  ```
- Ensure all new scripts have basic error handling.

## Pull Request Process

1.  Update the `CHANGELOG.md` with details of changes.
2.  Update `skills/SKILLS_CATALOG.md` if you added or modified a skill.
3.  Ensure your code passes the "Clean Code" standards (Tier 0 in `AGENTS.md`).
4.  Submit your PR to the `main` branch.

## License

By contributing, you agree that your contributions will be licensed under the project's [Apache-2.0 License](./LICENSE).
