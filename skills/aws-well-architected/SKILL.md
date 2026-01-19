---
name: aws-well-architected
description: AWS Well-Architected Security Assessment via MCP. Use for assessing environments against Security Pillar.
---

# AWS Well-Architected Skill

> Part of the [AWS skill family](../aws/SKILL.md).

Assess AWS environments against Well-Architected Framework Security Pillar.

## MCP Server Setup

```json
{
  "mcpServers": {
    "well-architected": {
      "command": "uvx",
      "args": ["awslabs.well-architected-security-mcp-server@latest"],
      "env": { "AWS_PROFILE": "default", "AWS_REGION": "us-east-1" }
    }
  }
}
```

## References

- [Well-Architected MCP Server](https://awslabs.github.io/mcp/servers/well-architected-security-mcp-server)
