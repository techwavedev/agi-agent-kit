# Common AWS Documentation Searches

Pre-defined search patterns for common topics.

## Security & IAM

| Topic                | Search Phrase                     | Product Types        |
| -------------------- | --------------------------------- | -------------------- |
| IAM policies         | "IAM policies best practices"     | `["iam"]`            |
| IAM roles            | "IAM roles trust policy"          | `["iam"]`            |
| MFA setup            | "MFA multi-factor authentication" | `["iam"]`            |
| Cross-account access | "cross-account IAM assume role"   | `["iam"]`            |
| Security best        | "security best practices"         | None (all)           |
| KMS encryption       | "KMS key management"              | `["kms"]`            |
| Secrets Manager      | "secrets manager rotation"        | `["secretsmanager"]` |

## Networking & VPC

| Topic           | Search Phrase                     | Product Types |
| --------------- | --------------------------------- | ------------- |
| VPC setup       | "VPC virtual private cloud setup" | `["vpc"]`     |
| Security groups | "security groups inbound rules"   | `["vpc"]`     |
| NAT Gateway     | "NAT gateway configuration"       | `["vpc"]`     |
| VPC Peering     | "VPC peering connection"          | `["vpc"]`     |
| Transit Gateway | "transit gateway routing"         | `["vpc"]`     |
| PrivateLink     | "VPC endpoint PrivateLink"        | `["vpc"]`     |

## Compute

| Topic            | Search Phrase                   | Product Types     |
| ---------------- | ------------------------------- | ----------------- |
| EC2 instances    | "EC2 instance types"            | `["ec2"]`         |
| Launch templates | "EC2 launch template"           | `["ec2"]`         |
| Auto Scaling     | "auto scaling group policy"     | `["autoscaling"]` |
| Spot instances   | "spot instances interruption"   | `["ec2"]`         |
| Lambda functions | "lambda function configuration" | `["lambda"]`      |
| Lambda layers    | "lambda layers dependencies"    | `["lambda"]`      |

## Storage

| Topic           | Search Phrase               | Product Types |
| --------------- | --------------------------- | ------------- |
| S3 buckets      | "S3 bucket policy"          | `["s3"]`      |
| S3 lifecycle    | "S3 lifecycle rules"        | `["s3"]`      |
| EBS volumes     | "EBS volume types"          | `["ebs"]`     |
| EFS file system | "EFS elastic file system"   | `["efs"]`     |
| Glacier archive | "Glacier archive retrieval" | `["glacier"]` |

## Database

| Topic           | Search Phrase                     | Product Types     |
| --------------- | --------------------------------- | ----------------- |
| RDS setup       | "RDS database instance"           | `["rds"]`         |
| Aurora clusters | "Aurora cluster configuration"    | `["aurora"]`      |
| DynamoDB tables | "DynamoDB table design"           | `["dynamodb"]`    |
| DynamoDB GSI    | "DynamoDB global secondary index" | `["dynamodb"]`    |
| ElastiCache     | "ElastiCache Redis cluster"       | `["elasticache"]` |
| Redshift        | "Redshift data warehouse"         | `["redshift"]`    |

## Containers & Kubernetes

| Topic             | Search Phrase                    | Product Types |
| ----------------- | -------------------------------- | ------------- |
| EKS clusters      | "EKS cluster setup"              | `["eks"]`     |
| EKS managed nodes | "EKS managed node groups"        | `["eks"]`     |
| EKS IRSA          | "EKS IAM roles service accounts" | `["eks"]`     |
| ECS services      | "ECS service deployment"         | `["ecs"]`     |
| ECS Fargate       | "ECS Fargate task definition"    | `["ecs"]`     |
| ECR repositories  | "ECR container registry"         | `["ecr"]`     |

## Serverless

| Topic          | Search Phrase                  | Product Types       |
| -------------- | ------------------------------ | ------------------- |
| API Gateway    | "API Gateway REST API"         | `["apigateway"]`    |
| Step Functions | "Step Functions state machine" | `["stepfunctions"]` |
| EventBridge    | "EventBridge rules events"     | `["eventbridge"]`   |
| SQS queues     | "SQS queue configuration"      | `["sqs"]`           |
| SNS topics     | "SNS topic subscription"       | `["sns"]`           |

## Monitoring & Logging

| Topic              | Search Phrase               | Product Types        |
| ------------------ | --------------------------- | -------------------- |
| CloudWatch metrics | "CloudWatch custom metrics" | `["cloudwatch"]`     |
| CloudWatch alarms  | "CloudWatch alarm actions"  | `["cloudwatch"]`     |
| CloudWatch Logs    | "CloudWatch Logs insights"  | `["cloudwatchlogs"]` |
| X-Ray tracing      | "X-Ray distributed tracing" | `["xray"]`           |
| CloudTrail         | "CloudTrail audit logging"  | `["cloudtrail"]`     |

## Infrastructure as Code

| Topic           | Search Phrase                | Product Types        |
| --------------- | ---------------------------- | -------------------- |
| CloudFormation  | "CloudFormation template"    | `["cloudformation"]` |
| CDK             | "CDK constructs patterns"    | `["cdk"]`            |
| SAM             | "SAM serverless application" | `["sam"]`            |
| Service Catalog | "Service Catalog portfolio"  | `["servicecatalog"]` |

## Cost & Billing

| Topic              | Search Phrase                   | Product Types      |
| ------------------ | ------------------------------- | ------------------ |
| Cost Explorer      | "Cost Explorer reports"         | `["costexplorer"]` |
| Budgets            | "AWS Budgets alerts"            | `["budgets"]`      |
| Savings Plans      | "Savings Plans recommendations" | `["savingsplans"]` |
| Reserved Instances | "Reserved Instances pricing"    | `["ec2"]`          |

## Usage Examples

### Search for IAM Best Practices

```
Use search_documentation with:
- search_phrase: "IAM security best practices"
- limit: 5
- product_types: ["iam"]
```

### Search for EKS Troubleshooting

```
Use search_documentation with:
- search_phrase: "EKS troubleshooting node not ready"
- limit: 10
- product_types: ["eks"]
```

### Search Across All Services

```
Use search_documentation with:
- search_phrase: "high availability architecture"
- limit: 10
- product_types: null (search all)
```
