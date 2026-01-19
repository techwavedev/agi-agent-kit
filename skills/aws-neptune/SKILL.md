---
name: aws-neptune
description: Amazon Neptune graph database via MCP. Use for graph queries with openCypher and Gremlin.
---

# AWS Neptune Skill

> Part of the [AWS skill family](../aws/SKILL.md).

Graph database queries with openCypher and Gremlin.

## MCP Server Setup

```json
{
  "mcpServers": {
    "neptune": {
      "command": "uvx",
      "args": ["awslabs.amazon-neptune-mcp-server@latest"],
      "env": { "AWS_PROFILE": "default", "AWS_REGION": "eu-west-1" }
    }
  }
}
```

## References

- [Neptune MCP Server](https://awslabs.github.io/mcp/servers/amazon-neptune-mcp-server)
