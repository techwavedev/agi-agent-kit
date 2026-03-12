---
name: azure-ai-transcription-py
description: Azure AI Transcription SDK for Python. Use for real-time and batch speech-to-text transcription with timestamps and diarization.
risk: unknown
source: community
date_added: '2026-02-27'
---

# Azure AI Transcription SDK for Python

Client library for Azure AI Transcription (speech-to-text) with real-time and batch transcription.

## Installation

```bash
pip install azure-ai-transcription
```

## Environment Variables

```bash
TRANSCRIPTION_ENDPOINT=https://<resource>.cognitiveservices.azure.com
TRANSCRIPTION_KEY=<your-key>
```

## Authentication

Use subscription key authentication (DefaultAzureCredential is not supported for this client):

```python
import os
from azure.ai.transcription import TranscriptionClient

client = TranscriptionClient(
    endpoint=os.environ["TRANSCRIPTION_ENDPOINT"],
    credential=os.environ["TRANSCRIPTION_KEY"]
)
```

## Transcription (Batch)

```python
job = client.begin_transcription(
    name="meeting-transcription",
    locale="en-US",
    content_urls=["https://<storage>/audio.wav"],
    diarization_enabled=True
)
result = job.result()
print(result.status)
```

## Transcription (Real-time)

```python
stream = client.begin_stream_transcription(locale="en-US")
stream.send_audio_file("audio.wav")
for event in stream:
    print(event.text)
```

## Best Practices

1. **Enable diarization** when multiple speakers are present
2. **Use batch transcription** for long files stored in blob storage
3. **Capture timestamps** for subtitle generation
4. **Specify language** to improve recognition accuracy
5. **Handle streaming backpressure** for real-time transcription
6. **Close transcription sessions** when complete

## When to Use
This skill is applicable to execute the workflow or actions described in the overview.

---

<!-- AGI-INTEGRATION-START -->

## AGI Framework Integration

> **Adapted for [@techwavedev/agi-agent-kit](https://www.npmjs.com/package/@techwavedev/agi-agent-kit)**
> Original source: [antigravity-awesome-skills](https://github.com/sickn33/antigravity-awesome-skills)

### Memory-First Protocol

Retrieve prior deployment configurations, rollback procedures, and incident post-mortems. Avoid re-discovering infrastructure patterns.

```bash
# Check for prior infrastructure context before starting
python3 execution/memory_manager.py auto --query "deployment configuration and patterns for Azure Ai Transcription Py"
```

### Storing Results

After completing work, store infrastructure decisions for future sessions:

```bash
python3 execution/memory_manager.py store \
  --content "Deployment pipeline: configured blue-green deployment with health checks on port 8080" \
  --type technical --project <project> \
  --tags azure-ai-transcription-py devops
```

### Multi-Agent Collaboration

Broadcast deployment changes so frontend and backend agents update their configurations accordingly.

```bash
python3 execution/cross_agent_context.py store \
  --agent "<your-agent>" \
  --action "Deployed infrastructure changes — updated CI/CD pipeline with new health check endpoints" \
  --project <project>
```

### Playbook Integration

Use the `ship-saas-mvp` or `full-stack-deploy` playbook to sequence this skill with testing, documentation, and deployment verification.

<!-- AGI-INTEGRATION-END -->
