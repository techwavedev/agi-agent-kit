# evaluate_skill.py

Automated structural evaluation of skills against binary criteria.

## Purpose

Validates skill structure (SKILL.md, frontmatter, line count, scripts, naming) against a set of criteria. Stores results in Qdrant for cross-agent visibility and historical trend tracking.

## Usage

```bash
# Full evaluation with Qdrant storage
python3 skill-creator/scripts/evaluate_skill.py \
  --skill-path skills/pdf-reader \
  --test-input "Read this PDF and extract key points" \
  --criteria '["SKILL.md exists", "Has YAML frontmatter", "Under 200 lines"]' \
  --runs 3

# JSON output, skip Qdrant
python3 skill-creator/scripts/evaluate_skill.py \
  --skill-path skills/my-skill \
  --test-input "test" \
  --criteria '["Has required fields"]' \
  --json --no-store
```

## Arguments

| Flag | Required | Default | Description |
|------|----------|---------|-------------|
| `--skill-path` | Yes | - | Path to skill directory |
| `--test-input` | Yes | - | Test prompt / input description |
| `--criteria` | Yes | - | JSON array of binary criteria strings |
| `--runs` | No | `3` | Number of evaluation runs |
| `--project` | No | `agi-agent-kit` | Project name for Qdrant storage |
| `--json` | No | off | JSON-only output |
| `--no-store` | No | off | Skip storing results in Qdrant |

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | All criteria passed |
| 1 | Some criteria failed |
| 2 | Invalid arguments or skill path not found |
| 3 | Qdrant connection error (evaluation still runs) |
| 4 | Unexpected error |

## Built-in Checks

These criteria are matched automatically by name (case-insensitive partial match):

| Criterion | What It Checks |
|-----------|---------------|
| SKILL.md exists | `SKILL.md` file present in skill directory |
| Has YAML frontmatter | Valid `---` delimited YAML block at top of SKILL.md |
| Has required fields (name, description) | `name` and `description` in frontmatter |
| Under 200 lines (progressive disclosure) | SKILL.md line count <= 200 |
| Has scripts/ directory | `scripts/` subdirectory exists |
| Has references/ directory | `references/` subdirectory exists |
| Scripts are executable | Scripts have shebang or executable bit |
| Name follows hyphen-case convention | Frontmatter `name` is valid hyphen-case |

Custom criteria not matching a built-in check use a keyword heuristic against SKILL.md content.

## Qdrant Integration

- **Stores** evaluation results with type `evaluation`, tagged with skill name
- **Retrieves** historical evaluations to show trend (improved/declined/stable)
- Graceful degradation: evaluation runs even if Qdrant is unavailable

## Dependencies

- Qdrant at `QDRANT_URL` (default `http://localhost:6333`) -- optional
- Ollama at `OLLAMA_URL` (default `http://localhost:11434`) -- for embeddings, optional
- PyYAML -- optional (falls back to basic parser)
