---
name: aws-support
description: AWS Support case management via MCP. Use for creating and managing AWS Support cases.
---

# AWS Support Skill

> Part of the [AWS skill family](../aws/SKILL.md).

Create and manage AWS Support cases.

## MCP Server Setup

```json
{
  "mcpServers": {
    "support": {
      "command": "uvx",
      "args": ["awslabs.aws-support-mcp-server@latest"],
      "env": { "AWS_PROFILE": "default", "AWS_REGION": "us-east-1" }
    }
  }
}
```

## References

- [Support MCP Server](https://awslabs.github.io/mcp/servers/aws-support-mcp-server)
