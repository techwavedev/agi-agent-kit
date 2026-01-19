---
name: aws-bedrock-agentcore
description: Amazon Bedrock AgentCore via MCP. Use for building, deploying, and managing intelligent agents.
---

# AWS Bedrock AgentCore Skill

> Part of the [AWS skill family](../aws/SKILL.md).

Build, deploy, and manage intelligent agents with memory and OAuth.

## MCP Server Setup

```json
{
  "mcpServers": {
    "bedrock-agentcore": {
      "command": "uvx",
      "args": ["awslabs.amazon-bedrock-agentcore-mcp-server@latest"],
      "env": { "AWS_PROFILE": "default", "AWS_REGION": "us-east-1" }
    }
  }
}
```

## References

- [Bedrock AgentCore MCP Server](https://awslabs.github.io/mcp/servers/amazon-bedrock-agentcore-mcp-server)
