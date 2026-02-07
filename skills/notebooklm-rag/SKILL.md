---
name: notebooklm-rag
description: "Deep-search RAG knowledge layer powered by Google NotebookLM + Gemini 2.5. Use when explicitly asked to research, investigate, plan with docs, or query knowledge bases. Complement to qdrant-memory (token saver). Triggers on: '@notebooklm', 'research my docs', 'check my notebooks', 'deep search', 'investigate with docs'."
---

# NotebookLM RAG — Deep-Search Knowledge Layer

## Overview

This skill transforms Google NotebookLM into a **deep-search RAG database** for the Agi Agent Framework. While `qdrant-memory` serves as a fast semantic cache (token saver), NotebookLM RAG provides **Gemini 2.5-powered document synthesis** for complex research, investigation, deployment planning, and multi-source analysis.

### Positioning

```
┌─────────────────────────────────────────────────────────────┐
│  USER QUERY                                                  │
│  ↓                                                           │
│  qdrant-memory (AUTO)          notebooklm-rag (EXPLICIT)     │
│  ├─ Semantic cache check       ├─ Deep document search       │
│  ├─ Token savings: 80-100%     ├─ Multi-source synthesis     │
│  ├─ Speed: <100ms              ├─ Speed: 5-30s               │
│  └─ Local, private             └─ Gemini-powered, grounded   │
│                                                              │
│  FAST + CHEAP                  DEEP + ACCURATE               │
└─────────────────────────────────────────────────────────────┘
```

| Feature         | qdrant-memory         | notebooklm-rag                     |
| --------------- | --------------------- | ---------------------------------- |
| **Purpose**     | Token saver / cache   | Deep-search knowledge base         |
| **Trigger**     | Automatic (every req) | Explicit only (`@notebooklm`)      |
| **Speed**       | <100ms                | 5-30s per query                    |
| **Accuracy**    | Keyword similarity    | Gemini 2.5 synthesis               |
| **Hallucation** | Returns what it finds | Refuses if not in docs             |
| **Best for**    | Repeated patterns     | Investigation, planning, debugging |
| **Limit**       | Disk space            | ~50 queries/day per Google account |

---

## Prerequisites

This skill requires the **notebooklm-mcp** skill to be configured:

1. ✅ MCP server running (`npx -y notebooklm-mcp@latest`)
2. ✅ Google authentication completed (browser login)
3. ✅ At least one notebook in your library

**Verify readiness:**

```
Use the get_health MCP tool → check authenticated: true
Use the list_notebooks MCP tool → verify notebooks exist
```

---

## When to Use (Explicit Triggers)

This skill activates **ONLY** when the user explicitly requests it:

### Direct Triggers

| User Says                             | Action                           |
| ------------------------------------- | -------------------------------- |
| `@notebooklm <question>`              | Single-query research            |
| `"research my docs for..."`           | Deep research workflow           |
| `"check my notebooks about..."`       | Library search + targeted query  |
| `"deep search: <topic>"`              | Multi-notebook investigation     |
| `"investigate with docs"`             | Full research mode               |
| `"what do my notebooks say about..."` | Cross-reference query            |
| `"use NotebookLM to plan..."`         | Planning with document grounding |

### Workflow Integration Triggers

| Workflow       | When NotebookLM RAG Helps                    |
| -------------- | -------------------------------------------- |
| `/plan`        | User says "ground this in my docs"           |
| `/deploy`      | User says "check deployment docs first"      |
| `/orchestrate` | User says "research before implementing"     |
| `/debug`       | User says "check if docs mention this error" |

---

## Research Modes

### Mode 1: Quick Query (Single Question)

**Trigger:** User asks a specific question with `@notebooklm` or "check my notebooks"

**Flow:**

```
1. Identify most relevant notebook (by topic match)
2. select_notebook → set active
3. ask_question → get grounded answer
4. Return synthesized response with source attribution
```

**Example:**

```
User: "@notebooklm how does our API handle rate limiting?"
Agent: Selects "API Documentation" notebook → queries → returns answer
```

### Mode 2: Deep Research (Multi-Question Investigation)

**Trigger:** User says "research", "investigate", "deep search"

**Flow:**

```
1. Identify relevant notebook(s)
2. Generate 3-5 research questions from user's intent
3. Execute iterative queries (each answer informs next question)
4. Synthesize findings into structured report
5. Present with confidence levels and source references
```

**Example:**

