#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────
# publish.sh — Manual publish to NPM / GitHub Packages / Both
# Location: .tmp/publish.sh (gitignored, never shipped)
# Usage:    bash .tmp/publish.sh
# ─────────────────────────────────────────────────────────
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

VERSION=$(node -p "require('./package.json').version")
TAG="v${VERSION}"
REMOTE="public-repo"

echo ""
echo "╔══════════════════════════════════════════════════╗"
echo "║  📦 Publish @techwavedev/agi-agent-kit v${VERSION}     "
echo "╚══════════════════════════════════════════════════╝"
echo ""

# ── Step 1: Security Scan ──────────────────────────────
echo "🔍 Security scan..."
SENSITIVE=$(npm pack --dry-run 2>&1 | grep -iE "data/|auth_info|cookie|__pycache__|\.pyc|token\.json|credential" | grep -v "\.example" || true)
if [ -n "$SENSITIVE" ]; then
  echo "❌ BLOCKED: Sensitive files detected in package!"
  echo "$SENSITIVE"
  exit 1
fi
echo "   ✅ Clean — no sensitive files found"
echo ""

# ── Step 2: Choose target ─────────────────────────────
echo "📋 Where do you want to publish?"
echo ""
echo "   1) NPM only"
echo "   2) GitHub Packages only"
echo "   3) Both NPM + GitHub Packages"
echo "   4) Cancel"
echo ""
read -p "   Choose [1-4]: " CHOICE
echo ""

PUBLISH_NPM=false
PUBLISH_GITHUB=false

case "$CHOICE" in
  1) PUBLISH_NPM=true ;;
  2) PUBLISH_GITHUB=true ;;
  3) PUBLISH_NPM=true; PUBLISH_GITHUB=true ;;
  4|*) echo "❌ Aborted."; exit 0 ;;
esac

# ── Step 3: Confirm ───────────────────────────────────
echo "📋 Summary:"
echo "   • Version:  ${VERSION}"
echo "   • Tag:      ${TAG}"
echo "   • Branch:   $(git branch --show-current)"
$PUBLISH_NPM && echo "   • Target:   📦 NPM (npmjs.org)"
$PUBLISH_GITHUB && echo "   • Target:   🐙 GitHub Packages (npm.pkg.github.com)"
echo ""
read -p "   Proceed? (y/N) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
  echo "❌ Aborted."
  exit 0
fi
echo ""

# ── Step 4: Publish to NPM ────────────────────────────
if $PUBLISH_NPM; then
  echo "📦 Publishing to NPM..."
  npm publish --access public
  echo "   ✅ Published to NPM"
  echo ""
fi

# ── Step 5: Publish to GitHub Packages ─────────────────
if $PUBLISH_GITHUB; then
  echo "🐙 Publishing to GitHub Packages..."
  npm publish --registry=https://npm.pkg.github.com
  echo "   ✅ Published to GitHub Packages"
  echo ""
fi

# ── Step 6: Create GitHub Release ──────────────────────
echo "🏷️  Creating GitHub Release..."

if git rev-parse "$TAG" >/dev/null 2>&1; then
  echo "   Tag ${TAG} already exists, skipping tag creation"
else
  git tag "$TAG"
  echo "   Created tag ${TAG}"
fi
git push "$REMOTE" "$TAG" 2>/dev/null || echo "   Tag already pushed"

# Extract changelog section
CHANGELOG=$(awk "/^## .*${VERSION}/,/^## /" CHANGELOG.md | head -n -1 2>/dev/null || echo "Release v${VERSION}")
if [ -z "$CHANGELOG" ]; then
  CHANGELOG="Release v${VERSION}"
fi

gh release create "$TAG" \
  --repo "techwavedev/agi-agent-kit" \
  --title "$TAG" \
  --notes "$CHANGELOG" \
  2>/dev/null && echo "   ✅ GitHub Release created" \
  || echo "   ⚠️  Release may already exist (check GitHub)"
echo ""

# ── Step 7: Release branch snapshot ───────────────────
RELEASE_BRANCH="release/${TAG}"
if git show-ref --verify --quiet "refs/heads/${RELEASE_BRANCH}" 2>/dev/null; then
  echo "📌 Release branch ${RELEASE_BRANCH} already exists"
else
  git branch "$RELEASE_BRANCH" "$(git branch --show-current)"
  git push "$REMOTE" "$RELEASE_BRANCH"
  echo "📌 Created release branch: ${RELEASE_BRANCH}"
fi

echo ""
echo "╔══════════════════════════════════════════════════╗"
echo "║  ✅ All done! v${VERSION} published                   "
echo "╠══════════════════════════════════════════════════╣"
$PUBLISH_NPM && echo "║  NPM:      https://npmjs.com/package/@techwavedev/agi-agent-kit"
$PUBLISH_GITHUB && echo "║  GitHub:   https://github.com/techwavedev/agi-agent-kit/pkgs/npm/agi-agent-kit"
echo "║  Release:  https://github.com/techwavedev/agi-agent-kit/releases/tag/${TAG}"
echo "╚══════════════════════════════════════════════════╝"
