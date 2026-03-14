---
name: interview-coach
description: "Full job search coaching system — JD decoding, resume, storybank, mock interviews, transcript analysis, comp negotiation. 23 commands, persistent state."
category: productivity
risk: safe
source: community
date_added: "2026-03-11"
author: dbhat93
tags: [interview, job-search, coaching, career, storybank, negotiation]
tools: [claude]
---

# Interview Coach

## Overview

A persistent, adaptive coaching system for the full job search lifecycle.
Not a question bank — an opinionated system that tracks your patterns,
scores your answers, and gets sharper the more you use it. State persists
in `coaching_state.md` across sessions so you always pick up where you left off.

## Install

```bash
npx skills add dbhat93/job-search-os
```

Then type `/coach` → `kickoff`.

## When to Use This Skill

- Use when starting a job search and need a structured system
- Use when preparing for a specific interview (company research, mock, hype)
- Use when you want to analyze a past interview transcript
- Use when negotiating an offer or handling comp questions on recruiter screens
- Use when building or maintaining a storybank of interview-ready stories

## What It Covers

- **JD decoding** — six lenses, fit verdict, recruiter questions to ask
- **Resume + LinkedIn** — ATS audit, bullet rewrites, platform-native optimization
- **Mock interviews** — behavioral, system design, case, panel, technical formats
- **Transcript analysis** — paste from Otter/Zoom/Grain, auto-detected format
- **Storybank** — STAR stories with earned secrets, retrieval drills, portfolio optimization
- **Comp + negotiation** — pre-offer scripting, offer analysis, exact negotiation scripts
- **23 total commands** across the full search lifecycle

## Examples

### Example 1: Start your job search

```
/coach
kickoff
```

The coach asks for your resume, target role, and timeline — then builds
your profile and gives you a prioritized action plan.

### Example 2: Prep for a specific company

```
/coach
prep Stripe Senior PM
```

Runs company research, generates a role-specific prep brief, and queues
up mock interview questions tailored to Stripe's process.

### Example 3: Analyze an interview transcript

```
/coach
analyze
```

Paste a raw transcript from Otter, Zoom, or any tool. The coach
auto-detects the format, scores each answer across five dimensions,
and gives you a drill plan targeting your specific gaps.

### Example 4: Handle a comp question

```
/coach
salary
```

Coaches you through the recruiter screen "what are your salary
expectations?" moment with a defensible range and exact scripts.

## Source

https://github.com/dbhat93/job-search-os

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
  --tags interview-coach <relevant-tags>
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
