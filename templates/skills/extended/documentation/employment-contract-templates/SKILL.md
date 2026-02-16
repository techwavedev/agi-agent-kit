---
name: employment-contract-templates
description: Create employment contracts, offer letters, and HR policy documents following legal best practices. Use when drafting employment agreements, creating HR policies, or standardizing employment documentation.
---

# Employment Contract Templates

Templates and patterns for creating legally sound employment documentation including contracts, offer letters, and HR policies.

## Use this skill when

- Drafting employment contracts
- Creating offer letters
- Writing employee handbooks
- Developing HR policies
- Standardizing employment documentation
- Preparing onboarding documentation

## Do not use this skill when

- You need jurisdiction-specific legal advice
- The task requires licensed counsel review
- The request is unrelated to employment documentation

## Instructions

- Confirm jurisdiction, employment type, and required clauses.
- Choose a document template and tailor role-specific terms.
- Validate compensation, benefits, and compliance requirements.
- Add signature, confidentiality, and IP assignment terms as needed.
- If detailed templates are required, open `resources/implementation-playbook.md`.

## Safety

- These templates are not legal advice; consult qualified counsel before use.

## Resources

- `resources/implementation-playbook.md` for detailed templates and checklists.


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
  --tags employment-contract-templates <relevant-tags>
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