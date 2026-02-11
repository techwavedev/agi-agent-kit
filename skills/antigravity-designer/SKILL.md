---
name: antigravity-designer
description: "Website design specialist powered by the AntiGravity design system (Jack Roberts). Uses NotebookLM Deep RAG to query curated design patterns: Cloud-to-Local workflow, UI Sniping, automated accessibility/SEO, Firecrawl brand extraction, and GitHub+Vercel CI/CD. Triggers on: 'design website', 'UI patterns', 'visual design', 'web aesthetics', '@designer'."
skills:
  - notebooklm-rag
---

# Antigravity Designer — Website Design Specialist

> **Deep RAG Skill.** Queries the `antigravity-designer` NotebookLM notebook for design patterns grounded in Jack Roberts' AntiGravity design system.

## Prerequisites

> [!IMPORTANT]
> This skill requires NotebookLM MCP to be configured and authenticated. On first use, the agent will:
>
> 1. Check auth via `get_health` — if `authenticated: false`, propose `setup_auth` (opens browser for Google login)
> 2. Check if `antigravity-designer` notebook is in the library — if missing, register it via `add_notebook`
> 3. Select the notebook as active via `select_notebook`

**Notebook URL:** `https://notebooklm.google.com/notebook/9fecdc06-5e9a-4aa5-8a1b-642083aa6300`

## Knowledge Base (From Notebook)

The notebook contains the AntiGravity design system covering **5 levels of automated design**:

### Level 1: Programmatic Image Generation

- **Nano Banana API** (Google interface) for batch image generation
- Custom HTML interface ("Image Designer Pro") for controlling dimensions, batches, reference images
- Runs on local host for immediate preview

### Level 2: Professional Presentations

- **Gamma API** integration for automated slide decks
- Meeting transcript → structured proposal conversion (Fireflies)
- Brand-consistent formatting

### Level 3: Interactive Websites ⭐ (Primary Focus)

- **Cloud-to-Local Workflow** (the "80% Rule"):
  1. Prototype in AI Studio → get "directionally correct" (80%)
  2. Download to local host (port 3000) for refinement
  3. Apply UI/UX skills for professional polish
  4. Deploy via GitHub → Vercel

- **UI Sniping**: Copy components from 21st.dev / CodePen → integrate while maintaining brand continuity

- **Automated Accessibility**: ARIA attributes, visible focus states, keyboard navigation, motion reduction

- **Automated SEO**: Meta descriptions, image optimization, semantic tags

- **Firecrawl Style Extraction**: Analyze existing sites (e.g., Apple) to extract brand DNA (colors, fonts, spacing)

- **Reference-Based Design**: Upload HTML/screenshots to guide AI toward a specific visual direction

- **Iterative Sparring**: Refine through dialogue ("reduce underwater effect to 5%", "make CTA more prominent")

### Level 4: Automated Infographics

- Connect to NotebookLM notebooks for research-backed infographics
- Spin up multiple knowledge bases for different topics

### Level 5: Documents & Administration

- Programmatic Excel, financial metrics, invoices
- Brand consistency enforcement (logos, color palettes)

## Design Patterns

| Pattern                  | Description                                                                 |
| ------------------------ | --------------------------------------------------------------------------- |
| **Master Orchestrator**  | User conducts, AI agents execute across multiple APIs simultaneously        |
| **Cloud-to-Local**       | Start in AI Studio (speed) → refine locally (control) → deploy (CI/CD)      |
| **UI Sniping**           | Find premium components on 21st.dev/CodePen → integrate into your brand     |
| **Reference-Based**      | Feed reference HTML/screenshots to guide the AI's visual output             |
| **Firecrawl Extraction** | Analyze competitor sites to extract brand DNA without copying layouts       |
| **SOP-Driven**           | Save successful prompts as SOPs for consistent, repeatable output           |
| **MCP Integration**      | Universal protocol connecting AI to external apps (Fireflies, Notion, etc.) |

## Autonomous Workflow

When a design request is detected, the agent **automatically**:

```
1. Check auth          → get_health → if false → propose setup_auth
2. Check notebook      → list_notebooks → if missing → add_notebook with URL above
3. Select notebook     → select_notebook("antigravity-designer")
4. Check Qdrant cache  → if similar pattern cached → return from cache
5. Query notebook      → ask_question with targeted design questions
6. Follow up           → ask additional questions if gaps detected
7. Cache results       → store in Qdrant for future reuse
8. Synthesize          → create design spec from all answers
9. Implement           → generate production code following the spec
```

## Query Strategy

When querying the notebook, ask targeted questions based on request type:

### Landing Page

1. "What Cloud-to-Local workflow applies to landing pages?"
2. "What UI Sniping components work for [industry] landing pages?"
3. "What accessibility and SEO automation should be applied?"

### Full Website

1. "What is the complete Cloud-to-Local workflow for building a website?"
2. "How does reference-based design guide the initial prototype?"
3. "What Firecrawl extraction patterns help establish brand DNA?"
4. "What deployment workflow connects GitHub to Vercel?"

### Design Refresh

1. "How does UI Sniping modernize existing components?"
2. "What automated UI/UX skills elevate from 'junior to interstellar'?"
3. "What animation refinement technique uses iterative sparring?"

## Integration

| Skill             | How It Integrates                                                                      |
| ----------------- | -------------------------------------------------------------------------------------- |
| `stitch-loop`     | Generate DESIGN.md from notebook insights, then implement via Stitch workflow          |
| `qdrant-memory`   | Cache design patterns for reuse across projects (100% token savings on repeat queries) |
| `frontend-design` | Complements with design thinking principles (notebook provides specific patterns)      |
| `notebooklm-rag`  | Underlying Deep RAG engine — handles auth, querying, caching                           |

## Triggers

- "design website", "design landing page", "design app"
- "UI patterns", "UX flow", "visual design", "web aesthetics"
- "UI sniping", "cloud to local", "firecrawl", "reference design"
- "@designer", "@antigravity-designer"

## Limitations

- Requires NotebookLM MCP server configured in AI host
- Subject to NotebookLM rate limits (50/day free, 250/day Pro)
- Knowledge is based on the Jack Roberts AntiGravity tutorial — add more sources to the notebook for broader coverage
- Browser overhead: ~5-10 seconds per query

## Credits

Knowledge source: [Jack Roberts — "The greatest design system I've ever used (AntiGravity)"](https://www.youtube.com/@JackRoberts)
Built on the `notebooklm-rag` skill foundation.
