---
name: aws-redshift
description: Amazon Redshift via MCP. Use for discovering, exploring, and querying Redshift clusters and serverless workgroups.
---

# AWS Redshift Skill

> Part of the [AWS skill family](../aws/SKILL.md).

Discover, explore, and query Redshift data warehouses.

## MCP Server Setup

```json
{
  "mcpServers": {
    "redshift": {
      "command": "uvx",
      "args": ["awslabs.redshift-mcp-server@latest"],
      "env": { "AWS_PROFILE": "default", "AWS_REGION": "eu-west-1" }
    }
  }
}
```

## References

- [Redshift MCP Server](https://awslabs.github.io/mcp/servers/redshift-mcp-server)
