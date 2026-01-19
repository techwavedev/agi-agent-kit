---
name: aws-data-processing
description: Amazon Data Processing via MCP. Use for AWS Glue and EMR data processing pipelines.
---

# AWS Data Processing Skill

> Part of the [AWS skill family](../aws/SKILL.md).

Data processing tools for AWS Glue and Amazon EMR-EC2.

## MCP Server Setup

```json
{
  "mcpServers": {
    "data-processing": {
      "command": "uvx",
      "args": ["awslabs.aws-dataprocessing-mcp-server@latest"],
      "env": { "AWS_PROFILE": "default", "AWS_REGION": "eu-west-1" }
    }
  }
}
```

## References

- [Data Processing MCP Server](https://awslabs.github.io/mcp/servers/aws-dataprocessing-mcp-server)
