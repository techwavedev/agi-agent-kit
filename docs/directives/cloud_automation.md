# Cloud Automation Directive

Pointer doc for `directives/cloud_automation.md`.

## Summary

Defines four automation tiers for the AGI Agent Kit:

| Tier | Method | When to Use |
|------|--------|-------------|
| 1 | **Local Agent** | Terminal-based, fully autonomous loops and scheduled tasks |
| 2 | **Cowork** | Desktop VM agent, reads local files, triggered via mobile or schedule |
| 3 | **Cloud Tasks** | 24/7 on Anthropic servers, survives laptop shutdown |
| 4 | **Channels** | Telegram/Discord remote control of local Claude Code |

All tiers share Qdrant memory for cross-session and cross-agent context.

## Key Integration Points

- **Worktree isolation**: Tier 1 uses `execution/worktree_isolator.py` for parallel agents
- **Cowork export**: `skills/cowork-export/scripts/export_context.py` packages git + memory + files
- **Cross-agent handoff**: `execution/cross_agent_context.py handoff` tracks delegation between tiers
- **Memory sync**: All tiers push results to Qdrant for downstream consumption

## Full Directive

See `directives/cloud_automation.md` for complete setup instructions, automation patterns, and edge cases.
