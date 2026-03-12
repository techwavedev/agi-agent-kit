---
name: expo-cicd-workflows
description: Helps understand and write EAS workflow YAML files for Expo projects. Use this skill when the user asks about CI/CD or workflows in an Expo or EAS context, mentions .eas/workflows/, or wants help with EAS build pipelines or deployment automation.
allowed-tools: "Read,Write,Bash(node:*)"
version: 1.0.0
license: MIT License
---

# EAS Workflows Skill

Help developers write and edit EAS CI/CD workflow YAML files.

## Reference Documentation

Fetch these resources before generating or validating workflow files. Use the fetch script (implemented using Node.js) in this skill's `scripts/` directory; it caches responses using ETags for efficiency:

```bash
# Fetch resources
node {baseDir}/scripts/fetch.js <url>
```

1. **JSON Schema** — https://api.expo.dev/v2/workflows/schema
   - It is NECESSARY to fetch this schema
   - Source of truth for validation
   - All job types and their required/optional parameters
   - Trigger types and configurations
   - Runner types, VM images, and all enums

2. **Syntax Documentation** — https://raw.githubusercontent.com/expo/expo/refs/heads/main/docs/pages/eas/workflows/syntax.mdx
   - Overview of workflow YAML syntax
   - Examples and English explanations
   - Expression syntax and contexts

3. **Pre-packaged Jobs** — https://raw.githubusercontent.com/expo/expo/refs/heads/main/docs/pages/eas/workflows/pre-packaged-jobs.mdx
   - Documentation for supported pre-packaged job types
   - Job-specific parameters and outputs

Do not rely on memorized values; these resources evolve as new features are added.

## Workflow File Location

Workflows live in `.eas/workflows/*.yml` (or `.yaml`).

## Top-Level Structure

A workflow file has these top-level keys:

- `name` — Display name for the workflow
- `on` — Triggers that start the workflow (at least one required)
- `jobs` — Job definitions (required)
- `defaults` — Shared defaults for all jobs
- `concurrency` — Control parallel workflow runs

Consult the schema for the full specification of each section.

## Expressions

Use `${{ }}` syntax for dynamic values. The schema defines available contexts:

- `github.*` — GitHub repository and event information
- `inputs.*` — Values from `workflow_dispatch` inputs
- `needs.*` — Outputs and status from dependent jobs
- `jobs.*` — Job outputs (alternative syntax)
- `steps.*` — Step outputs within custom jobs
- `workflow.*` — Workflow metadata

## Generating Workflows

When generating or editing workflows:

1. Fetch the schema to get current job types, parameters, and allowed values
2. Validate that required fields are present for each job type
3. Verify job references in `needs` and `after` exist in the workflow
4. Check that expressions reference valid contexts and outputs
5. Ensure `if` conditions respect the schema's length constraints

## Validation

After generating or editing a workflow file, validate it against the schema:

```sh
# Install dependencies if missing
[ -d "{baseDir}/scripts/node_modules" ] || npm install --prefix {baseDir}/scripts

node {baseDir}/scripts/validate.js <workflow.yml> [workflow2.yml ...]
```

The validator fetches the latest schema and checks the YAML structure. Fix any reported errors before considering the workflow complete.

## Answering Questions

When users ask about available options (job types, triggers, runner types, etc.), fetch the schema and derive the answer from it rather than relying on potentially outdated information.

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
  --tags expo-cicd-workflows <relevant-tags>
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
