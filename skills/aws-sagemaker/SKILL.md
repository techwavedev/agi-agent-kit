---
name: aws-sagemaker
description: Amazon SageMaker AI resource management via MCP. Use for model development, training, and deployment.
---

# AWS SageMaker Skill

> Part of the [AWS skill family](../aws/SKILL.md).

SageMaker AI resource management and model development.

## MCP Server Setup

```json
{
  "mcpServers": {
    "sagemaker": {
      "command": "uvx",
      "args": ["awslabs.sagemaker-ai-mcp-server@latest"],
      "env": { "AWS_PROFILE": "default", "AWS_REGION": "us-east-1" }
    }
  }
}
```

## References

- [SageMaker AI MCP Server](https://awslabs.github.io/mcp/servers/sagemaker-ai-mcp-server)
