---
name: aws-prometheus
description: AWS Managed Prometheus via MCP. Use for Prometheus-compatible monitoring operations.
---

# AWS Prometheus Skill

> Part of the [AWS skill family](../aws/SKILL.md).

Prometheus-compatible operations.

## MCP Server Setup

```json
{
  "mcpServers": {
    "prometheus": {
      "command": "uvx",
      "args": ["awslabs.prometheus-mcp-server@latest"],
      "env": { "AWS_PROFILE": "default", "AWS_REGION": "eu-west-1" }
    }
  }
}
```

## References

- [Prometheus MCP Server](https://awslabs.github.io/mcp/servers/prometheus-mcp-server)
