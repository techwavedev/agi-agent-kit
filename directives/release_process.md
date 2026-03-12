# Release Process Directive

## Goal

Safely release a new version of the Agi Agent Kit to NPM and the public repository, ensuring all quality gates are passed.

## Inputs

- `package.json` (version to be released)
- `CHANGELOG.md` (release notes)
- Codebase state (must be clean)

## Execution Protocol (MANDATORY)

1. **Pre-Flight Check**:
   - Run `python3 .agent/scripts/release_gate.py`
   - If it fails, STOP. Fix issues. Do not bypass.

2. **Version Bump**:
   - Update `package.json` version.
   - Run `npm install` to update lockfile if needed.

3. **Changelog Update**:
   - Add new version header to `CHANGELOG.md`.
   - List all features, fixes, and breaking changes.

4. **Trigger Release**:
   - Push changes: `git push origin main`
   - Create a Release on GitHub matching `package.json` version (e.g., `v1.3.8`).
   - This triggers the `.github/workflows/publish.yml` action.
   - The action will run `release_gate.py` and publish to NPM automatically.

5. **Verify**:
   - Check Actions tab for success.
   - Check NPM for new version.

## Edge Cases

- **Gate Failure**: If `release_gate.py` finds secrets or syntax errors, they MUST be resolved.
- **Docs Missing**: If README is stale, update it before release.
