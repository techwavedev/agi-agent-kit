---
name: aws-synthetic-data
description: Synthetic Data via MCP. Use for generating realistic test data for development and ML.
---

# AWS Synthetic Data Skill

> Part of the [AWS skill family](../aws/SKILL.md).

Generate realistic test data for development and ML.

## MCP Server Setup

```json
{
  "mcpServers": {
    "synthetic-data": {
      "command": "uvx",
      "args": ["awslabs.syntheticdata-mcp-server@latest"]
    }
  }
}
```

## References

- [Synthetic Data MCP Server](https://awslabs.github.io/mcp/servers/syntheticdata-mcp-server)
