---
name: videodb-skills
description: "Upload, stream, search, edit, transcribe, and generate AI video and audio using the VideoDB SDK."
category: media
risk: safe
source: community
tags: "[video, editing, transcription, subtitles, search, streaming, ai-generation, media]"
date_added: "2026-02-27"
---

# VideoDB Skills

## Purpose

The only video skill your agent needs. Upload any video, connect real-time streams, search inside by what was said or shown, build complex editing workflows with overlays, generate AI media, add subtitles, and get instant streaming links — all via the VideoDB Python SDK.

## When to Use This Skill

- User wants to upload and process videos from YouTube, URLs, or local files
- User needs to search for moments by speech or visual scenes
- User asks for transcription, subtitles, or subtitle styling
- User wants to edit clips — trim, combine, add text/image/audio overlays
- User needs AI-generated media (images, video, music, sound effects, voiceovers)
- User wants to transcode, change resolution, or reframe for social platforms
- User needs real-time screen or audio capture with AI transcription
- User asks for playable streaming links for any video output

## Setup

### Step 1: Install the skill

```bash
npx skills add video-db/skills
```

### Step 2: Run setup

```
/videodb setup
```

The agent guides API key setup ($20 free credits, no credit card), installs the SDK, and verifies the connection.

Alternatively, set the API key manually:

```bash
export VIDEO_DB_API_KEY=sk-xxx
```

### Step 3: Install the SDK

```bash
pip install "videodb[capture]" python-dotenv
```

## Capabilities

| Capability  | Description                                                               |
| ----------- | ------------------------------------------------------------------------- |
| Upload      | Ingest videos from YouTube, URLs, or local files                          |
| Search      | Find moments by speech (semantic/keyword) or visual scenes                |
| Transcripts | Generate timestamped transcripts from any video                           |
| Edit        | Combine clips, trim, add text/image/audio overlays                        |
| Subtitles   | Auto-generate and style subtitles                                         |
| AI Generate | Create images, video, music, sound effects, and voiceovers from text      |
| Capture     | Real-time screen and audio capture with AI transcription                  |
| Transcode   | Change resolution, quality, aspect ratio, or reframe for social platforms |
| Stream      | Get playable HLS links for anything you build                             |

## Examples

**Upload and transcribe:**

```
"Upload https://www.youtube.com/watch?v=FgrO9ADPZSA and give me a transcript"
```

**Search across videos:**

```
"Search for 'product demo' in my latest video"
```

**Add subtitles:**

```
"Add subtitles with white text on black background"
```

**Multi-clip editing:**

```
"Take clips from 10s-30s and 45s-60s, add a title card, and combine them"
```

**AI media generation:**

```
"Generate background music and overlay it on my video"
```

**Real-time capture:**

```
"Capture my screen and transcribe it in real-time"
```

**Reframe for social:**

```
"Convert this to vertical for Instagram Reels"
```

## Repository

https://github.com/video-db/skills

**Version:** 1.1.0
**Maintained By:** [VideoDB](https://github.com/video-db)

---

<!-- AGI-INTEGRATION-START -->

## AGI Framework Integration

> **Adapted for [@techwavedev/agi-agent-kit](https://www.npmjs.com/package/@techwavedev/agi-agent-kit)**
> Original source: [antigravity-awesome-skills](https://github.com/sickn33/antigravity-awesome-skills)

### Memory-First Protocol

Retrieve prior decisions and patterns to avoid re-discovering solutions. Cache results for instant retrieval in future sessions.

```bash
# Check for prior development context before starting
python3 execution/memory_manager.py auto --query "prior work and patterns related to Videodb Skills"
```

### Storing Results

After completing work, store development decisions for future sessions:

```bash
python3 execution/memory_manager.py store \
  --content "Completed task with key insights documented for future reference" \
  --type decision --project <project> \
  --tags videodb-skills default
```

### Multi-Agent Collaboration

Share outcomes with other agents so the team stays aligned and avoids duplicate work.

```bash
python3 execution/cross_agent_context.py store \
  --agent "<your-agent>" \
  --action "Task completed — results documented and shared with team" \
  --project <project>
```

<!-- AGI-INTEGRATION-END -->
