---
description: Update AGI Agent Kit to the latest version from NPM
---

# Update Workflow

Updates skills, agents, workflows, and other framework components to the latest published version.

## Quick Check

// turbo

1. Check for available updates
   Run `python3 skills/self-update/scripts/update_kit.py --check-only`

## Full Update

2. Run the update (requires confirmation)
   Run `python3 skills/self-update/scripts/update_kit.py`

## Post-Update Verification

// turbo 3. Run system checkup
Run `python3 execution/system_checkup.py --verbose`

## Manual Update (Alternative)

If the script doesn't work, run directly:

```bash
npx @techwavedev/agi-agent-kit@latest init --pack=full
```
