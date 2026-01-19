---
name: aws-git-repo
description: Git Repo Research via MCP. Use for semantic code search and repository analysis.
---

# AWS Git Repo Research Skill

> Part of the [AWS skill family](../aws/SKILL.md).

Semantic code search and repository analysis.

## MCP Server Setup

```json
{
  "mcpServers": {
    "git-repo": {
      "command": "uvx",
      "args": ["awslabs.git-repo-research-mcp-server@latest"]
    }
  }
}
```

## References

- [Git Repo Research MCP Server](https://awslabs.github.io/mcp/servers/git-repo-research-mcp-server)
