---
description: Comprehensive Release Protocol for Agi Agent Kit. Enforces documentation reviews, security scans, and version checks before any publish or public merge.
---

## Release Governance Protocol (MANDATORY)

> **⚠️ REPOSITORY MAP — Read before every release:**
>
> | Repo                        | Remote        | Purpose             | NPM Publish? |
> | --------------------------- | ------------- | ------------------- | ------------ |
> | `techwavedev/agi`           | `origin`      | Private development | ❌ NEVER     |
> | `techwavedev/agi-agent-kit` | `public-repo` | Public distribution | ✅ YES       |
>
> **Flow:** `main` → filtered merge to `public` branch → push to `public-repo` → create release → NPM auto-publishes

### 0. Private/Public Separation (CRITICAL)

> **🚫 NEVER run `git merge main` on the public branch directly.**
> Use the filtered publish script instead:

```bash
git checkout public
python3 execution/publish_to_public.py --dry-run  # preview what would happen
python3 execution/publish_to_public.py --push      # merge + filter + push
```

This script reads `.private` manifest and automatically removes private-only files
after merging. The `.private` file at repo root is the **single source of truth** for
what must never appear on the public branch.

**Adding new private files?** Add the path to `.private` before committing.

Before merging to `public` branch or publishing the Github Actions release, execute this protocol.

### 1. Preparation

- [ ] Ensure `CHANGELOG.md` is updated with all features/fixes.
- [ ] Ensure `package.json` version is bumped correctly (semver).
- [ ] Review `README.md` for any API changes.
- [ ] If you added new internal-only files, add them to `.private` manifest.

### 2. Automated Gate

Run the Release Gate script to enforce checks:

```bash
python3 .agent/scripts/release_gate.py
```

This script will verify:

- Git status (clean working tree)
- Documentation presence
- Secret scanning (no API keys)
- **Private info leak detection** (repo URLs, usernames, NAS IPs)
- **Private-only file presence** (from `.private` manifest)
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

1. Checkout the `public` branch and run the filtered merge:

```bash
git checkout public
python3 execution/publish_to_public.py --push
```

2. Tag the release: `git tag -a vX.Y.Z -m "Release vX.Y.Z"`
3. Push the tag:

```bash
git push public-repo vX.Y.Z
```

4. Create the release directly on the `public-repo` GitHub UI (or via `gh release create vX.Y.Z -R "techwavedev/agi-agent-kit"`). This will natively trigger `publish.yml` and handle the NPM rollout!
