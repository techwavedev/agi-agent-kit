---
name: professional-proofreader
description: >
    Use when a user asks to "proofread", "review and correct", "fix grammar", "improve readability while keeping my voice", and to proofread a document file and save an updated version.
risk: safe
source: original
date_added: "2026-03-04"
---

# Professional Proofreader

## Overview

This skill transforms flawed writing — whether pasted text or uploaded documents — into publication-ready prose without altering the author’s intent.
It eliminates grammatical, spelling, punctuation, clarity, and tone issues while strictly preserving the author’s voice and intent.
Returns a corrected version plus a structured modification log, or generates an updated file when requested. Not for code editing or technical refactoring.

---

## When to Use

- Use when user asks to "proofread", "review and correct", "fix grammar", "polish this text", "improve readability while keeping my voice".
- Use when user asks to proofread a document file (like .docx, .pdf, .txt) and save the updated version as new file with 'UPDATED_' prefix.

---

# WORKFLOW MODES

This skill operates in two modes:
1. Inline Text Mode
2. File Processing Mode

### MODE 1: Inline Text

Refer [markdown](references/inline-text-mode.md) for complete inline text mode.

### MODE 2: File Processing

Trigger when user says:

- "Proofread [filename].[extension]
- "Edit this document"
- "Correct grammar in this file"
- "Save updated version"
- "Add prefix UPDATED_"
- "Return corrected .[extension]"

Refer [markdown](references/file-processing-mode.md) for complete file processing mode.

---

## Best Practices

### ✅ **Do:** [Good practice]
- Always include modification explanations.
- Always keep quality standards equivalent to: Academic proofreading, business document refinement, pre-publication review.
- Always follow below editing standards:

#### Grammar
- Subject-verb agreement  
- Tense consistency 
- Article usage 
- Prepositions
- Pronoun clarity 

#### Spelling
- Correct typos 
- Maintain original spelling variant (US/UK)

#### Punctuation
- Commas 
- Apostrophes 
- Quotation marks 
- Sentence boundaries 

#### Style & Tone
- Maintain author voice 
- Avoid unnecessary formalization 
- Preserve rhetorical choices 

#### Readability
- Improve structure 
- Enhance logical flow 
- Remove redundancy 

### ❌ **Don't:** [What to avoid] 
- Never alter meaning.
- Never drop formatting intentionally.
- Never change file name logic beyond request.
- Never expand the content

---

# Output Rules

If inline:
-> Return Corrected Version + Modifications list.

If file rewrite:
-> Save updated file.
-> Confirm filename.
-> Provide modifications list unless suppressed.

Give friendly message to user in the end.

---

---

<!-- AGI-INTEGRATION-START -->

## AGI Framework Integration

> **Adapted for [@techwavedev/agi-agent-kit](https://www.npmjs.com/package/@techwavedev/agi-agent-kit)**
> Original source: [antigravity-awesome-skills](https://github.com/sickn33/antigravity-awesome-skills)

### Memory-First Protocol

Retrieve prior decisions and patterns to avoid re-discovering solutions. Cache results for instant retrieval in future sessions.

```bash
# Check for prior development context before starting
python3 execution/memory_manager.py auto --query "prior work and patterns related to Professional Proofreader"
```

### Storing Results

After completing work, store development decisions for future sessions:

```bash
python3 execution/memory_manager.py store \
  --content "Completed task with key insights documented for future reference" \
  --type decision --project <project> \
  --tags professional-proofreader default
```

### Multi-Agent Collaboration

Share outcomes with other agents so the team stays aligned and avoids duplicate work.

```bash
python3 execution/cross_agent_context.py store \
  --agent "<your-agent>" \
  --action "Task completed — results documented and shared with team" \
  --project <project>
```

<!-- AGI-INTEGRATION-END -->
