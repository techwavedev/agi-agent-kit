---
name: aws-document-loader
description: Document parsing and content extraction via MCP. Use for loading and parsing documents for AI processing.
---

# AWS Document Loader Skill

> Part of the [AWS skill family](../aws/SKILL.md).

Document parsing and content extraction.

## MCP Server Setup

```json
{
  "mcpServers": {
    "document-loader": {
      "command": "uvx",
      "args": ["awslabs.document-loader-mcp-server@latest"]
    }
  }
}
```

## References

- [Document Loader MCP Server](https://awslabs.github.io/mcp/servers/document-loader-mcp-server)
