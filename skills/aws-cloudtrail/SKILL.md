---
name: aws-cloudtrail
description: AWS CloudTrail via MCP. Use for API activity, user, and resource analysis.
---

# AWS CloudTrail Skill

> Part of the [AWS skill family](../aws/SKILL.md).

AWS API Activity, User or Resource analysis using CloudTrail Logs.

## MCP Server Setup

```json
{
  "mcpServers": {
    "cloudtrail": {
      "command": "uvx",
      "args": ["awslabs.cloudtrail-mcp-server@latest"],
      "env": { "AWS_PROFILE": "default", "AWS_REGION": "eu-west-1" }
    }
  }
}
```

## References

- [CloudTrail MCP Server](https://awslabs.github.io/mcp/servers/cloudtrail-mcp-server)
