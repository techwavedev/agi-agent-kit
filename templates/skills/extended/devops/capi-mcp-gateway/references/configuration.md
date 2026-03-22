# CAPI MCP Gateway — Complete Configuration Reference

## Full `config.yaml`

```yaml
capi:
  version: 1.0.0
  instanceName: default
  strictToInstanceName: true
  publicEndpoint: http://localhost:8380/api/
  runningMode: full                     # full | websocket | sse
  adminPort: 8381
  reverseProxyHost:                     # Override X-Forwarded-Host

  rest:
    enabled: true
    port: 8380
    listeningAddress: 0.0.0.0
    contextPath: /api
    connectionRequestTimeout: 5000
    requestTimeout: 5000
    responseTimeout: 120000
    proxyPoolSize: 200
    proxyMaxPoolSize: 500

  mcp:
    enabled: true                       # Enable MCP Gateway
    port: 8383                          # MCP listener port
    sessionTtl: 1800000                 # Session TTL (ms), default 30 min
    toolCallTimeout: 30000              # Tool execution timeout (ms)

  websocket:
    enabled: false
    port: 8382
    listeningAddress: 0.0.0.0
    contextPath: /api/*

  grpc:
    enabled: false
    port: 8384

  ssl:
    enabled: false
    keyStoreType: PKCS12
    path:
    password:

  trustStore:
    enabled: false
    path:
    encoded:                            # Base64-encoded truststore (alt to path)
    password:

  consulCatalogDiscoverInterval: 60000  # Consul poll interval (ms)
  consulHosts:
    - endpoint: http://localhost:8500
      token:                            # Consul ACL token
  consulStore:
    enabled: false
    endpoint: http://localhost:8500
    token:

  oauth2:
    enabled: false
    cookieName:
    keys:
      - http://localhost:8080/realms/capi/protocol/openid-connect/certs

  opa:
    enabled: false
    endpoint: http://localhost:8181

  traces:
    enabled: false
    serviceName: capi
    endpoint: http://localhost:4318     # OTLP endpoint
    extraMetadataPrefix:

  corsEnabled: false
  allowedHeaders:
    - Origin
    - Accept
    - X-Requested-With
    - Content-Type
    - Access-Control-Request-Method
    - Authorization

  throttle:
    enabled: false
    kubernetesNamespace:
    kubernetesServiceName:
```

---

## MCP-Specific Fields

| Field | Default | Description |
|-------|---------|-------------|
| `mcp.enabled` | `false` | Start the MCP listener |
| `mcp.port` | `8383` | Port for MCP JSON-RPC endpoint |
| `mcp.sessionTtl` | `1800000` | Session time-to-live in ms (30 min) |
| `mcp.toolCallTimeout` | `30000` | Per-tool execution timeout in ms |

---

## Ports Summary

| Port | Purpose | Config Key |
|------|---------|------------|
| 8380 | REST Gateway | `capi.rest.port` |
| 8381 | Admin API | `capi.adminPort` |
| 8382 | WebSocket / SSE | `capi.websocket.port` |
| 8383 | **MCP Gateway** | `capi.mcp.port` |
| 8384 | gRPC Gateway | `capi.grpc.port` |

---

## Consul MCP Metadata (Service Registration)

| Key | Required | Description |
|-----|----------|-------------|
| `group` | **Yes** | Route group (e.g. `v1`). Services without `group` are ignored. |
| `mcp-enabled` | **Yes** | `"true"` to expose as MCP tools |
| `mcp-tools` | **Yes** | Comma-separated tool names |
| `mcp-tools-{name}-description` | **Yes** | Human-readable description per tool |
| `mcp-tools-{name}-inputSchema` | Recommended | JSON Schema string for tool input |
| `mcp-toolPrefix` | Recommended | Namespace prefix (e.g. `orders` → `orders.get`) |
| `mcp-streaming` | No | Tools supporting SSE streaming |
| `mcp-category` | No | Semantic category for OPA policies |
| `mcp-timeout` | No | Per-service timeout override (ms) |
| `root-context` | No | Backend path prefix (default `/`) |
| `scheme` | No | `http` or `https` (default `http`) |
| `secured` | No | Require OAuth2 for this service |
| `opa-rego` | No | OPA policy path for authorization |

---

## Docker Compose Example

```yaml
version: "3.8"
services:
  consul:
    image: hashicorp/consul:1.17
    ports:
      - "8500:8500"
    command: agent -dev -client=0.0.0.0

  capi:
    image: surisoft/capi-core
    ports:
      - "8380:8380"
      - "8381:8381"
      - "8383:8383"
    volumes:
      - ./config.yaml:/capi/config/config.yaml
    environment:
      CAPI_CONFIG_FILE: /capi/config/config.yaml
    depends_on:
      - consul

  # Example backend (your REST API)
  order-service:
    image: my-order-service:latest
    ports:
      - "8080:8080"
```

---

## Helm Values (Kubernetes)

Key values for MCP:

```yaml
capi:
  mcp:
    enabled: true
    port: 8383

# Expose MCP port in service
service:
  ports:
    - name: mcp
      port: 8383
      targetPort: 8383

# Ingress for MCP (optional)
ingress:
  enabled: true
  hosts:
    - host: mcp.example.com
      paths:
        - path: /mcp
          pathType: Prefix
          servicePort: 8383
```

See [helm/capi-core/values.yaml](https://github.com/surisoft-io/capi-core/blob/main/helm/capi-core/values.yaml) for all options.
