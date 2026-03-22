---
name: e2e-testing-patterns
description: "Master end-to-end testing with Playwright and Cypress to build reliable test suites that catch bugs, improve confidence, and enable fast deployment. Use when implementing E2E tests, debugging flaky..."
risk: unknown
source: community
date_added: "2026-02-27"
---

# E2E Testing Patterns

Build reliable, fast, and maintainable end-to-end test suites that provide confidence to ship code quickly and catch regressions before users do.

## Use this skill when

- Implementing end-to-end test automation
- Debugging flaky or unreliable tests
- Testing critical user workflows
- Setting up CI/CD test pipelines
- Testing across multiple browsers
- Validating accessibility requirements
- Testing responsive designs
- Establishing E2E testing standards

## Do not use this skill when

- You only need unit or integration tests
- The environment cannot support stable UI automation
- You cannot provision safe test accounts or data

## Instructions

1. Identify critical user journeys and success criteria.
2. Build stable selectors and test data strategies.
3. Implement tests with retries, tracing, and isolation.
4. Run in CI with parallelization and artifact capture.

## Safety

- Avoid running destructive tests against production.
- Use dedicated test data and scrub sensitive output.

## Resources

- `resources/implementation-playbook.md` for detailed E2E patterns and templates.

---

<!-- AGI-INTEGRATION-START -->

## AGI Framework Integration

> **Adapted for [@techwavedev/agi-agent-kit](https://www.npmjs.com/package/@techwavedev/agi-agent-kit)**
> Original source: [antigravity-awesome-skills](https://github.com/sickn33/antigravity-awesome-skills)

### Memory-First Protocol

Retrieve prior test strategies, known flaky tests, and coverage gaps. Cache test infrastructure setup to avoid re-configuring test environments.

```bash
# Check for prior testing/QA context before starting
python3 execution/memory_manager.py auto --query "test patterns and coverage strategies for E2E Testing Patterns"
```

### Storing Results

After completing work, store testing/QA decisions for future sessions:

```bash
python3 execution/memory_manager.py store \
  --content "Testing strategy: integration tests hit real DB (no mocks), 85% line coverage, mutation testing on critical paths" \
  --type technical --project <project> \
  --tags e2e-testing-patterns testing
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
