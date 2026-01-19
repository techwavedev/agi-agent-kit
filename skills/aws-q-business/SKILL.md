---
name: aws-q-business
description: Amazon Q Business anonymous access via MCP. Use for AI assistant based on knowledge base with anonymous access.
---

# AWS Q Business Skill

> Part of the [AWS skill family](../aws/SKILL.md).

AI assistant based on knowledge base with anonymous access.

## MCP Server Setup

```json
{
  "mcpServers": {
    "q-business": {
      "command": "uvx",
      "args": ["awslabs.amazon-qbusiness-anonymous-mcp-server@latest"],
      "env": { "AWS_PROFILE": "default", "AWS_REGION": "us-east-1" }
    }
  }
}
```

## References

- [Q Business MCP Server](https://awslabs.github.io/mcp/servers/amazon-qbusiness-anonymous-mcp-server)
