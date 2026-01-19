---
name: aws-nova-canvas
description: Amazon Nova Canvas AI image generation via MCP. Use for generating images with text and color guidance.
---

# AWS Nova Canvas Skill

> Part of the [AWS skill family](../aws/SKILL.md).

AI image generation with text and color guidance.

## MCP Server Setup

```json
{
  "mcpServers": {
    "nova-canvas": {
      "command": "uvx",
      "args": ["awslabs.nova-canvas-mcp-server@latest"],
      "env": { "AWS_PROFILE": "default", "AWS_REGION": "us-east-1" }
    }
  }
}
```

## References

- [Nova Canvas MCP Server](https://awslabs.github.io/mcp/servers/nova-canvas-mcp-server)
