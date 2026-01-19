# AWS MCP Servers Reference

Complete list of AWS MCP servers from [awslabs/mcp](https://awslabs.github.io/mcp/).

## Core Servers

| Server         | Package                        | Description               |
| -------------- | ------------------------------ | ------------------------- |
| AWS API        | `awslabs.aws-api-mcp-server`   | General AWS CLI commands  |
| CloudFormation | `awslabs.cfn-mcp-server`       | CloudFormation management |
| CDK            | `awslabs.cdk-mcp-server`       | AWS CDK development       |
| Terraform      | `awslabs.terraform-mcp-server` | Terraform workflows       |

## Container & Kubernetes

| Server | Package                    | Description                   |
| ------ | -------------------------- | ----------------------------- |
| EKS    | `awslabs.eks-mcp-server`   | Kubernetes cluster management |
| ECS    | `awslabs.ecs-mcp-server`   | Container orchestration       |
| Finch  | `awslabs.finch-mcp-server` | Local container building      |

## Serverless

| Server      | Package                             | Description              |
| ----------- | ----------------------------------- | ------------------------ |
| Serverless  | `awslabs.aws-serverless-mcp-server` | SAM CLI lifecycle        |
| Lambda Tool | `awslabs.lambda-tool-mcp-server`    | Execute Lambda functions |

## Database

| Server            | Package                                | Description           |
| ----------------- | -------------------------------------- | --------------------- |
| DynamoDB          | `awslabs.dynamodb-mcp-server`          | DynamoDB operations   |
| Aurora PostgreSQL | `awslabs.aurora-postgresql-mcp-server` | PostgreSQL on Aurora  |
| Aurora MySQL      | `awslabs.aurora-mysql-mcp-server`      | MySQL on Aurora       |
| DocumentDB        | `awslabs.documentdb-mcp-server`        | DocumentDB operations |
| Neptune           | `awslabs.neptune-mcp-server`           | Graph database        |

## AI & ML

| Server      | Package                                   | Description              |
| ----------- | ----------------------------------------- | ------------------------ |
| Bedrock KB  | `awslabs.bedrock-kb-retrieval-mcp-server` | Knowledge base retrieval |
| Kendra      | `awslabs.amazon-kendra-index-mcp-server`  | Enterprise search        |
| Nova Canvas | `awslabs.amazon-nova-canvas-mcp-server`   | Image generation         |
| SageMaker   | `awslabs.sagemaker-mcp-server`            | ML workflows             |

## Recommended Configuration

For general AWS development:

```json
{
  "mcpServers": {
    "aws-api": {
      "command": "uvx",
      "args": ["awslabs.aws-api-mcp-server@latest"],
      "env": { "AWS_PROFILE": "default", "AWS_REGION": "eu-west-1" }
    },
    "cloudformation": {
      "command": "uvx",
      "args": ["awslabs.cfn-mcp-server@latest"],
      "env": { "AWS_PROFILE": "default", "AWS_REGION": "eu-west-1" }
    }
  }
}
```

For Kubernetes workloads, add:

```json
{
  "mcpServers": {
    "eks": {
      "command": "uvx",
      "args": [
        "awslabs.eks-mcp-server@latest",
        "--allow-write",
        "--allow-sensitive-data-access"
      ],
      "env": { "AWS_PROFILE": "default", "AWS_REGION": "eu-west-1" }
    }
  }
}
```

## Installation

All servers use `uvx` (recommended) or `pip`:

```bash
# Install uvx
pip install uvx

# Run any server
uvx awslabs.<server-name>@latest
```
