---
name: antigravity-designer
description: "Elite website design specialist powered by NotebookLM Deep RAG. Queries the 'antigravity-designer' notebook for cutting-edge design patterns, UI/UX best practices, and visual excellence strategies. Triggers on: 'design website', 'UI patterns', 'visual design', 'web aesthetics', '@designer'."
---

# Antigravity Designer — Deep RAG Website Design Specialist

> **Elite Design Intelligence:** This skill queries a curated NotebookLM notebook (`antigravity-designer`) containing advanced website design patterns, UI/UX psychology, visual systems, and modern web aesthetics.

## Purpose

Transform generic design requests into **premium, production-ready** website designs by leveraging deep knowledge from the `antigravity-designer` notebook.

## Architecture

```
User: "Design a landing page for X"
    ↓
Agent checks Qdrant → prior design patterns cached?
    ↓ miss
Agent queries antigravity-designer notebook:
  - "What are the latest landing page design patterns for [industry]?"
  - "What visual hierarchy works best for [goal]?"
  - "What color psychology applies to [audience]?"
    ↓
Agent synthesizes answers → creates design spec
    ↓
Agent caches in Qdrant → reuse patterns
    ↓
Agent generates implementation (HTML/CSS/JS)
```

## Workflow

### 1. Design Discovery (Automatic)

When user requests a design, the agent **automatically**:

1. **Check Qdrant cache** for similar design patterns
2. **Query NotebookLM** with targeted questions:
   - "What are modern design patterns for [type] websites?"
   - "What visual hierarchy works for [goal]?"
   - "What color systems suit [industry/audience]?"
   - "What typography pairings are trending?"
   - "What micro-interactions enhance [user action]?"

3. **Follow-up automatically** if answers have gaps:
   - "What specific spacing/grid system?"
   - "What animation timing curves?"
   - "What accessibility considerations?"

4. **Cache results** in Qdrant for future reuse

### 2. Design Synthesis

Agent combines NotebookLM answers into a cohesive design spec:

```markdown
## Design Specification

### Visual System

- Color Palette: [from notebook]
- Typography: [from notebook]
- Spacing Scale: [from notebook]

### Layout Patterns

- Hero Section: [pattern from notebook]
- Content Grid: [pattern from notebook]
- Navigation: [pattern from notebook]

### Interactions

- Hover States: [from notebook]
- Scroll Animations: [from notebook]
- Transitions: [from notebook]

### Accessibility

- Contrast Ratios: [from notebook]
- Focus States: [from notebook]
- ARIA Patterns: [from notebook]
```

### 3. Implementation

Agent generates production code following the synthesized spec.

## Notebook Setup

### First Time: Add the Notebook

If `antigravity-designer` is not in the library:

```
User: "I have a NotebookLM with design knowledge"
Agent: "What is the NotebookLM URL?"
User: [provides URL]
Agent: [uses ask_question to discover content]
Agent: [proposes metadata]
  Name: antigravity-designer
  Description: Advanced website design patterns and visual systems
  Topics: [UI/UX, Visual Design, Web Aesthetics, Typography, Color Theory, ...]
  Use cases: [Website design, Landing pages, Design systems, ...]
Agent: "Add it to your library?"
User: "Yes"
Agent: [calls add_notebook]
```

### Ongoing: Auto-Select

The skill automatically selects `antigravity-designer` when design questions are detected.

## Query Patterns

### Landing Page Design

```
User: "Design a SaaS landing page"
Agent queries:
  1. "What are effective SaaS landing page patterns?"
  2. "What visual hierarchy converts for B2B SaaS?"
  3. "What trust signals work for enterprise buyers?"
  4. "What CTA placements maximize conversions?"
```

### Design System

```
User: "Create a design system for a fintech app"
Agent queries:
  1. "What are modern fintech design system patterns?"
  2. "What color palettes convey trust and security?"
  3. "What typography scales work for financial data?"
  4. "What component libraries are standard?"
```

### Visual Refresh

```
User: "Modernize this outdated website"
Agent queries:
  1. "What are current web design trends for [industry]?"
  2. "What visual updates signal modernity?"
  3. "What animation patterns feel contemporary?"
  4. "What layout shifts improve user experience?"
```

## Integration with Other Skills

### Stitch Loop

After querying `antigravity-designer`, the agent can use `stitch-loop` to:

1. Generate `DESIGN.md` from NotebookLM insights
2. Implement components following discovered patterns
3. Iterate based on design principles from the notebook

### Qdrant Memory

- **Pattern Reuse:** Design patterns are cached and reused across projects
- **Context Building:** Each design builds on prior research
- **Token Savings:** Avoid re-querying for known patterns

## Autonomous Behavior

The agent **does not ask** for permission to query NotebookLM. It:

1. Detects design intent in user request
2. Checks Qdrant for cached patterns
3. Queries `antigravity-designer` automatically
4. Synthesizes answers into design spec
5. Generates implementation
6. Caches for future use

## Example Session

```
User: "Design a landing page for an AI coding assistant"

Agent (internal):
  - Checks Qdrant: no cached AI tool landing pages
  - Queries antigravity-designer:
    Q1: "What are effective landing page patterns for developer tools?"
    Q2: "What visual hierarchy works for technical audiences?"
    Q3: "What code-related visual elements enhance credibility?"
    Q4: "What color schemes appeal to developers?"
  - Synthesizes answers
  - Caches in Qdrant

Agent (to user):
  "Based on modern developer tool design patterns, here's the spec:

  **Visual System:**
  - Dark mode primary (90% of devs prefer)
  - Accent: Electric blue (#0066FF) for CTAs
  - Typography: JetBrains Mono (code) + Inter (UI)
  - Grid: 12-column with 24px gutters

  **Hero Section:**
  - Animated code editor demo (left 60%)
  - Value prop + CTA (right 40%)
  - Syntax highlighting with real code examples

  **Trust Signals:**
  - GitHub stars counter
  - Live code playground
  - Developer testimonials with code snippets

  Implementing now..."

  [Generates HTML/CSS/JS following the spec]
```

## Triggers

This skill activates when user request contains:

- "design website", "design landing page", "design app"
- "UI patterns", "UX flow", "visual design"
- "modern web design", "web aesthetics"
- "@designer", "@antigravity-designer"
- "how should I design...", "what design pattern..."

## MCP Tools Used

- `get_health` — Check auth before querying
- `list_notebooks` — Verify `antigravity-designer` is registered
- `select_notebook` — Set as active for queries
- `ask_question` — Query design knowledge
- `add_notebook` — Register if not in library (first time)

## Qdrant Integration

### Cache Structure

```python
{
  "content": "Q: [design question] A: [notebook answer]",
  "type": "design_pattern",
  "project": "antigravity-designer",
  "tags": ["ui", "landing-page", "saas", "visual-hierarchy"]
}
```

### Retrieval

Before querying NotebookLM, check Qdrant:

```bash
python3 execution/memory_manager.py auto --query "SaaS landing page patterns"
```

If cache hit, skip browser automation and use cached answer.

## Limitations

- Requires `antigravity-designer` notebook to be set up in NotebookLM
- Subject to NotebookLM rate limits (50/day free, 250/day Pro)
- Design knowledge is as current as the notebook content
- Browser overhead: ~3-5 seconds per query

## Credits

Built on the `notebooklm-rag` skill foundation.
Powered by Google NotebookLM + Gemini 2.0.
Integrated with Qdrant for pattern caching and reuse.
