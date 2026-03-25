---
name: debug-llm
description: "Instrument, trace, and monitor LLM calls securely inside a self-hosted Langfuse instance running via Docker Compose. Analyze agent performance, debug complex flows, and compute LLM costs natively. Default debug-llm locally deployed. Triggers on: '@debug-llm', 'monitor llm', 'trace my agent', 'langfuse local', 'see how it is performing'."
---

# Debug LLM (Self-hosted Langfuse)

> **This is an Observability and Tracing tool.** The agent uses a self-hosted instance of Langfuse via Docker Compose to trace LLM calls, calculate performance, assess costs, and help you "see how it is performing".
>
> **Opt-in:** Fully local, fully self-hosted, your data never leaves the Docker container unless explicitly sent to your own keys.

## Architecture

```
User question/command
    ↓
Agent checks Langfuse Health → not running? → start (docker-compose up)
    ↓ running
Agent provides Langfuse UI link (localhost:3000)
    ↓
Agent instruments requests via Langfuse SDK wrappers
    ↓
Agent queries traces inside Langfuse (or reviews dashboard)
    ↓
Agent identifies bottlenecks, high costs, or failing traces
    ↓
Agent reports LLM performance metrics
```

## Quick Start

### 1. Check if Langfuse is running

```
Agent calls: status
If not running:
  Agent calls: start (runs docker-compose up -d)
  Wait for healthcheck (localhost:3000)
```

### 2. Configure Environment

After starting Langfuse locally, the agent should configure the environment variables needed to push traces:

* `LANGFUSE_PUBLIC_KEY`
* `LANGFUSE_SECRET_KEY`
* `LANGFUSE_HOST=http://localhost:3000`

> Note: For automatic local telemetry, generate the keys inside the Langfuse local dashboard (username: admin@langfuse.com, password: randomly assigned or setup manually upon first startup).

### 3. Trace

Start observing any LLM agent logic using these environment variables, or through the python SDK:
```python
from langfuse import Langfuse
langfuse = Langfuse(
  secret_key="...",
  public_key="...",
  host="http://localhost:3000"
)
langfuse.auth_check()
```

## Agent Scripts Reference

The agent has direct access to these scripts via `scripts/run.py`:

| Tool     | When                           |
| -------- | ------------------------------ |
| `start`  | Bring up local Langfuse Docker |
| `stop`   | Tear down Langfuse Docker      |
| `status` | See if containers are running  |

## Autonomous Workflow

### Health Gate (Mandatory First Step)

> [!CAUTION]
> **ALWAYS check status before attempting to trace.** If `status: stopped`, propose `start` to the user before proceeding to link metrics.

```
run.py status → running?
  → true:  proceed to query or show link
  → false: tell user "Langfuse is not running. I will start it via Docker Compose."
           → run.py start → Verify localhost:3000 is open
```

### On "Monitor LLM" or "See how it is performing":

1. **Check if Langfuse container status is running** — `run.py status`. 
2. **Launch Langfuse** — If down, `run.py start`.
3. **Instruct the User** — Direct the user to go to `http://localhost:3000`, register an admin account (in local dev mode, first login creates the admin account), and generate API keys.
4. **Hook it into the code** — Using the provided API keys, instrument the project code (via OpenAI SDK wrapper or directly with Langfuse Python/TS SDKs).
5. **Run tests/Agents** — Execute the standard project agent flow so traces start flowing.
6. **Review Dashboard** — The user can verify LLM cost, generation latency, and full prompt structures via the trace Explorer.

## Troubleshooting

| Problem                  | Solution                                                |
| ------------------------ | ------------------------------------------------------- |
| Port 3000 blocked        | Edit `docker-compose.yml` mapped ports                  |
| Docker not running       | Agent must prompt user to start Docker engine natively  |
| Traces not captured      | Ensure `LANGFUSE_HOST` specifically says `http://` and points to the exposed port |
| Database errors          | Container db `langfuse_db_data` might need to be erased. Stop and rm volumes. |

## AGI Framework Integration

### Qdrant Memory Integration

Before running deep diagnostics:
```bash
python3 execution/memory_manager.py auto --query "Local Langfuse observability setup and tracing configuration"
```

If you fix an issue regarding missing traces or misconfigured environments, save the resolution:
```bash
python3 execution/memory_manager.py store \
  --content "Resolved Langfuse trace missing by pointing LANGFUSE_HOST explicitly to http://localhost:3000 and removing trailing slash" \
  --type error \
  --tags debug-llm langfuse observability docker
```
