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

4. **Git Commit**:
   - Commit changes: `git commit -m "chore(release): vX.Y.Z"`
   - Tag version: `git tag vX.Y.Z`

5. **Publish**:
   - Run `npm publish --access public`
   - (The `prepublishOnly` hook will run `release_gate.py` again automatically).

6. **Push**:
   - `git push origin main --tags`

## Edge Cases

- **Gate Failure**: If `release_gate.py` finds secrets or syntax errors, they MUST be resolved.
- **Docs Missing**: If README is stale, update it before release.
