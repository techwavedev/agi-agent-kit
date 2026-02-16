---
name: test-driven-development
description: RED-GREEN-REFACTOR enforcement. MANDATORY for new features, bug fixes, and behavior changes. Write the test first, watch it fail, then implement.
version: 1.0.0
---

# Test-Driven Development (TDD)

> Adapted from obra/superpowers — platform-agnostic commands.

## Overview

Write the test first. Watch it fail. Write minimal code to pass.

**Core principle:** If you didn't watch the test fail, you don't know if it tests the right thing.

---

## The Iron Law

```
NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST
```

Write code before the test? **Delete it.** Start over.

**No exceptions:**

- Don't keep it as "reference"
- Don't "adapt" it while writing tests
- Don't look at it
- Delete means delete

---

## When to Use

**Always:**

- New features
- Bug fixes
- Refactoring
- Behavior changes

**Exceptions (ask the user):**

- Throwaway prototypes
- Generated code
- Configuration-only changes

Thinking "skip TDD just this once"? Stop. That's rationalization.

---

## Red-Green-Refactor Cycle

### 🔴 RED — Write Failing Test

Write one minimal test showing what **should** happen.

**Requirements:**

- One behavior per test
- Clear, descriptive name
- Real code (no mocks unless unavoidable)

```
✅ test('rejects empty email with error message')
❌ test('test1')  /  test('validates email and domain and whitespace')
```

### 🔴 Verify RED — Watch It Fail

**MANDATORY. Never skip.**

Run the test. Confirm:

- Test **fails** (not errors — compilation errors are different from test failures)
- Failure message is expected (feature missing, not typos)

**Test passes immediately?** You're testing existing behavior. Fix the test.

### 🟢 GREEN — Minimal Code

Write the **simplest** code to pass the test.

- Don't add features beyond what the test requires
- Don't refactor other code
- Don't "improve" beyond the test
- YAGNI ruthlessly

### 🟢 Verify GREEN — Watch It Pass

**MANDATORY.**

Run the test. Confirm:

- New test passes
- All other tests still pass
- Output pristine (no errors, warnings)

**Test fails?** Fix the code, not the test.

### 🔵 REFACTOR — Clean Up

After green only:

- Remove duplication
- Improve names
- Extract helpers

**Keep tests green during refactoring.** Don't add behavior.

### 🔁 Repeat

Next failing test for next behavior.

---

## Good Tests vs Bad Tests

| Quality          | Good                               | Bad                                                 |
| ---------------- | ---------------------------------- | --------------------------------------------------- |
| **Minimal**      | One thing. "and" in name? Split it | `test('validates email and domain and whitespace')` |
| **Clear**        | Name describes behavior            | `test('test1')`                                     |
| **Real**         | Tests actual code                  | Tests mock behavior                                 |
| **Shows intent** | Demonstrates desired API           | Obscures what code should do                        |

---

## Why Order Matters

| Rationalization                        | Reality                                                                 |
| -------------------------------------- | ----------------------------------------------------------------------- |
| "I'll write tests after to verify"     | Tests written after pass immediately — proves nothing                   |
| "Already manually tested"              | Manual = ad-hoc, no record, can't re-run                                |
| "Deleting X hours of work is wasteful" | Sunk cost fallacy. Unverified code is tech debt                         |
| "TDD is dogmatic"                      | TDD IS pragmatic: finds bugs before commit                              |
| "Tests after achieve same goals"       | Tests-after = "what does this do?" Tests-first = "what should this do?" |

---

## Common Rationalizations

| Excuse                                 | Reality                                                    |
| -------------------------------------- | ---------------------------------------------------------- |
| "Too simple to test"                   | Simple code breaks. Test takes 30 seconds                  |
| "I'll test after"                      | Tests passing immediately prove nothing                    |
| "Keep as reference, write tests first" | You'll adapt it. That's testing after. Delete means delete |
| "Need to explore first"                | Fine. Throw away exploration, start with TDD               |
| "Test hard = skip it"                  | Hard to test = hard to use. Simplify the design            |
| "TDD will slow me down"                | TDD is faster than debugging. Always                       |
| "Existing code has no tests"           | You're improving it. Add tests for what you touch          |

---

## Red Flags — STOP and Start Over

- Code written before test
- Test passes immediately (never saw it fail)
- Can't explain why the test failed
- Rationalizing "just this once"
- "Keep as reference" or "adapt existing code"
- "This is different because..."

**All of these mean: Delete code. Start over with TDD.**

---

## Bug Fix Example

**Bug:** Empty email accepted

**🔴 RED:**

```
test('rejects empty email') → assert result.error == 'Email required'
```

**🔴 Verify RED:**

```
$ run tests → FAIL: expected 'Email required', got undefined ✓
```

**🟢 GREEN:**

```
if not data.email: return error('Email required')
```

**🟢 Verify GREEN:**

```
$ run tests → PASS ✓
```

---

## Verification Checklist

Before marking work complete:

- [ ] Every new function/method has a test
- [ ] Watched each test fail before implementing
- [ ] Each test failed for expected reason
- [ ] Wrote minimal code to pass each test
- [ ] All tests pass
- [ ] Output pristine (no errors, warnings)
- [ ] Tests use real code (mocks only if unavoidable)
- [ ] Edge cases and errors covered

Can't check all boxes? You skipped TDD. Start over.

---

## When Stuck

| Problem                | Solution                                                      |
| ---------------------- | ------------------------------------------------------------- |
| Don't know how to test | Write the wished-for API. Write assertion first. Ask the user |
| Test too complicated   | Design too complicated. Simplify the interface                |
| Must mock everything   | Code too coupled. Use dependency injection                    |
| Test setup is huge     | Extract helpers. Still complex? Simplify the design           |

---

## Integration

| Skill                            | Relationship                               |
| -------------------------------- | ------------------------------------------ |
| `executing-plans`                | TDD cycle used during task implementation  |
| `systematic-debugging`           | Bug found → write failing test → TDD cycle |
| `verification-before-completion` | Gate before claiming tests pass            |
| `plan-writing`                   | Plans include TDD step structure           |
