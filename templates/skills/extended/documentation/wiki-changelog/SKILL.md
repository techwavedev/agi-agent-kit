---
name: wiki-changelog
description: "Analyzes git commit history and generates structured changelogs categorized by change type. Use when the user asks about recent changes, wants a changelog, or needs to understand what changed in th..."
risk: unknown
source: community
date_added: "2026-02-27"
---

# Wiki Changelog

Generate structured changelogs from git history.

## When to Activate

- User asks "what changed recently", "generate a changelog", "summarize commits"
- User wants to understand recent development activity

## Procedure

1. Examine git log (commits, dates, authors, messages)
2. Group by time period: daily (last 7 days), weekly (older)
3. Classify each commit: Features (🆕), Fixes (🐛), Refactoring (🔄), Docs (📝), Config (🔧), Dependencies (📦), Breaking (⚠️)
4. Generate concise user-facing descriptions using project terminology

## Constraints

- Focus on user-facing changes
- Merge related commits into coherent descriptions
- Use project terminology from README
- Highlight breaking changes prominently with migration notes

## When to Use
This skill is applicable to execute the workflow or actions described in the overview.

---

<!-- AGI-INTEGRATION-START -->

## AGI Framework Integration

> **Adapted for [@techwavedev/agi-agent-kit](https://www.npmjs.com/package/@techwavedev/agi-agent-kit)**
> Original source: [antigravity-awesome-skills](https://github.com/sickn33/antigravity-awesome-skills)

### Memory-First Protocol

Retrieve prior documentation structure and content to maintain consistency. Cache generated docs to avoid regenerating unchanged sections.

```bash
# Check for prior documentation context before starting
python3 execution/memory_manager.py auto --query "documentation patterns and prior content for Wiki Changelog"
```

### Storing Results

After completing work, store documentation decisions for future sessions:

```bash
python3 execution/memory_manager.py store \
  --content "Documentation: API reference generated from OpenAPI spec, deployment guide updated with new env vars" \
  --type technical --project <project> \
  --tags wiki-changelog documentation
```

### Multi-Agent Collaboration

Share documentation changes with all agents so they reference the latest guides and APIs.

```bash
python3 execution/cross_agent_context.py store \
  --agent "<your-agent>" \
  --action "Documentation updated — API reference, deployment guide, and CHANGELOG all current" \
  --project <project>
```

### Agent Team: Documentation

This skill pairs with `documentation_team` — dispatched automatically after any code change to keep docs in sync.

<!-- AGI-INTEGRATION-END -->
