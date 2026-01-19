---
name: aws-knowledge
description: Access AWS documentation, API references, best practices, and architectural guidance via AWS Knowledge MCP Server. Use when needing to search AWS docs, get API usage examples, find regional availability info, learn AWS Amplify patterns, or get CDK/CloudFormation guidance. No authentication required.
---

# AWS Knowledge Skill

> Part of the [AWS skill family](../aws/SKILL.md). For CLI operations, see [aws-cli](../aws-cli/SKILL.md).

Access AWS documentation, best practices, and architectural guidance via MCP.

## MCP Server Setup

The AWS Knowledge MCP Server is a **remote HTTP server** — no local installation required.

### Quick Setup

**For clients supporting HTTP transport (recommended):**

```json
{
  "mcpServers": {
    "aws-knowledge": {
      "url": "https://knowledge-mcp.global.api.aws",
      "type": "http"
    }
  }
}
```

**For clients requiring stdio (Claude Desktop, etc.):**

```json
{
  "mcpServers": {
    "aws-knowledge": {
      "command": "uvx",
      "args": ["fastmcp", "run", "https://knowledge-mcp.global.api.aws"]
    }
  }
}
```

### Auto-Configure

```bash
python scripts/configure_mcp.py
```

### Notes

- **No authentication required** — just configure and use
- Subject to rate limits
- No data used for ML training

## MCP Tools Available

| Tool                        | Description                                          |
| --------------------------- | ---------------------------------------------------- |
| `search_documentation`      | Search across AWS docs with optional topic filtering |
| `read_documentation`        | Retrieve AWS doc pages as markdown                   |
| `recommend`                 | Get content recommendations for AWS topics           |
| `list_regions`              | List all AWS regions with IDs and names              |
| `get_regional_availability` | Check service/feature availability by region         |

## Knowledge Sources

The server provides access to:

- AWS Documentation (latest)
- API References
- What's New posts
- Getting Started guides
- AWS Blog posts
- Well-Architected guidance
- Troubleshooting guides
- AWS Amplify docs
- CDK/CloudFormation docs and patterns

## Workflows

### 1. Search for Documentation

```
Use `search_documentation` with query:
- "How to configure S3 bucket policies"
- "EKS best practices for production"
- "Lambda concurrency limits"
```

### 2. Get API Usage Details

```
Use `search_documentation` with topic filter:
- Query: "CreateCluster"
- Topic: "EKS API Reference"
```

### 3. Check Regional Availability

```
Use `get_regional_availability`:
- Service: "eks"
- Feature: "Fargate"
```

### 4. Get Recommendations

```
Use `recommend` for related content:
- Input: Current documentation URL or topic
- Output: Related guides, patterns, examples
```

## Example Queries

| Need            | Query                                                       |
| --------------- | ----------------------------------------------------------- |
| Best practices  | "What are the best practices for securing S3 buckets?"      |
| Getting started | "How do I get started with AWS Lambda?"                     |
| Troubleshooting | "Why am I getting AccessDenied errors in S3?"               |
| Architecture    | "What's the recommended architecture for a serverless API?" |
| IaC             | "Show me a CDK example for creating a VPC"                  |

## Testing

Test the server directly with MCP Inspector:

```bash
npx @modelcontextprotocol/inspector https://knowledge-mcp.global.api.aws
```

## Scripts

| Script                     | Purpose                                         |
| -------------------------- | ----------------------------------------------- |
| `scripts/configure_mcp.py` | Auto-configure MCP client with Knowledge server |

## References

- [AWS Knowledge MCP Server Docs](https://awslabs.github.io/mcp/servers/aws-knowledge-mcp-server)
- [Smithery Registry](https://smithery.ai/server/@FaresYoussef94/aws-knowledge-mcp)
- [Cursor Registry](https://cursor.directory/mcp/aws-knowledge-mcp-1)
