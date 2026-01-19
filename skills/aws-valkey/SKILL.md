---
name: aws-valkey
description: Amazon ElastiCache/MemoryDB for Valkey via MCP. Use for advanced data structures and caching with Valkey.
---

# AWS Valkey Skill

> Part of the [AWS skill family](../aws/SKILL.md).

Advanced data structures and caching with Valkey.

## MCP Server Setup

```json
{
  "mcpServers": {
    "valkey": {
      "command": "uvx",
      "args": ["awslabs.valkey-mcp-server@latest"],
      "env": { "AWS_PROFILE": "default", "AWS_REGION": "eu-west-1" }
    }
  }
}
```

## References

- [Valkey MCP Server](https://awslabs.github.io/mcp/servers/valkey-mcp-server)