```
User: "Deep search: how should we migrate our auth system to OAuth 2.1?"
Agent:
  Q1: "What authentication methods are currently documented?"
  Q2: "What OAuth standards are mentioned in the architecture docs?"
  Q3: "Are there migration guides or breaking changes documented?"
  Q4: "What security requirements apply to the auth system?"
  Q5: "What dependencies exist on the current auth implementation?"
  → Synthesized migration plan grounded in actual documentation
```

### Mode 3: Cross-Reference (Multi-Notebook Query)

**Trigger:** User says "cross-reference", "check all notebooks", topic spans multiple notebooks

**Flow:**

```
1. list_notebooks → identify all potentially relevant notebooks
2. search_notebooks with topic keywords
3. Query top 2-3 relevant notebooks with same question
4. Compare and synthesize across sources
5. Flag contradictions or gaps
```

### Mode 4: Planning with Docs (Grounded Planning)

**Trigger:** User says "plan with docs", "use docs to plan", combined with `/plan`

**Flow:**

```
1. Understand planning objective
2. Research relevant documentation (Mode 2)
3. Generate plan grounded in documented constraints
4. Cite specific doc sections that inform each decision
5. Flag assumptions that AREN'T backed by documentation
```

---

## Research Protocol (B.L.A.S.T.)

When performing deep research, follow the **B.L.A.S.T.** protocol:

### B — Browse Library

```
1. list_notebooks → get full library
2. search_notebooks with keywords from user's query
3. Rank notebooks by relevance (topic match + description match)
4. Select top 1-3 notebooks for investigation
```

### L — Load Context

```
1. get_notebook for each selected notebook (check metadata)
2. select_notebook → set the primary research target
3. Start with broad context question: "What topics are covered in this notebook?"
```

### A — Ask Iteratively

```
1. Ask focused questions based on user's intent
2. Use session_id to maintain conversation context
3. Each answer → generate follow-up questions
4. Minimum 3 questions for deep research, 5+ for investigation
5. Track confidence in findings (documented vs. inferred)
```

### S — Synthesize

```
1. Compile all answers into structured findings
2. Organize by: Confirmed Facts | Inferences | Gaps
3. Cross-reference across notebooks if multiple were queried
4. Rate confidence: HIGH (direct docs) | MEDIUM (inferred) | LOW (not found)
```

### T — Transfer

```
1. Present findings in actionable format
2. Include source attribution (which notebook, which query)
3. Distinguish documented facts from assumptions
4. Suggest follow-up actions or remaining unknowns
```

---

## Session Management

### Session Strategy

| Research Type   | Session Approach                                   |
| --------------- | -------------------------------------------------- |
| Quick Query     | New session (no reuse needed)                      |
| Deep Research   | Single session with `session_id` for context chain |
| Cross-Reference | Separate session per notebook                      |
| Follow-up       | Reuse previous session_id if same topic            |

### Session Lifecycle

```python
# Deep research session flow
session_id = None  # Let first ask_question create a session

# Q1: Broad context
response_1 = ask_question(question="...", notebook_id="...", session_id=session_id)
session_id = extract_session_id(response_1)  # Reuse for follow-ups

# Q2-Q5: Iterative deep dive (same session = context accumulates)
response_2 = ask_question(question="...", session_id=session_id)
# ... etc

# Cleanup when done
close_session(session_id=session_id)
```

### Rate Limit Awareness

- **Free tier:** ~50 queries/day per Google account
- **Budget per research:** Reserve 5-8 queries for a deep research session
- **Optimization:** Batch related sub-questions into single compound questions
- **Fallback:** If rate limited, suggest `re_auth` to switch Google account

---

## Output Formats

### Quick Query Response

```markdown
📓 **NotebookLM Research** (notebook: "API Documentation")

**Answer:** [Grounded answer from NotebookLM]

**Confidence:** HIGH — Direct documentation match
**Source:** Query to "API Documentation" notebook
```

### Deep Research Report

```markdown
## 📓 Research Report: [Topic]

**Notebooks Consulted:** [list]
**Questions Asked:** [count]
**Session Duration:** [time]

### Confirmed Findings

1. [Finding with HIGH confidence] — _Source: [notebook]_
2. [Finding with HIGH confidence] — _Source: [notebook]_

### Inferred Insights

1. [Finding with MEDIUM confidence] — _Based on: [reasoning]_

### Knowledge Gaps

1. [What the docs DON'T cover]
2. [Areas needing additional documentation]

### Recommended Actions

1. [Action grounded in findings]
2. [Action to fill knowledge gaps]
```

---

## Integration with Other Skills

### With `qdrant-memory` (Complementary)

