---
name: aws-aurora-postgresql
description: Amazon Aurora PostgreSQL via RDS Data API. Use for PostgreSQL database operations.
---

# AWS Aurora PostgreSQL Skill

> Part of the [AWS skill family](../aws/SKILL.md).

PostgreSQL database operations via RDS Data API.

## MCP Server Setup

```json
{
  "mcpServers": {
    "aurora-postgresql": {
      "command": "uvx",
      "args": ["awslabs.postgres-mcp-server@latest"],
      "env": { "AWS_PROFILE": "default", "AWS_REGION": "eu-west-1" }
    }
  }
}
```

## References

- [Aurora PostgreSQL MCP Server](https://awslabs.github.io/mcp/servers/postgres-mcp-server)
