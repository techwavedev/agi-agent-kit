---
name: aws-iot-sitewise
description: AWS IoT SiteWise via MCP. Use for industrial IoT asset management, data ingestion, monitoring, and analytics.
---

# AWS IoT SiteWise Skill

> Part of the [AWS skill family](../aws/SKILL.md).

Industrial IoT asset management and analytics.

## MCP Server Setup

```json
{
  "mcpServers": {
    "iot-sitewise": {
      "command": "uvx",
      "args": ["awslabs.aws-iot-sitewise-mcp-server@latest"],
      "env": { "AWS_PROFILE": "default", "AWS_REGION": "eu-west-1" }
    }
  }
}
```

## References

- [IoT SiteWise MCP Server](https://awslabs.github.io/mcp/servers/aws-iot-sitewise-mcp-server)
