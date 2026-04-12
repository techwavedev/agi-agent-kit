---
name: algolia-search
description: "Expert patterns for Algolia search implementation, indexing strategies, React InstantSearch, and relevance tuning Use when: adding search to, algolia, instantsearch, search api, search functionality."
risk: unknown
source: "vibeship-spawner-skills (Apache 2.0)"
date_added: "2026-02-27"
---

# Algolia Search Integration

## Patterns

### React InstantSearch with Hooks

Modern React InstantSearch setup using hooks for type-ahead search.

Uses react-instantsearch-hooks-web package with algoliasearch client.
Widgets are components that can be customized with classnames.

Key hooks:
- useSearchBox: Search input handling
- useHits: Access search results
- useRefinementList: Facet filtering
- usePagination: Result pagination
- useInstantSearch: Full state access

### Next.js Server-Side Rendering

SSR integration for Next.js with react-instantsearch-nextjs package.

Use <InstantSearchNext> instead of <InstantSearch> for SSR.
Supports both Pages Router and App Router (experimental).

Key considerations:
- Set dynamic = 'force-dynamic' for fresh results
- Handle URL synchronization with routing prop
- Use getServerState for initial state

### Data Synchronization and Indexing

Indexing strategies for keeping Algolia in sync with your data.

Three main approaches:
1. Full Reindexing - Replace entire index (expensive)
2. Full Record Updates - Replace individual records
3. Partial Updates - Update specific attributes only

Best practices:
- Batch records (ideal: 10MB, 1K-10K records per batch)
- Use incremental updates when possible
- partialUpdateObjects for attribute-only changes
- Avoid deleteBy (computationally expensive)

## ⚠️ Sharp Edges

| Issue | Severity | Solution |
|-------|----------|----------|
| Issue | critical | See docs |
| Issue | high | See docs |
| Issue | medium | See docs |
| Issue | medium | See docs |
| Issue | medium | See docs |
| Issue | medium | See docs |
| Issue | medium | See docs |
| Issue | medium | See docs |

## When to Use
This skill is applicable to execute the workflow or actions described in the overview.

---

<!-- AGI-INTEGRATION-START -->

## AGI Framework Integration

> **Adapted for [@techwavedev/agi-agent-kit](https://www.npmjs.com/package/@techwavedev/agi-agent-kit)**
> Original source: [antigravity-awesome-skills](https://github.com/sickn33/antigravity-awesome-skills)

### Memory-First Protocol

Retrieve prior design decisions (color palettes, typography, spacing scales) to maintain visual consistency across sessions. Cache generated design tokens.

```bash
# Check for prior frontend/design context before starting
python3 execution/memory_manager.py auto --query "design system decisions and component patterns for Algolia Search"
```

### Storing Results

After completing work, store frontend/design decisions for future sessions:

```bash
python3 execution/memory_manager.py store \
  --content "Design system: adopted 8px grid, Inter font family, HSL color tokens with dark mode support" \
  --type decision --project <project> \
  --tags algolia-search frontend
```

### Multi-Agent Collaboration

Share design decisions with backend agents (API contract changes) and QA agents (visual regression baselines).

```bash
python3 execution/cross_agent_context.py store \
  --agent "<your-agent>" \
  --action "Implemented UI components — new design system with accessibility compliance (WCAG 2.1 AA)" \
  --project <project>
```

### Design Memory Persistence

Store design system tokens and component decisions in Qdrant so any agent on any platform (Claude, Gemini, Cursor) can retrieve and apply consistent styling.

<!-- AGI-INTEGRATION-END -->
