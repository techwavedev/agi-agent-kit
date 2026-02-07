# Checkov Security Scanning Reference

Comprehensive guide for security and compliance scanning with Checkov.

## Quick Start

```bash
# Scan current directory
checkov -d .

# Scan with specific framework
checkov -d . --framework terraform

# Output as JSON
checkov -d . -o json > checkov-report.json

# Compact output
checkov -d . --compact
```

---

## Common AWS Checks

### S3 Buckets

| Check ID      | Description                       | Severity |
| ------------- | --------------------------------- | -------- |
| `CKV_AWS_18`  | S3 bucket access logging enabled  | MEDIUM   |
| `CKV_AWS_19`  | S3 bucket encryption enabled      | HIGH     |
| `CKV_AWS_20`  | S3 bucket public access block     | HIGH     |
| `CKV_AWS_21`  | S3 bucket versioning enabled      | MEDIUM   |
| `CKV_AWS_53`  | S3 bucket lifecycle configuration | LOW      |
| `CKV_AWS_145` | S3 bucket encrypted with CMK      | MEDIUM   |

### EC2 Instances

| Check ID      | Description                     | Severity |
| ------------- | ------------------------------- | -------- |
| `CKV_AWS_79`  | IMDSv2 required                 | HIGH     |
| `CKV_AWS_88`  | EC2 not assigned public IP      | MEDIUM   |
| `CKV_AWS_126` | EC2 detailed monitoring enabled | LOW      |
| `CKV_AWS_135` | EBS optimized instance          | LOW      |
| `CKV_AWS_8`   | EBS encryption enabled          | HIGH     |

### Security Groups

| Check ID      | Description                        | Severity |
| ------------- | ---------------------------------- | -------- |
| `CKV_AWS_23`  | Security group has description     | LOW      |
| `CKV_AWS_24`  | No SSH from 0.0.0.0/0              | HIGH     |
| `CKV_AWS_25`  | No RDP from 0.0.0.0/0              | HIGH     |
| `CKV_AWS_260` | No unrestricted ingress to port 80 | MEDIUM   |
| `CKV_AWS_277` | No unrestricted egress             | LOW      |

### RDS

| Check ID      | Description             | Severity |
| ------------- | ----------------------- | -------- |
| `CKV_AWS_16`  | RDS encryption enabled  | HIGH     |
| `CKV_AWS_17`  | RDS logging enabled     | MEDIUM   |
| `CKV_AWS_118` | RDS enhanced monitoring | LOW      |
| `CKV_AWS_157` | RDS multi-AZ enabled    | MEDIUM   |
| `CKV_AWS_161` | RDS IAM authentication  | MEDIUM   |

### Lambda

| Check ID      | Description                     | Severity |
| ------------- | ------------------------------- | -------- |
| `CKV_AWS_45`  | Lambda in VPC                   | MEDIUM   |
| `CKV_AWS_50`  | X-Ray tracing enabled           | LOW      |
| `CKV_AWS_115` | Reserved concurrency set        | LOW      |
| `CKV_AWS_116` | Dead letter queue configured    | MEDIUM   |
| `CKV_AWS_173` | Environment variables encrypted | HIGH     |

### IAM

| Check ID      | Description                   | Severity |
| ------------- | ----------------------------- | -------- |
| `CKV_AWS_40`  | No wildcard actions in IAM    | HIGH     |
| `CKV_AWS_49`  | No wildcard resources in IAM  | HIGH     |
| `CKV_AWS_109` | IAM policy allows assume role | MEDIUM   |
| `CKV_AWS_289` | No admin access policy        | CRITICAL |

---

## Skipping Checks

### Inline Skip

```hcl
#checkov:skip=CKV_AWS_18:Access logging disabled for non-production
resource "aws_s3_bucket" "dev" {
  bucket = "my-dev-bucket"
}
```

### Multiple Skips

```hcl
#checkov:skip=CKV_AWS_18:Access logging disabled for dev
#checkov:skip=CKV_AWS_21:Versioning not needed for temp data
resource "aws_s3_bucket" "temp" {
  bucket = "temp-processing-bucket"
}
```

### Command-Line Skip

```bash
# Skip specific checks
checkov -d . --skip-check CKV_AWS_18,CKV_AWS_21

# Skip by severity
checkov -d . --check LOW --skip-check-severity MEDIUM,HIGH
```

