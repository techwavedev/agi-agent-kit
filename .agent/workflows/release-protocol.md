---
description: Comprehensive Release Protocol for Agi Agent Kit. Enforces documentation reviews, security scans, and version checks before any publish or public merge.
---

## Release Governance Protocol (MANDATORY)

> **⚠️ REPOSITORY MAP — Read before every release:**
>
> | Repo                        | Physical Location        | Purpose             | NPM Publish? |
> | --------------------------- | ------------------------ | ------------------- | ------------ |
> | `techwavedev/agi`           | `.` (Root Directory)     | Private development | ❌ NEVER     |
> | `techwavedev/agi-agent-kit` | `./public_release_repo/`      | Public distribution | ✅ YES       |
>
> **Flow:** `main` → Airgap Sync to `public_release_repo/` → commit & tag inside `public_release_repo/` → push to origin -> NPM auto-publishes

### 0. Private/Public Physical Separation (CRITICAL)

> **🚫 NEVER run `git merge` between private and public branches.**
> The repository uses a strict **Physical Airgap**. 
> The public release lives purely in the `public_release_repo/` directory.

```bash
# Sync public files from root to the public_release_repo/ airgap
python3 execution/publish_to_public.py --dry-run   # preview blocked private files
python3 execution/publish_to_public.py             # wipe and sync files securely
```

This script reads the `.private` manifest and explicitly omits those files
when copying to the `public_release_repo/` folder. The `.private` file at repo root is the
**single source of truth** for what must never appear on the public repository.

As a failsafe, the sync script dynamically executes `.agent/scripts/release_gate.py` ON the copied destination path BEFORE it commits, guaranteeing nothing slips through.

**Adding new private files?** Add the absolute or relative path to `.private` before syncing.

### 1. Preparation

- [ ] Ensure `CHANGELOG.md` is updated with all features/fixes.
- [ ] Ensure `package.json` version is bumped correctly (semver).
- [ ] Review `README.md` for any API changes.
- [ ] If you added new internal-only files, add them to `.private` manifest.

### 2. Manual Review

- [ ] Check if `AGENTS.md` reflects new capabilities.
- [ ] Verify `memory_integration.md` if memory system changed.
- [ ] Ensure no temporary files in `execution/` or `skills/` unless intended.

### 3. Publish (Automated via GitHub Actions)

**DO NOT RUN `npm publish` LOCALLY!** The NPM package is published securely and automatically via OIDC provenance by a GitHub Action when a new tag is pushed to the public repo.

To trigger the release:

1. Sync the files across the airgap:

```bash
python3 execution/publish_to_public.py
```

2. Change to the public repository directory:

```bash
cd public_release_repo
```

3. Tag the release and push:

```bash
git tag -a vX.Y.Z -m "Release vX.Y.Z"
git push origin public
git push origin vX.Y.Z
```

4. Create the release directly on the `techwavedev/agi-agent-kit` GitHub UI (or via `gh release create vX.Y.Z -R "techwavedev/agi-agent-kit"`). This will natively trigger `publish.yml` and handle the NPM rollout!
