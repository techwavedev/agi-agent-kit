---
name: aws-documentdb
description: Amazon DocumentDB via MCP. Use for MongoDB-compatible document database operations.
---

# AWS DocumentDB Skill

> Part of the [AWS skill family](../aws/SKILL.md).

MongoDB-compatible document database operations.

## MCP Server Setup

```json
{
  "mcpServers": {
    "documentdb": {
      "command": "uvx",
      "args": ["awslabs.documentdb-mcp-server@latest"],
      "env": { "AWS_PROFILE": "default", "AWS_REGION": "eu-west-1" }
    }
  }
}
```

## References

- [DocumentDB MCP Server](https://awslabs.github.io/mcp/servers/documentdb-mcp-server)
