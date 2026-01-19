---
name: aws-bedrock-kb
description: Amazon Bedrock Knowledge Bases retrieval via MCP. Use for querying enterprise knowledge bases with citation support and RAG.
---

# AWS Bedrock Knowledge Bases Skill

> Part of the [AWS skill family](../aws/SKILL.md).

Query enterprise knowledge bases with citation support.

## MCP Server Setup

```json
{
  "mcpServers": {
    "bedrock-kb": {
      "command": "uvx",
      "args": ["awslabs.bedrock-kb-retrieval-mcp-server@latest"],
      "env": { "AWS_PROFILE": "default", "AWS_REGION": "us-east-1" }
    }
  }
}
```

## References

- [Bedrock KB MCP Server](https://awslabs.github.io/mcp/servers/bedrock-kb-retrieval-mcp-server)
