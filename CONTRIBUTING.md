# Contributing to Agi Agent Kit

Thank you for your interest in contributing to `@techwavedev/agi-agent-kit`! This framework is designed to bring deterministic reliability to AI agents, and your contributions help make that mission a reality.

## ⚠️ Contribution Rules

1. **All contributions go through Pull Requests** — direct pushes to `main` are blocked.
2. **Every PR requires maintainer approval** before merging.
3. **Discuss first** — open an [Issue](https://github.com/techwavedev/agi-agent-kit/issues) or [Discussion](https://github.com/techwavedev/agi-agent-kit/discussions) before working on significant changes.
4. **Fork-based workflow only** — contributors work on their own fork and submit PRs from there.

## How to Contribute

### Step 1: Fork & Clone

```bash
# Fork the repo on GitHub, then:
git clone https://github.com/YOUR_USERNAME/agi-agent-kit.git
cd agi-agent-kit
git remote add upstream https://github.com/techwavedev/agi-agent-kit.git
```

### Step 2: Create a Feature Branch

```bash
git checkout -b feature/amazing-skill
```

### Step 3: Make Your Changes

Follow the core architecture:

1. **Directives (Intent)**: Markdown SOPs in `directives/`.
2. **Orchestration (Agent)**: The LLM reads directives and decides actions.
3. **Execution (Code)**: Deterministic Python scripts in `execution/`.

**Golden Rule:** Push complexity into deterministic scripts. Agents act as routers, not code generators.

### Step 4: Submit a Pull Request

```bash
git push origin feature/amazing-skill
```

Then open a PR on GitHub from your fork → `techwavedev/agi-agent-kit:main`.

## What We Accept

### Bug Reports

- Search [existing issues](https://github.com/techwavedev/agi-agent-kit/issues) first.
- Use the **Bug Report** template when creating a new issue.
- Include steps to reproduce, expected vs. actual behavior, and environment details.

### New Skills

Skills live in `templates/base/skills/`. To add a skill:

1. Run `python3 skill-creator/scripts/init_skill.py <skill-name>`.
2. Ensure it includes a `SKILL.md` and a `scripts/` directory.
3. Scripts must be deterministic and error-resilient.

### Feature Requests

- Use the **Feature Request** template.
- Explain the problem it solves and any alternatives considered.

## Code Standards

- **Python:** Follow PEP 8.
- **Markdown:** GitHub Flavored Markdown.
- **Directives:** Follow `templates/base/directives/template.md`.
- **Testing:** Run `python3 execution/system_checkup.py` before submitting.
- **Changelog:** Update `CHANGELOG.md` with your changes.
- **Catalog:** Update `skills/SKILLS_CATALOG.md` if you added/modified a skill.

## 🛡️ Release Governance Protocol (MANDATORY)

Before submitting any Pull Request or preparing a release, you MUST run the Release Gate:

```bash
python3 .agent/scripts/release_gate.py
```

This automated gate validates:

1. Documentation updates (README/CHANGELOG)
2. Security checks (No leaked secrets)
3. Code Syntax (Python/JS integrity)
4. Version Consistency (package.json matches CHANGELOG)

**PRs failing these checks will be automatically rejected.**

## What Will Get Your PR Rejected

- PRs without a linked issue or prior discussion (for significant changes)
- Code that doesn't follow the project's architecture
- Missing documentation or changelog updates
- Spam, AI-generated boilerplate, or trivial cosmetic-only changes

## License

By contributing, you agree that your contributions will be licensed under the project's [Apache-2.0 License](./LICENSE).
