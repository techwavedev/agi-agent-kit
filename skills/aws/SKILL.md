---
name: aws
description: AWS cloud operations hub. Use for any AWS-related task including EKS, Lambda, Step Functions, networking, pricing, and IaC. This skill routes to specialized sub-skills and provides shared context (profiles, regions) across all AWS operations. Start here for AWS work.
---

# AWS Skill

Central hub for AWS cloud operations. Routes to 14 specialized sub-skills.

## Quick Start

### 1. Set up credentials

```bash
# List existing profiles
python aws-cli/scripts/list_profiles.py

# Create new profile
python aws-cli/scripts/create_profile.py --profile myprofile --access-key AKIA... --secret-key ...

# Switch profile
eval $(python aws-cli/scripts/switch_profile.py --profile myprofile)
```

### 2. Configure MCP servers

Each sub-skill has its own `configure_mcp.py` script.

## Sub-Skills

| Skill                                              | Purpose           | When to Use                                  |
| -------------------------------------------------- | ----------------- | -------------------------------------------- |
| [aws-api](../aws-api/SKILL.md)                     | AWS CLI via MCP   | Execute any AWS CLI command                  |
| [aws-ccapi](../aws-ccapi/SKILL.md)                 | Cloud Control API | Declarative resource CRUD with security      |
| [aws-cfn](../aws-cfn/SKILL.md)                     | CloudFormation    | Template generation, resource schemas        |
| [aws-cli](../aws-cli/SKILL.md)                     | Credentials       | Profile management, SSO, switching           |
| [aws-cost-explorer](../aws-cost-explorer/SKILL.md) | Cost Explorer     | Analyze actual costs, forecasts              |
| [aws-docs](../aws-docs/SKILL.md)                   | Documentation     | Best practices, troubleshooting              |
| [aws-eks](../aws-eks/SKILL.md)                     | EKS               | Kubernetes clusters, deployments             |
| [aws-iac](../aws-iac/SKILL.md)                     | IaC Hub           | CDK, CloudFormation, Terraform               |
| [aws-knowledge](../aws-knowledge/SKILL.md)         | Knowledge         | Search docs, API refs, regional availability |
| [aws-lambda](../aws-lambda/SKILL.md)               | Lambda Tools      | Invoke functions as AI tools                 |
| [aws-network](../aws-network/SKILL.md)             | Networking        | VPC, TGW, Cloud WAN troubleshooting          |
| [aws-pricing](../aws-pricing/SKILL.md)             | Pricing           | Lookup prices, estimate costs                |
| [aws-serverless](../aws-serverless/SKILL.md)       | Serverless        | SAM apps, web deployments                    |
| [aws-stepfunctions](../aws-stepfunctions/SKILL.md) | Step Functions    | Execute workflows as tools                   |
| [aws-terraform](../aws-terraform/SKILL.md)         | Terraform         | HCL workflows, modules                       |

## Routing Guide

**Credentials & Profiles:**
→ `aws-cli`

**Execute AWS CLI Commands:**
→ `aws-api`

**Declarative Resource Management:**
→ `aws-ccapi` (with security scanning)
→ `aws-cfn` (templates)

**Infrastructure as Code:**
→ `aws-iac` (hub for CDK/CFN/TF)
→ `aws-terraform` (Terraform specific)

**Documentation & Knowledge:**
→ `aws-docs` (documentation lookup)
→ `aws-knowledge` (search, regional availability)

**Kubernetes:**
→ `aws-eks`

**Serverless:**
→ `aws-serverless` (SAM, web apps)
→ `aws-lambda` (invoke functions)
→ `aws-stepfunctions` (execute workflows)

**Networking:**
→ `aws-network` (troubleshooting, flow logs)

**Costs:**
→ `aws-pricing`

## Shared Context

All AWS sub-skills inherit from the active profile:

```bash
export AWS_PROFILE=myprofile
export AWS_REGION=eu-west-1
```

## MCP Servers Overview

```json
{
  "mcpServers": {
    "aws-api": {
      "command": "uvx",
      "args": ["awslabs.aws-api-mcp-server@latest"]
    },
    "aws-knowledge": {
      "url": "https://knowledge-mcp.global.api.aws",
      "type": "http"
    },
    "ccapi": { "command": "uvx", "args": ["awslabs.ccapi-mcp-server@latest"] },
    "eks": { "command": "uvx", "args": ["awslabs.eks-mcp-server@latest"] },
    "serverless": {
      "command": "uvx",
      "args": ["awslabs.aws-serverless-mcp-server@latest"]
    },
    "network": {
      "command": "uvx",
      "args": ["awslabs.aws-network-mcp-server@latest"]
    },
    "pricing": {
      "command": "uvx",
      "args": ["awslabs.aws-pricing-mcp-server@latest"]
    }
  }
}
```

See [references/mcp_servers.md](references/mcp_servers.md) for complete list.

## Adding New AWS Sub-Skills

1. Create `skills/aws-<service>/` directory
2. Follow skill-creator pattern
3. Add entry to this routing table
4. Include parent reference in sub-skill header

## References

- [references/mcp_servers.md](references/mcp_servers.md) — All AWS MCP servers
- [references/common_patterns.md](references/common_patterns.md) — Shared patterns
