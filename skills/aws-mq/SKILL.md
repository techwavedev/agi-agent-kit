---
name: aws-mq
description: Amazon MQ via MCP. Use for message broker management with RabbitMQ and ActiveMQ.
---

# AWS MQ Skill

> Part of the [AWS skill family](../aws/SKILL.md).

Message broker management for RabbitMQ and ActiveMQ.

## MCP Server Setup

```json
{
  "mcpServers": {
    "mq": {
      "command": "uvx",
      "args": ["awslabs.amazon-mq-mcp-server@latest"],
      "env": { "AWS_PROFILE": "default", "AWS_REGION": "eu-west-1" }
    }
  }
}
```

## References

- [Amazon MQ MCP Server](https://awslabs.github.io/mcp/servers/amazon-mq-mcp-server)
