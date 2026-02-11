#!/bin/bash
set -e

# Configuration
PUBLIC_BRANCH="public"
MAIN_BRANCH="main"

# Private patterns to exclude/remove
PRIVATE_FILES=(
    ".agent"
    ".claude"
    ".gemini"
    "AGENTS.md"
    "CLAUDE.md"
    "GEMINI.md"
    "OPENCODE.md"
    "skills"
    "execution"
    "directives"
    "scripts"
    "skill-creator"
    "*.skill"
    "requirements.txt"
    "verify_public_release.py"
)

echo "🔍 DRY RUN: Release sync from $MAIN_BRANCH to $PUBLIC_BRANCH"
echo "============================================================"
echo ""

# Ensure clean state
if [[ -n $(git status -s) ]]; then
    echo "❌ Error: Working directory not clean. Please commit or stash changes."
    exit 1
fi

# Create a temporary branch for dry run
TEMP_BRANCH="dry-run-public-$(date +%s)"
echo "📋 Creating temporary branch: $TEMP_BRANCH"
git checkout -b $TEMP_BRANCH $PUBLIC_BRANCH

echo "📥 Merging changes from $MAIN_BRANCH..."
git merge $MAIN_BRANCH --no-commit --no-ff || true

echo ""
echo "🧹 Files that would be removed:"
echo "--------------------------------"
for pattern in "${PRIVATE_FILES[@]}"; do
    if git ls-files "$pattern" 2>/dev/null | grep -q .; then
        echo "   ❌ $pattern"
    fi
done

echo ""
echo "📊 Summary of changes:"
echo "----------------------"
git status -s | head -20
echo ""
if [ $(git status -s | wc -l) -gt 20 ]; then
    echo "   ... and $(($(git status -s | wc -l) - 20)) more files"
fi

echo ""
echo "📦 What would be in the NPM package:"
echo "------------------------------------"
npm pack --dry-run 2>&1 | grep "npm notice" | tail -20

echo ""
echo "🔄 Cleaning up dry run..."
git merge --abort 2>/dev/null || true
git checkout $MAIN_BRANCH
git branch -D $TEMP_BRANCH

echo ""
echo "✅ Dry run complete! No changes were made."
echo ""
echo "To actually release, run: bash scripts/release_to_public.sh"
