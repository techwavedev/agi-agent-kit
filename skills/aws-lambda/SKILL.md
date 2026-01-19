---
name: aws-lambda
description: Execute AWS Lambda functions as AI tools for private resource access. Use when you need AI to invoke Lambda functions that access VPC resources, databases, internal APIs, or other AWS services without direct network access. Supports function filtering by prefix, list, or tags.
---

# AWS Lambda Tool Skill

> Part of the [AWS skill family](../aws/SKILL.md). For serverless deployment, see [aws-iac](../aws-iac/SKILL.md).

Execute Lambda functions as AI tools for private resource access.

## MCP Server Setup

```json
{
  "mcpServers": {
    "lambda": {
      "command": "uvx",
      "args": ["awslabs.lambda-tool-mcp-server@latest"],
      "env": {
        "AWS_PROFILE": "default",
        "AWS_REGION": "eu-west-1",
        "FUNCTION_PREFIX": "ai-tools-"
      }
    }
  }
}
```

### Auto-Configure

```bash
python scripts/configure_mcp.py --prefix ai-tools-
```

## Features

- **Lambda as Tools** — AI invokes Lambda functions directly
- **Private Access** — Access VPC resources, databases, internal APIs
- **Segregation of Duties** — AI only invokes, Lambda has permissions
- **Schema Support** — EventBridge Schema Registry for input validation
- **Flexible Filtering** — By prefix, list, or tags

## Architecture

```
Model → MCP Client → Lambda MCP Server → Lambda Function
                                              ↓
                                    ├── Other AWS Services
                                    ├── VPC Resources
                                    └── Internet
```

## Configuration

| Variable                            | Description                     |
| ----------------------------------- | ------------------------------- |
| `FUNCTION_PREFIX`                   | Filter functions by name prefix |
| `FUNCTION_LIST`                     | Comma-separated function names  |
| `FUNCTION_TAG_KEY`                  | Filter by tag key               |
| `FUNCTION_TAG_VALUE`                | Filter by tag value             |
| `FUNCTION_INPUT_SCHEMA_ARN_TAG_KEY` | Tag containing schema ARN       |

### Filter Methods

**By Prefix:**

```json
"env": { "FUNCTION_PREFIX": "ai-tools-" }
```

**By List:**

```json
"env": { "FUNCTION_LIST": "query-db, send-email, fetch-data" }
```

**By Tag:**

```json
"env": {
  "FUNCTION_TAG_KEY": "mcp-enabled",
  "FUNCTION_TAG_VALUE": "true"
}
```

## Workflows

### 1. Query Private Database

```
Ask: "Query the users table for active accounts"
→ Invokes Lambda with VPC access to RDS
→ Returns query results
```

### 2. Access Internal API

```
Ask: "Get the latest order status from our internal system"
→ Invokes Lambda in VPC with API access
→ Returns order data
```

### 3. Send Notifications

```
Ask: "Send a notification to the ops team"
→ Invokes Lambda with SNS/SES permissions
→ Sends notification
```

## Best Practices

1. **Least Privilege** — Lambda role only gets needed permissions
2. **Input Validation** — Use EventBridge schemas
3. **Prefix Naming** — Use consistent prefix for AI tools
4. **VPC Isolation** — Place sensitive functions in VPC
5. **Logging** — Enable CloudWatch for audit trail

## Scripts

| Script                     | Purpose                   |
| -------------------------- | ------------------------- |
| `scripts/configure_mcp.py` | Auto-configure MCP client |

## References

- [AWS Lambda Tool MCP Server](https://awslabs.github.io/mcp/servers/lambda-tool-mcp-server)
- [EventBridge Schema Registry](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-schema.html)
