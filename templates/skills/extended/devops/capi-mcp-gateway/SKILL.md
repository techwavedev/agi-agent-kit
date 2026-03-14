---
name: capi-mcp-gateway
description: "Deploy, configure, and interact with CAPI Gateway's MCP (Model Context Protocol) endpoint. Turns any REST API into an MCP tool without backend code changes — LLM agents discover and invoke tools via JSON-RPC 2.0 over Streamable HTTP. Use when: (1) exposing existing REST services as MCP tools for AI agents, (2) setting up a CAPI MCP Gateway (Docker, JAR, or Helm), (3) registering services in Consul with MCP metadata, (4) connecting Claude Desktop, Cursor, or custom agents to a CAPI /mcp endpoint, (5) building Python/TypeScript agent loops that use CAPI-discovered tools, (6) debugging MCP sessions, tool routing, or JSON-RPC errors."
---

# CAPI MCP Gateway Skill

Deploy and operate the [CAPI Gateway](https://github.com/surisoft-io/capi-core) MCP endpoint — a REST-to-MCP bridge that lets LLM agents discover and invoke any Consul-registered REST API as MCP tools, with zero code changes on backends.

---

## Quick Start

### 1. Start CAPI with MCP Enabled

**Docker (fastest):**

```bash
docker run -p 8380:8380 -p 8381:8381 -p 8383:8383 \
  -v $(pwd)/config.yaml:/capi/config/config.yaml \
  -e CAPI_CONFIG_FILE=/capi/config/config.yaml \
  surisoft/capi-core
```

**JAR:**

```bash
CAPI_CONFIG_FILE=config.yaml java -jar capi-core.jar
```

**Helm (Kubernetes):**

```bash
helm install capi-core helm/capi-core -f my-values.yaml
```

### 2. Minimal `config.yaml` with MCP

```yaml
capi:
  version: 1.0.0
  instanceName: default
  publicEndpoint: http://localhost:8380/api/
  runningMode: full
  adminPort: 8381

  rest:
    enabled: true
    port: 8380

  mcp:
    enabled: true
    port: 8383
    sessionTtl: 1800000       # 30 min
    toolCallTimeout: 30000    # 30 sec

  consulHosts:
    - endpoint: http://localhost:8500
```

### 3. Register a Service in Consul

```json
{
  "ID": "order-service-1",
  "Name": "order-service",
  "Address": "10.0.1.50",
  "Port": 8080,
  "Meta": {
    "group": "v1",
    "scheme": "http",
    "root-context": "/api",
    "mcp-enabled": "true",
    "mcp-toolPrefix": "orders",
    "mcp-tools": "get,create,search",
    "mcp-tools-get-description": "Get an order by ID",
    "mcp-tools-get-inputSchema": "{\"type\":\"object\",\"properties\":{\"orderId\":{\"type\":\"string\"}},\"required\":[\"orderId\"]}",
    "mcp-tools-create-description": "Create a new order",
    "mcp-tools-create-inputSchema": "{\"type\":\"object\",\"properties\":{\"product\":{\"type\":\"string\"},\"quantity\":{\"type\":\"integer\"}}}",
    "mcp-tools-search-description": "Search orders by criteria",
    "mcp-tools-search-inputSchema": "{\"type\":\"object\",\"properties\":{\"query\":{\"type\":\"string\"}}}",
    "mcp-category": "commerce",
    "mcp-timeout": "10000",
    "mcp-streaming": "search"
  }
}
```

Register via Consul HTTP API:

```bash
curl -X PUT http://localhost:8500/v1/agent/service/register \
  -H "Content-Type: application/json" \
  -d @service.json
```

### 4. Verify Tools

```bash
curl http://localhost:8381/info/mcp/tools
```

---

## MCP Wire Protocol (JSON-RPC 2.0)

All interactions go to a single `POST /mcp` endpoint on port `8383`.

| Method | Description |
|--------|-------------|
| `initialize` | Create session; returns `Mcp-Session-Id` header |
| `tools/list` | Aggregated tool catalog from all MCP-enabled services |
| `tools/call` | Invoke a tool — CAPI routes to the correct backend |
| `ping` | Health check |

### curl Walkthrough

```bash
# 1. Initialize session
curl -s -D- -X POST http://localhost:8383/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"initialize","id":1}'
# → Mcp-Session-Id header in response

# 2. List tools
curl -s -X POST http://localhost:8383/mcp \
  -H "Content-Type: application/json" \
  -H "Mcp-Session-Id: <session-id>" \
  -d '{"jsonrpc":"2.0","method":"tools/list","id":2}'

# 3. Call a tool
curl -s -X POST http://localhost:8383/mcp \
  -H "Content-Type: application/json" \
  -H "Mcp-Session-Id: <session-id>" \
  -d '{"jsonrpc":"2.0","method":"tools/call","id":3,"params":{"name":"orders.get","arguments":{"orderId":"12345"}}}'

# 4. Streaming tool call (SSE)
curl -N -X POST http://localhost:8383/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -H "Mcp-Session-Id: <session-id>" \
  -d '{"jsonrpc":"2.0","method":"tools/call","id":4,"params":{"name":"orders.search","arguments":{"query":"pending"}}}'

# 5. Health
curl http://localhost:8383/mcp/health
```

---

## Client Integration

### Claude Desktop

Use `mcp-remote` to bridge stdio → HTTP:

```json
{
  "mcpServers": {
    "capi": {
      "command": "npx",
      "args": ["-y", "mcp-remote", "http://localhost:8383/mcp"]
    }
  }
}
```

> If OAuth2 is enabled, pass Bearer token via `mcp-remote` flags.

### Cursor / IDE

Same `mcp-remote` bridge applies — configure in your IDE's MCP settings.

### Python Agent

```python
import requests

BASE = "http://localhost:8383/mcp"
HEADERS = {"Content-Type": "application/json"}

def jsonrpc(method, params=None, req_id=1, extra_headers=None):
    body = {"jsonrpc": "2.0", "method": method, "id": req_id}
    if params:
        body["params"] = params
    h = {**HEADERS, **(extra_headers or {})}
    return requests.post(BASE, json=body, headers=h)

# Initialize
resp = jsonrpc("initialize")
session_id = resp.headers["Mcp-Session-Id"]
sh = {"Mcp-Session-Id": session_id}

# List tools
tools = jsonrpc("tools/list", req_id=2, extra_headers=sh).json()["result"]["tools"]

# Call tool
result = jsonrpc("tools/call", req_id=3, extra_headers=sh,
    params={"name": "orders.get", "arguments": {"orderId": "12345"}})
print(result.json()["result"]["content"][0]["text"])
```

See [references/agent_loop.md](references/agent_loop.md) for the full LLM agent loop pattern.

---

## Consul MCP Metadata Reference

| Key | Description |
|-----|-------------|
| `mcp-enabled` | `"true"` to expose service as MCP tools |
| `mcp-tools` | Comma-separated tool names (e.g. `"get,create,search"`) |
| `mcp-tools-{name}-description` | Human-readable description for LLM tool selection |
| `mcp-tools-{name}-inputSchema` | JSON Schema defining tool input parameters |
| `mcp-toolPrefix` | Namespace prefix (e.g. `"orders"` → `orders.get`) |
| `mcp-streaming` | Comma-separated tool names that support SSE streaming |
| `mcp-category` | Semantic classification; used as OPA input |
| `mcp-timeout` | Per-service timeout in ms |

> If a service exposes an OpenAPI definition and omits `inputSchema`, CAPI derives schemas from the spec.

---

## Admin Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /info/mcp` | MCP status: enabled, port, tool count, sessions |
| `GET /info/mcp/tools` | Full tool catalog as JSON |
| `GET /info/mcp/sessions` | Active session count |
| `GET /info/health` | Gateway health (`8381`) |
| `GET /info/routes` | All managed REST routes |

---

## Session Management

- Sessions created via `initialize` JSON-RPC method
- Identified by `Mcp-Session-Id` HTTP header
- TTL-based with sliding expiration (default 30 min)
- Stored in Hazelcast distributed cache
- Client can close via a `close` notification

---

## Error Codes

| Code | Meaning |
|------|---------|
| `-32700` | Parse error — invalid JSON |
| `-32600` | Invalid request — missing `jsonrpc` or `method` |
| `-32601` | Method not found |
| `-32602` | Invalid params — tool not found |
| `-32603` | Internal error — backend failure |
| `-32000` | Auth error — missing/invalid token or OPA deny |

---

## Security (OAuth2 + OPA)

When `oauth2.enabled: true` in config, clients must include a Bearer token:

```bash
curl -X POST http://localhost:8383/mcp \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"initialize","id":1}'
```

For fine-grained control, enable OPA. MCP extends the OPA input with:
- MCP client identity
- Session metadata
- Tool name and category

See [references/security.md](references/security.md) for OPA Rego policy examples.

---

## Ports Summary

| Port | Purpose | Config Key |
|------|---------|------------|
| 8380 | REST gateway | `capi.rest.port` |
| 8381 | Admin API | `capi.adminPort` |
| 8382 | WebSocket/SSE | `capi.websocket.port` |
| 8383 | **MCP Gateway** | `capi.mcp.port` |
| 8384 | gRPC Gateway | `capi.grpc.port` |

---

## Troubleshooting

| Issue | Likely Cause | Fix |
|-------|-------------|-----|
| No tools in `tools/list` | Service missing `mcp-enabled` metadata | Add `"mcp-enabled": "true"` to Consul Meta |
| `Tool not found` error | Wrong prefix or name | Check `mcp-toolPrefix` + `mcp-tools` values |
| Session rejected | OAuth2 enabled but no token | Send `Authorization: Bearer <token>` header |
| Backend timeout | Slow service | Increase `mcp-timeout` or `toolCallTimeout` |
| Connection refused on 8383 | MCP not enabled | Set `capi.mcp.enabled: true` in config |

---

## Reference Files

- [Agent Loop Pattern](references/agent_loop.md) — Full LLM agent loop with CAPI MCP
- [Security & OPA](references/security.md) — Auth config, OPA Rego examples
- [Configuration Reference](references/configuration.md) — Complete `config.yaml` reference

---

## AGI Framework Integration

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
  --tags capi-mcp-gateway <relevant-tags>
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

---

<!-- AGI-INTEGRATION-START -->

## AGI Framework Integration

> **Adapted for [@techwavedev/agi-agent-kit](https://www.npmjs.com/package/@techwavedev/agi-agent-kit)**
> Original source: [antigravity-awesome-skills](https://github.com/sickn33/antigravity-awesome-skills)

### Memory-First Protocol

Retrieve prior deployment configurations, rollback procedures, and incident post-mortems. Avoid re-discovering infrastructure patterns.

```bash
# Check for prior infrastructure context before starting
python3 execution/memory_manager.py auto --query "deployment configuration and patterns for Capi Mcp Gateway"
```

### Storing Results

After completing work, store infrastructure decisions for future sessions:

```bash
python3 execution/memory_manager.py store \
  --content "Deployment pipeline: configured blue-green deployment with health checks on port 8080" \
  --type technical --project <project> \
  --tags capi-mcp-gateway devops
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
