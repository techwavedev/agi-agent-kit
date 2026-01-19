---
name: aws-memcached
description: Amazon ElastiCache for Memcached via MCP. Use for high-speed caching operations.
---

# AWS Memcached Skill

> Part of the [AWS skill family](../aws/SKILL.md).

High-speed caching operations.

## MCP Server Setup

```json
{
  "mcpServers": {
    "memcached": {
      "command": "uvx",
      "args": ["awslabs.memcached-mcp-server@latest"],
      "env": { "AWS_PROFILE": "default", "AWS_REGION": "eu-west-1" }
    }
  }
}
```

## References

- [Memcached MCP Server](https://awslabs.github.io/mcp/servers/memcached-mcp-server)
