# Sub-Agent Directive: test-verifier

## Identity

| Field      | Value           |
|------------|-----------------|
| Sub-agent  | `test-verifier` |
| Team       | `qa_team`       |
| Invoked by | Team orchestrator after `test-generator` completes |

---

## Goal

Run the test files produced by `test-generator` and report structured pass/fail results. If tests fail, diagnose whether the issue is a **test bug** (wrong expectation) or a **code bug** (implementation defect), and flag accordingly.

---

## Inputs

| Name          | Type   | Required | Description |
|---------------|--------|----------|-------------|
| `test_files`  | list   | ✅       | Test files to run (from test-generator output) |
| `test_runner` | string | ✅       | `pytest` / `jest` / `node` |
| `changed_files` | list | ✅       | Original source files being tested |

---

## Execution

1. **Run the tests:**
   ```bash
   # Python
   python3 -m pytest <test_files> -v --tb=short 2>&1

   # Node/Jest
   npx jest <test_files> --verbose 2>&1
   ```

2. **Parse results** — extract pass count, fail count, error messages

3. **For each failure, classify:**
   - 🔴 **Code bug** — test expectation is correct, implementation is wrong
   - 🟡 **Test bug** — test expectation is wrong (wrong assumption about API)
   - 🔵 **Environment issue** — missing dependency, wrong Python version, etc.

4. **Output structured result**

5. **Store to memory:**
   ```bash
   python3 execution/memory_manager.py store \
     --content "test-verifier: <passed>/<total> tests passed for <changed_files>" \
     --type decision \
     --tags qa-team test-verifier
   ```

---

## Outputs

```json
{
  "sub_agent": "test-verifier",
  "status": "pass|fail",
  "passed": 6,
  "failed": 1,
  "skipped": 0,
  "total": 7,
  "failures": [
    {
      "test": "test_returns_error_on_missing_team",
      "type": "code_bug",
      "error": "AssertionError: expected exit code 2, got 0",
      "file": "tests/test_dispatch_agent_team.py",
      "line": 47
    }
  ],
  "overall_status": "pass|fail"
}
```

---

## Edge Cases

- **No test files produced:** Return `"status": "blocked"` — escalate to primary agent
- **All failures are environment issues:** Return `"status": "blocked"`, list deps to install
- **Test runner not installed:** Attempt `pip install pytest` or `npm install` once; if fails → blocked
- **Mixed code/test bugs:** Return `"status": "fail"` for code bugs, `"status": "warning"` for test bugs only

---

## Quality Rules

- Do NOT fix the tests or code yourself — classify and report only
- A passing test suite with 0 tests is NOT a pass — verify `total > 0`
- Environment issues must list the exact missing package to unblock
- Code bugs must cite the exact line in the source file that's wrong (not just the test line)
