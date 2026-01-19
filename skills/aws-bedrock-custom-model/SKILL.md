---
name: aws-bedrock-custom-model
description: Amazon Bedrock Custom Model Import via MCP. Use for managing custom models in Bedrock for on-demand inference.
---

# AWS Bedrock Custom Model Skill

> Part of the [AWS skill family](../aws/SKILL.md).

Manage custom models in Bedrock for on-demand inference.

## MCP Server Setup

```json
{
  "mcpServers": {
    "bedrock-custom-model": {
      "command": "uvx",
      "args": ["awslabs.aws-bedrock-custom-model-import-mcp-server@latest"],
      "env": { "AWS_PROFILE": "default", "AWS_REGION": "us-east-1" }
    }
  }
}
```

## References

- [Bedrock Custom Model MCP Server](https://awslabs.github.io/mcp/servers/aws-bedrock-custom-model-import-mcp-server)
