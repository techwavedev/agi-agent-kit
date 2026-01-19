# Skills Catalog

> **Auto-generated Documentation** — Last updated: 2026-01-19 23:30
>
> This catalog is automatically maintained. Update it by running:
> ```bash
> python skill-creator/scripts/update_catalog.py --skills-dir skills/
> ```

This document provides comprehensive documentation on available skills, how to use them, and when each skill should be triggered.

---

## Table of Contents

- [What Are Skills?](#what-are-skills)
- [Available Skills](#available-skills)
  - [AWS (Hub)](#aws-hub)
  - [Aws Api](#aws-api)
  - [Aws Ccapi](#aws-ccapi)
  - [Aws Cfn](#aws-cfn)
  - [Aws Cli](#aws-cli)
  - [Aws Cost Explorer](#aws-cost-explorer)
  - [Aws Docs](#aws-docs)
  - [Aws Eks](#aws-eks)
  - [Aws Iac](#aws-iac)
  - [Aws Knowledge](#aws-knowledge)
  - [Aws Lambda](#aws-lambda)
  - [Aws Network](#aws-network)
  - [Aws Pricing](#aws-pricing)
  - [Aws Serverless](#aws-serverless)
  - [Aws Stepfunctions](#aws-stepfunctions)
  - [Aws Terraform](#aws-terraform)
  - [Pdf Reader](#pdf-reader)
- [Using Skills](#using-skills)
- [Creating New Skills](#creating-new-skills)
- [Maintenance](#maintenance)

---

## What Are Skills?

**Skills** are modular, self-contained packages that extend the AI agent's capabilities with specialized knowledge, workflows, and tools.

### Skill Structure

```
skill-name/
├── SKILL.md           # (required) Main instruction file
├── scripts/           # (optional) Executable scripts
├── references/        # (optional) Documentation
└── assets/            # (optional) Templates, images, etc.
```

---

## Available Skills

### AWS (Hub)

| Property | Value |
| -------- | ----- |
| **Name** | `aws` |
| **Location** | `skills/aws/` |
| **Type** | Router / Hub |

**Description:** AWS cloud operations hub. Use for any AWS-related task including EKS, Lambda, Step Functions, networking, pricing, and IaC. This skill routes to specialized sub-skills and provides shared context (profiles, regions) across all AWS operations. Start here for AWS work.

**References:**
- `references/common_patterns.md`
- `references/mcp_servers.md`

---

### Aws Docs

| Property | Value |
| -------- | ----- |
| **Name** | `aws-docs` |
| **Location** | `skills/aws-docs/` |
| **Parent** | [Aws](#aws) |

**Description:** AWS documentation expert using the AWS Documentation MCP Server. Use for consulting AWS documentation, searching for best practices, getting recommendations on AWS service usage, and generating documentation output. Triggers on queries like "look up AWS documentation on...", "what does AWS recommend for...", "search AWS docs for...", "help me understand AWS...", or any request requiring authoritative AWS technical guidance.

**References:**
- `references/common_searches.md`
- `references/documentation_urls.md`

---

### Aws Api

| Property | Value |
| -------- | ----- |
| **Name** | `aws-api` |
| **Location** | `skills/aws-api/` |
| **Type** | Standalone |

**Description:** Execute AWS CLI commands through AI assistance via AWS API MCP Server. Use for any AWS operation including creating resources, managing infrastructure, running CLI commands, and getting command suggestions. Supports all AWS services with command validation and hallucination protection.

**Scripts:**

| Script | Purpose |
| ------ | ------- |
| `scripts/configure_mcp.py` | *[See script for details]* |

---

### Aws Ccapi

| Property | Value |
| -------- | ----- |
| **Name** | `aws-ccapi` |
| **Location** | `skills/aws-ccapi/` |
| **Type** | Standalone |

**Description:** Manage 1,100+ AWS resources via Cloud Control API with integrated security scanning. Use for declarative resource creation, reading, updating, deleting, and listing. Features security-first workflow with Checkov scanning, credential awareness, and template generation.

**Scripts:**

| Script | Purpose |
| ------ | ------- |
| `scripts/configure_mcp.py` | *[See script for details]* |

---

### Aws Cfn

| Property | Value |
| -------- | ----- |
| **Name** | `aws-cfn` |
| **Location** | `skills/aws-cfn/` |
| **Type** | Standalone |

**Description:** Manage AWS CloudFormation resources and templates via MCP Server. Use for creating, reading, updating, and deleting resources through Cloud Control API, getting resource schemas, and generating CloudFormation templates from existing resources.

**Scripts:**

| Script | Purpose |
| ------ | ------- |
| `scripts/configure_mcp.py` | *[See script for details]* |

---

### Aws Cli

| Property | Value |
| -------- | ----- |
| **Name** | `aws-cli` |
| **Location** | `skills/aws-cli/` |
| **Type** | Standalone |

**Description:** Manage AWS CLI profiles for authentication and credential management. Use when creating new AWS profiles, listing existing profiles, switching between profiles, configuring SSO access, or setting up cross-account role assumption. Essential for any AWS operation requiring specific credentials or multi-account access.

**Scripts:**

| Script | Purpose |
| ------ | ------- |
| `scripts/create_profile.py` | *[See script for details]* |
| `scripts/list_profiles.py` | *[See script for details]* |
| `scripts/switch_profile.py` | *[See script for details]* |

**References:**
- `references/assume_role.md`
- `references/sso_configuration.md`

---

### Aws Cost Explorer

| Property | Value |
| -------- | ----- |
| **Name** | `aws-cost-explorer` |
| **Location** | `skills/aws-cost-explorer/` |
| **Type** | Standalone |

**Description:** Analyze actual AWS costs and usage data via Cost Explorer MCP. Use for cost breakdowns by service/region, comparing costs between periods, forecasting future costs, and identifying cost drivers. Queries your actual AWS billing data.

---

### Aws Eks

| Property | Value |
| -------- | ----- |
| **Name** | `aws-eks` |
| **Location** | `skills/aws-eks/` |
| **Type** | Standalone |

**Description:** Manage AWS EKS (Elastic Kubernetes Service) clusters via AWS EKS MCP Server. Use for creating, updating, or deleting EKS clusters, managing node groups, configuring kubectl access, deploying workloads, and troubleshooting Kubernetes issues. Integrates with Amazon EKS MCP Server for AI-assisted cluster management.

**Scripts:**

| Script | Purpose |
| ------ | ------- |
| `scripts/cluster_info.py` | *[See script for details]* |
| `scripts/configure_mcp.py` | *[See script for details]* |

**References:**
- `references/cluster_operations.md`
- `references/iam_roles.md`
- `references/mcp_setup.md`
- `references/troubleshooting.md`

---

### Aws Iac

| Property | Value |
| -------- | ----- |
| **Name** | `aws-iac` |
| **Location** | `skills/aws-iac/` |
| **Type** | Standalone |

**Description:** Infrastructure as Code for AWS using CDK, CloudFormation, or Terraform via MCP servers. Use for creating IaC templates, deploying infrastructure, managing resources declaratively, getting CDK patterns, or running Terraform workflows. Includes security scanning with CDK Nag and Checkov.

**Scripts:**

| Script | Purpose |
| ------ | ------- |
| `scripts/configure_mcp.py` | *[See script for details]* |

---

### Aws Knowledge

| Property | Value |
| -------- | ----- |
| **Name** | `aws-knowledge` |
| **Location** | `skills/aws-knowledge/` |
| **Type** | Standalone |

**Description:** Access AWS documentation, API references, best practices, and architectural guidance via AWS Knowledge MCP Server. Use when needing to search AWS docs, get API usage examples, find regional availability info, learn AWS Amplify patterns, or get CDK/CloudFormation guidance. No authentication required.

**Scripts:**

| Script | Purpose |
| ------ | ------- |
| `scripts/configure_mcp.py` | *[See script for details]* |

---

### Aws Lambda

| Property | Value |
| -------- | ----- |
| **Name** | `aws-lambda` |
| **Location** | `skills/aws-lambda/` |
| **Type** | Standalone |

**Description:** Execute AWS Lambda functions as AI tools for private resource access. Use when you need AI to invoke Lambda functions that access VPC resources, databases, internal APIs, or other AWS services without direct network access. Supports function filtering by prefix, list, or tags.

**Scripts:**

| Script | Purpose |
| ------ | ------- |
| `scripts/configure_mcp.py` | *[See script for details]* |

---

### Aws Network

| Property | Value |
| -------- | ----- |
| **Name** | `aws-network` |
| **Location** | `skills/aws-network/` |
| **Type** | Standalone |

**Description:** AWS network troubleshooting and analysis via MCP. Use for path tracing, flow log analysis, Transit Gateway/Cloud WAN routing, VPC connectivity issues, Network Firewall rules, and VPN connections. Read-only operations for safe troubleshooting.

---

### Aws Pricing

| Property | Value |
| -------- | ----- |
| **Name** | `aws-pricing` |
| **Location** | `skills/aws-pricing/` |
| **Type** | Standalone |

**Description:** AWS pricing discovery, cost analysis, and planning via MCP. Use for querying service prices, comparing regions, analyzing CDK/Terraform project costs, and getting cost optimization recommendations aligned with Well-Architected Framework.

---

### Aws Serverless

| Property | Value |
| -------- | ----- |
| **Name** | `aws-serverless` |
| **Location** | `skills/aws-serverless/` |
| **Type** | Standalone |

**Description:** Complete serverless application lifecycle with SAM CLI. Use for initializing, building, deploying SAM apps, deploying web apps (Express, Next.js) to Lambda, managing domains, viewing logs/metrics, and getting Lambda event schemas.

---

### Aws Stepfunctions

| Property | Value |
| -------- | ----- |
| **Name** | `aws-stepfunctions` |
| **Location** | `skills/aws-stepfunctions/` |
| **Type** | Standalone |

**Description:** Execute AWS Step Functions state machines as AI tools. Use for running complex multi-step workflows, orchestrating AWS services, and executing business processes. Supports Standard and Express workflows with EventBridge Schema Registry integration.

**Scripts:**

| Script | Purpose |
| ------ | ------- |
| `scripts/configure_mcp.py` | *[See script for details]* |

---

### Aws Terraform

| Property | Value |
| -------- | ----- |
| **Name** | `aws-terraform` |
| **Location** | `skills/aws-terraform/` |
| **Type** | Standalone |

**Description:** Terraform workflows for AWS with integrated security scanning via Checkov. Use for AWS provider documentation, Terraform Registry module analysis, running terraform/terragrunt commands, and accessing AWS-IA GenAI modules. Supports init, plan, apply, and destroy operations.

**Scripts:**

| Script | Purpose |
| ------ | ------- |
| `scripts/configure_mcp.py` | *[See script for details]* |

---

### Pdf Reader

| Property | Value |
| -------- | ----- |
| **Name** | `pdf-reader` |
| **Location** | `skills/pdf-reader/` |
| **Type** | Standalone |

**Description:** Extract text from PDF files for manipulation, search, and reference. Use when needing to read PDF content, extract text from documents, search within PDFs, or convert PDF to text for further processing. Supports multiple extraction methods (pdfplumber, PyMuPDF, pdfminer) with automatic fallback.

**Scripts:**

| Script | Purpose |
| ------ | ------- |
| `scripts/extract_text.py` | *[See script for details]* |

**References:**
- `references/pdf_libraries.md`

---
## Using Skills

Skills are automatically triggered based on the user's request matching the skill description. You can also explicitly invoke a skill:

```
"Use the <skill-name> skill to <task>"
```

---

## Creating New Skills

```bash
# Initialize a new skill
python skill-creator/scripts/init_skill.py my-new-skill --path skills/

# Package the skill
python skill-creator/scripts/package_skill.py skills/my-new-skill
```

For detailed guidance, see: `skill-creator/SKILL_skillcreator.md`

---

## Maintenance

### Updating This Catalog

**IMPORTANT:** This catalog must be updated whenever skills are created, modified, or deleted.

```bash
python skill-creator/scripts/update_catalog.py --skills-dir skills/
```

---

*This catalog is part of the [3-Layer Architecture](../AGENTS.md) for reliable AI agent operations.*
