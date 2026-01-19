---
name: aws-healthlake
description: AWS HealthLake via MCP. Use for FHIR interactions and healthcare datastore management.
---

# AWS HealthLake Skill

> Part of the [AWS skill family](../aws/SKILL.md).

FHIR interactions and HealthLake datastore management.

## MCP Server Setup

```json
{
  "mcpServers": {
    "healthlake": {
      "command": "uvx",
      "args": ["awslabs.healthlake-mcp-server@latest"],
      "env": { "AWS_PROFILE": "default", "AWS_REGION": "us-east-1" }
    }
  }
}
```

## References

- [HealthLake MCP Server](https://awslabs.github.io/mcp/servers/healthlake-mcp-server)
