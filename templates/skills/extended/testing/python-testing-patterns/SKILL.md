---
name: python-testing-patterns
description: "Implement comprehensive testing strategies with pytest, fixtures, mocking, and test-driven development. Use when writing Python tests, setting up test suites, or implementing testing best practices."
risk: unknown
source: community
date_added: "2026-02-27"
---

# Python Testing Patterns

Comprehensive guide to implementing robust testing strategies in Python using pytest, fixtures, mocking, parameterization, and test-driven development practices.

## Use this skill when

- Writing unit tests for Python code
- Setting up test suites and test infrastructure
- Implementing test-driven development (TDD)
- Creating integration tests for APIs and services
- Mocking external dependencies and services
- Testing async code and concurrent operations
- Setting up continuous testing in CI/CD
- Implementing property-based testing
- Testing database operations
- Debugging failing tests

## Do not use this skill when

- The task is unrelated to python testing patterns
- You need a different domain or tool outside this scope

## Instructions

- Clarify goals, constraints, and required inputs.
- Apply relevant best practices and validate outcomes.
- Provide actionable steps and verification.
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
python3 execution/memory_manager.py auto --query "test patterns and coverage strategies for Python Testing Patterns"
```

### Storing Results

After completing work, store testing/QA decisions for future sessions:

```bash
python3 execution/memory_manager.py store \
  --content "Testing strategy: integration tests hit real DB (no mocks), 85% line coverage, mutation testing on critical paths" \
  --type technical --project <project> \
  --tags python-testing-patterns testing
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
