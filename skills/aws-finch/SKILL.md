---
name: aws-finch
description: Local container building with ECR integration via Finch MCP. Use for building containers locally and pushing to Amazon ECR.
---

# AWS Finch Skill

> Part of the [AWS skill family](../aws/SKILL.md).

Local container building with ECR integration.

## MCP Server Setup

```json
{
  "mcpServers": {
    "finch": {
      "command": "uvx",
      "args": ["awslabs.finch-mcp-server@latest"],
      "env": { "AWS_PROFILE": "default", "AWS_REGION": "eu-west-1" }
    }
  }
}
```

## References

- [Finch MCP Server](https://awslabs.github.io/mcp/servers/finch-mcp-server)
