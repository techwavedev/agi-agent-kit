---
name: systematic-debugging
description: 4-phase root cause debugging process. Use for ANY technical issue — test failures, bugs, unexpected behavior, performance problems. ALWAYS find root cause before attempting fixes.
version: 1.0.0
---

# Systematic Debugging

> Adapted from obra/superpowers — integrated with agi `debugger` agent.

## Overview

Random fixes waste time and create new bugs. Quick patches mask underlying issues.

**Core principle:** ALWAYS find root cause before attempting fixes. Symptom fixes are failure.

---

## The Iron Law

```
NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST
```

If you haven't completed Phase 1, you cannot propose fixes.

---

## When to Use

Use for **ANY** technical issue:

- Test failures
- Bugs in production
- Unexpected behavior
- Performance problems
- Build failures
- Integration issues

**Use ESPECIALLY when:**

- Under time pressure (emergencies make guessing tempting)
- "Just one quick fix" seems obvious
- You've already tried multiple fixes
- Previous fix didn't work

**Don't skip when:**

- Issue seems simple (simple bugs have root causes too)
- You're in a hurry (systematic is faster than thrashing)

---

## The Four Phases

You MUST complete each phase before proceeding to the next.

### Phase 1: Root Cause Investigation

**BEFORE attempting ANY fix:**

1. **Read Error Messages Carefully**
   - Don't skip past errors or warnings
   - Read stack traces completely
   - Note line numbers, file paths, error codes

2. **Reproduce Consistently**
   - Can you trigger it reliably?
   - What are the exact steps?
   - If not reproducible → gather more data, don't guess

3. **Check Recent Changes**
   - `git diff`, recent commits
   - New dependencies, config changes
   - Environmental differences

4. **Gather Evidence in Multi-Component Systems**

   When system has multiple components:

   ```
   For EACH component boundary:
     - Log what data enters component
     - Log what data exits component
     - Verify environment/config propagation
     - Check state at each layer

   Run once → analyze evidence → identify failing component
   ```

5. **Trace Data Flow**
   - Where does the bad value originate?
   - What called this with the bad value?
   - Keep tracing up until you find the source
   - Fix at source, not at symptom

### Phase 2: Pattern Analysis

1. **Find Working Examples**
   - Locate similar working code in the same codebase
   - What works that's similar to what's broken?

2. **Compare Against References**
   - Read reference implementation COMPLETELY (don't skim)
   - Understand the pattern fully before applying

3. **Identify Differences**
   - What's different between working and broken?
   - List every difference, however small
   - Don't assume "that can't matter"

4. **Understand Dependencies**
   - What other components does this need?
   - What settings, config, environment?

### Phase 3: Hypothesis and Testing

1. **Form Single Hypothesis**
   - State clearly: "I think X is the root cause because Y"
   - Be specific, not vague

2. **Test Minimally**
   - Make the SMALLEST possible change to test hypothesis
   - One variable at a time
   - Don't fix multiple things at once

3. **Verify**
   - Did it work? Yes → Phase 4
   - Didn't work? Form NEW hypothesis
   - DON'T add more fixes on top

### Phase 4: Implementation

1. **Create Failing Test Case**
   - Simplest possible reproduction
   - Use `test-driven-development` skill
   - MUST exist before fixing

2. **Implement Single Fix**
   - Address the root cause identified
   - ONE change at a time
   - No "while I'm here" improvements

3. **Verify Fix**
   - Test passes now?
   - No other tests broken?
   - Issue actually resolved?

4. **If 3+ Fixes Failed: Question Architecture**

   **Pattern indicating architectural problem:**
   - Each fix reveals new coupling in different place
   - Fixes require "massive refactoring"
   - Each fix creates new symptoms elsewhere

   **STOP and discuss with the user before more fix attempts.**

---

## Quick Reference

| Phase                 | Key Activities                                         | Success Criteria            |
| --------------------- | ------------------------------------------------------ | --------------------------- |
| **1. Root Cause**     | Read errors, reproduce, check changes, gather evidence | Understand WHAT and WHY     |
| **2. Pattern**        | Find working examples, compare                         | Identify differences        |
| **3. Hypothesis**     | Form theory, test minimally                            | Confirmed or new hypothesis |
| **4. Implementation** | Create test, fix, verify                               | Bug resolved, tests pass    |

---

## Red Flags — STOP and Return to Phase 1

If you catch yourself thinking:

- "Quick fix for now, investigate later"
- "Just try changing X and see if it works"
- "Add multiple changes, run tests"
- "It's probably X, let me fix that"
- "I don't fully understand but this might work"
- Proposing solutions before tracing data flow
- "One more fix attempt" (when already tried 2+)

---

## Common Rationalizations

| Excuse                                       | Reality                                                             |
| -------------------------------------------- | ------------------------------------------------------------------- |
| "Issue is simple, don't need process"        | Simple issues have root causes too. Process is fast for simple bugs |
| "Emergency, no time for process"             | Systematic debugging is FASTER than guess-and-check thrashing       |
| "Just try this first, then investigate"      | First fix sets the pattern. Do it right from the start              |
| "I'll write test after confirming fix works" | Untested fixes don't stick. Test first proves it                    |
| "Multiple fixes at once saves time"          | Can't isolate what worked. Causes new bugs                          |
| "I see the problem, let me fix it"           | Seeing symptoms ≠ understanding root cause                          |

---

## Real-World Impact

| Approach     | Time to Fix | First-Time Fix Rate | New Bugs  |
| ------------ | ----------- | ------------------- | --------- |
| Systematic   | 15-30 min   | ~95%                | Near zero |
| Random fixes | 2-3 hours   | ~40%                | Common    |

---

## Integration

| Skill/Agent                      | Relationship                                                      |
| -------------------------------- | ----------------------------------------------------------------- |
| `debugger` agent                 | Domain expertise for investigation; use this skill as its process |
| `test-driven-development`        | Phase 4: creating failing test case                               |
| `verification-before-completion` | Verify fix before claiming it works                               |
| `executing-plans`                | When debugging blocks plan execution                              |
