---
name: aws-terraform
description: AWS infrastructure deployments using Terraform and Terragrunt. Use for any task involving: (1) Writing, validating, or deploying Terraform/HCL code for AWS, (2) Security scanning with Checkov, (3) AWS provider documentation lookup, (4) Terraform Registry module analysis, (5) Terragrunt multi-environment orchestration, (6) Infrastructure as Code best practices for AWS. Parent skill: aws.
---

# AWS Terraform Skill

Deploy and manage AWS infrastructure using Terraform and Terragrunt with security-first best practices.

> **Parent Skill:** `aws` - Inherits defaults from [`../aws/defaults.yaml`](../aws/defaults.yaml)

## Quick Reference

| Operation     | Command                      |
| ------------- | ---------------------------- |
| Initialize    | `terraform init`             |
| Validate      | `terraform validate`         |
| Plan          | `terraform plan -out=tfplan` |
| Apply         | `terraform apply tfplan`     |
| Destroy       | `terraform destroy`          |
| Security Scan | `checkov -d .`               |

## MCP Server Configuration

```json
{
  "awslabs.terraform-mcp-server": {
    "command": "uvx",
    "args": ["awslabs.terraform-mcp-server@latest"],
    "env": {
      "FASTMCP_LOG_LEVEL": "ERROR",
      "AWS_PROFILE": "default",
      "AWS_REGION": "eu-west-1"
    }
  }
}
```

Run `scripts/configure_mcp.py` to auto-configure.

---

## MCP Tools

| Tool                         | Purpose                                                   |
| ---------------------------- | --------------------------------------------------------- |
| `SearchAWSProviderDocs`      | Search AWS/AWSCC provider resource documentation          |
| `SearchAWSCCProviderDocs`    | Search AWSCC-specific documentation                       |
| `GetAWSIAGenAIModuleDetails` | Get AI/ML module details (Bedrock, OpenSearch, SageMaker) |
| `AnalyzeTerraformModule`     | Analyze Terraform Registry modules                        |
| `RunCheckovScan`             | Security and compliance scanning                          |
| `TerraformInit`              | Initialize working directory                              |
| `TerraformValidate`          | Validate configuration syntax                             |
| `TerraformPlan`              | Generate execution plan                                   |
| `TerraformApply`             | Apply infrastructure changes                              |
| `TerraformDestroy`           | Destroy managed infrastructure                            |
| `TerragruntInit`             | Initialize Terragrunt                                     |
| `TerragruntPlan`             | Plan with Terragrunt                                      |
| `TerragruntApply`            | Apply with Terragrunt                                     |
| `TerragruntRunAll`           | Execute across all configurations                         |

## MCP Resources

| Resource URI                                   | Content                               |
| ---------------------------------------------- | ------------------------------------- |
| `terraform://workflow_guide`                   | Security-focused development workflow |
| `terraform://aws_best_practices`               | AWS-specific Terraform guidance       |
| `terraform://aws_provider_resources_listing`   | AWS provider resource list            |
| `terraform://awscc_provider_resources_listing` | AWSCC provider resource list          |

---

## Security-First Workflow

Follow this structured process for all Terraform development:

### 1. Initialize & Configure

```bash
# Set AWS credentials
export AWS_PROFILE=default
export AWS_REGION=eu-west-1

# Initialize Terraform
terraform init
```

### 2. Write Infrastructure Code

- **Prefer AWSCC provider** for consistent API behavior and better security defaults
- Follow AWS Well-Architected Framework principles
- Use modules from Terraform Registry when available

### 3. Validate & Scan

```bash
# Syntax validation
terraform validate

# Security scan with Checkov
checkov -d . --framework terraform
```

### 4. Plan & Review

```bash
terraform plan -out=tfplan
```

Review the plan output carefully before applying.

### 5. Apply

```bash
terraform apply tfplan
```

---

## User Defaults

Inherited from parent `aws` skill:

| Setting              | Value                | Source                 |
| -------------------- | -------------------- | ---------------------- |
| Region               | `eu-west-1`          | `../aws/defaults.yaml` |
| Account ID           | `511383368449`       | `../aws/defaults.yaml` |
| SSH Key              | `tooling-key`        | `../aws/defaults.yaml` |
| IAM Instance Profile | `SSMInstanceProfile` | `../aws/defaults.yaml` |

