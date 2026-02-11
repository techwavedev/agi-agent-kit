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

echo "🚀 Starting release sync from $MAIN_BRANCH to $PUBLIC_BRANCH..."

# Ensure clean state
if [[ -n $(git status -s) ]]; then
    echo "❌ Error: Working directory not clean. Please commit or stash changes."
    exit 1
fi

# Switch to public and merge main
echo "twisted: Switching to $PUBLIC_BRANCH..."
git checkout $PUBLIC_BRANCH
git pull origin $PUBLIC_BRANCH

echo "twisted: Merging changes from $MAIN_BRANCH..."
# Merge without committing to allow cleanup
git merge $MAIN_BRANCH --no-commit --no-ff || true

echo "🧹 Sanitizing private files..."
# Remove private files from the index and working directory
for pattern in "${PRIVATE_FILES[@]}"; do
    echo "   - Removing $pattern..."
    git rm -rf "$pattern" 2>/dev/null || true
    rm -rf "$pattern" 2>/dev/null || true
done

# Check status
echo "📋 Status checks:"
git status -s

echo "❓ Ready to commit and push? (y/n)"
read -r response
if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    echo "💾 Committing RELEASE..."
    # You might want to grab the version from package.json
    VERSION=$(grep '"version":' package.json | cut -d'"' -f4)
    git commit -m "chore: release v$VERSION (sync from main)"
    
    echo "⬆️ Pushing to origin..."
    git push origin $PUBLIC_BRANCH
    
    echo "✅ Done! You can now run .tmp/publish.sh"
else
    echo "❌ Aborted. You are still on $PUBLIC_BRANCH with uncommitted changes."
fi
