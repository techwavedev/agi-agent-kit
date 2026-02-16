---
description: Comprehensive Release Protocol for Agi Agent Kit. Enforces documentation reviews, security scans, and version checks before any publish or public merge.
---

## Release Governance Protocol (MANDATORY)

Before merging to `public` branch or running `npm publish`, execute this protocol.

### 1. Preparation

- [ ] Ensure `CHANGELOG.md` is updated with all features/fixes.
- [ ] Ensure `package.json` version is bumped correctly (semver).
- [ ] Review `README.md` for any API changes.

### 2. Automated Gate

Run the Release Gate script to enforce checks:

```bash
python3 .agent/scripts/release_gate.py
```

This script will verify:

- Git status (clean working tree)
- Documentation presence
- Secret scanning (no API keys)
- Version consistency
- Python syntax validity

### 3. Manual Review

- [ ] Check if `AGENTS.md` reflects new capabilities.
- [ ] Verify `memory_integration.md` if memory system changed.
- [ ] Ensure no temporary files in `execution/` or `skills/` unless intended.

### 4. Publish

Only proceed if Step 2 passes.

```bash
npm publish --access public
```
