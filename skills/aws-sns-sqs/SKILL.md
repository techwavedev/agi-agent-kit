---
name: aws-sns-sqs
description: Amazon SNS/SQS via MCP. Use for event-driven messaging and queue management.
---

# AWS SNS/SQS Skill

> Part of the [AWS skill family](../aws/SKILL.md).

Event-driven messaging and queue management.

## MCP Server Setup

```json
{
  "mcpServers": {
    "sns-sqs": {
      "command": "uvx",
      "args": ["awslabs.amazon-sns-sqs-mcp-server@latest"],
      "env": { "AWS_PROFILE": "default", "AWS_REGION": "eu-west-1" }
    }
  }
}
```

## References

- [SNS/SQS MCP Server](https://awslabs.github.io/mcp/servers/amazon-sns-sqs-mcp-server)
