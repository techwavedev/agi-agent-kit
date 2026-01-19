---
name: aws-aurora-dsql
description: Amazon Aurora DSQL distributed SQL via MCP. Use for PostgreSQL-compatible distributed SQL operations.
---

# AWS Aurora DSQL Skill

> Part of the [AWS skill family](../aws/SKILL.md).

Distributed SQL with PostgreSQL compatibility.

## MCP Server Setup

```json
{
  "mcpServers": {
    "aurora-dsql": {
      "command": "uvx",
      "args": ["awslabs.aurora-dsql-mcp-server@latest"],
      "env": { "AWS_PROFILE": "default", "AWS_REGION": "us-east-1" }
    }
  }
}
```

## References

- [Aurora DSQL MCP Server](https://awslabs.github.io/mcp/servers/aurora-dsql-mcp-server)
