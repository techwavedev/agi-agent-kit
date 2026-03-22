# Cowork Export Patterns

## Common Delegation Scenarios

### 1. Code Review
```bash
python3 skills/cowork-export/scripts/export_context.py \
  --task "Review the diff for bugs, security issues, and style. Provide line-specific feedback." \
  --compact --clipboard
```

### 2. Test Generation
```bash
python3 skills/cowork-export/scripts/export_context.py \
  --task "Write unit tests for the changed files. Use pytest. Cover edge cases." \
  --include-files <changed-files> \
  --clipboard
```

### 3. Documentation Draft
```bash
python3 skills/cowork-export/scripts/export_context.py \
  --task "Write user-facing documentation for the new features in this diff." \
  --compact --clipboard
```

### 4. Architecture Review
```bash
python3 skills/cowork-export/scripts/export_context.py \
  --task "Evaluate this architecture. Identify coupling issues, suggest improvements." \
  --include-files src/main.py src/config.py \
  --constraints "Must remain backward compatible with v2 API" \
  --clipboard
```

### 5. Research Task
```bash
python3 skills/cowork-export/scripts/export_context.py \
  --git-only \
  --task "Research best practices for implementing rate limiting in Python async APIs. Return a comparison of approaches." \
  --priority high \
  --deadline "2026-03-23" \
  --clipboard
```

## Re-importing Results

When the remote agent completes work, feed results back to the local session:

```bash
# Store the result as a memory for continuity
python3 execution/memory_manager.py store \
  --content "Cowork result: <paste summary here>" \
  --type decision \
  --project <project-name> \
  --tags cowork-result

# Mark the handoff as completed
python3 execution/cross_agent_context.py store \
  --agent "cowork" \
  --action "Completed: <task summary>" \
  --project <project-name> \
  --tags cowork-result
```

## Size Guidelines

| Context Type | Typical Size | Cowork Limit |
|-------------|-------------|--------------|
| Git diff (small PR) | 500-2000 chars | Fine |
| Git diff (large PR) | 5000-15000 chars | Truncated at 15k |
| Qdrant memory (10 chunks) | 2000-5000 chars | Fine |
| Inline file (1 file) | 1000-10000 chars | Truncated at 10k |
| Full briefing | 3000-25000 chars | Aim for <20k |

Keep briefings under 20k characters for best results in Claude's web interface.
