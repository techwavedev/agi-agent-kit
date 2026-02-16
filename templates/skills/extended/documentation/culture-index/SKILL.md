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

## 🧠 AGI Framework Integration

> **Adapted for [@techwavedev/agi-agent-kit](https://www.npmjs.com/package/@techwavedev/agi-agent-kit)**
> Original source: [antigravity-awesome-skills](https://github.com/sickn33/antigravity-awesome-skills)

### Hybrid Memory Integration (Qdrant + BM25)

Before executing complex tasks with this skill:
```bash
python3 execution/memory_manager.py auto --query "<task summary>"
```

**Decision Tree:**
- **Cache hit?** Use cached response directly — no need to re-process.
- **Memory match?** Inject `context_chunks` into your reasoning.
- **No match?** Proceed normally, then store results:

```bash
python3 execution/memory_manager.py store \
  --content "Description of what was decided/solved" \
  --type decision \
  --tags culture-index <relevant-tags>
```

> **Note:** Storing automatically updates both Vector (Qdrant) and Keyword (BM25) indices.

### Agent Team Collaboration

- **Strategy**: This skill communicates via the shared memory system.
- **Orchestration**: Invoked by `orchestrator` via intelligent routing.
- **Context Sharing**: Always read previous agent outputs from memory before starting.

### Local LLM Support

When available, use local Ollama models for embedding and lightweight inference:
- Embeddings: `nomic-embed-text` via Qdrant memory system
- Lightweight analysis: Local models reduce API costs for repetitive patterns