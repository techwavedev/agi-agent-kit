---
name: aws-openapi
description: OpenAPI via MCP. Use for dynamic API integration through OpenAPI specifications.
---

# AWS OpenAPI Skill

> Part of the [AWS skill family](../aws/SKILL.md).

Dynamic API integration through OpenAPI specifications.

## MCP Server Setup

```json
{
  "mcpServers": {
    "openapi": {
      "command": "uvx",
      "args": ["awslabs.openapi-mcp-server@latest"]
    }
  }
}
```

## References

- [OpenAPI MCP Server](https://awslabs.github.io/mcp/servers/openapi-mcp-server)
