---
name: api-documentation
description: "API documentation workflow for generating OpenAPI specs, creating developer guides, and maintaining comprehensive API documentation."
category: granular-workflow-bundle
risk: safe
source: personal
date_added: "2026-02-27"
---

# API Documentation Workflow

## Overview

Specialized workflow for creating comprehensive API documentation including OpenAPI/Swagger specs, developer guides, code examples, and interactive documentation.

## When to Use This Workflow

Use this workflow when:
- Creating API documentation
- Generating OpenAPI specs
- Writing developer guides
- Adding code examples
- Setting up API portals

## Workflow Phases

### Phase 1: API Discovery

#### Skills to Invoke
- `api-documenter` - API documentation
- `api-design-principles` - API design

#### Actions
1. Inventory endpoints
2. Document request/response
3. Identify authentication
4. Map error codes
5. Note rate limits

#### Copy-Paste Prompts
```
Use @api-documenter to discover and document API endpoints
```

### Phase 2: OpenAPI Specification

#### Skills to Invoke
- `openapi-spec-generation` - OpenAPI
- `api-documenter` - API specs

#### Actions
1. Create OpenAPI schema
2. Define paths
3. Add schemas
4. Configure security
5. Add examples

#### Copy-Paste Prompts
```
Use @openapi-spec-generation to create OpenAPI specification
```

### Phase 3: Developer Guide

#### Skills to Invoke
- `api-documentation-generator` - Documentation
- `documentation-templates` - Templates

#### Actions
1. Create getting started
2. Write authentication guide
3. Document common patterns
4. Add troubleshooting
5. Create FAQ

#### Copy-Paste Prompts
```
Use @api-documentation-generator to create developer guide
```

### Phase 4: Code Examples

#### Skills to Invoke
- `api-documenter` - Code examples
- `tutorial-engineer` - Tutorials

#### Actions
1. Create example requests
2. Write SDK examples
3. Add curl examples
4. Create tutorials
5. Test examples

#### Copy-Paste Prompts
```
Use @api-documenter to generate code examples
```

### Phase 5: Interactive Docs

#### Skills to Invoke
- `api-documenter` - Interactive docs

#### Actions
1. Set up Swagger UI
2. Configure Redoc
3. Add try-it functionality
4. Test interactivity
5. Deploy docs

#### Copy-Paste Prompts
```
Use @api-documenter to set up interactive documentation
```

### Phase 6: Documentation Site

#### Skills to Invoke
- `docs-architect` - Documentation architecture
- `wiki-page-writer` - Documentation

#### Actions
1. Choose platform
2. Design structure
3. Create pages
4. Add navigation
5. Configure search

#### Copy-Paste Prompts
```
Use @docs-architect to design API documentation site
```

### Phase 7: Maintenance

#### Skills to Invoke
- `api-documenter` - Doc maintenance

#### Actions
1. Set up auto-generation
2. Configure validation
3. Add review process
4. Schedule updates
5. Monitor feedback

#### Copy-Paste Prompts
```
Use @api-documenter to set up automated doc generation
```

## Quality Gates

- [ ] OpenAPI spec complete
- [ ] Developer guide written
- [ ] Code examples working
- [ ] Interactive docs functional
- [ ] Documentation deployed

## Related Workflow Bundles

- `documentation` - Documentation
- `api-development` - API development
- `development` - Development

---

<!-- AGI-INTEGRATION-START -->

## 🧠 AGI Framework Integration

> **Adapted for [@techwavedev/agi-agent-kit](https://www.npmjs.com/package/@techwavedev/agi-agent-kit)**
> Original source: [antigravity-awesome-skills](https://github.com/sickn33/antigravity-awesome-skills)

### Qdrant Memory Integration

Before executing complex tasks with this skill:
```bash
python3 execution/memory_manager.py auto --query "<task summary>"
```
- **Cache hit?** Use cached response directly — no need to re-process.
- **Memory match?** Inject `context_chunks` into your reasoning.
- **No match?** Proceed normally, then store results:
```bash
python3 execution/memory_manager.py store \\
  --content "Description of what was decided/solved" \\
  --type decision \\
  --tags api-documentation <relevant-tags>
```

### Agent Team Collaboration

- This skill can be invoked by the `orchestrator` agent via intelligent routing.
- In **Agent Teams mode**, results are shared via Qdrant shared memory for cross-agent context.
- In **Subagent mode**, this skill runs in isolation with its own memory namespace.

### Local LLM Support

When available, use local Ollama models for embedding and lightweight inference:
- Embeddings: `nomic-embed-text` via Qdrant memory system
- Lightweight analysis: Local models reduce API costs for repetitive patterns

<!-- AGI-INTEGRATION-END -->
