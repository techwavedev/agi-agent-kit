---
name: imagen
description: "AI image generation skill powered by Google Gemini, enabling seamless visual content creation for UI placeholders, documentation, and design assets."
risk: safe
source: "https://github.com/sanjay3290/ai-skills/tree/main/skills/imagen"
date_added: "2026-02-27"
---

# Imagen - AI Image Generation Skill

## Overview

This skill generates images using Google Gemini's image generation model (`gemini-3-pro-image-preview`). It enables seamless image creation during any Claude Code session - whether you're building frontend UIs, creating documentation, or need visual representations of concepts.

**Cross-Platform**: Works on Windows, macOS, and Linux.

## When to Use This Skill

Automatically activate this skill when:
- User requests image generation (e.g., "generate an image of...", "create a picture...")
- Frontend development requires placeholder or actual images
- Documentation needs illustrations or diagrams
- Visualizing concepts, architectures, or ideas
- Creating icons, logos, or UI assets
- Any task where an AI-generated image would be helpful

## How It Works

1. Takes a text prompt describing the desired image
2. Calls Google Gemini API with image generation configuration
3. Saves the generated image to a specified location (defaults to current directory)
4. Returns the file path for use in your project

## Usage

### Python (Cross-Platform - Recommended)

```bash
# Basic usage
python scripts/generate_image.py "A futuristic city skyline at sunset"

# With custom output path
python scripts/generate_image.py "A minimalist app icon for a music player" "./assets/icons/music-icon.png"

# With custom size
python scripts/generate_image.py --size 2K "High resolution landscape" "./wallpaper.png"
```

## Requirements

- `GEMINI_API_KEY` environment variable must be set
- Python 3.6+ (uses standard library only, no pip install needed)

## Output

Generated images are saved as PNG files. The script returns:
- Success: Path to the generated image
- Failure: Error message with details

## Examples

### Frontend Development
```
User: "I need a hero image for my landing page - something abstract and tech-focused"
-> Generates and saves image, provides path for use in HTML/CSS
```

### Documentation
```
User: "Create a diagram showing microservices architecture"
-> Generates visual representation, ready for README or docs
```

### UI Assets
```
User: "Generate a placeholder avatar image for the user profile component"
-> Creates image in appropriate size for component use
```

---

<!-- AGI-INTEGRATION-START -->

## AGI Framework Integration

> **Adapted for [@techwavedev/agi-agent-kit](https://www.npmjs.com/package/@techwavedev/agi-agent-kit)**
> Original source: [antigravity-awesome-skills](https://github.com/sickn33/antigravity-awesome-skills)

### Memory-First Protocol

Retrieve prior agent configurations, team compositions, and orchestration patterns. Critical for multi-agent system consistency.

```bash
# Check for prior AI agent orchestration context before starting
python3 execution/memory_manager.py auto --query "agent patterns and orchestration strategies for Imagen"
```

### Storing Results

After completing work, store AI agent orchestration decisions for future sessions:

```bash
python3 execution/memory_manager.py store \
  --content "Agent pattern: hierarchical orchestration with Control Tower dispatcher, 3 specialist sub-agents" \
  --type decision --project <project> \
  --tags imagen ai-agents
```

### Multi-Agent Collaboration

This skill is inherently multi-agent. Use cross-agent context to coordinate task distribution and avoid duplicate work.

```bash
python3 execution/cross_agent_context.py store \
  --agent "<your-agent>" \
  --action "Agent architecture designed — Control Tower + specialist agents with shared Qdrant memory" \
  --project <project>
```

### Control Tower Integration

Register agents and tasks with the Control Tower (`execution/control_tower.py`) for centralized orchestration across machines and LLM providers.

### Blockchain Identity

Each agent has a cryptographic Ed25519 identity. All memory writes are signed — enabling trust verification in multi-agent systems.

<!-- AGI-INTEGRATION-END -->
