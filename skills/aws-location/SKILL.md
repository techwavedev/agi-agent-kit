---
name: aws-location
description: Amazon Location Service via MCP. Use for place search, geocoding, and route optimization.
---

# AWS Location Skill

> Part of the [AWS skill family](../aws/SKILL.md).

Place search, geocoding, and route optimization.

## MCP Server Setup

```json
{
  "mcpServers": {
    "location": {
      "command": "uvx",
      "args": ["awslabs.aws-location-mcp-server@latest"],
      "env": { "AWS_PROFILE": "default", "AWS_REGION": "eu-west-1" }
    }
  }
}
```

## References

- [Location Service MCP Server](https://awslabs.github.io/mcp/servers/aws-location-mcp-server)
