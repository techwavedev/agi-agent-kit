---
name: aws-cloudwatch-signals
description: Amazon CloudWatch Application Signals via MCP. Use for application monitoring and performance insights.
---

# AWS CloudWatch Application Signals Skill

> Part of the [AWS skill family](../aws/SKILL.md).

Application monitoring and performance insights.

## MCP Server Setup

```json
{
  "mcpServers": {
    "cloudwatch-signals": {
      "command": "uvx",
      "args": ["awslabs.cloudwatch-applicationsignals-mcp-server@latest"],
      "env": { "AWS_PROFILE": "default", "AWS_REGION": "eu-west-1" }
    }
  }
}
```

## References

- [CloudWatch Application Signals MCP Server](https://awslabs.github.io/mcp/servers/cloudwatch-applicationsignals-mcp-server)
