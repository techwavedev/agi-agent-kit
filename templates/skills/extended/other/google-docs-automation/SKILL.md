---
name: google-docs-automation
description: |
  Interact with Google Docs - create documents, search by title, read content, and edit text.
  Use when user asks to: create a Google Doc, find a document, read doc content, add text to a doc,
  or replace text in a document. Lightweight alternative to full Google...
--- Apache-2.0
metadata:
  author: sanjay3290
  version: "1.0"
---

# Google Docs

Lightweight Google Docs integration with standalone OAuth authentication. No MCP server required.

> **⚠️ Requires Google Workspace account.** Personal Gmail accounts are not supported.

## First-Time Setup

Authenticate with Google (opens browser):
```bash
python scripts/auth.py login
```

Check authentication status:
```bash
python scripts/auth.py status
```

Logout when needed:
```bash
python scripts/auth.py logout
```

## Commands

All operations via `scripts/docs.py`. Auto-authenticates on first use if not logged in.

```bash
# Create a new document
python scripts/docs.py create "Meeting Notes"

# Create a document with initial content
python scripts/docs.py create "Project Plan" --content "# Overview\n\nThis is the project plan."

# Find documents by title
python scripts/docs.py find "meeting" --limit 10

# Get text content of a document
python scripts/docs.py get-text 1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms

# Get text using a full URL
python scripts/docs.py get-text "https://docs.google.com/document/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/edit"

# Append text to end of document
python scripts/docs.py append-text 1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms "New paragraph at the end."

# Insert text at beginning of document
python scripts/docs.py insert-text 1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms "Text at the beginning.\n\n"

# Replace text in document
python scripts/docs.py replace-text 1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms "old text" "new text"
```

## Document ID Format

Google Docs uses document IDs like `1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms`. You can:
- Use the full URL (the ID will be extracted automatically)
- Use just the document ID
- Get document IDs from the `find` command results

## Token Management

Tokens stored securely using the system keyring:
- **macOS**: Keychain
- **Windows**: Windows Credential Locker
- **Linux**: Secret Service API (GNOME Keyring, KDE Wallet, etc.)

Service name: `google-docs-skill-oauth`

Access tokens are automatically refreshed when expired using Google's cloud function.

---

<!-- AGI-INTEGRATION-START -->

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
python3 execution/memory_manager.py store \\
  --content "Description of what was decided/solved" \\
  --type decision \\
  --tags google-docs-automation <relevant-tags>
```

### Agent Team Collaboration

- This skill can be invoked by the `orchestrator` agent via intelligent routing.
- In **Agent Teams mode**, results are shared via Qdrant shared memory for cross-agent context.
- In **Subagent mode**, this skill runs in isolation with its own memory namespace.

### Local LLM Support

When available, use local Ollama models for embedding and lightweight inference:
- Embeddings: `nomic-embed-text` via Qdrant memory system
- Lightweight analysis: Local models reduce API costs for repetitive patterns

<!-- AGI-INTEGRATION-END -->
