---
description: System checkup to verify agents, workflows, skills, and core files.
---

# System Checkup Workflow

This workflow performs a comprehensive health check of the Agi Agent Kit environment.
It verifies:

1. Core file existence (AGENTS.md, GEMINI.md, etc.)
2. Skill structure (SKILL.md, scripts validity)
3. Workflow syntax and structure
4. Execution scripts python syntax
5. Directives validity

## Execution

// turbo

1. Run system checkup script
   Run `python3 execution/system_checkup.py --verbose`

## Verification

- [ ] Check the output for any ❌ ERROR or ⚠️ WARNING messages.
- [ ] If errors are found, investigate the specific file mentioned.
