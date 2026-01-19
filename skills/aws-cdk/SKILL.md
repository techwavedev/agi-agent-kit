---
name: aws-cdk
description: AWS CDK via MCP. Use for CDK development with security compliance using CDK-nag.
---

# AWS CDK Skill

> Part of the [AWS skill family](../aws/SKILL.md). For full IaC hub, see [aws-iac](../aws-iac/SKILL.md).

AWS CDK development with security compliance.

## MCP Server Setup

```json
{
  "mcpServers": {
    "cdk": {
      "command": "uvx",
      "args": ["awslabs.cdk-mcp-server@latest"],
      "env": { "FASTMCP_LOG_LEVEL": "ERROR" }
    }
  }
}
```

## Features

- CDK construct patterns
- CDK-nag compliance checking
- AWS Solutions Constructs patterns
- GenAI CDK constructs

## References

- [CDK MCP Server](https://awslabs.github.io/mcp/servers/cdk-mcp-server)
