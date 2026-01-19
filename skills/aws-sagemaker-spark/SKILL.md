---
name: aws-sagemaker-spark
description: SageMaker Unified Studio Spark via MCP. Use for Spark troubleshooting, code recommendation, and upgrades.
---

# AWS SageMaker Spark Skill

> Part of the [AWS skill family](../aws/SKILL.md).

Apache Spark troubleshooting, code recommendation, and upgrades.

## MCP Server Setup

```json
{
  "mcpServers": {
    "sagemaker-spark": {
      "command": "uvx",
      "args": [
        "awslabs.sagemaker-unified-studio-spark-troubleshooting-mcp-server@latest"
      ],
      "env": { "AWS_PROFILE": "default", "AWS_REGION": "us-east-1" }
    }
  }
}
```

## References

- [SageMaker Spark MCP Server](https://awslabs.github.io/mcp/servers/sagemaker-unified-studio-spark-troubleshooting-mcp-server)
