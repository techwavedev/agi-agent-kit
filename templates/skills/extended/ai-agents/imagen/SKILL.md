---
name: imagen
description: |
source: "https://github.com/sanjay3290/ai-skills/tree/main/skills/imagen"
risk: safe
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
  --tags imagen <relevant-tags>
```

### Agent Team Collaboration

- This skill can be invoked by the `orchestrator` agent via intelligent routing.
- In **Agent Teams mode**, results are shared via Qdrant shared memory for cross-agent context.
- In **Subagent mode**, this skill runs in isolation with its own memory namespace.

### Local LLM Support

When available, use local Ollama models for embedding and lightweight inference:
- Embeddings: `nomic-embed-text` via Qdrant memory system
- Lightweight analysis: Local models reduce API costs for repetitive patterns