```
NotebookLM RAG produces deep findings
  → Store key findings in qdrant-memory as "technical" type
  → Future queries hit qdrant cache first (fast)
  → NotebookLM reserved for NEW research only
```

### With `/plan` Workflow

```
User: "/plan with docs: implement OAuth 2.1 migration"
  → notebooklm-rag researches constraints and patterns
  → plan-writing skill structures the plan
  → Each plan step cites documentation source
```

### With `/orchestrate` Workflow

```
User: "/orchestrate: comprehensive security review, check my docs"
  → notebooklm-rag provides documented security requirements
  → Orchestrator assigns specialist agents with doc-grounded context
```

### With `/debug` Workflow

```
User: "/debug: API returning 503, check if docs mention this"
  → notebooklm-rag searches for error handling documentation
  → Debugger uses findings to narrow investigation
```

---

## Best Practices

### DO ✅

- Use session_id for multi-question deep research
- Close sessions when research is complete
- Cite which notebook provided each finding
- Distinguish HIGH/MEDIUM/LOW confidence findings
- Batch related questions to conserve rate limit
- Store important findings in qdrant-memory for future speed
- Ask the user which notebook to target if multiple match

### DON'T ❌

- Auto-trigger without explicit user request
- Use all 50 daily queries on a single research task
- Present NotebookLM answers without source attribution
- Skip library search (don't assume which notebook to query)
- Mix findings from different notebooks without attribution
- Ignore rate limits (always budget queries)

---

## Troubleshooting

| Issue                   | Solution                                               |
| ----------------------- | ------------------------------------------------------ |
| "Not authenticated"     | Run `setup_auth` MCP tool → browser login              |
| "No notebooks found"    | Use `add_notebook` to add a NotebookLM share link      |
| Rate limited (50/day)   | Use `re_auth` to switch Google account                 |
| Wrong notebook selected | Use `list_notebooks` → `select_notebook` explicitly    |
| Session context lost    | Start new session — context doesn't persist across MCP |
| Vague answers           | Ask more specific questions, provide context in query  |
| "Not in docs"           | This is CORRECT behavior — the docs don't cover it     |

---

## Examples

### Example 1: Quick Infrastructure Query

```
User: "@notebooklm what ports does our Kafka cluster use?"

Agent:
1. search_notebooks(query="kafka infrastructure")
2. select_notebook(id="infra-docs")
3. ask_question(question="What ports does the Kafka cluster use and what are they for?")
4. Return formatted answer with notebook attribution
```

### Example 2: Deep Deployment Research

```
User: "Deep search: what's our rollback procedure for EKS deployments?"

Agent (B.L.A.S.T.):
1. BROWSE: list_notebooks → find "EKS Deployment", "Runbooks"
2. LOAD:   select_notebook("eks-deployment")
3. ASK:    5 iterative questions about rollback procedures
4. SYNTHESIZE: Compile into structured rollback guide
5. TRANSFER: Present with confidence ratings + gaps
```

### Example 3: Planning with Docs

```
User: "/plan with docs: migrate from Redis 6 to Redis 7"

Agent:
1. notebooklm-rag: Research current Redis configuration, known issues, migration notes
2. plan-writing: Structure migration plan grounded in documentation
3. Output: Plan where each step cites doc source + flags undocumented assumptions
```

---

## Configuration

### Environment Variables

No additional environment variables required beyond `notebooklm-mcp` skill setup.

### MCP Tools Used

This skill consumes the following MCP tools from the `notebooklm` server:

| Tool               | Used For                       |
| ------------------ | ------------------------------ |
| `ask_question`     | Core research queries          |
| `list_notebooks`   | Library discovery              |
| `search_notebooks` | Topic-based notebook selection |
| `select_notebook`  | Setting active research target |
| `get_notebook`     | Notebook metadata inspection   |
| `get_health`       | Pre-flight auth verification   |
| `list_sessions`    | Session management             |
| `close_session`    | Cleanup after research         |
| `reset_session`    | Clear session for new topic    |

---

## Important Notes

- **Explicit only**: This skill NEVER auto-triggers. Users must opt-in.
- **Complement, not replace**: Works alongside qdrant-memory, not instead of it.
- **Zero hallucination**: NotebookLM refuses answers not grounded in uploaded docs.
- **Rate awareness**: Always budget queries (50/day free tier).
- **EC Scoped**: Not included in public `@techwavedev/agi-agent-kit` distribution.
- **Dependency**: Requires `notebooklm-mcp` skill and MCP server to be configured.
