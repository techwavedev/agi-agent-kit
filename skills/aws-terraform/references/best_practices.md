# Terraform Best Practices for AWS

Reference guide for AWS Terraform development.

## Provider Selection

### AWS Provider vs AWSCC Provider

| Provider                      | Use When                                                |
| ----------------------------- | ------------------------------------------------------- |
| **AWS** (`hashicorp/aws`)     | Most common resources, extensive documentation          |
| **AWSCC** (`hashicorp/awscc`) | New resources, consistent API behavior, better defaults |

**Recommendation:** Prefer AWSCC when available for new projects; it provides better security defaults and consistent API behavior.

---

## State Management

### Remote State with S3

```hcl
terraform {
  backend "s3" {
    bucket         = "terraform-state-511383368449"
    key            = "project/terraform.tfstate"
    region         = "eu-west-1"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}
```

### State Locking

Always enable DynamoDB locking for team environments:

```hcl
resource "aws_dynamodb_table" "terraform_locks" {
  name         = "terraform-locks"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "LockID"

  attribute {
    name = "LockID"
    type = "S"
  }

  tags = {
    Purpose   = "Terraform State Locking"
    ManagedBy = "terraform"
  }
}
```

---

## Security Patterns

### Least Privilege IAM

```hcl
data "aws_iam_policy_document" "lambda_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "lambda" {
  name               = "lambda-execution-role"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume.json
}

# Attach only required permissions
resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}
```

### Encryption at Rest

Always enable encryption for data stores:

```hcl
# RDS
resource "aws_db_instance" "main" {
  # ...
  storage_encrypted = true
  kms_key_id        = aws_kms_key.rds.arn
}

# EBS
resource "aws_ebs_volume" "main" {
  # ...
  encrypted  = true
  kms_key_id = aws_kms_key.ebs.arn
}

# S3
resource "aws_s3_bucket_server_side_encryption_configuration" "main" {
  bucket = aws_s3_bucket.main.id
  rule {
    apply_server_side_encryption_by_default {
      kms_master_key_id = aws_kms_key.s3.arn
      sse_algorithm     = "aws:kms"
    }
  }
}
```

### Security Groups - Explicit Rules

```hcl
resource "aws_security_group" "web" {
  name        = "web-sg"
  description = "Security group for web servers"
  vpc_id      = var.vpc_id

  # HTTPS from anywhere
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "HTTPS traffic"
  }

  # Explicit egress rules
  egress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "HTTPS to external services"
  }

  tags = {
    Name        = "web-sg"
    Environment = var.environment
  }
}
```

---

## Tagging Strategy

### Default Tags Provider

```hcl
provider "aws" {
  region = "eu-west-1"

  default_tags {
    tags = {
      Environment = var.environment
      Project     = var.project_name
      ManagedBy   = "terraform"
      Owner       = var.owner
      CostCenter  = var.cost_center
    }
  }
}
```

### Required Tags

| Tag           | Purpose                           |
| ------------- | --------------------------------- |
| `Environment` | dev, staging, prod                |
| `Project`     | Project/application name          |
| `ManagedBy`   | terraform, manual, cloudformation |
| `Owner`       | Team or individual owner          |
| `CostCenter`  | For billing allocation            |

---

## Modules Best Practices

### Module Structure

```
modules/
└── vpc/
    ├── main.tf          # Primary resources
    ├── variables.tf     # Input variables
    ├── outputs.tf       # Output values
    ├── versions.tf      # Provider requirements
    └── README.md        # Usage documentation
```

### Module Versioning

```hcl
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"  # Allow patch updates

  # Pin major version to avoid breaking changes
}
```

### Local Module Usage

```hcl
module "app_vpc" {
  source = "../../modules/vpc"

  name        = "app-vpc"
  environment = var.environment
  cidr_block  = "10.0.0.0/16"
}
```

---

## Variable Best Practices

### Type Constraints

```hcl
variable "instance_type" {
  type        = string
  default     = "t3.micro"
  description = "EC2 instance type"

  validation {
    condition     = can(regex("^t3\\.", var.instance_type))
    error_message = "Instance type must be in the t3 family."
  }
}

variable "allowed_cidrs" {
  type        = list(string)
  default     = []
  description = "List of CIDRs allowed to access resources"

  validation {
    condition = alltrue([
      for cidr in var.allowed_cidrs :
      can(cidrhost(cidr, 0))
    ])
    error_message = "All values must be valid CIDR blocks."
  }
}
```

### Sensitive Variables

```hcl
variable "database_password" {
  type        = string
  sensitive   = true
  description = "Database master password"
}
```

---

## Lifecycle Rules

### Prevent Accidental Destruction

```hcl
resource "aws_db_instance" "main" {
  # ...

  lifecycle {
    prevent_destroy = true
  }
}
```

### Ignore External Changes

```hcl
resource "aws_autoscaling_group" "main" {
  # ...

  lifecycle {
    ignore_changes = [
      desired_capacity,  # Allow autoscaling to manage
    ]
  }
}
```

### Create Before Destroy

```hcl
resource "aws_instance" "main" {
  # ...

  lifecycle {
    create_before_destroy = true
  }
}
```

---

## Data Sources

### Current Account Info

```hcl
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

locals {
  account_id = data.aws_caller_identity.current.account_id
  region     = data.aws_region.current.name
}
```

### Latest AMI

```hcl
data "aws_ami" "amazon_linux" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-*-x86_64"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}
```

---

## Workspace Strategy

Use workspaces for environment isolation:

```bash
# Create workspaces
terraform workspace new dev
terraform workspace new staging
terraform workspace new prod

# Select workspace
terraform workspace select dev
```

Reference workspace in code:

```hcl
locals {
  environment = terraform.workspace

  instance_type = {
    dev     = "t3.micro"
    staging = "t3.small"
    prod    = "t3.medium"
  }[local.environment]
}
```

---

## Performance Tips

### Parallelism

```bash
# Increase parallelism for large deployments
terraform apply -parallelism=20
```

### Target Specific Resources

```bash
# Apply only specific resources
terraform apply -target=module.vpc
terraform apply -target=aws_instance.web
```

### Refresh State

```bash
# Skip refresh for faster plans
terraform plan -refresh=false
```
