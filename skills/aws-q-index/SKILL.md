---
name: aws-q-index
description: Amazon Q Index search via MCP. Use for searching through enterprise's Q index.
---

# AWS Q Index Skill

> Part of the [AWS skill family](../aws/SKILL.md).

Search through enterprise's Q index.

## MCP Server Setup

```json
{
  "mcpServers": {
    "q-index": {
      "command": "uvx",
      "args": ["awslabs.amazon-qindex-mcp-server@latest"],
      "env": { "AWS_PROFILE": "default", "AWS_REGION": "us-east-1" }
    }
  }
}
```

## References

- [Q Index MCP Server](https://awslabs.github.io/mcp/servers/amazon-qindex-mcp-server)
