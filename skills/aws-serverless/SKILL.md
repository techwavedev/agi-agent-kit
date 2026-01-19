---
name: aws-serverless
description: Complete serverless application lifecycle with SAM CLI. Use for initializing, building, deploying SAM apps, deploying web apps (Express, Next.js) to Lambda, managing domains, viewing logs/metrics, and getting Lambda event schemas.
---

# AWS Serverless Skill

> Part of the [AWS skill family](../aws/SKILL.md). For Lambda tools, see [aws-lambda](../aws-lambda/SKILL.md).

Complete serverless application lifecycle with SAM CLI.

## MCP Server Setup

```json
{
  "mcpServers": {
    "serverless": {
      "command": "uvx",
      "args": ["awslabs.aws-serverless-mcp-server@latest", "--allow-write"],
      "env": {
        "AWS_PROFILE": "default",
        "AWS_REGION": "eu-west-1"
      }
    }
  }
}
```

### Flags

- `--allow-write` — Enable deployment operations
- `--allow-sensitive-data-access` — Access logs and metrics

## Features

- **SAM Lifecycle** — Init, build, deploy SAM applications
- **Web App Deployment** — Deploy Express, Next.js to Lambda
- **Custom Domains** — ACM certificates, Route53 DNS
- **Observability** — Logs and metrics retrieval
- **Templates** — Serverless Land patterns
- **Event Schemas** — Lambda event source schemas

## MCP Tools

### SAM CLI Tools

| Tool               | Description                |
| ------------------ | -------------------------- |
| `sam_init`         | Initialize new SAM project |
| `sam_build`        | Build Lambda functions     |
| `sam_deploy`       | Deploy to AWS              |
| `sam_logs`         | View function logs         |
| `sam_local_invoke` | Test locally               |

### Web App Tools

| Tool                     | Description                       |
| ------------------------ | --------------------------------- |
| `deploy_webapp`          | Deploy fullstack/frontend/backend |
| `configure_domain`       | Set up custom domain              |
| `update_webapp_frontend` | Update S3 assets                  |
| `get_metrics`            | CloudWatch metrics                |
| `webapp_deployment_help` | Deployment guidance               |

### Guidance Tools

| Tool                       | Description              |
| -------------------------- | ------------------------ |
| `get_iac_guidance`         | IaC framework selection  |
| `get_lambda_guidance`      | Lambda best practices    |
| `get_lambda_event_schemas` | Event source schemas     |
| `get_serverless_templates` | Serverless Land patterns |

## Workflows

### 1. Create Lambda Function

```
Ask: "Create a Python Lambda function with API Gateway"
→ sam_init with python runtime
→ sam_build
→ sam_deploy
→ Returns API endpoint
```

### 2. Deploy Web App

```
Ask: "Deploy my Next.js app to Lambda"
→ deploy_webapp with fullstack type
→ configure_domain (optional)
→ Returns CloudFront URL
```

### 3. View Logs

```
Ask: "Show me the logs for my function"
→ sam_logs with function name
→ Returns CloudWatch logs
```

## Prerequisites

```bash
# Install SAM CLI
brew install aws-sam-cli

# Install AWS CLI
brew install awscli
```

## Scripts

| Script                     | Purpose                   |
| -------------------------- | ------------------------- |
| `scripts/configure_mcp.py` | Auto-configure MCP client |

## References

- [AWS Serverless MCP Server](https://awslabs.github.io/mcp/servers/aws-serverless-mcp-server)
- [Serverless Land](https://serverlessland.com/)
- [SAM CLI Docs](https://docs.aws.amazon.com/serverless-application-model/)
