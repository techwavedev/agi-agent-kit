---
name: aws-elasticache
description: Amazon ElastiCache via MCP. Use for complete ElastiCache operations.
---

# AWS ElastiCache Skill

> Part of the [AWS skill family](../aws/SKILL.md).

Complete ElastiCache operations.

## MCP Server Setup

```json
{
  "mcpServers": {
    "elasticache": {
      "command": "uvx",
      "args": ["awslabs.elasticache-mcp-server@latest"],
      "env": { "AWS_PROFILE": "default", "AWS_REGION": "eu-west-1" }
    }
  }
}
```

## References

- [ElastiCache MCP Server](https://awslabs.github.io/mcp/servers/elasticache-mcp-server)
