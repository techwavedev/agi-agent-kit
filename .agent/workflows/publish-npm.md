---
description: Full NPM publish workflow from dev to public release
---

# Publish NPM Workflow

## Pre-Conditions

- All changes committed on `main`
- Template synced and validated
- Agent team tests passing

## Steps

### 1. Sync Templates

// turbo

```bash
python3 execution/sync_to_template.py --sync
python3 execution/validate_template.py
```

### 2. Run Release Gate

// turbo

```bash
python3 .agent/scripts/release_gate.py
```

Fix any failures before proceeding. The release gate now includes the **Security Team** scan automatically.

### 3. Security Team Review (MANDATORY — blocks release)

Dispatch the security team for full review. This is also run inside the release gate, but dispatching the agent team gives you detailed sub-agent reports with handoff state.

```bash
python3 execution/dispatch_agent_team.py \
  --team security_team \
  --payload '{"changed_files": ["<list>"], "release_version": "vX.Y.Z", "release_type": "npm"}'
```

Then invoke each sub-agent in order:
1. `secret-scanner` — reads `directives/subagents/secret_scanner.md`
2. `dependency-auditor` — reads `directives/subagents/dependency_auditor.md`
3. `code-security-reviewer` — reads `directives/subagents/code_security_reviewer.md`

**Any ❌ from a sub-agent = STOP. Do not proceed to version bump.**

### 4. Bump Version

Edit `package.json` — follow patch-until-99 policy (see `versioning_rules.md`).

```bash
npm install  # update lockfile
```

### 5. Update CHANGELOG.md

Add version header and list all changes since last release.

### 6. Commit and Push to Main

```bash
git add package.json package-lock.json CHANGELOG.md
git commit -m "chore: bump version to vX.Y.Z"
git push origin main
```

### 7. Merge to Public Branch

```bash
git checkout public
git merge main
git push public-repo public
```

### 8. Create Release

```bash
git tag -a vX.Y.Z -m "Release vX.Y.Z"
git push public-repo vX.Y.Z
gh release create vX.Y.Z -R "techwavedev/agi-agent-kit" --title "vX.Y.Z" --notes "<changelog excerpt>"
```

This triggers `publish.yml` GitHub Action for NPM publish with OIDC provenance.

### 9. Verify

```bash
# Check GitHub Actions
gh run list -R "techwavedev/agi-agent-kit" --limit 1

# Check NPM (after action completes)
npm view @techwavedev/agi-agent-kit version
```

### 10. Store to Memory

```bash
python3 execution/memory_manager.py store \
  --content "Released vX.Y.Z to NPM: <summary>" \
  --type decision --project agi-agent-kit --tags release npm
```
