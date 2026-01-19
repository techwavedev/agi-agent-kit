---
name: aws-bedrock-data-automation
description: Amazon Bedrock Data Automation via MCP. Use for analyzing documents, images, videos, and audio files.
---

# AWS Bedrock Data Automation Skill

> Part of the [AWS skill family](../aws/SKILL.md).

Analyze documents, images, videos, and audio files.

## MCP Server Setup

```json
{
  "mcpServers": {
    "bedrock-data-automation": {
      "command": "uvx",
      "args": ["awslabs.aws-bedrock-data-automation-mcp-server@latest"],
      "env": { "AWS_PROFILE": "default", "AWS_REGION": "us-east-1" }
    }
  }
}
```

## References

- [Bedrock Data Automation MCP Server](https://awslabs.github.io/mcp/servers/aws-bedrock-data-automation-mcp-server)
