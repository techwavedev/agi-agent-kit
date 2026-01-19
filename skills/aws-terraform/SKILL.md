---
name: aws-terraform
description: Terraform workflows for AWS with integrated security scanning via Checkov. Use for AWS provider documentation, Terraform Registry module analysis, running terraform/terragrunt commands, and accessing AWS-IA GenAI modules. Supports init, plan, apply, and destroy operations.
---

# AWS Terraform Skill

> Part of the [AWS skill family](../aws/SKILL.md). For CDK, see [aws-iac](../aws-iac/SKILL.md).

Terraform workflows for AWS with security scanning.

## MCP Server Setup

```json
{
  "mcpServers": {
    "terraform": {
      "command": "uvx",
      "args": ["awslabs.terraform-mcp-server@latest"],
      "env": { "FASTMCP_LOG_LEVEL": "ERROR" }
    }
  }
}
```

### Auto-Configure

```bash
python scripts/configure_mcp.py
```

## Features

- **AWS Provider Docs** — Search AWS/AWSCC provider resources
- **Module Analysis** — Analyze Terraform Registry modules
- **Workflow Execution** — Run terraform init/plan/apply/destroy
- **Terragrunt Support** — Multi-environment workflows
- **GenAI Modules** — Bedrock, SageMaker, OpenSearch Serverless
- **Security Scanning** — Checkov integration

## MCP Tools

| Tool                 | Description                                  |
| -------------------- | -------------------------------------------- |
| Search provider docs | Find AWS provider resources and attributes   |
| Module analysis      | Extract inputs, outputs, README from modules |
| Workflow execution   | Run terraform commands directly              |
| Terragrunt execution | Run terragrunt with config flags             |

## MCP Resources

| Resource                                       | Description               |
| ---------------------------------------------- | ------------------------- |
| `terraform://workflow_guide`                   | Security-focused workflow |
| `terraform://aws_best_practices`               | AWS-specific guidance     |
| `terraform://aws_provider_resources_listing`   | AWS provider resources    |
| `terraform://awscc_provider_resources_listing` | AWSCC provider resources  |

## AWS-IA GenAI Modules

| Module                | Purpose                    |
| --------------------- | -------------------------- |
| Amazon Bedrock        | Generative AI applications |
| OpenSearch Serverless | Vector search              |
| SageMaker Endpoint    | ML model hosting           |
| Serverless Streamlit  | AI interfaces              |

## Workflows

### 1. Initialize Project

```
Ask: "Help me set up a Terraform project for AWS"
→ Provides best practices from terraform://workflow_guide
→ Suggests project structure
→ terraform init
```

### 2. Find Provider Resources

```
Ask: "How do I create an S3 bucket in Terraform?"
→ Searches AWS provider docs
→ Returns resource definition and attributes
```

### 3. Analyze Module

```
Ask: "Analyze the terraform-aws-modules/vpc/aws module"
→ Extracts inputs, outputs, README
→ Shows usage patterns
```

### 4. Execute Workflow

```
Ask: "Plan my Terraform changes"
→ Runs terraform plan
→ Shows formatted output
→ Runs Checkov security scan
```

### 5. Deploy with Terragrunt

```
Ask: "Apply terragrunt in my dev environment"
→ Runs terragrunt plan -var-file=dev.tfvars
→ terragrunt apply after confirmation
```

## Prerequisites

```bash
# Install Terraform CLI
brew install terraform

# Install Checkov for security scanning
pip install checkov

# Optional: Terragrunt
brew install terragrunt
```

## Scripts

| Script                     | Purpose                   |
| -------------------------- | ------------------------- |
| `scripts/configure_mcp.py` | Auto-configure MCP client |

## References

- [AWS Terraform MCP Server](https://awslabs.github.io/mcp/servers/terraform-mcp-server)
- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest)
- [AWSCC Provider](https://registry.terraform.io/providers/hashicorp/awscc/latest)
