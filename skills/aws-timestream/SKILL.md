---
name: aws-timestream
description: Amazon Timestream for InfluxDB via MCP. Use for InfluxDB-compatible time series operations.
---

# AWS Timestream Skill

> Part of the [AWS skill family](../aws/SKILL.md).

InfluxDB-compatible time series operations.

## MCP Server Setup

```json
{
  "mcpServers": {
    "timestream": {
      "command": "uvx",
      "args": ["awslabs.timestream-for-influxdb-mcp-server@latest"],
      "env": { "AWS_PROFILE": "default", "AWS_REGION": "eu-west-1" }
    }
  }
}
```

## References

- [Timestream MCP Server](https://awslabs.github.io/mcp/servers/timestream-for-influxdb-mcp-server)
