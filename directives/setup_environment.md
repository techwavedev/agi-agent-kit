# Directive: Setup Environment

> **Trigger**: First session on a new machine, or when `session_boot.py` reports failures.
> **Goal**: Fully bootstrap the AGI Agent Kit development environment so all execution scripts, skills, and memory systems work correctly.

---

## Prerequisites (macOS)

The following tools MUST be installed via **Homebrew** (`/opt/homebrew/bin/brew`):

| Tool       | Install Command               | Purpose                                  |
|------------|-------------------------------|------------------------------------------|
| Python 3.10+ | `brew install python`       | Runtime for all execution scripts        |
| Node.js    | `brew install node`           | NPM publishing, `bin/init.js`            |
| Ollama     | `brew install ollama`         | Local model inference & embeddings       |
| GitHub CLI | `brew install gh`             | Issue/PR creation from terminal          |
| Docker     | Install Docker Desktop        | Qdrant vector database (container)       |

**PATH**: Homebrew binaries live at `/opt/homebrew/bin`. If your agent's shell doesn't include this path, **always prefix commands** with:

```bash
export PATH="/opt/homebrew/bin:/opt/homebrew/sbin:$PATH"
```

---

## Step 1: Python Virtual Environment

The project **requires** a `.venv` at the project root. All `python3 execution/...` commands MUST use `.venv/bin/python3` — never the system Python.

```bash
# Create venv (if missing) with the required Homebrew Python 3.10+
/opt/homebrew/bin/python3 -m venv .venv

# Install all dependencies into that venv
.venv/bin/python3 -m pip install -r requirements.txt
```

### Agent Rule (MANDATORY)

When invoking any Python script in this project, agents MUST use:

```bash
.venv/bin/python3 execution/<script>.py [args]
```

**NOT** `python3 execution/<script>.py` — the system Python (e.g., `/usr/bin/python3`) is too old and lacks the required packages.

---

## Step 2: Ollama Models

The memory system **requires** the embedding model. Generative models are **optional but recommended** for local task routing (saves cloud tokens).

| Model                    | Purpose                        | Size   | Required? |
|--------------------------|--------------------------------|--------|-----------|
| `nomic-embed-text`       | Embeddings for Qdrant memory   | ~274MB | **Yes**   |
| `gemma4:e4b`             | Fast local inference (4B)      | ~9.6GB | No (recommended) |
| `glm-4.7-flash:latest`   | Medium local inference (12B)   | ~12GB  | No (recommended) |

```bash
ollama pull nomic-embed-text
ollama pull gemma4:e4b
ollama pull glm-4.7-flash:latest
```

> **Note**: `gemma4:e4b` and `glm-4.7-flash` are optional but strongly recommended for local task routing (saves cloud tokens). The memory system only requires `nomic-embed-text`.

---

## Step 3: Qdrant (Vector Database)

Qdrant runs as a Docker container:

```bash
docker run -d --name qdrant -p 6333:6333 -v qdrant_storage:/qdrant/storage qdrant/qdrant
```

Verify: `curl http://localhost:6333/healthz` → `{"title":"qdrant"}`

---

## Step 4: Session Boot

Once all services are running, execute the session boot to verify and initialize:

```bash
.venv/bin/python3 execution/session_boot.py --auto-fix
```

Expected output: `✅ Memory system ready — N memories, N cached responses`

---

## Step 5: NPM Dependencies

For the `bin/init.js` publishing pipeline:

```bash
npm install
```

---

## Repository

| Repository | URL | Purpose |
|---|---|---|
| **Public** | `https://github.com/techwavedev/agi-agent-kit` | Public distribution. Auto-deploys to NPM on tagged releases. |

### Branch Workflow

```
main
  └── feat/xyz or fix/xyz  →  PR  →  merge to main  →  NPM publish
```

**Rules**:
- All changes go through **issues → branches → PRs → merge approval**.
- Never push directly to `main`.
- Use `execution/session_boot.py --auto-fix` as the first command in every agent session.

---

## Quick Reference (New Machine Bootstrap)

```bash
# 1. Clone
git clone https://github.com/techwavedev/agi-agent-kit.git && cd agi-agent-kit

# 2. Homebrew deps
brew install python node ollama gh

# 3. Python venv (use Homebrew Python explicitly)
/opt/homebrew/bin/python3 -m venv .venv
.venv/bin/python3 -m pip install -r requirements.txt

# 4. Ollama models
ollama serve &  # if not already running
ollama pull nomic-embed-text
ollama pull gemma4:e4b

# 5. Qdrant
docker run -d --name qdrant -p 6333:6333 -v qdrant_storage:/qdrant/storage qdrant/qdrant

# 6. Boot
.venv/bin/python3 execution/session_boot.py --auto-fix

# 7. npm
npm install
```
