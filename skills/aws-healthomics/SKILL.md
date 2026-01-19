---
name: aws-healthomics
description: AWS HealthOmics via MCP. Use for lifescience workflows and genomic analysis.
---

# AWS HealthOmics Skill

> Part of the [AWS skill family](../aws/SKILL.md).

Generate, run, debug and optimize lifescience workflows.

## MCP Server Setup

```json
{
  "mcpServers": {
    "healthomics": {
      "command": "uvx",
      "args": ["awslabs.aws-healthomics-mcp-server@latest"],
      "env": { "AWS_PROFILE": "default", "AWS_REGION": "us-east-1" }
    }
  }
}
```

## References

- [HealthOmics MCP Server](https://awslabs.github.io/mcp/servers/aws-healthomics-mcp-server)
