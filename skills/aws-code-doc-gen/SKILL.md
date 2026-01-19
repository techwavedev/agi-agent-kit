---
name: aws-code-doc-gen
description: Code Documentation Generation via MCP. Use for automated documentation from code analysis.
---

# AWS Code Doc Gen Skill

> Part of the [AWS skill family](../aws/SKILL.md).

Automated documentation from code analysis.

## MCP Server Setup

```json
{
  "mcpServers": {
    "code-doc-gen": {
      "command": "uvx",
      "args": ["awslabs.code-doc-gen-mcp-server@latest"]
    }
  }
}
```

## References

- [Code Doc Gen MCP Server](https://awslabs.github.io/mcp/servers/code-doc-gen-mcp-server)
