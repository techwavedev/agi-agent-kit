---
name: aws-appsync
description: AWS AppSync via MCP. Use for backend API management and GraphQL operations.
---

# AWS AppSync Skill

> Part of the [AWS skill family](../aws/SKILL.md).

AWS AppSync backend API management and operations execution.

## MCP Server Setup

```json
{
  "mcpServers": {
    "appsync": {
      "command": "uvx",
      "args": ["awslabs.aws-appsync-mcp-server@latest"],
      "env": { "AWS_PROFILE": "default", "AWS_REGION": "eu-west-1" }
    }
  }
}
```

## References

- [AppSync MCP Server](https://awslabs.github.io/mcp/servers/aws-appsync-mcp-server)
