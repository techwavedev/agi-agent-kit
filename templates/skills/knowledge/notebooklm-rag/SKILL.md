---
name: notebooklm-rag
description: "Deep research and retrieval-augmented generation using Google NotebookLM. Triggers on: 'research my docs', 'check my notebooks', 'deep search', '@notebooklm'. Provides structured research workflows for document analysis, knowledge synthesis, and evidence-based answers."
---

# NotebookLM RAG - Deep Document Research

## Overview

This skill enables deep research workflows using Google NotebookLM as a Retrieval-Augmented Generation (RAG) backend. It goes beyond simple queries by providing structured research patterns, multi-source synthesis, and evidence-based answer generation from your uploaded documents.

## When to Use

| Trigger             | Example                                                   |
| ------------------- | --------------------------------------------------------- |
| **Research docs**   | "Research my docs for deployment patterns"                |
| **Check notebooks** | "Check my notebooks for API design decisions"             |
| **Deep search**     | "Deep search for authentication best practices"           |
| **@notebooklm**     | "@notebooklm find all references to caching strategies"   |
| **Synthesize**      | "Synthesize what my documents say about error handling"   |
| **Evidence-based**  | "What do my sources say about microservices vs monolith?" |

## Prerequisites

This skill requires the `notebooklm-mcp` skill to be configured and authenticated. See `skills/notebooklm-mcp/SKILL.md` for setup instructions.

Ensure the MCP server is running and you have at least one notebook with uploaded sources.

## Research Workflows

### 1. Single-Source Deep Dive

Extract comprehensive knowledge from a single document or notebook.

**Steps:**

1. Identify the target notebook using `list_notebooks()`
2. Review available sources with `get_notebook(notebook_id)`
3. Execute a series of focused queries to extract key themes
4. Synthesize findings into a structured summary

**Example Prompt:**

```
Research my architecture docs notebook for all deployment patterns mentioned.
Summarize each pattern with pros, cons, and when to use.
```

### 2. Cross-Source Synthesis

Compare and synthesize information across multiple sources within a notebook.

**Steps:**

1. Query the notebook with a broad topic question
2. Follow up with specific comparison questions
3. Identify agreements and contradictions across sources
4. Produce a unified synthesis with source attribution

**Example Prompt:**

```
Check my notebooks for what different sources say about database scaling.
Compare the approaches and highlight any contradictions.
```

### 3. Evidence-Based Q&A

Answer specific questions with citations from uploaded documents.

**Steps:**

1. Formulate a precise question
2. Query the notebook for relevant passages
3. Extract direct quotes and page references
4. Construct an answer grounded in source material

**Example Prompt:**

```
@notebooklm What are the exact security requirements mentioned in the compliance docs?
Include direct quotes.
```

### 4. Knowledge Gap Analysis

Identify what your documents do NOT cover.

**Steps:**

1. Define the expected knowledge domain
2. Query for each expected subtopic
3. Flag topics with no or weak source coverage
4. Report gaps for further research

**Example Prompt:**

```
Deep search my project docs. Do they cover: error handling, logging, monitoring,
alerting, rollback procedures? List what's missing.
```

## Research Report Format

When producing research outputs, use this structure:

```markdown
# Research Report: [Topic]

## Query

[Original research question]

## Key Findings

1. **Finding 1** — [Summary] (Source: [document name])
2. **Finding 2** — [Summary] (Source: [document name])

## Supporting Evidence

> "Direct quote from source" — [Source, Page/Section]

## Synthesis

[Unified analysis combining all findings]

## Gaps & Limitations

- [Topics not covered by available sources]

## Recommendations

- [Actionable next steps based on findings]
```

## Integration with Memory System

When the `qdrant-memory` skill is available, research results are automatically cached:

```bash
# Research results are stored for future retrieval
python3 execution/memory_manager.py store \
  --content "Research findings on [topic]" \
  --type technical \
  --tags notebooklm research [topic]
```

This prevents redundant queries and enables cross-session knowledge persistence.

## Best Practices

1. **Be Specific**: Narrow queries yield better results than broad ones
2. **Iterate**: Start broad, then drill down into specific subtopics
3. **Cross-Reference**: Query the same topic from different angles
4. **Cite Sources**: Always attribute findings to specific documents
5. **Cache Results**: Store valuable research in the memory system for reuse
6. **Verify Currency**: Check document upload dates for time-sensitive topics

## Limitations

- Depends on the quality and completeness of uploaded sources
- Cannot access documents not uploaded to NotebookLM
- Query complexity is limited by NotebookLM's context window
- Rate limits apply (50 queries/day for free accounts, higher for AI Pro/Ultra)
