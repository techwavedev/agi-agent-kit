# Multi-LLM Collaboration Directive

## Goal

Enable all AI agents (Claude, Antigravity/Gemini, Cursor, Copilot, OpenCode, OpenClaw) to collaborate on the AGI Agent Kit framework via shared Qdrant memory and structured handoffs.

## Architecture

```
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│    Claude     │  │ Antigravity  │  │   Cursor     │
│  (CLAUDE.md)  │  │ (GEMINI.md)  │  │ (AGENTS.md)  │
└──────┬───────┘  └──────┬───────┘  └──────┬───────┘
       │                 │                 │
       └────────────┬────┴────────────────┘
                    │
              ┌─────▼─────┐
              │   Qdrant   │  ← Shared semantic memory
              │ :6333      │  ← All agents read/write here
              └─────┬──────┘
                    │
              ┌─────▼─────┐
              │   Ollama   │  ← Shared embeddings
              │ :11434     │  ← nomic-embed-text
              └────────────┘
```

All agents share the SAME Qdrant instance and embedding model. Context flows between agents via tagged memory entries.

## Agent Registry

| Agent | Instruction File | Primary Role |
|-------|-----------------|--------------|
| `claude` | CLAUDE.md | Orchestration, complex reasoning, code review |
| `antigravity` | GEMINI.md | Research, multi-modal, large context tasks |
| `gemini` | GEMINI.md | Same as antigravity (alias) |
| `cursor` | AGENTS.md | IDE-integrated coding, fast iteration |
| `copilot` | COPILOT.md | Code completion, inline suggestions |
| `opencode` | OPENCODE.md | Terminal-based coding, CI/CD tasks |
| `openclaw` | OPENCLAW.md | Specialized domain tasks |

## Session Protocol (MANDATORY for every agent)

### 1. Boot & Check Pending

```bash
# Boot memory
python3 execution/session_boot.py --auto-fix

# Check what other agents have done
python3 execution/cross_agent_context.py sync --agent "<your-name>" --project agi-agent-kit

# Check if anyone handed you a task
python3 execution/cross_agent_context.py pending --agent "<your-name>" --project agi-agent-kit
```

### 2. During Work — Share Context

After key decisions or completing subtasks:

```bash
# Store your work for the team
python3 execution/cross_agent_context.py store \
  --agent "<your-name>" \
  --action "What you did" \
  --project agi-agent-kit \
  --tags relevant-tag1 relevant-tag2
```

### 3. Hand Off Work

When a task needs another agent's capabilities:

```bash
python3 execution/cross_agent_context.py handoff \
  --from "<your-name>" --to "<target>" \
  --task "Task description" \
  --context "File paths, decisions, current state" \
  --project agi-agent-kit
```

### 4. Broadcast Team-Wide Updates

For decisions that affect all agents:

```bash
python3 execution/cross_agent_context.py broadcast \
  --agent "<your-name>" \
  --message "Breaking change: memory_manager.py now requires --project flag" \
  --project agi-agent-kit \
  --tags breaking-change memory
```

## Collaboration Patterns

### Pattern 1: Sequential Handoff

Agent A completes phase 1 → hands off to Agent B for phase 2.

```
Claude: implement execution script
  → handoff to Antigravity: "Write tests and documentation"
    → handoff to Cursor: "Integrate into IDE workflow"
```

### Pattern 2: Parallel Work

Multiple agents work on independent domains simultaneously, sharing via Qdrant.

```
Claude: execution scripts (store decisions to Qdrant)
Antigravity: skills development (reads Claude's decisions from Qdrant)
Cursor: IDE integration (reads both agents' context from Qdrant)
```

### Pattern 3: Review Chain

One agent writes, another reviews, via team dispatch + cross-agent handoff.

```
Claude: implement feature
  → dispatch code_review_team (local sub-agents)
  → handoff to Antigravity: "Validate against upstream patterns"
  → broadcast: "Feature X merged, all agents update your context"
```

### Pattern 4: Cache Distribution

Agent A solves a problem → caches response → all agents benefit.

```bash
# Agent A stores the solution
python3 execution/memory_manager.py cache-store \
  --query "How to handle rate limits in scrape_single_site.py" \
  --response "Use exponential backoff with max 3 retries..."

# Agent B (hours later) hits cache automatically
python3 execution/memory_manager.py auto --query "rate limit handling in scraping"
# Returns cache_hit: true → 100% token savings
```

## Qdrant Memory Tags Convention

All cross-agent entries use structured tags for filtering:

| Tag | Purpose |
|-----|---------|
| `cross-agent` | Marks entry as cross-agent (always present) |
| `agent:<name>` | Who created it |
| `for:<name>` | Who it's intended for (handoffs) |
| `handoff` | Task handoff between agents |
| `broadcast` | Team-wide announcement |
| `framework-dev` | Framework development context |
| `upstream-sync` | Upstream synchronization context |
| `release` | Release-related decisions |

## Pattern 5: Parallel Worktree Isolation (Same Machine)

When multiple agents work on the same repo from the same machine, use **git worktrees** to prevent conflicts. Each agent gets an isolated copy of the repo on a separate branch.

```
Orchestrator
  ├─ worktree_isolator.py create-all --agents '["claude-1", "gemini-1"]'
  │     ├── /tmp/agi-worktrees/<project>/<run-id>-claude-1/  (branch: worktree/<run-id>/claude-1)
  │     └── /tmp/agi-worktrees/<project>/<run-id>-gemini-1/  (branch: worktree/<run-id>/gemini-1)
  ├─ Dispatch agents to their worktree directories (in parallel)
  ├─ Wait for completion
  ├─ worktree_isolator.py merge-all --run-id <run-id>
  └─ worktree_isolator.py cleanup (remove worktrees + branches)
```

### Key Rules

1. **Validate partitions first** — Before parallel dispatch, check that agents won't edit the same files:
   ```bash
   python3 execution/worktree_isolator.py validate-partitions \
     --partitions '{"agent-1": ["src/api/**"], "agent-2": ["src/ui/**"]}'
   ```
2. **`.env` auto-copied** — `worktree_isolator.py` automatically copies `.env` from the repo root into each new worktree.
3. **Merge sequentially** — After all agents finish, merge branches back one at a time to catch conflicts early.
4. **Never push worktree branches to main** — Always push to a named branch, then PR.

### Claude Code Integration

Claude Code's Agent tool supports `isolation: "worktree"` natively:
```
Agent(prompt="Task description", isolation="worktree")
```

### dispatch_agent_team.py --parallel

```bash
python3 execution/dispatch_agent_team.py \
  --team my_team \
  --payload '{"task": "..."}' \
  --parallel \
  --partitions '{"agent-1": ["src/api/**"], "agent-2": ["tests/**"]}'
```

This auto-creates worktrees, validates partitions, and enriches the manifest with worktree paths per sub-agent.

## Edge Cases

- **Qdrant down**: All agents fall back to local-only mode. Sync when Qdrant recovers.
- **Conflicting decisions**: Last-write-wins. If two agents decide differently, the most recent Qdrant entry takes precedence. Broadcast to resolve.
- **Agent not available**: Handoffs persist in Qdrant indefinitely. The target agent picks them up whenever it starts a session.
- **Stale context**: Use `--hours` flag on sync to limit lookback window (default 24h).
- **Worktree merge conflict**: `merge-all` aborts the conflicting merge, reports which agents conflict, and continues merging the rest. Resolve manually.
- **Orphaned worktrees**: Run `python3 execution/worktree_isolator.py status` to find stale worktrees, then `cleanup` them.
