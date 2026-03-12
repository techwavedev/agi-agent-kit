---
name: bats-testing-patterns
description: "Master Bash Automated Testing System (Bats) for comprehensive shell script testing. Use when writing tests for shell scripts, CI/CD pipelines, or requiring test-driven development of shell utilities."
risk: unknown
source: community
date_added: "2026-02-27"
---

# Bats Testing Patterns

Comprehensive guidance for writing comprehensive unit tests for shell scripts using Bats (Bash Automated Testing System), including test patterns, fixtures, and best practices for production-grade shell testing.

## Use this skill when

- Writing unit tests for shell scripts
- Implementing TDD for scripts
- Setting up automated testing in CI/CD pipelines
- Testing edge cases and error conditions
- Validating behavior across shell environments

## Do not use this skill when

- The project does not use shell scripts
- You need integration tests beyond shell behavior
- The goal is only linting or formatting

## Instructions

- Confirm shell dialects and supported environments.
- Set up a test structure with helpers and fixtures.
- Write tests for exit codes, output, and side effects.
- Add setup/teardown and run tests in CI.
- If detailed examples are required, open `resources/implementation-playbook.md`.

## Resources

- `resources/implementation-playbook.md` for detailed patterns and examples.

---

<!-- AGI-INTEGRATION-START -->

## AGI Framework Integration

> **Adapted for [@techwavedev/agi-agent-kit](https://www.npmjs.com/package/@techwavedev/agi-agent-kit)**
> Original source: [antigravity-awesome-skills](https://github.com/sickn33/antigravity-awesome-skills)

### Memory-First Protocol

Retrieve prior test strategies, known flaky tests, and coverage gaps. Cache test infrastructure setup to avoid re-configuring test environments.

```bash
# Check for prior testing/QA context before starting
python3 execution/memory_manager.py auto --query "test patterns and coverage strategies for Bats Testing Patterns"
```

### Storing Results

After completing work, store testing/QA decisions for future sessions:

```bash
python3 execution/memory_manager.py store \
  --content "Testing strategy: integration tests hit real DB (no mocks), 85% line coverage, mutation testing on critical paths" \
  --type technical --project <project> \
  --tags bats-testing-patterns testing
```

### Multi-Agent Collaboration

Share test results and coverage reports with code review agents so they can verify adequate coverage on changed code.

```bash
python3 execution/cross_agent_context.py store \
  --agent "<your-agent>" \
  --action "QA complete — test suite expanded with 12 new integration tests, all passing" \
  --project <project>
```

### TDD Enforcement

This skill integrates with the framework's iron-law RED-GREEN-REFACTOR cycle. No production code without a failing test first.

### Agent Team: QA

Dispatch `qa_team` to generate tests and verify they pass before marking implementation complete.

<!-- AGI-INTEGRATION-END -->
