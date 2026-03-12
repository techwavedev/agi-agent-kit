---
name: culture-index
description: "Index and search culture documentation"
source: "https://github.com/trailofbits/skills/tree/main/plugins/culture-index"
risk: safe
---

# Culture Index

## Overview

Index and search culture documentation to help teams understand organizational values, practices, and guidelines.

## When to Use This Skill

Use this skill when you need to index and search culture documentation.

Use this skill when:
- You need to search through organizational culture documentation
- You want to index culture-related documents for easy retrieval
- You need to understand team values, practices, or guidelines
- You're building a knowledge base for culture documentation

## Instructions

This skill provides capabilities for indexing and searching culture documentation. It helps teams:

1. **Index Culture Documents**: Organize and index culture-related documentation
2. **Search Functionality**: Quickly find relevant culture information
3. **Knowledge Retrieval**: Access organizational values and practices efficiently

## Usage

When working with culture documentation:

1. Identify the culture documents to index
2. Use the indexing functionality to organize the content
3. Search through indexed documents to find relevant information
4. Retrieve specific culture guidelines or practices as needed

## Resources

For more information, see the [source repository](https://github.com/trailofbits/skills/tree/main/plugins/culture-index).


---

<!-- AGI-INTEGRATION-START -->

## AGI Framework Integration

> **Adapted for [@techwavedev/agi-agent-kit](https://www.npmjs.com/package/@techwavedev/agi-agent-kit)**
> Original source: [antigravity-awesome-skills](https://github.com/sickn33/antigravity-awesome-skills)

### Memory-First Protocol

Retrieve prior documentation structure and content to maintain consistency. Cache generated docs to avoid regenerating unchanged sections.

```bash
# Check for prior documentation context before starting
python3 execution/memory_manager.py auto --query "documentation patterns and prior content for Culture Index"
```

### Storing Results

After completing work, store documentation decisions for future sessions:

```bash
python3 execution/memory_manager.py store \
  --content "Documentation: API reference generated from OpenAPI spec, deployment guide updated with new env vars" \
  --type technical --project <project> \
  --tags culture-index documentation
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