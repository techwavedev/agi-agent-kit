---
name: github-issue-creator
description: "Convert raw notes, error logs, voice dictation, or screenshots into crisp GitHub-flavored markdown issue reports. Use when the user pastes bug info, error messages, or informal descriptions and wan..."
risk: unknown
source: community
date_added: "2026-02-27"
---

# GitHub Issue Creator

Transform messy input (error logs, voice notes, screenshots) into clean, actionable GitHub issues.

## Output Template

```markdown
## Summary
[One-line description of the issue]

## Environment
- **Product/Service**: 
- **Region/Version**: 
- **Browser/OS**: (if relevant)

## Reproduction Steps
1. [Step]
2. [Step]
3. [Step]

## Expected Behavior
[What should happen]

## Actual Behavior
[What actually happens]

## Error Details
```
[Error message/code if applicable]
```

## Visual Evidence
[Reference to attached screenshots/GIFs]

## Impact
[Severity: Critical/High/Medium/Low + brief explanation]

## Additional Context
[Any other relevant details]
```

## Output Location

**Create issues as markdown files** in `/issues/` directory at the repo root. Use naming convention: `YYYY-MM-DD-short-description.md`

## Guidelines

**Be crisp**: No fluff. Every word should add value.

**Extract structure from chaos**: Voice dictation and raw notes often contain the facts buried in casual language. Pull them out.

**Infer missing context**: If user mentions "same project" or "the dashboard", use context from conversation or memory to fill in specifics.

**Placeholder sensitive data**: Use `[PROJECT_NAME]`, `[USER_ID]`, etc. for anything that might be sensitive.

**Match severity to impact**:
- Critical: Service down, data loss, security issue
- High: Major feature broken, no workaround
- Medium: Feature impaired, workaround exists
- Low: Minor inconvenience, cosmetic

**Image/GIF handling**: Reference attachments inline. Format: `!Description`

## Examples

**Input (voice dictation)**:
> so I was trying to deploy the agent and it just failed silently no error nothing the workflow ran but then poof gone from the list had to refresh and try again three times

**Output**:
```markdown
## Summary
Agent deployment fails silently - no error displayed, agent disappears from list

## Environment
- **Product/Service**: Azure AI Foundry
- **Region/Version**: westus2

## Reproduction Steps
1. Navigate to agent deployment
2. Configure and deploy agent
3. Observe workflow completes
4. Check agent list

## Expected Behavior
Agent appears in list with deployment status, errors shown if deployment fails

## Actual Behavior
Agent disappears from list. No error message. Requires page refresh and retry.

## Impact
**High** - Blocks agent deployment workflow, no feedback on failure cause

## Additional Context
Required 3 retry attempts before successful deployment
```

---

**Input (error paste)**:
> Error: PERMISSION_DENIED when publishing to Teams channel. Code: 403. Was working yesterday.

**Output**:
```markdown
## Summary
403 PERMISSION_DENIED error when publishing to Teams channel

## Environment
- **Product/Service**: Copilot Studio → Teams integration
- **Region/Version**: [REGION]

## Reproduction Steps
1. Configure agent for Teams channel
2. Attempt to publish

## Expected Behavior
Agent publishes successfully to Teams channel

## Actual Behavior
Returns `PERMISSION_DENIED` with code 403

## Error Details
```
Error: PERMISSION_DENIED
Code: 403
```

## Impact
**High** - Blocks Teams integration, regression from previous working state

## Additional Context
Was working yesterday - possible permission/config change or service regression
```

## When to Use
This skill is applicable to execute the workflow or actions described in the overview.

---

<!-- AGI-INTEGRATION-START -->

## AGI Framework Integration

> **Adapted for [@techwavedev/agi-agent-kit](https://www.npmjs.com/package/@techwavedev/agi-agent-kit)**
> Original source: [antigravity-awesome-skills](https://github.com/sickn33/antigravity-awesome-skills)

### Memory-First Protocol

Cache workflow configurations and automation patterns. Retrieve prior pipeline designs to avoid re-building similar flows from scratch.

```bash
# Check for prior workflow/automation context before starting
python3 execution/memory_manager.py auto --query "automation patterns and workflow configurations for Github Issue Creator"
```

### Storing Results

After completing work, store workflow/automation decisions for future sessions:

```bash
python3 execution/memory_manager.py store \
  --content "Workflow: automated data pipeline with retry logic, dead-letter queue, and Slack alerts on failure" \
  --type technical --project <project> \
  --tags github-issue-creator workflow
```

### Multi-Agent Collaboration

Share workflow state with other agents so they can trigger, monitor, or extend the automation.

```bash
python3 execution/cross_agent_context.py store \
  --agent "<your-agent>" \
  --action "Workflow automation deployed — pipeline processing 1000+ events/day with 99.9% success rate" \
  --project <project>
```

### Playbook Engine

Combine this skill with others using the Playbook Engine (`execution/workflow_engine.py`) for guided multi-step automation with progress tracking.

<!-- AGI-INTEGRATION-END -->
