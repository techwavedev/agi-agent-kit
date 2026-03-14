# Skill Development Directive

## Goal

Create, test, and publish modular skills for the AGI Agent Kit framework.

## Skill Structure

```
skills/<skill-name>/
├── SKILL.md          # Frontmatter (name, description) + instructions
├── scripts/          # Deterministic tools
│   └── *.py
└── references/       # Documentation loaded on-demand
    └── *.md
```

## Creating a New Skill

### 1. Scaffold

```bash
python3 skill-creator/scripts/init_skill.py <name> --path skills/
```

### 2. Write SKILL.md

Required frontmatter:
```yaml
---
name: <skill-name>
description: "One-line description of what this skill does"
---
```

Body: triggers, execution steps, input/output, edge cases. Keep under 1,500 words.

### 3. Write Scripts

Follow `execution/` script conventions:
- CLI arguments via argparse
- JSON output on stdout
- Structured error output on stderr
- Exit codes: 0=success, 1=args, 2=not found, 3=network, 4=processing

### 4. Validate

```bash
python3 skill-creator/scripts/quick_validate.py skills/<name>
```

### 5. Update Catalog

```bash
python3 skill-creator/scripts/update_catalog.py --skills-dir skills/
```

### 6. Determine Tier

| Tier | Location | Ships with |
|------|----------|------------|
| Core | `templates/skills/core/` | All packs |
| Knowledge | `templates/skills/knowledge/` | Medium + Full |
| Extended | `templates/skills/extended/` | Full only |

### 7. Sync to Template

If core skill:
```bash
python3 execution/sync_to_template.py --files skills/<name>
```

If knowledge/extended: copy directly to `templates/skills/<tier>/<name>/`.

## Updating Existing Skills

1. Edit in `skills/` (root, not template)
2. Test the scripts directly
3. Sync to template
4. Update catalog

## Upstream Skills

Community skills from tracked forks. Use `upstream-sync` skill:
```bash
python3 skills/upstream-sync/scripts/sync_upstream.py --id <upstream-id> --dry-run
```

Review the report, then run without `--dry-run` to apply.

## Edge Cases

- **Skill name collision**: Check `SKILLS_CATALOG.md` before naming.
- **Script depends on external API**: Document required env vars in SKILL.md and `.env.example`.
- **Large reference docs**: Split into multiple files in `references/`. Only load what's needed.
