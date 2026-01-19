---
name: aws-dynamodb
description: Amazon DynamoDB operations via MCP. Use for complete DynamoDB operations and table management.
---

# AWS DynamoDB Skill

> Part of the [AWS skill family](../aws/SKILL.md).

Complete DynamoDB operations and table management.

## MCP Server Setup

```json
{
  "mcpServers": {
    "dynamodb": {
      "command": "uvx",
      "args": ["awslabs.dynamodb-mcp-server@latest"],
      "env": { "AWS_PROFILE": "default", "AWS_REGION": "eu-west-1" }
    }
  }
}
```

## References

- [DynamoDB MCP Server](https://awslabs.github.io/mcp/servers/dynamodb-mcp-server)
