---
name: aws-s3-tables
description: AWS S3 Tables via MCP. Use for managing, querying, and ingesting S3-based tables with SQL support.
---

# AWS S3 Tables Skill

> Part of the [AWS skill family](../aws/SKILL.md).

Manage, query, and ingest S3-based tables with SQL support.

## MCP Server Setup

```json
{
  "mcpServers": {
    "s3-tables": {
      "command": "uvx",
      "args": ["awslabs.s3-tables-mcp-server@latest"],
      "env": { "AWS_PROFILE": "default", "AWS_REGION": "eu-west-1" }
    }
  }
}
```

## References

- [S3 Tables MCP Server](https://awslabs.github.io/mcp/servers/s3-tables-mcp-server)
