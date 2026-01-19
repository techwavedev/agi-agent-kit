---
name: aws-keyspaces
description: Amazon Keyspaces via MCP. Use for Apache Cassandra-compatible operations.
---

# AWS Keyspaces Skill

> Part of the [AWS skill family](../aws/SKILL.md).

Apache Cassandra-compatible operations.

## MCP Server Setup

```json
{
  "mcpServers": {
    "keyspaces": {
      "command": "uvx",
      "args": ["awslabs.amazon-keyspaces-mcp-server@latest"],
      "env": { "AWS_PROFILE": "default", "AWS_REGION": "eu-west-1" }
    }
  }
}
```

## References

- [Keyspaces MCP Server](https://awslabs.github.io/mcp/servers/amazon-keyspaces-mcp-server)
