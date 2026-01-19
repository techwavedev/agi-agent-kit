---
name: aws-aurora-mysql
description: Amazon Aurora MySQL via RDS Data API. Use for MySQL database operations.
---

# AWS Aurora MySQL Skill

> Part of the [AWS skill family](../aws/SKILL.md).

MySQL database operations via RDS Data API.

## MCP Server Setup

```json
{
  "mcpServers": {
    "aurora-mysql": {
      "command": "uvx",
      "args": ["awslabs.mysql-mcp-server@latest"],
      "env": { "AWS_PROFILE": "default", "AWS_REGION": "eu-west-1" }
    }
  }
}
```

## References

- [Aurora MySQL MCP Server](https://awslabs.github.io/mcp/servers/mysql-mcp-server)
