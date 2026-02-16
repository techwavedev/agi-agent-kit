---
name: azure-ai-contentsafety-py
description: |
  Azure AI Content Safety SDK for Python. Use for detecting harmful content in text and images with multi-severity classification.
  Triggers: "azure-ai-contentsafety", "ContentSafetyClient", "content moderation", "harmful content", "text analysis", "image analysis".
package: azure-ai-contentsafety
---

# Azure AI Content Safety SDK for Python

Detect harmful user-generated and AI-generated content in applications.

## Installation

```bash
pip install azure-ai-contentsafety
```

## Environment Variables

```bash
CONTENT_SAFETY_ENDPOINT=https://<resource>.cognitiveservices.azure.com
CONTENT_SAFETY_KEY=<your-api-key>
```

## Authentication

### API Key

```python
from azure.ai.contentsafety import ContentSafetyClient
from azure.core.credentials import AzureKeyCredential
import os

client = ContentSafetyClient(
    endpoint=os.environ["CONTENT_SAFETY_ENDPOINT"],
    credential=AzureKeyCredential(os.environ["CONTENT_SAFETY_KEY"])
)
```

### Entra ID

```python
from azure.ai.contentsafety import ContentSafetyClient
from azure.identity import DefaultAzureCredential

client = ContentSafetyClient(
    endpoint=os.environ["CONTENT_SAFETY_ENDPOINT"],
    credential=DefaultAzureCredential()
)
```

## Analyze Text

```python
from azure.ai.contentsafety import ContentSafetyClient
from azure.ai.contentsafety.models import AnalyzeTextOptions, TextCategory
from azure.core.credentials import AzureKeyCredential

client = ContentSafetyClient(endpoint, AzureKeyCredential(key))

request = AnalyzeTextOptions(text="Your text content to analyze")
response = client.analyze_text(request)

# Check each category
for category in [TextCategory.HATE, TextCategory.SELF_HARM, 
                 TextCategory.SEXUAL, TextCategory.VIOLENCE]:
    result = next((r for r in response.categories_analysis 
                   if r.category == category), None)
    if result:
        print(f"{category}: severity {result.severity}")
```

## Analyze Image

```python
from azure.ai.contentsafety import ContentSafetyClient
from azure.ai.contentsafety.models import AnalyzeImageOptions, ImageData
from azure.core.credentials import AzureKeyCredential
import base64

client = ContentSafetyClient(endpoint, AzureKeyCredential(key))

# From file
with open("image.jpg", "rb") as f:
    image_data = base64.b64encode(f.read()).decode("utf-8")

request = AnalyzeImageOptions(
    image=ImageData(content=image_data)
)

response = client.analyze_image(request)

for result in response.categories_analysis:
    print(f"{result.category}: severity {result.severity}")
```

### Image from URL

```python
from azure.ai.contentsafety.models import AnalyzeImageOptions, ImageData

request = AnalyzeImageOptions(
    image=ImageData(blob_url="https://example.com/image.jpg")
)

response = client.analyze_image(request)
```

## Text Blocklist Management

### Create Blocklist

```python
from azure.ai.contentsafety import BlocklistClient
from azure.ai.contentsafety.models import TextBlocklist
from azure.core.credentials import AzureKeyCredential

blocklist_client = BlocklistClient(endpoint, AzureKeyCredential(key))

blocklist = TextBlocklist(
    blocklist_name="my-blocklist",
    description="Custom terms to block"
)

result = blocklist_client.create_or_update_text_blocklist(
    blocklist_name="my-blocklist",
    options=blocklist
)
```

### Add Block Items

```python
from azure.ai.contentsafety.models import AddOrUpdateTextBlocklistItemsOptions, TextBlocklistItem

items = AddOrUpdateTextBlocklistItemsOptions(
    blocklist_items=[
        TextBlocklistItem(text="blocked-term-1"),
        TextBlocklistItem(text="blocked-term-2")
    ]
)

result = blocklist_client.add_or_update_blocklist_items(
    blocklist_name="my-blocklist",
    options=items
)
```

### Analyze with Blocklist

```python
from azure.ai.contentsafety.models import AnalyzeTextOptions

request = AnalyzeTextOptions(
    text="Text containing blocked-term-1",
    blocklist_names=["my-blocklist"],
    halt_on_blocklist_hit=True
)

response = client.analyze_text(request)

if response.blocklists_match:
    for match in response.blocklists_match:
        print(f"Blocked: {match.blocklist_item_text}")
```

## Severity Levels

Text analysis returns 4 severity levels (0, 2, 4, 6) by default. For 8 levels (0-7):

```python
from azure.ai.contentsafety.models import AnalyzeTextOptions, AnalyzeTextOutputType

request = AnalyzeTextOptions(
    text="Your text",
    output_type=AnalyzeTextOutputType.EIGHT_SEVERITY_LEVELS
)
```

## Harm Categories

| Category | Description |
|----------|-------------|
| `Hate` | Attacks based on identity (race, religion, gender, etc.) |
| `Sexual` | Sexual content, relationships, anatomy |
| `Violence` | Physical harm, weapons, injury |
| `SelfHarm` | Self-injury, suicide, eating disorders |

## Severity Scale

| Level | Text Range | Image Range | Meaning |
|-------|------------|-------------|---------|
| 0 | Safe | Safe | No harmful content |
| 2 | Low | Low | Mild references |
| 4 | Medium | Medium | Moderate content |
| 6 | High | High | Severe content |

## Client Types

| Client | Purpose |
|--------|---------|
| `ContentSafetyClient` | Analyze text and images |
| `BlocklistClient` | Manage custom blocklists |

## Best Practices

1. **Use blocklists** for domain-specific terms
2. **Set severity thresholds** appropriate for your use case
3. **Handle multiple categories** — content can be harmful in multiple ways
4. **Use halt_on_blocklist_hit** for immediate rejection
5. **Log analysis results** for audit and improvement
6. **Consider 8-severity mode** for finer-grained control
7. **Pre-moderate AI outputs** before showing to users


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
  --tags azure-ai-contentsafety-py <relevant-tags>
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