---
name: aws-msk
description: AWS MSK via MCP. Use for managing, monitoring, and optimizing Amazon MSK clusters.
---

# AWS MSK Skill

> Part of the [AWS skill family](../aws/SKILL.md).

Manage, monitor, and optimize Amazon MSK Kafka clusters.

## MCP Server Setup

```json
{
  "mcpServers": {
    "msk": {
      "command": "uvx",
      "args": ["awslabs.aws-msk-mcp-server@latest"],
      "env": { "AWS_PROFILE": "default", "AWS_REGION": "eu-west-1" }
    }
  }
}
```

## References

- [MSK MCP Server](https://awslabs.github.io/mcp/servers/aws-msk-mcp-server)
