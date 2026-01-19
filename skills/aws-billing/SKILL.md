---
name: aws-billing
description: AWS Billing and Cost Management via MCP. Use for billing management and cost analysis.
---

# AWS Billing Skill

> Part of the [AWS skill family](../aws/SKILL.md).

AWS Billing and Cost Management.

## MCP Server Setup

```json
{
  "mcpServers": {
    "billing": {
      "command": "uvx",
      "args": ["awslabs.billing-cost-management-mcp-server@latest"],
      "env": { "AWS_PROFILE": "default", "AWS_REGION": "us-east-1" }
    }
  }
}
```

## References

- [Billing MCP Server](https://awslabs.github.io/mcp/servers/billing-cost-management-mcp-server)