---

## Common Patterns

### Basic EC2 Instance

```hcl
resource "aws_instance" "main" {
  ami                    = data.aws_ami.amazon_linux.id
  instance_type          = "t3.micro"
  key_name               = "tooling-key"
  iam_instance_profile   = "SSMInstanceProfile"
  vpc_security_group_ids = [aws_security_group.main.id]
  subnet_id              = var.subnet_id

  tags = {
    Name        = "example-instance"
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}
```

### S3 Bucket with Security

```hcl
resource "aws_s3_bucket" "main" {
  bucket = "my-secure-bucket-${data.aws_caller_identity.current.account_id}"

  tags = {
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

resource "aws_s3_bucket_versioning" "main" {
  bucket = aws_s3_bucket.main.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "main" {
  bucket = aws_s3_bucket.main.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "main" {
  bucket = aws_s3_bucket.main.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
```

### VPC with Public/Private Subnets

```hcl
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"

  name = "main-vpc"
  cidr = "10.0.0.0/16"

  azs             = ["eu-west-1a", "eu-west-1b", "eu-west-1c"]
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]

  enable_nat_gateway = true
  single_nat_gateway = true

  tags = {
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}
```

---

## Checkov Integration

### Run Full Scan

```bash
checkov -d . --framework terraform
```

### Skip Specific Checks

```hcl
#checkov:skip=CKV_AWS_18:Access logging intentionally disabled for dev
resource "aws_s3_bucket" "dev" {
  # ...
}
```

### Common Checkov Rules

| Rule         | Description                   |
| ------------ | ----------------------------- |
| `CKV_AWS_18` | S3 bucket access logging      |
| `CKV_AWS_19` | S3 bucket encryption          |
| `CKV_AWS_20` | S3 bucket public access block |
| `CKV_AWS_21` | S3 bucket versioning          |
| `CKV_AWS_79` | EC2 IMDSv2 required           |
| `CKV_AWS_88` | EC2 public IP                 |

---

## Project Structure

```
infrastructure/
├── environments/
│   ├── dev/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   ├── outputs.tf
│   │   └── terraform.tfvars
│   ├── staging/
│   └── prod/
├── modules/
│   ├── vpc/
│   ├── ec2/
│   └── rds/
├── terragrunt.hcl          # Root Terragrunt config
└── README.md
```

---

## Terragrunt Multi-Environment

### Root terragrunt.hcl

```hcl
remote_state {
  backend = "s3"
  config = {
    bucket         = "terraform-state-${get_aws_account_id()}"
    key            = "${path_relative_to_include()}/terraform.tfstate"
    region         = "eu-west-1"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}

generate "provider" {
  path      = "provider.tf"
  if_exists = "overwrite_terragrunt"
  contents  = <<EOF
provider "aws" {
  region = "eu-west-1"
  default_tags {
    tags = {
      ManagedBy   = "terragrunt"
      Environment = "${basename(get_terragrunt_dir())}"
    }
  }
}
EOF
}
```

### Environment-Specific Config

```hcl
# environments/dev/terragrunt.hcl
include "root" {
  path = find_in_parent_folders()
}

terraform {
  source = "../../modules//vpc"
}

inputs = {
  environment = "dev"
  cidr_block  = "10.0.0.0/16"
}
```

---

## Prerequisites

Ensure these tools are installed:

```bash
# Terraform
brew install terraform

# Terragrunt (optional)
brew install terragrunt

# Checkov
pip install checkov

# uv (for MCP server)
curl -LsSf https://astral.sh/uv/install.sh | sh
```

---

## References

- [AWS Terraform MCP Server](https://awslabs.github.io/mcp/servers/terraform-mcp-server)
- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [Terraform AWSCC Provider](https://registry.terraform.io/providers/hashicorp/awscc/latest/docs)
- [Checkov Documentation](https://www.checkov.io/1.Welcome/Quick%20Start.html)
- [AWS Well-Architected Framework](https://aws.amazon.com/architecture/well-architected/)
- See `references/` for detailed guides
