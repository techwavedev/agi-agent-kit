# NotebookLM RAG — Research Patterns & Workflows

## Quick Reference: Research Modes

### Mode Decision Matrix

| User Intent                          | Mode        | Queries | Session Strategy      |
| ------------------------------------ | ----------- | ------- | --------------------- |
| Single specific question             | `quick`     | 1       | New session           |
| "Research X", "Investigate Y"        | `deep`      | 3-5     | Reuse session_id      |
| "Compare across docs", "All sources" | `cross-ref` | 2-6     | Separate per notebook |
| "Plan based on docs"                 | `plan`      | 3-5     | Reuse session_id      |

---

## Workflow Templates

### Template 1: Quick Query

```
Agent Workflow:
├── 1. get_health → verify auth
├── 2. search_notebooks(query=<keywords>) → find best match
├── 3. select_notebook(id=<best_match>)
├── 4. ask_question(question=<user_query>)
└── 5. Format response with notebook attribution
```

### Template 2: Deep Research (B.L.A.S.T.)

```
Agent Workflow:
├── B. BROWSE
│   ├── list_notebooks → get full library
│   └── search_notebooks(query=<keywords>) → rank by relevance
├── L. LOAD
│   ├── select_notebook(id=<top_match>)
│   └── ask broad context question (session starts)
├── A. ASK (3-5 iterations, reuse session_id)
│   ├── Q1: Coverage — "What topics are covered about X?"
│   ├── Q2: Details — "What are the technical specifics of X?"
│   ├── Q3: Risks — "What constraints or issues exist for X?"
│   ├── Q4: Dependencies — "What systems connect to X?"
│   └── Q5: Synthesis — "What's the recommended approach for X?"
├── S. SYNTHESIZE
│   ├── Compile answers into Confirmed | Inferred | Gaps
│   └── Assign confidence: HIGH | MEDIUM | LOW
└── T. TRANSFER
    ├── Present structured report
    ├── Close session (close_session)
    └── Optionally store in qdrant-memory for future cache
```

### Template 3: Cross-Reference

```
Agent Workflow:
├── 1. list_notebooks → find all potentially relevant notebooks
├── 2. For each relevant notebook:
│   ├── select_notebook(id=<notebook_id>)
│   ├── ask_question(question=<same_question>)
│   └── Record answer + source
├── 3. Compare answers across notebooks
│   ├── Identify agreements
│   ├── Flag contradictions
│   └── Note coverage gaps
└── 4. Present synthesis with per-notebook attribution
```

### Template 4: Planning with Docs

```
Agent Workflow:
├── 1. Deep Research on topic (Template 2)
├── 2. For each plan step:
│   ├── Cite supporting documentation
│   ├── Flag steps WITHOUT doc backing (assumptions)
│   └── Note relevant constraints from docs
├── 3. Risk assessment grounded in doc findings
│   ├── Documented risks → HIGH confidence
│   ├── Inferred risks → MEDIUM confidence
│   └── Unknown risks → flagged for investigation
└── 4. Output: Plan with [DOC] and [ASSUMPTION] markers
```

---

## Query Optimization Patterns

### Compound Questions (Rate Limit Saver)

Instead of asking 3 separate questions:

```
❌ "What ports does Kafka use?"
❌ "What security is configured for Kafka?"
❌ "What monitoring exists for Kafka?"
```

Combine into one:

```
✅ "What are the ports, security configuration, and monitoring setup documented for the Kafka cluster?"
```

### Context-Building Questions

Start broad, then narrow:

```
Q1: "What is documented about the authentication system?" (broad)
Q2: "What OAuth flows are mentioned?" (narrow based on Q1)
Q3: "What are the session management details for the OAuth PKCE flow?" (specific based on Q2)
```

### Negative Questions (Finding Gaps)

```
"Is there any documentation about disaster recovery procedures for the database?"
→ If answer is "No relevant information found" → this is a confirmed gap
```

---

## Integration Patterns

### NotebookLM RAG → Qdrant Memory Pipeline

After a deep research session, store key findings for future speed:

```python
# After research report is generated
for finding in high_confidence_findings:
    qdrant_store_memory(
        content=finding["answer"],
        metadata={
            "type": "technical",
            "source": "notebooklm-rag",
            "notebook": finding["notebook"],
            "topic": research_topic,
            "confidence": "HIGH",
            "date": "2026-02-07",
        }
    )
```

Next time the same topic is queried:

1. `qdrant-memory` finds the cached finding → instant response
2. NotebookLM is only consulted for NEW questions

### With Agent Workflows

```
/plan + @notebooklm:
  → notebooklm-rag runs B.L.A.S.T. research first
  → plan-writing receives doc-grounded context
  → Each plan step marked with [DOC] or [ASSUMPTION]

/debug + @notebooklm:
  → Agent checks docs for known error patterns
  → Documented fix → apply directly
  → Undocumented → standard debug workflow

/orchestrate + @notebooklm:
  → Research phase uses notebooklm-rag
  → Specialist agents receive doc context
  → Findings cited in orchestrator's synthesis
```

---

## Rate Limit Strategy

### Budget Planning

| Research Type | Queries Needed | Sessions Remaining (of 50) |
| ------------- | -------------- | -------------------------- |
| Quick Query   | 1              | 49                         |
| Deep Research | 5              | 45                         |
| Cross-Ref (3) | 6              | 39                         |
| Planning      | 5              | 34                         |

### Multi-Account Strategy

If you hit the daily limit:

1. `re_auth` → Switch to another Google account
2. Notebooks are tied to Google account, so shared notebooks work across accounts
3. Library metadata is local (preserved across re-auth if `preserve_library=true`)

---

## Error Handling

| Error                     | Recovery                                          |
| ------------------------- | ------------------------------------------------- |
| "Not authenticated"       | `setup_auth` → browser login                      |
| Rate limit reached        | `re_auth` → switch account                        |
| "No notebooks found"      | `add_notebook` → add share link                   |
| Session timeout           | Start new session (context lost)                  |
| Vague or unhelpful answer | Rephrase with more specific keywords              |
| "Not in documentation"    | This is CORRECT — document the gap                |
| Browser crash             | `cleanup_data(preserve_library=true)` → `re_auth` |
