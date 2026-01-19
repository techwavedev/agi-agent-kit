---
name: aws-ecs
description: Amazon ECS container orchestration and application deployment via MCP. Use for deploying containers, managing services, task definitions, and cluster operations.
---

# AWS ECS Skill

> Part of the [AWS skill family](../aws/SKILL.md).

Container orchestration and ECS application deployment.

## MCP Server Setup

```json
{
  "mcpServers": {
    "ecs": {
      "command": "uvx",
      "args": ["awslabs.ecs-mcp-server@latest"],
      "env": { "AWS_PROFILE": "default", "AWS_REGION": "eu-west-1" }
    }
  }
}
```

## References

- [ECS MCP Server](https://awslabs.github.io/mcp/servers/ecs-mcp-server)