### Skip File

Create `.checkov.yml`:

```yaml
skip-check:
  - CKV_AWS_18 # Access logging for dev buckets
  - CKV_AWS_21 # Versioning for temp buckets

framework:
  - terraform

compact: true
```

---

## CI/CD Integration

### GitHub Actions

```yaml
name: Terraform Security Scan

on:
  pull_request:
    paths:
      - "**.tf"

jobs:
  checkov:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Run Checkov
        uses: bridgecrewio/checkov-action@master
        with:
          directory: .
          framework: terraform
          soft_fail: false
          skip_check: CKV_AWS_18
```

### Pre-commit Hook

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/bridgecrewio/checkov
    rev: "3.0.0"
    hooks:
      - id: checkov
        args: [--framework, terraform]
```

---

## Output Formats

```bash
# CLI output (default)
checkov -d .

# JSON output
checkov -d . -o json > report.json

# JUnit XML (for CI)
checkov -d . -o junitxml > report.xml

# SARIF (for GitHub Security)
checkov -d . -o sarif > report.sarif

# Multiple outputs
checkov -d . -o cli -o json > report.json
```

---

## Fixing Common Issues

### CKV_AWS_79: IMDSv2

```hcl
resource "aws_instance" "main" {
  # ... other config

  metadata_options {
    http_tokens                 = "required"  # Enforce IMDSv2
    http_endpoint               = "enabled"
    http_put_response_hop_limit = 1
  }
}
```

### CKV_AWS_20: S3 Public Access Block

```hcl
resource "aws_s3_bucket_public_access_block" "main" {
  bucket = aws_s3_bucket.main.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
```

### CKV_AWS_24: No SSH from 0.0.0.0/0

```hcl
resource "aws_security_group_rule" "ssh" {
  type              = "ingress"
  from_port         = 22
  to_port           = 22
  protocol          = "tcp"
  # Use specific CIDR, not 0.0.0.0/0
  cidr_blocks       = ["10.0.0.0/8"]
  security_group_id = aws_security_group.main.id
  description       = "SSH from internal network"
}
```

### CKV_AWS_16: RDS Encryption

```hcl
resource "aws_db_instance" "main" {
  # ... other config

  storage_encrypted = true
  kms_key_id        = aws_kms_key.rds.arn
}
```

### CKV_AWS_173: Lambda Environment Encryption

```hcl
resource "aws_lambda_function" "main" {
  # ... other config

  kms_key_arn = aws_kms_key.lambda.arn

  environment {
    variables = {
      API_KEY = var.api_key  # Will be encrypted with KMS
    }
  }
}
```

---

## Custom Policies

### Python Custom Check

```python
# custom_checks/s3_naming.py
from checkov.terraform.checks.resource.base_resource_check import BaseResourceCheck
from checkov.common.models.enums import CheckResult, CheckCategories

class S3NamingConvention(BaseResourceCheck):
    def __init__(self):
        name = "S3 bucket follows naming convention"
        id = "CKV_CUSTOM_1"
        supported_resources = ["aws_s3_bucket"]
        categories = [CheckCategories.CONVENTION]
        super().__init__(name=name, id=id, categories=categories,
                        supported_resources=supported_resources)

    def scan_resource_conf(self, conf):
        bucket_name = conf.get("bucket", [""])[0]
        if bucket_name.startswith("company-"):
            return CheckResult.PASSED
        return CheckResult.FAILED

check = S3NamingConvention()
```

Run with custom checks:

```bash
checkov -d . --external-checks-dir ./custom_checks
```

---

## Severity Levels

| Level        | Description              | Action              |
| ------------ | ------------------------ | ------------------- |
| **CRITICAL** | Must fix immediately     | Block deployment    |
| **HIGH**     | Security vulnerability   | Fix before prod     |
| **MEDIUM**   | Security best practice   | Fix soon            |
| **LOW**      | Hardening recommendation | Fix when convenient |

### Filter by Severity

```bash
# Only high and critical
checkov -d . --check HIGH,CRITICAL

# Fail on critical only
checkov -d . --hard-fail-on CRITICAL
```

---

## Performance Tips

```bash
# Parallel scanning
checkov -d . --parallelism 8

# Skip downloads
checkov -d . --skip-download

# Cache results
checkov -d . --cache-dir /tmp/.checkov_cache
```
