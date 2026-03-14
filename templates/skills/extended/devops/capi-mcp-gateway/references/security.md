# CAPI MCP Gateway — Security & Authorization

## OAuth2 / OIDC Configuration

Enable JWT token validation in `config.yaml`:

```yaml
capi:
  oauth2:
    enabled: true
    cookieName: auth_token       # optional, for browser clients
    keys:
      - http://keycloak:8080/realms/capi/protocol/openid-connect/certs
      # Multiple OIDC providers supported:
      - http://auth0.com/.well-known/jwks.json
```

When enabled, ALL MCP requests require a valid Bearer token:

```bash
curl -X POST http://localhost:8383/mcp \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"initialize","id":1}'
```

Per-service opt-in: set `"secured": "true"` in Consul metadata to require auth for specific services only.

---

## OPA Authorization

Enable Open Policy Agent for fine-grained tool-level authorization:

```yaml
capi:
  opa:
    enabled: true
    endpoint: http://localhost:8181
```

### OPA Input for MCP Requests

CAPI extends the standard OPA input with MCP context:

```json
{
  "input": {
    "method": "tools/call",
    "path": "/mcp",
    "token": {
      "sub": "user@example.com",
      "roles": ["analyst"],
      "iss": "https://keycloak/realms/capi"
    },
    "mcp": {
      "sessionId": "abc-123",
      "toolName": "orders.get",
      "toolCategory": "commerce",
      "clientIdentity": "claude-desktop"
    }
  }
}
```

### Example Rego Policies

**Allow only specific roles to call tools:**

```rego
package capi.mcp_policy

default allow = false

# Allow analysts to use commerce tools
allow {
    input.token.roles[_] == "analyst"
    input.mcp.toolCategory == "commerce"
}

# Allow admins to use everything
allow {
    input.token.roles[_] == "admin"
}
```

**Restrict specific tools:**

```rego
package capi.mcp_policy

default allow = false

# Block destructive tools for read-only users
allow {
    input.token.roles[_] == "viewer"
    not endswith(input.mcp.toolName, ".delete")
    not endswith(input.mcp.toolName, ".create")
}

# Full access for editors
allow {
    input.token.roles[_] == "editor"
}
```

**Rate-limit by tool category:**

```rego
package capi.mcp_policy

default allow = true

# Deny access to financial tools outside business hours
deny {
    input.mcp.toolCategory == "finance"
    not is_business_hours
}

is_business_hours {
    time.clock(time.now_ns())[0] >= 9
    time.clock(time.now_ns())[0] < 17
}

allow {
    not deny
}
```

### Consul Metadata for OPA

Set `opa-rego` in service metadata to specify the policy path:

```json
{
  "Meta": {
    "mcp-enabled": "true",
    "mcp-category": "commerce",
    "opa-rego": "capi/mcp_policy"
  }
}
```

---

## Claude Desktop with Auth

When OAuth2 is enabled, use `mcp-remote` with auth headers:

```json
{
  "mcpServers": {
    "capi": {
      "command": "npx",
      "args": [
        "-y", "mcp-remote",
        "http://localhost:8383/mcp",
        "--header", "Authorization: Bearer ${CAPI_TOKEN}"
      ]
    }
  }
}
```

Set `CAPI_TOKEN` as an environment variable for token management.

---

## TLS / SSL

Enable TLS termination on all CAPI listeners:

```yaml
capi:
  ssl:
    enabled: true
    keyStoreType: PKCS12
    path: /certs/keystore.p12
    password: changeit

  trustStore:
    enabled: true
    path: /certs/truststore.jks
    password: changeit
```

With TLS, MCP endpoint becomes `https://localhost:8383/mcp`.

---

## Security Checklist

- [ ] Enable OAuth2 with at least one JWKS endpoint
- [ ] Configure OPA policies for tool-level authorization
- [ ] Set `"secured": "true"` on sensitive Consul services
- [ ] Use TLS in production
- [ ] Set `mcp-category` on services to enable category-based OPA policies
- [ ] Review session TTL (default 30 min) — shorten for high-security environments
- [ ] Monitor active sessions via `GET /info/mcp/sessions`
