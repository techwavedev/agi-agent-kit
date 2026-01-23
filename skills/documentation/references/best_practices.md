# Documentation Best Practices

Best practices and patterns for maintaining synchronized documentation across the codebase.

---

## Documentation Standards

### Python Docstrings

Follow Google-style docstrings for all Python code:

```python
def function_name(param1: str, param2: int) -> bool:
    """Brief one-line description.

    Longer description if needed. Can span multiple lines
    and include additional context.

    Args:
        param1: Description of first parameter.
        param2: Description of second parameter.

    Returns:
        Description of return value.

    Raises:
        ValueError: When param1 is empty.

    Example:
        >>> function_name("test", 42)
        True
    """
```

### Script Documentation

Every executable script should include:

1. **Module docstring** with:
   - Purpose/description
   - Usage example
   - Arguments list
   - Exit codes

2. **Function docstrings** for public functions

3. **Comments** for complex logic

Example:

```python
#!/usr/bin/env python3
"""
Script Name - Brief Description

Longer description of what the script does and when to use it.

Usage:
    python script_name.py --arg1 <value> [options]

Arguments:
    --arg1      Description (required)
    --verbose   Enable verbose output (optional)

Exit Codes:
    0 - Success
    1 - Invalid arguments
    2 - Runtime error
"""
```

---

## SKILL.md Structure

### Required Sections

1. **Frontmatter** (YAML)

   ```yaml
   ---
   name: skill-name
   description: "Comprehensive description with trigger keywords..."
   ---
   ```

2. **Title and Overview** - Brief introduction

3. **Quick Start** - Immediate usage examples

4. **Core Workflow** - Step-by-step process

5. **Scripts** - All scripts with usage

6. **Configuration** - Relevant settings

7. **Common Workflows** - Real-world examples

### Optional Sections

- **Troubleshooting** - Common issues and solutions
- **Dependencies** - Required packages
- **Related Skills** - Links to related skills
- **External Resources** - Helpful links

---

## Changelog Format

Follow [Keep a Changelog](https://keepachangelog.com/) format:

```markdown
## [Unreleased]

### Added

- New feature description

### Changed

- Modified behavior description

### Deprecated

- Soon-to-be-removed feature

### Removed

- Removed feature description

### Fixed

- Bug fix description

### Security

- Security improvement description
```

---

## Update Triggers

Document when documentation must be updated:

| Code Change                | Documentation Update              |
| -------------------------- | --------------------------------- |
| New script added           | SKILL.md scripts section, catalog |
| Script renamed/removed     | SKILL.md, catalog                 |
| New skill created          | SKILLS_CATALOG.md                 |
| Skill description changed  | SKILLS_CATALOG.md                 |
| New reference added        | SKILL.md references section       |
| Function signature changed | Docstrings, usage examples        |
| Breaking change            | Changelog, migration notes        |

---

## Automation Integration

### Git Hooks (optional)

Pre-commit hook to check documentation:

```bash
#!/bin/bash
# .git/hooks/pre-commit

# Check for SKILL.md in skill directories
for skill_dir in skills/*/; do
    if [ ! -f "${skill_dir}SKILL.md" ]; then
        echo "Error: Missing SKILL.md in $skill_dir"
        exit 1
    fi
done
```

### CI Integration (optional)

Add to CI pipeline:

```yaml
documentation-check:
  script:
    - python skills/documentation/scripts/detect_changes.py --scope skills/ --since HEAD~1
    - python skill-creator/scripts/update_catalog.py --skills-dir skills/
```

---

## Quality Checklist

Before committing documentation:

- [ ] All scripts have module docstrings
- [ ] SKILL.md has complete frontmatter
- [ ] Quick Start examples are tested and working
- [ ] Related skills are cross-referenced
- [ ] Changelog entry added for significant changes
- [ ] SKILLS_CATALOG.md is updated
- [ ] Timestamps are current
