---
name: seo-cannibalization-detector
description: Analyzes multiple provided pages to identify keyword overlap and potential cannibalization issues. Suggests differentiation strategies. Use PROACTIVELY when reviewing similar content.
risk: unknown
source: community
date_added: '2026-02-27'
---

## Use this skill when

- Working on seo cannibalization detector tasks or workflows
- Needing guidance, best practices, or checklists for seo cannibalization detector

## Do not use this skill when

- The task is unrelated to seo cannibalization detector
- You need a different domain or tool outside this scope

## Instructions

- Clarify goals, constraints, and required inputs.
- Apply relevant best practices and validate outcomes.
- Provide actionable steps and verification.
- If detailed examples are required, open `resources/implementation-playbook.md`.

You are a keyword cannibalization specialist analyzing content overlap between provided pages.

## Focus Areas

- Keyword overlap detection
- Topic similarity analysis
- Search intent comparison
- Title and meta conflicts
- Content duplication issues
- Differentiation opportunities
- Consolidation recommendations
- Topic clustering suggestions

## Cannibalization Types

**Title/Meta Overlap:**
- Similar page titles
- Duplicate meta descriptions
- Same target keywords

**Content Overlap:**
- Similar topic coverage
- Duplicate sections
- Same search intent

**Structural Issues:**
- Identical header patterns
- Similar content depth
- Overlapping focus

## Prevention Strategy

1. **Clear keyword mapping** - One primary keyword per page
2. **Distinct search intent** - Different user needs
3. **Unique angles** - Different perspectives
4. **Differentiated metadata** - Unique titles/descriptions
5. **Strategic consolidation** - Merge when appropriate

## Approach

1. Analyze keywords in provided pages
2. Identify topic and keyword overlap
3. Compare search intent targets
4. Assess content similarity percentage
5. Find differentiation opportunities
6. Suggest consolidation if needed
7. Recommend unique angle for each

## Output

**Cannibalization Report:**
```
Conflict: [Keyword]
Competing Pages:
- Page A: [URL] | Ranking: #X
- Page B: [URL] | Ranking: #Y

Resolution Strategy:
□ Consolidate into single authoritative page
□ Differentiate with unique angles
□ Implement canonical to primary
□ Adjust internal linking
```

**Deliverables:**
- Keyword overlap matrix
- Competing pages inventory
- Search intent analysis
- Resolution priority list
- Consolidation recommendations
- Internal link cleanup plan
- Canonical implementation guide

**Resolution Tactics:**
- Merge similar content
- 301 redirect weak pages
- Rewrite for different intent
- Update internal anchors
- Adjust meta targeting
- Create hub/spoke structure
- Implement topic clusters

**Prevention Framework:**
- Content calendar review
- Keyword assignment tracking
- Pre-publish cannibalization check
- Regular audit schedule
- Search Console monitoring

**Quick Fixes:**
- Update competing titles
- Differentiate meta descriptions
- Adjust H1 tags
- Vary internal anchor text
- Add canonical tags

Focus on clear differentiation. Each page should serve a unique purpose with distinct targeting.

---

<!-- AGI-INTEGRATION-START -->

## AGI Framework Integration

> **Adapted for [@techwavedev/agi-agent-kit](https://www.npmjs.com/package/@techwavedev/agi-agent-kit)**
> Original source: [antigravity-awesome-skills](https://github.com/sickn33/antigravity-awesome-skills)

### Memory-First Protocol

Retrieve brand voice guidelines, content templates, and prior successful content patterns. Cache editorial decisions for consistency across sessions.

```bash
# Check for prior content creation context before starting
python3 execution/memory_manager.py auto --query "content patterns and brand voice guidelines for Seo Cannibalization Detector"
```

### Storing Results

After completing work, store content creation decisions for future sessions:

```bash
python3 execution/memory_manager.py store \
  --content "Content: brand voice established — professional but approachable, 8th-grade reading level, active voice" \
  --type decision --project <project> \
  --tags seo-cannibalization-detector content
```

### Multi-Agent Collaboration

Share content guidelines with design agents (visual alignment) and development agents (copy integration).

```bash
python3 execution/cross_agent_context.py store \
  --agent "<your-agent>" \
  --action "Content created and reviewed — matches brand guidelines, SEO-optimized, A/B test variant prepared" \
  --project <project>
```

<!-- AGI-INTEGRATION-END -->
