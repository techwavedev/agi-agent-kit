---
name: aws-cloudwatch
description: Amazon CloudWatch via MCP. Use for metrics, alarms, and logs analysis.
---

# AWS CloudWatch Skill

> Part of the [AWS skill family](../aws/SKILL.md).

Metrics, Alarms, and Logs analysis and operational troubleshooting.

## MCP Server Setup

```json
{
  "mcpServers": {
    "cloudwatch": {
      "command": "uvx",
      "args": ["awslabs.cloudwatch-mcp-server@latest"],
      "env": { "AWS_PROFILE": "default", "AWS_REGION": "eu-west-1" }
    }
  }
}
```

## References

- [CloudWatch MCP Server](https://awslabs.github.io/mcp/servers/cloudwatch-mcp-server)
