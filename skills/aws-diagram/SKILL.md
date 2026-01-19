---
name: aws-diagram
description: AWS Diagram via MCP. Use for generating architecture diagrams and technical illustrations.
---

# AWS Diagram Skill

> Part of the [AWS skill family](../aws/SKILL.md).

Generate architecture diagrams and technical illustrations.

## MCP Server Setup

```json
{
  "mcpServers": {
    "diagram": {
      "command": "uvx",
      "args": ["awslabs.aws-diagram-mcp-server@latest"]
    }
  }
}
```

## References

- [AWS Diagram MCP Server](https://awslabs.github.io/mcp/servers/aws-diagram-mcp-server)
