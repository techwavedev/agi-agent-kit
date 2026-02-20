---
description: Comprehensive Release Protocol for Agi Agent Kit. Enforces documentation reviews, security scans, and version checks before any publish or public merge.
---

## Release Governance Protocol (MANDATORY)

Before merging to `public` branch or publishing the Github Actions release, execute this protocol.

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

### 4. Publish (Automated via GitHub Actions)

Only proceed if Step 2 passes.

**DO NOT RUN `npm publish` LOCALLY!** The NPM package is published securely and automatically via OIDC provenance by a GitHub Action when a new release is published to the `public-repo` remote.

To trigger the release:

1. Checkout the `public` branch and ensure it is synced with `main`.
2. Tag the release: `git tag -a vX.Y.Z -m "Release vX.Y.Z"`
3. Push everything to the **public** remote:

```bash
git push public-repo public
git push public-repo vX.Y.Z
```

4. Create the release directly on the `public-repo` GitHub UI (or via `gh release create vX.Y.Z -R "techwavedev/agi-agent-kit"`). This will natively trigger `publish.yml` and handle the NPM rollout!
