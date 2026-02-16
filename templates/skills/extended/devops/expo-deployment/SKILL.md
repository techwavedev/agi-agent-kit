---
name: expo-deployment
description: "Deploy Expo apps to production"
source: "https://github.com/expo/skills/tree/main/plugins/expo-deployment"
risk: safe
---

# Expo Deployment

## Overview

Deploy Expo applications to production environments, including app stores and over-the-air updates.

## When to Use This Skill

Use this skill when you need to deploy Expo apps to production.

Use this skill when:
- Deploying Expo apps to production
- Publishing to app stores (iOS App Store, Google Play)
- Setting up over-the-air (OTA) updates
- Configuring production build settings
- Managing release channels and versions

## Instructions

This skill provides guidance for deploying Expo apps:

1. **Build Configuration**: Set up production build settings
2. **App Store Submission**: Prepare and submit to app stores
3. **OTA Updates**: Configure over-the-air update channels
4. **Release Management**: Manage versions and release channels
5. **Production Optimization**: Optimize apps for production

## Deployment Workflow

### Pre-Deployment

1. Ensure all tests pass
2. Update version numbers
3. Configure production environment variables
4. Review and optimize app bundle size
5. Test production builds locally

### App Store Deployment

1. Build production binaries (iOS/Android)
2. Configure app store metadata
3. Submit to App Store Connect / Google Play Console
4. Manage app store listings and screenshots
5. Handle app review process

### OTA Updates

1. Configure update channels (production, staging, etc.)
2. Build and publish updates
3. Manage rollout strategies
4. Monitor update adoption
5. Handle rollbacks if needed

## Best Practices

- Use EAS Build for reliable production builds
- Test production builds before submission
- Implement proper error tracking and analytics
- Use release channels for staged rollouts
- Keep app store metadata up to date
- Monitor app performance in production

## Resources

For more information, see the [source repository](https://github.com/expo/skills/tree/main/plugins/expo-deployment).


---

## 🧠 AGI Framework Integration

> **Adapted for [@techwavedev/agi-agent-kit](https://www.npmjs.com/package/@techwavedev/agi-agent-kit)**
> Original source: [antigravity-awesome-skills](https://github.com/sickn33/antigravity-awesome-skills)

### Qdrant Memory Integration

Before executing complex tasks with this skill:
```bash
python3 execution/memory_manager.py auto --query "<task summary>"
```
- **Cache hit?** Use cached response directly — no need to re-process.
- **Memory match?** Inject `context_chunks` into your reasoning.
- **No match?** Proceed normally, then store results:
```bash
python3 execution/memory_manager.py store \
  --content "Description of what was decided/solved" \
  --type decision \
  --tags expo-deployment <relevant-tags>
```

### Agent Team Collaboration

- This skill can be invoked by the `orchestrator` agent via intelligent routing.
- In **Agent Teams mode**, results are shared via Qdrant shared memory for cross-agent context.
- In **Subagent mode**, this skill runs in isolation with its own memory namespace.

### Local LLM Support

When available, use local Ollama models for embedding and lightweight inference:
- Embeddings: `nomic-embed-text` via Qdrant memory system
- Lightweight analysis: Local models reduce API costs for repetitive patterns
