# Framework Development Directive

## Goal

Develop and maintain the AGI Agent Kit public framework (`templates/base/`) using the private repo's own 3-layer architecture. Eat your own dog food.

## Architecture

| Layer | Root | Public Distribution (templates/base/) |
|-------|---------------------|-------------------------------|
| Remote | `origin` | `techwavedev/agi-agent-kit` |
| Purpose | Development & orchestration | NPM distribution |
| Branch flow | `main` → tagged release → push to remote |

### Key Mapping: Root → Template

| Root Path | Template Path | Sync? |
|-----------|---------------|-------|
| `execution/` | `templates/base/execution/` | Yes — shared scripts |
| `directives/` | `templates/base/directives/` | Partial — only public SOPs |
| `.agent/rules/` | `templates/base/.agent/rules/` | Partial — only `core_rules.md`, `agent_team_rules.md` |
| `.agent/workflows/` | `templates/base/.agent/workflows/` | Partial |
| `skills/` | `templates/skills/core/` | Core skills only |
| `skill-creator/` | `templates/base/skill-creator/` | Yes — full sync |
| `data/` | `templates/base/data/` | Yes |
| `AGENTS.md` | `templates/base/AGENTS.md` | Yes — identical |

## Execution Protocol

### Adding a New Feature

1. **Query memory** for prior work on this area:
   ```bash
   python3 execution/memory_manager.py auto --query "<feature summary>"
   ```

2. **Implement** in root first (execution scripts, directives, etc.)

3. **Test locally** by running the scripts directly from root

4. **Sync to template** once validated:
   ```bash
   python3 execution/sync_to_template.py --check
   python3 execution/sync_to_template.py --sync
   ```

5. **Validate template** integrity:
   ```bash
   python3 execution/validate_template.py
   ```

6. **Dispatch doc team** (mandatory per agent_team_rules):
   ```bash
   python3 execution/dispatch_agent_team.py \
     --team documentation_team \
     --payload '{"changed_files": ["<list>"], "commit_msg": "<msg>", "change_type": "feat"}'
   ```

7. **Store to memory**:
   ```bash
   python3 execution/memory_manager.py store \
     --content "<what was built and why>" \
     --type decision --project agi-agent-kit --tags framework-dev
   ```

### Modifying Execution Scripts

Any change to `execution/*.py` must be reflected in `templates/base/execution/`:

1. Edit the root script
2. Run `python3 execution/sync_to_template.py --files execution/<script>.py`
3. Validate: `python3 execution/validate_template.py --check-scripts`

### Adding Skills

See `directives/skill_development.md` for the full skill creation SOP.

## Private-Only Files (NEVER sync to template)

- `directives/framework_development.md` (this file)
- `directives/template_sync.md`
- `directives/skill_development.md`
- `execution/sync_to_template.py`
- `execution/validate_template.py`
- `.agent/rules/framework_dev_rules.md`
- Any `.env`, credentials, or `.tmp/` files
- `skills/upstream-sync/` (internal sync tooling)

## Multi-LLM Development Protocol

When developing the framework, leverage ALL available agents via Qdrant shared memory.

### At Session Start

```bash
python3 execution/cross_agent_context.py sync --agent "<your-name>" --project agi-agent-kit
python3 execution/cross_agent_context.py pending --agent "<your-name>" --project agi-agent-kit
```

### After Implementing a Feature

```bash
# Share with team
python3 execution/cross_agent_context.py store \
  --agent "<your-name>" \
  --action "Implemented <feature>: <files changed>" \
  --project agi-agent-kit --tags framework-dev <feature-tag>

# If another agent should continue (e.g., tests, docs, review)
python3 execution/cross_agent_context.py handoff \
  --from "<your-name>" --to "<target>" \
  --task "Write tests for <feature>" \
  --context "Files: <list>. Key decisions: <summary>" \
  --project agi-agent-kit
```

### Breaking Changes

```bash
python3 execution/cross_agent_context.py broadcast \
  --agent "<your-name>" \
  --message "Breaking: <what changed and why>" \
  --project agi-agent-kit --tags breaking-change
```

See `directives/multi_llm_collaboration.md` for full collaboration patterns.

## Edge Cases

- **AGENTS.md divergence**: Root `AGENTS.md` is the source of truth. Always copy root → template, never the reverse.
- **Template has custom changes**: Run `--check` before `--sync` to see diffs. Preserve `<!-- AGI-INTEGRATION -->` blocks.
- **Script works in root but fails in template context**: Template paths are relative to project root. Ensure scripts use `__file__` or argument-based paths, not hardcoded absolute paths.
