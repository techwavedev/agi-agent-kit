---
name: upgrading-expo
description: "Upgrade Expo SDK versions"
source: "https://github.com/expo/skills/tree/main/plugins/upgrading-expo"
risk: safe
---

# Upgrading Expo

## Overview

Upgrade Expo SDK versions safely, handling breaking changes, dependencies, and configuration updates.

## When to Use This Skill

Use this skill when you need to upgrade Expo SDK versions.

Use this skill when:
- Upgrading to a new Expo SDK version
- Handling breaking changes between SDK versions
- Updating dependencies for compatibility
- Migrating deprecated APIs to new versions
- Preparing apps for new Expo features

## Instructions

This skill guides you through upgrading Expo SDK versions:

1. **Pre-Upgrade Planning**: Review release notes and breaking changes
2. **Dependency Updates**: Update packages for SDK compatibility
3. **Configuration Migration**: Update app.json and configuration files
4. **Code Updates**: Migrate deprecated APIs to new versions
5. **Testing**: Verify app functionality after upgrade

## Upgrade Process

### 1. Pre-Upgrade Checklist

- Review Expo SDK release notes
- Identify breaking changes affecting your app
- Check compatibility of third-party packages
- Backup current project state
- Create a feature branch for the upgrade

### 2. Update Expo SDK

```bash
# Update Expo CLI
npm install -g expo-cli@latest

# Upgrade Expo SDK
npx expo install expo@latest

# Update all Expo packages
npx expo install --fix
```

### 3. Handle Breaking Changes

- Review migration guides for breaking changes
- Update deprecated API calls
- Modify configuration files as needed
- Update native dependencies if required
- Test affected features thoroughly

### 4. Update Dependencies

```bash
# Check for outdated packages
npx expo-doctor

# Update packages to compatible versions
npx expo install --fix

# Verify compatibility
npx expo-doctor
```

### 5. Testing

- Test core app functionality
- Verify native modules work correctly
- Check for runtime errors
- Test on both iOS and Android
- Verify app store builds still work

## Common Issues

### Dependency Conflicts

- Use `expo install` instead of `npm install` for Expo packages
- Check package compatibility with new SDK version
- Resolve peer dependency warnings

### Configuration Changes

- Update `app.json` for new SDK requirements
- Migrate deprecated configuration options
- Update native configuration files if needed

### Breaking API Changes

- Review API migration guides
- Update code to use new APIs
- Test affected features after changes

## Best Practices

- Always upgrade in a feature branch
- Test thoroughly before merging
- Review release notes carefully
- Update dependencies incrementally
- Keep Expo CLI updated
- Use `expo-doctor` to verify setup

## Resources

For more information, see the [source repository](https://github.com/expo/skills/tree/main/plugins/upgrading-expo).


---

## 🧠 AGI Framework Integration

> **Adapted for [@techwavedev/agi-agent-kit](https://www.npmjs.com/package/@techwavedev/agi-agent-kit)**
> Original source: [antigravity-awesome-skills](https://github.com/sickn33/antigravity-awesome-skills)

### Hybrid Memory Integration (Qdrant + BM25)

Before executing complex tasks with this skill:
```bash
python3 execution/memory_manager.py auto --query "<task summary>"
```

**Decision Tree:**
- **Cache hit?** Use cached response directly — no need to re-process.
- **Memory match?** Inject `context_chunks` into your reasoning.
- **No match?** Proceed normally, then store results:

```bash
python3 execution/memory_manager.py store \
  --content "Description of what was decided/solved" \
  --type decision \
  --tags upgrading-expo <relevant-tags>
```

> **Note:** Storing automatically updates both Vector (Qdrant) and Keyword (BM25) indices.

### Agent Team Collaboration

- **Strategy**: This skill communicates via the shared memory system.
- **Orchestration**: Invoked by `orchestrator` via intelligent routing.
- **Context Sharing**: Always read previous agent outputs from memory before starting.

### Local LLM Support

When available, use local Ollama models for embedding and lightweight inference:
- Embeddings: `nomic-embed-text` via Qdrant memory system
- Lightweight analysis: Local models reduce API costs for repetitive patterns