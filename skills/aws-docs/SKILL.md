---
name: aws-docs
description: AWS documentation expert using the AWS Documentation MCP Server. Use for consulting AWS documentation, searching for best practices, getting recommendations on AWS service usage, and generating documentation output. Triggers on queries like "look up AWS documentation on...", "what does AWS recommend for...", "search AWS docs for...", "help me understand AWS...", or any request requiring authoritative AWS technical guidance.
---

# AWS Documentation Skill

Specialist skill for AWS documentation lookup, search, and recommendations using the AWS Documentation MCP Server.

## MCP Server Configuration

Ensure the AWS Documentation MCP Server is configured:

```json
{
  "mcpServers": {
    "aws-docs": {
      "command": "uvx",
      "args": ["awslabs.aws-documentation-mcp-server@latest"],
      "env": {
        "FASTMCP_LOG_LEVEL": "ERROR",
        "AWS_DOCUMENTATION_PARTITION": "aws",
        "MCP_USER_AGENT": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
      },
      "disabled": false,
      "autoApprove": []
    }
  }
}
```

**Environment Variables:**

| Variable                      | Values           | Description                         |
| ----------------------------- | ---------------- | ----------------------------------- |
| `FASTMCP_LOG_LEVEL`           | `ERROR`, `DEBUG` | Log verbosity (use ERROR for prod)  |
| `AWS_DOCUMENTATION_PARTITION` | `aws`, `aws-cn`  | Region partition (default: `aws`)   |
| `MCP_USER_AGENT`              | Browser UA       | Required for corporate proxy bypass |

## MCP Tools Available

### read_documentation

Fetch and convert AWS documentation pages to markdown format.

```python
read_documentation(url: str) -> str
```

**Usage:** Provide a full AWS documentation URL to retrieve its content in markdown.

**Example:**

```
Read the AWS S3 bucket naming rules documentation from:
https://docs.aws.amazon.com/AmazonS3/latest/userguide/bucketnamingrules.html
```

### search_documentation

Search AWS documentation using the official search API.

```python
search_documentation(
    search_phrase: str,
    limit: int = 10,
    product_types: Optional[List[str]] = None,
    guide_types: Optional[List[str]] = None
) -> SearchResponse
```

**Usage:** Search for topics across all AWS documentation.

**Example:**

```
Search AWS docs for "IAM best practices" with limit 5
```

### recommend

Get content recommendations for an AWS documentation page.

```python
recommend(url: str) -> list[dict]
```

**Usage:** Get related content and next steps for a given documentation page.

**Example:**

```
Get recommendations for:
https://docs.aws.amazon.com/AmazonS3/latest/userguide/bucketnamingrules.html
```

## Workflow Patterns

### 1. Documentation Lookup

When user asks about AWS service details:

1. Use `search_documentation` to find relevant pages
2. Use `read_documentation` to fetch full content
3. Summarize key points and cite sources

### 2. Best Practices Research

When user needs AWS recommendations:

1. Search for "[service] best practices" or "[service] guidelines"
2. Read the most relevant documentation pages
3. Extract actionable recommendations
4. Use `recommend` to find related guidance

### 3. Troubleshooting Issues

When user has AWS-related problems:

1. Search for error messages or symptoms
2. Read relevant troubleshooting guides
3. Extract resolution steps
4. Cite official documentation sources

### 4. Documentation Output Generation

When creating AWS-related documentation:

1. Research authoritative AWS sources
2. Extract official terminology and patterns
3. Include proper citations with URLs
4. Follow AWS documentation conventions

## Output Formatting Guidelines

### Citing Sources

Always cite AWS documentation sources:

```markdown
## S3 Bucket Naming Rules

According to [AWS S3 Documentation](https://docs.aws.amazon.com/AmazonS3/latest/userguide/bucketnamingrules.html):

- Bucket names must be between 3-63 characters
- Names can only contain lowercase letters, numbers, and hyphens
- ...
```

### Structured Recommendations

Format recommendations clearly:

```markdown
## AWS Recommendations for [Topic]

### Security

- **Enable versioning**: Protects against accidental deletion
- **Use encryption**: Enable SSE-S3 or SSE-KMS
  - Source: [S3 Security Best Practices](https://docs.aws.amazon.com/...)

### Performance

- **Use transfer acceleration**: For global uploads
- **Multipart uploads**: For files > 100MB
```

## Common Queries

| Query Type          | Tool to Use            | Example                                    |
| ------------------- | ---------------------- | ------------------------------------------ |
| Service overview    | `search_documentation` | "What is AWS Lambda?"                      |
| Configuration guide | `read_documentation`   | "How to configure S3 CORS"                 |
| Best practices      | `search_documentation` | "DynamoDB best practices"                  |
| Error resolution    | `search_documentation` | "S3 AccessDenied error"                    |
| Related content     | `recommend`            | "What else should I know about IAM roles?" |
| Service comparison  | `search_documentation` | "Aurora vs RDS differences"                |
| Quota/limits        | `search_documentation` | "Lambda execution limits"                  |
| Security guidance   | `search_documentation` | "EC2 security best practices"              |

## Integration with Other AWS Skills

This skill integrates with the AWS skills ecosystem:

| Related Skill                  | Integration Point                     |
| ------------------------------ | ------------------------------------- |
| [aws](../aws/SKILL.md)         | Routes documentation queries here     |
| [aws-cli](../aws-cli/SKILL.md) | Lookup CLI command documentation      |
| [aws-eks](../aws-eks/SKILL.md) | EKS-specific documentation and guides |

## References

- [references/common_searches.md](references/common_searches.md) — Pre-defined search patterns for common topics
- [references/documentation_urls.md](references/documentation_urls.md) — Direct URLs to frequently used documentation

## Troubleshooting

### MCP Server Not Responding

1. Verify `uvx` is installed: `pip install uvx`
2. Test server manually: `uvx awslabs.aws-documentation-mcp-server@latest`
3. Check logs with `FASTMCP_LOG_LEVEL=DEBUG`

### Rate Limiting

The AWS Documentation server may throttle requests:

- Wait 30 seconds between intensive searches
- Batch related queries together
- Cache frequently accessed content

### Corporate Proxy Issues

If blocked by corporate firewall, ensure `MCP_USER_AGENT` is set to a browser-like value in the MCP configuration.
