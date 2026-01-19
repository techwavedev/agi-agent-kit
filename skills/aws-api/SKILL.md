---
name: aws-api
description: Execute AWS CLI commands through AI assistance via AWS API MCP Server. Use for any AWS operation including creating resources, managing infrastructure, running CLI commands, and getting command suggestions. Supports all AWS services with command validation and hallucination protection.
---

# AWS API Skill

> Part of the [AWS skill family](../aws/SKILL.md). For credentials, see [aws-cli](../aws-cli/SKILL.md).

Execute AWS CLI commands through AI assistance with validation and safety controls.

## MCP Server Setup

### Quick Setup

```json
{
  "mcpServers": {
    "aws-api": {
      "command": "uvx",
      "args": ["awslabs.aws-api-mcp-server@latest"],
      "env": {
        "AWS_PROFILE": "default",
        "AWS_REGION": "eu-west-1"
      }
    }
  }
}
```

### Auto-Configure

```bash
python scripts/configure_mcp.py --profile default --region eu-west-1
```

### Read-Only Mode (Safer)

```json
{
  "mcpServers": {
    "aws-api": {
      "command": "uvx",
      "args": ["awslabs.aws-api-mcp-server@latest"],
      "env": {
        "AWS_PROFILE": "default",
        "AWS_REGION": "eu-west-1",
        "READ_OPERATIONS_ONLY": "true"
      }
    }
  }
}
```

## MCP Tools Available

| Tool                   | Description                                            |
| ---------------------- | ------------------------------------------------------ |
| `call_aws`             | Execute AWS CLI commands with validation               |
| `suggest_aws_commands` | Get command suggestions from natural language          |
| `get_execution_plan`   | Step-by-step guidance for complex tasks (experimental) |

## Features

- **All AWS Services** — Supports every AWS CLI command
- **Command Validation** — Validates before execution
- **Hallucination Protection** — Only valid CLI commands allowed
- **Read-Only Mode** — Disable mutations for safe exploration
- **Latest APIs** — Access services released after model training

## Configuration Options

| Variable                   | Default   | Description                    |
| -------------------------- | --------- | ------------------------------ |
| `AWS_PROFILE`              | default   | AWS profile to use             |
| `AWS_REGION`               | us-east-1 | Default region                 |
| `READ_OPERATIONS_ONLY`     | false     | Disable write operations       |
| `REQUIRE_MUTATION_CONSENT` | false     | Confirm before mutations       |
| `AWS_API_MCP_WORKING_DIR`  | temp      | Working directory for file ops |

## Workflows

### 1. Explore Resources (Read-Only)

```
Ask: "List all my S3 buckets"
→ Uses `suggest_aws_commands` to find: aws s3 ls
→ Executes via `call_aws`
```

### 2. Create Resources

```
Ask: "Create an S3 bucket called my-new-bucket in eu-west-1"
→ Suggests: aws s3 mb s3://my-new-bucket --region eu-west-1
→ Executes after validation
```

### 3. Complex Operations

```
Ask: "Help me set up a VPC with public and private subnets"
→ Uses `get_execution_plan` for step-by-step guidance
→ Executes each step with validation
```

### 4. Get Command Help

```
Ask: "What's the command to list EC2 instances with their tags?"
→ Uses `suggest_aws_commands` to provide options with parameters
```

## Example Commands

| Task                  | Suggested Command                              |
| --------------------- | ---------------------------------------------- |
| List EC2 instances    | `aws ec2 describe-instances`                   |
| Create S3 bucket      | `aws s3 mb s3://bucket-name`                   |
| List Lambda functions | `aws lambda list-functions`                    |
| Describe EKS cluster  | `aws eks describe-cluster --name cluster-name` |
| Get caller identity   | `aws sts get-caller-identity`                  |

## Scripts

| Script                     | Purpose                   |
| -------------------------- | ------------------------- |
| `scripts/configure_mcp.py` | Auto-configure MCP client |

## Security Best Practices

1. **Use Read-Only Mode** for exploration: `READ_OPERATIONS_ONLY=true`
2. **Require Consent** for mutations: `REQUIRE_MUTATION_CONSENT=true`
3. **Use Least-Privilege IAM** — Limit the profile's permissions
4. **Review Commands** — Check suggested commands before execution

## References

- [AWS API MCP Server Docs](https://awslabs.github.io/mcp/servers/aws-api-mcp-server)
- [AWS CLI Command Reference](https://docs.aws.amazon.com/cli/latest/)
