---
description: Publish new version to NPM with release branch snapshot
---

## Pre-Publish Checklist

1. Ensure all changes are committed and pushed to `public`
2. Run security check:

```bash
python3 verify_public_release.py
```

3. Verify package contents:

```bash
npm pack --dry-run 2>&1 | grep -iE "data/|auth_info|cookie|__pycache__|\.pyc|\.env" || echo "✅ Clean"
```

4. Update `CHANGELOG.md` with new version entry
5. Update version in `README.md` and `templates/base/README.md`
6. Bump version in `package.json`

## Publish

```bash
npm publish --access public
```

## Post-Publish: Create Release Branch

// turbo

```bash
git branch release/v$(node -p "require('./package.json').version") public
```

// turbo

```bash
git push origin release/v$(node -p "require('./package.json').version")
```

**Rule:** Every published version MUST have a corresponding `release/vX.Y.Z` branch as a frozen snapshot.

## Existing Release Branches

- `release/v1.2.6` — 2026-02-10
