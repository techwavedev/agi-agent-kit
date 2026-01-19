---
name: aws-kendra
description: Amazon Kendra enterprise search via MCP. Use for enterprise search and RAG enhancement.
---

# AWS Kendra Skill

> Part of the [AWS skill family](../aws/SKILL.md).

Enterprise search and RAG enhancement.

## MCP Server Setup

```json
{
  "mcpServers": {
    "kendra": {
      "command": "uvx",
      "args": ["awslabs.amazon-kendra-index-mcp-server@latest"],
      "env": { "AWS_PROFILE": "default", "AWS_REGION": "us-east-1" }
    }
  }
}
```

## References

- [Kendra MCP Server](https://awslabs.github.io/mcp/servers/amazon-kendra-index-mcp-server)
