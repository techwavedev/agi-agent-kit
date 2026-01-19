---
name: aws-iam
description: AWS IAM via MCP. Use for user, role, group, and policy management.
---

# AWS IAM Skill

> Part of the [AWS skill family](../aws/SKILL.md).

Comprehensive IAM management with security best practices.

## MCP Server Setup

```json
{
  "mcpServers": {
    "iam": {
      "command": "uvx",
      "args": ["awslabs.iam-mcp-server@latest"],
      "env": { "AWS_PROFILE": "default", "AWS_REGION": "us-east-1" }
    }
  }
}
```

## References

- [IAM MCP Server](https://awslabs.github.io/mcp/servers/iam-mcp-server)
