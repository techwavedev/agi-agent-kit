# Sub-Agent Directive: test-generator

## Identity

| Field      | Value          |
|------------|----------------|
| Sub-agent  | `test-generator` |
| Team       | `qa_team`      |
| Invoked by | Team orchestrator |

---

## Goal

Analyse changed source files and generate or update test cases that exercise their functionality. Tests must use the project's existing testing conventions and cover both happy paths and edge cases described in the task spec.

---

## Inputs

| Name            | Type   | Required | Description |
|-----------------|--------|----------|-------------|
| `changed_files` | list   | ✅       | Source files to generate tests for |
| `task_spec`     | string | ✅       | Original specification — describes expected behaviour |
| `test_runner`   | string | ❌       | `pytest` / `jest` / `node` (auto-detected if omitted) |
| `test_dir`      | string | ❌       | Output directory for tests (default: auto-detect) |

---

## Execution

1. **Detect test framework** — check for `pytest.ini`, `jest.config.*`, `package.json#scripts.test`

2. **Detect existing test conventions** — look at 1-2 existing test files for:
   - Naming pattern (`test_*.py`, `*.test.ts`, etc.)
   - Import style
   - Assertion library

3. **For each changed file**, generate tests covering:
   - ✅ All public functions/CLI arguments
   - ✅ Happy path (valid inputs → expected outputs)
   - ✅ Edge cases mentioned in spec
   - ✅ Error paths (invalid inputs, missing files, bad JSON)
   - ✅ Exit codes for CLI scripts

4. **Write test files** following the detected naming convention

5. **Output structured result:**
   ```bash
   python3 execution/memory_manager.py store \
     --content "test-generator: created tests for <files>" \
     --type decision \
     --tags qa-team test-generator
   ```

---

## Outputs

```json
{
  "sub_agent": "test-generator",
  "status": "pass|fail",
  "test_files": ["tests/test_dispatch_agent_team.py"],
  "test_count": 7,
  "framework": "pytest",
  "notes": ""
}
```

---

## Edge Cases

- **No test framework detected:** Default to Python `unittest` with `test_<module_name>.py`
- **File is a markdown/config:** Skip — only generate tests for executable code
- **Spec doesn't describe edge cases:** Generate at minimum: valid input, invalid input, empty input
- **Test file already exists:** Extend it — do NOT overwrite existing tests

---

## Quality Rules

- One `describe`/`class` per source file being tested
- Test names must describe the scenario, not the implementation: `test_returns_error_on_missing_team` not `test_line_47`
- Never mock real filesystem operations in tests for scripts that are supposed to read files
- Exit code tests matter: `assert result.returncode == 2` not just `assert result.returncode != 0`
