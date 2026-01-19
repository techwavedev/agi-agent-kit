---
name: aws-iac
description: Infrastructure as Code for AWS using CDK, CloudFormation, or Terraform via MCP servers. Use for creating IaC templates, deploying infrastructure, managing resources declaratively, getting CDK patterns, or running Terraform workflows. Includes security scanning with CDK Nag and Checkov.
---

# AWS IaC Skill

> Part of the [AWS skill family](../aws/SKILL.md). For CLI operations, see [aws-api](../aws-api/SKILL.md).

Infrastructure as Code for AWS using CDK, CloudFormation, or Terraform.

## Choose Your Tool

| Tool               | MCP Server                     | Best For                                     |
| ------------------ | ------------------------------ | -------------------------------------------- |
| **CDK**            | `awslabs.cdk-mcp-server`       | TypeScript/Python apps, constructs, patterns |
| **CloudFormation** | `awslabs.cfn-mcp-server`       | Direct resource management, templates        |
| **Terraform**      | `awslabs.terraform-mcp-server` | HCL workflows, multi-cloud, modules          |

## MCP Server Setup

### CDK Server

```json
{
  "mcpServers": {
    "cdk": {
      "command": "uvx",
      "args": ["awslabs.cdk-mcp-server@latest"],
      "env": { "FASTMCP_LOG_LEVEL": "ERROR" }
    }
  }
}
```

### CloudFormation Server

```json
{
  "mcpServers": {
    "cloudformation": {
      "command": "uvx",
      "args": ["awslabs.cfn-mcp-server@latest"],
      "env": {
        "AWS_PROFILE": "default",
        "AWS_REGION": "eu-west-1"
      }
    }
  }
}
```

### Terraform Server

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

### All IaC Servers (Full Setup)

```bash
python scripts/configure_mcp.py --all
```

## CDK Tools

| Tool                              | Description                        |
| --------------------------------- | ---------------------------------- |
| `CDKGeneralGuidance`              | Best practices for CDK apps        |
| `GetAwsSolutionsConstructPattern` | Find vetted architecture patterns  |
| `SearchGenAICDKConstructs`        | Discover GenAI CDK constructs      |
| `GenerateBedrockAgentSchema`      | Create OpenAPI schemas for Bedrock |
| `ExplainCDKNagRule`               | Understand CDK Nag security rules  |
| `CheckCDKNagSuppressions`         | Validate CDK Nag suppressions      |

### CDK Workflow

```
1. CDKGeneralGuidance → Get best practices
2. cdk init app → Initialize project
3. GetAwsSolutionsConstructPattern → Find patterns
4. Implement constructs
5. cdk synth → Generate template
6. ExplainCDKNagRule → Fix security issues
7. cdk deploy → Deploy stack
```

## CloudFormation Tools

| Tool                              | Description                               |
| --------------------------------- | ----------------------------------------- |
| `create_resource`                 | Create AWS resource via Cloud Control API |
| `get_resource`                    | Get resource details                      |
| `update_resource`                 | Update resource properties                |
| `delete_resource`                 | Delete resource                           |
| `list_resources`                  | List resources by type                    |
| `get_resource_schema_information` | Get resource schema                       |
| `create_template`                 | Generate CFN template from resources      |

### CloudFormation Workflow

```
1. list_resources → See existing resources
2. get_resource_schema_information → Understand properties
3. create_resource → Create with declarative config
4. create_template → Export as reusable template
```

## Terraform Tools

| Tool               | Description                        |
| ------------------ | ---------------------------------- |
| AWS Provider docs  | Search provider resources          |
| Module analysis    | Analyze Terraform Registry modules |
| Workflow execution | Run terraform init/plan/apply      |
| Terragrunt support | Multi-environment workflows        |

### Terraform Resources

- `terraform://workflow_guide` — Security-focused workflow
- `terraform://aws_best_practices` — AWS-specific guidance
- `terraform://aws_provider_resources_listing` — AWS resources

## Prerequisites

### CDK

```bash
npm install -g aws-cdk
uv python install 3.10
```

### Terraform

```bash
# Install Terraform CLI
brew install terraform

# Install Checkov for security scanning
pip install checkov
```

## Scripts

| Script                     | Purpose                        |
| -------------------------- | ------------------------------ |
| `scripts/configure_mcp.py` | Auto-configure IaC MCP servers |

## References

- [AWS CDK MCP Server](https://awslabs.github.io/mcp/servers/cdk-mcp-server)
- [CloudFormation MCP Server](https://awslabs.github.io/mcp/servers/cfn-mcp-server)
- [Terraform MCP Server](https://awslabs.github.io/mcp/servers/terraform-mcp-server)
