---
name: conductor-manage
description: "Manage track lifecycle: archive, restore, delete, rename, and cleanup"
risk: unknown
source: community
date_added: "2026-02-27"
---

# Track Manager

Manage the complete track lifecycle including archiving, restoring, deleting, renaming, and cleaning up orphaned artifacts.

## Use this skill when

- Archiving, restoring, renaming, or deleting Conductor tracks
- Listing track status or cleaning orphaned artifacts
- Managing the track lifecycle across active, completed, and archived states

## Do not use this skill when

- Conductor is not initialized in the repository
- You lack permission to modify track metadata or files
- The task is unrelated to Conductor track management

## Instructions

- Verify `conductor/` structure and required files before proceeding.
- Determine the operation mode from arguments or interactive prompts.
- Confirm destructive actions (delete/cleanup) before applying.
- Update `tracks.md` and metadata consistently.
- If detailed steps are required, open `resources/implementation-playbook.md`.

## Safety

- Backup track data before delete operations.
- Avoid removing archived tracks without explicit approval.

## Resources

- `resources/implementation-playbook.md` for detailed modes, prompts, and workflows.

---

<!-- AGI-INTEGRATION-START -->

## AGI Framework Integration

> **Adapted for [@techwavedev/agi-agent-kit](https://www.npmjs.com/package/@techwavedev/agi-agent-kit)**
> Original source: [antigravity-awesome-skills](https://github.com/sickn33/antigravity-awesome-skills)

### Memory-First Protocol

Retrieve prior API design decisions, database schema choices, and error handling patterns. Cache API response templates for consistent error formatting.

```bash
# Check for prior backend/API context before starting
python3 execution/memory_manager.py auto --query "API design patterns and architecture decisions for Conductor Manage"
```

### Storing Results

After completing work, store backend/API decisions for future sessions:

```bash
python3 execution/memory_manager.py store \
  --content "API architecture: REST with HATEOAS, JWT auth, rate limiting at 100 req/min per tenant" \
  --type decision --project <project> \
  --tags conductor-manage backend
```

### Multi-Agent Collaboration

Share API contract changes with frontend agents so they update their client code, and with QA agents for test coverage.

```bash
python3 execution/cross_agent_context.py store \
  --agent "<your-agent>" \
  --action "Implemented API endpoints — 5 new routes with OpenAPI spec and integration tests" \
  --project <project>
```

### Agent Team: Code Review

After implementation, dispatch `code_review_team` for two-stage review (spec compliance + code quality) before merging.

<!-- AGI-INTEGRATION-END -->
