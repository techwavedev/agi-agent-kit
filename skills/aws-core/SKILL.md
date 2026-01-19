---
name: aws-core
description: AWS Core MCP Server. Use for intelligent planning and AWS MCP server orchestration.
---

# AWS Core Skill

> Part of the [AWS skill family](../aws/SKILL.md).

Intelligent planning and AWS MCP server orchestration.

## MCP Server Setup

```json
{
  "mcpServers": {
    "core": {
      "command": "uvx",
      "args": ["awslabs.core-mcp-server@latest"],
      "env": { "AWS_PROFILE": "default", "AWS_REGION": "eu-west-1" }
    }
  }
}
```

## References

- [Core MCP Server](https://awslabs.github.io/mcp/servers/core-mcp-server)
