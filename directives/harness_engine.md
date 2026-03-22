# Agent Harness Engine

> Full-stack agent execution harness with Langfuse observability, state management,
> sandboxed execution, context compression, validation loops, and multi-agent fan-out.

## 8 Pillars

### 1. Langfuse Observability (AI Automators pattern)
- Session-level trace per conversation (created at SessionStart hook)
- Automatic span per tool call (PreToolUse opens, PostToolUse closes)
- Generation tracking for LLM API calls (`langfuse_model_proxy.py`)
- Scoring: cache_hit, retrieval_quality, compression_ratio, tool_error
- Cost/token tracking, latency percentiles
- Dashboard: `langfuse_dashboard.py overview|compare|traces|errors|slow`

### 2. State Management (inside the harness)
- File-based state protocol: `.tmp/harness_state.json`
- Session state: trace_id, span stack, open tasks, current phase
- State machine: `init → planning → executing → validating → complete`
- Rollback on failure, orphan cleanup at session end

### 3. Human-in-the-Loop + Fan-Out via Pulsar
- Qdrant shared memory: pull/push for cross-agent context
- Pulsar message bus (`docker-compose.pulsar.yml`) for fan-out
- Any agent (Gemini, Cursor, Copilot) picks up work, executes, pushes results
- Human approval gates via Telegram channel or CLI

### 4. Orchestrator on Powerful Models
- Planning + orchestration → Opus (expensive, accurate)
- Execution/sub-tasks → Haiku/Sonnet (cheap, fast)
- `langfuse_model_proxy.py` records every generation with model/tokens/cost
- Dashboard shows cost breakdown by model

### 5. Sandboxed Execution
- Commands run in Docker containers (`fastapi_tool_bridge.py` pattern)
- Harness validates outputs before state changes
- Destructive command blocking, timeout enforcement
- Subprocess isolation for untrusted code

### 6. Context Management + Compression
- Sub-agents get minimal relevant context (not full conversation)
- Qdrant retrieves relevant memory chunks before delegation
- Summary generation (cheap model) before sending to sub-agent
- Progressive disclosure: task + relevant chunks only

### 7. Context Isolation + Sharing
- Each hook/sub-agent: isolated context (no pollution)
- Shared state only via: Qdrant, `.tmp/` state files, Pulsar messages
- Trace IDs via env vars for Langfuse correlation
- `cross_agent_context.py` for explicit cross-agent sharing

### 8. Validation Loops
- Every sub-agent output → validate → retry or escalate
- Binary assertions (Karpathy loop pattern)
- Human-in-the-loop for subjective validation
- Pass/fail tracked in Langfuse scores

---

## Architecture

```
Harness Engine (execution/harness_engine.py)
├── State Machine (.tmp/harness_state.json)
├── Langfuse Tracing (execution/langfuse_harness.py)
│   ├── Session trace (1 per conversation)
│   ├── Tool spans (auto via hooks)
│   ├── Generation tracking (LLM calls)
│   └── Scoring (cache, quality, errors)
├── Context Manager
│   ├── Qdrant retrieval (relevant chunks only)
│   ├── Summary compression (cheap model)
│   └── Progressive disclosure
├── Orchestrator
│   ├── Plan (Opus)
│   ├── Delegate (Haiku/Sonnet)
│   ├── Validate (assertions + human gate)
│   └── Score + next step
├── Sandbox Executor
│   ├── Docker container isolation
│   ├── fastapi_tool_bridge.py
│   └── Output validation
└── Fan-Out (Pulsar + Qdrant)
    ├── Message publish (task dispatch)
    ├── Agent subscribe (Gemini/Cursor/Copilot)
    ├── Result collection
    └── Human-in-the-loop gates
```

## Trace Hierarchy

```
Session Trace (session_id=s-xxx)
├── Span: Read (CLAUDE.md)                    [auto: hook]
├── Span: Bash (memory_manager.py auto ...)   [auto: hook]
│   ├── Span: cache_check                     [harness: child]
│   ├── Span: memory_retrieve                 [harness: child]
│   │   └── Span: embed_generate              [harness: child]
│   └── Score: cache_hit=0.0
├── Span: Edit (file.py)                      [auto: hook]
├── Span: Bash (summarize.py --model haiku)   [auto: hook]
│   └── Generation: claude-haiku (200→50 tok) [model proxy]
├── Span: Bash (validate.py --assertions ...) [auto: hook]
│   └── Score: validation_pass=1.0
└── Session Scores: memories=3, tools=15, cost=$0.003
```

## State File Protocol

### Session state: `.tmp/langfuse_session.json`
```json
{
  "trace_id": "lf-abc123",
  "session_id": "s-1711100000",
  "started_at": "2026-03-22T20:16:24Z",
  "phase": "executing",
  "tool_call_count": 0,
  "spans_open": 0
}
```

### Span state: `.tmp/langfuse_spans/{tool}_{hash}.json`
```json
{
  "span_id": "lf-span-xyz",
  "trace_id": "lf-trace-abc",
  "tool_name": "Read",
  "start_time": 1711100001.234,
  "input_summary": {"file_path": "/path/to/file.py"}
}
```

## Implementation Phases

### Phase 1: Core Harness + Langfuse Tracing
1. `execution/langfuse_harness.py` — state file protocol, span lifecycle
2. Hook integration: SessionStart → init trace, PreToolUse → open span, PostToolUse → close span
3. Expand `settings.json` PreToolUse matcher to all tool types
4. `session_boot.py` auto-starts Langfuse docker
5. `session_wrapup.py` end_session() with scores + flush

### Phase 2: Context Management + Compression
6. `execution/harness_context.py` — Qdrant-powered context retrieval for sub-agents
7. Summary compression before delegation (cheap model)
8. Progressive disclosure: task + chunks → sub-agent

### Phase 3: Sandboxed Execution + Validation
9. Extend `fastapi_tool_bridge.py` for harness-controlled sandbox
10. `execution/harness_validator.py` — assertion-based validation loops
11. Human-in-the-loop gates (Telegram integration)

### Phase 4: Fan-Out via Pulsar
12. Pulsar producer/consumer in harness
13. Task dispatch to remote agents
14. Result collection + merge
15. Cross-agent state sync via Qdrant + Pulsar

## Key Scripts

| Script | Purpose |
|--------|---------|
| `execution/harness_engine.py` | Main orchestrator: plan → delegate → validate → score |
| `execution/langfuse_harness.py` | Trace/span lifecycle, state files, cross-process sharing |
| `execution/langfuse_tracing.py` | Singleton client, health check, metrics API |
| `execution/langfuse_dashboard.py` | CLI dashboard: overview, compare, traces, errors, slow |
| `execution/langfuse_model_proxy.py` | LLM call wrapper with generation tracking |
| `execution/harness_context.py` | Qdrant retrieval + summary compression for sub-agents |
| `execution/harness_validator.py` | Assertion-based validation loops |