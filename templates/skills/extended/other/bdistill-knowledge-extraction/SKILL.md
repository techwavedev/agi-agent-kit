---
name: bdistill-knowledge-extraction
description: "Extract structured domain knowledge from AI models in-session or from local open-source models via Ollama. No API key needed."
category: ai-research
risk: safe
source: community
date_added: "2026-03-20"
author: FrancyJGLisboa
tags: [ai, knowledge-extraction, domain-specific, data-moat, mcp, reference-data]
tools: [claude, cursor, codex, copilot]
---

# Knowledge Extraction

Extract structured, quality-scored domain knowledge from any AI model — in-session from closed models (no API key) or locally from open-source models via Ollama.

## Overview

bdistill turns your AI subscription sessions into a compounding knowledge base. The agent answers targeted domain questions, bdistill structures and quality-scores the responses, and the output accumulates into a searchable, exportable reference dataset.

Adversarial mode challenges the agent's claims — forcing evidence, corrections, and acknowledged limitations — producing validated knowledge entries.

## When to Use This Skill

- Use when you need structured reference data on any domain (medical, legal, finance, cybersecurity)
- Use when building lookup tables, Q&A datasets, or research corpora
- Use when generating training data for traditional ML models (regression, classification — NOT competing LLMs)
- Use when you want cross-model comparison on domain knowledge

## How It Works

### Step 1: Install

```bash
pip install bdistill
claude mcp add bdistill -- bdistill-mcp   # Claude Code
```

### Step 2: Extract knowledge in-session

```
/distill medical cardiology                    # Preset domain
/distill --custom kubernetes docker helm       # Custom terms
/distill --adversarial medical                 # With adversarial validation
```

### Step 3: Search, export, compound

```bash
bdistill kb list                               # Show all domains
bdistill kb search "atrial fibrillation"       # Keyword search
bdistill kb export -d medical -f csv           # Export as spreadsheet
bdistill kb export -d medical -f markdown      # Readable knowledge document
```

## Output Format

Structured reference JSONL — not training data:

```json
{
  "question": "What causes myocardial infarction?",
  "answer": "Myocardial infarction results from acute coronary artery occlusion...",
  "domain": "medical",
  "category": "cardiology",
  "tags": ["mechanistic", "evidence-based"],
  "quality_score": 0.73,
  "confidence": 1.08,
  "validated": true,
  "source_model": "Claude Sonnet 4"
}
```

## Tabular ML Data Generation

Generate structured training data for traditional ML models:

```
/schema sepsis | hr:float, bp:float, temp:float, wbc:float | risk:category[low,moderate,high,critical]
```

Exports as CSV ready for pandas/sklearn. Each row tracks source_model for cross-model analysis.

## Local Model Extraction (Ollama)

For open-source models running locally:

```bash
# Install Ollama from https://ollama.com
ollama serve
ollama pull qwen3:4b

bdistill extract --domain medical --model qwen3:4b
```

## Security & Safety Notes

- In-session extraction uses your existing subscription — no additional API keys
- Local extraction runs entirely on your machine via Ollama
- No data is sent to external services
- Output is reference data, not LLM training format

## Related Skills

- `@bdistill-behavioral-xray` - X-ray a model's behavioral patterns

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
  --tags bdistill-knowledge-extraction <relevant-tags>
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
