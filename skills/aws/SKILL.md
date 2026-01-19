---
name: aws
description: Comprehensive AWS MCP skill covering ALL AWS services. Use for any AWS-related task - infrastructure, databases, AI/ML, observability, networking, serverless, and more. This single skill provides access to 60+ AWS MCP servers organized by category.
---

# AWS Skill

Unified skill for all AWS MCP servers. One skill to rule them all.

> **Last Updated:** 2026-01-19 from [awslabs.github.io/mcp](https://awslabs.github.io/mcp/)

## Quick Start

```bash
# Set credentials
export AWS_PROFILE=default
export AWS_REGION=eu-west-1

# Configure MCP client (pick servers you need from below)
```

---

## ⚙️ User Defaults

**Configured in [`defaults.yaml`](defaults.yaml):**

```yaml
ssh_key: tooling-key
iam_instance_profile: SSMInstanceProfile
region: eu-west-1
account_id: "511383368449"
```

These apply to all AWS operations unless specified otherwise.

---

## 🏗️ Core & Infrastructure

### AWS API MCP Server

Execute AWS CLI commands via MCP.

```json
{
  "command": "uvx",
  "args": ["awslabs.aws-api-mcp-server@latest"],
  "env": { "AWS_PROFILE": "default", "AWS_REGION": "eu-west-1" }
}
```

[Docs](https://awslabs.github.io/mcp/servers/aws-api-mcp-server)

### AWS Cloud Control API (CCAPI)

Declarative resource CRUD with security scanning (1,100+ resource types).

```json
{
  "command": "uvx",
  "args": ["awslabs.ccapi-mcp-server@latest"],
  "env": {
    "AWS_PROFILE": "default",
    "AWS_REGION": "eu-west-1",
    "SECURITY_SCANNING": "enabled"
  }
}
```

[Docs](https://awslabs.github.io/mcp/servers/ccapi-mcp-server)

### AWS Core MCP Server

Intelligent planning and AWS MCP server orchestration.

```json
{
  "command": "uvx",
  "args": ["awslabs.core-mcp-server@latest"],
  "env": { "AWS_PROFILE": "default", "AWS_REGION": "eu-west-1" }
}
```

[Docs](https://awslabs.github.io/mcp/servers/core-mcp-server)

---

## 📝 Infrastructure as Code

### AWS CDK

CDK development with security compliance (CDK-nag).

```json
{
  "command": "uvx",
  "args": ["awslabs.cdk-mcp-server@latest"],
  "env": { "FASTMCP_LOG_LEVEL": "ERROR" }
}
```

[Docs](https://awslabs.github.io/mcp/servers/cdk-mcp-server)

### AWS CloudFormation

CloudFormation resource management via Cloud Control API.

```json
{
  "command": "uvx",
  "args": ["awslabs.cfn-mcp-server@latest"],
  "env": { "AWS_PROFILE": "default", "AWS_REGION": "eu-west-1" }
}
```

[Docs](https://awslabs.github.io/mcp/servers/cfn-mcp-server)

### AWS Terraform

Terraform workflows with security scanning.

```json
{
  "command": "uvx",
  "args": ["awslabs.terraform-mcp-server@latest"],
  "env": { "FASTMCP_LOG_LEVEL": "ERROR" }
}
```

[Docs](https://awslabs.github.io/mcp/servers/terraform-mcp-server)

---

## 🐳 Containers & Kubernetes

### Amazon EKS

Kubernetes cluster management and deployment.

```json
{
  "command": "uvx",
  "args": ["awslabs.eks-mcp-server@latest", "--allow-write"],
  "env": { "AWS_PROFILE": "default", "AWS_REGION": "eu-west-1" }
}
```

[Docs](https://awslabs.github.io/mcp/servers/eks-mcp-server)

### Amazon ECS

Container orchestration and ECS deployment.

```json
{
  "command": "uvx",
  "args": ["awslabs.ecs-mcp-server@latest"],
  "env": { "AWS_PROFILE": "default", "AWS_REGION": "eu-west-1" }
}
```

[Docs](https://awslabs.github.io/mcp/servers/ecs-mcp-server)

### Finch

Local container building with ECR integration.

```json
{
  "command": "uvx",
  "args": ["awslabs.finch-mcp-server@latest"],
  "env": { "AWS_PROFILE": "default", "AWS_REGION": "eu-west-1" }
}
```

[Docs](https://awslabs.github.io/mcp/servers/finch-mcp-server)

---

## ⚡ Serverless

### AWS Serverless

Complete serverless lifecycle with SAM CLI.

```json
{
  "command": "uvx",
  "args": ["awslabs.aws-serverless-mcp-server@latest", "--allow-write"],
  "env": { "AWS_PROFILE": "default", "AWS_REGION": "eu-west-1" }
}
```

[Docs](https://awslabs.github.io/mcp/servers/aws-serverless-mcp-server)

### AWS Lambda Tool

Execute Lambda functions as AI tools.

```json
{
  "command": "uvx",
  "args": ["awslabs.lambda-tool-mcp-server@latest"],
  "env": {
    "AWS_PROFILE": "default",
    "AWS_REGION": "eu-west-1",
    "FUNCTION_PREFIX": "ai-tools-"
  }
}
```

[Docs](https://awslabs.github.io/mcp/servers/lambda-tool-mcp-server)

### AWS Step Functions

Execute workflows as AI tools.

```json
{
  "command": "uvx",
  "args": ["awslabs.stepfunctions-tool-mcp-server@latest"],
  "env": { "AWS_PROFILE": "default", "AWS_REGION": "eu-west-1" }
}
```

[Docs](https://awslabs.github.io/mcp/servers/stepfunctions-tool-mcp-server)

---

## 🗄️ Databases

### Amazon DynamoDB

Complete DynamoDB operations.

```json
{
  "command": "uvx",
  "args": ["awslabs.dynamodb-mcp-server@latest"],
  "env": { "AWS_PROFILE": "default", "AWS_REGION": "eu-west-1" }
}
```

[Docs](https://awslabs.github.io/mcp/servers/dynamodb-mcp-server)

### Amazon Aurora PostgreSQL

PostgreSQL via RDS Data API.

```json
{
  "command": "uvx",
  "args": ["awslabs.postgres-mcp-server@latest"],
  "env": { "AWS_PROFILE": "default", "AWS_REGION": "eu-west-1" }
}
```

[Docs](https://awslabs.github.io/mcp/servers/postgres-mcp-server)

### Amazon Aurora MySQL

MySQL via RDS Data API.

```json
{
  "command": "uvx",
  "args": ["awslabs.mysql-mcp-server@latest"],
  "env": { "AWS_PROFILE": "default", "AWS_REGION": "eu-west-1" }
}
```

[Docs](https://awslabs.github.io/mcp/servers/mysql-mcp-server)

### Amazon Aurora DSQL

Distributed SQL with PostgreSQL compatibility.

```json
{
  "command": "uvx",
  "args": ["awslabs.aurora-dsql-mcp-server@latest"],
  "env": { "AWS_PROFILE": "default", "AWS_REGION": "us-east-1" }
}
```

[Docs](https://awslabs.github.io/mcp/servers/aurora-dsql-mcp-server)

### Amazon DocumentDB

MongoDB-compatible document database.

```json
{
  "command": "uvx",
  "args": ["awslabs.documentdb-mcp-server@latest"],
  "env": { "AWS_PROFILE": "default", "AWS_REGION": "eu-west-1" }
}
```

[Docs](https://awslabs.github.io/mcp/servers/documentdb-mcp-server)

### Amazon Neptune

Graph database with openCypher/Gremlin.

```json
{
  "command": "uvx",
  "args": ["awslabs.amazon-neptune-mcp-server@latest"],
  "env": { "AWS_PROFILE": "default", "AWS_REGION": "eu-west-1" }
}
```

[Docs](https://awslabs.github.io/mcp/servers/amazon-neptune-mcp-server)

### Amazon Keyspaces

Cassandra-compatible operations.

```json
{
  "command": "uvx",
  "args": ["awslabs.amazon-keyspaces-mcp-server@latest"],
  "env": { "AWS_PROFILE": "default", "AWS_REGION": "eu-west-1" }
}
```

[Docs](https://awslabs.github.io/mcp/servers/amazon-keyspaces-mcp-server)

### Amazon Timestream for InfluxDB

InfluxDB-compatible time series.

```json
{
  "command": "uvx",
  "args": ["awslabs.timestream-for-influxdb-mcp-server@latest"],
  "env": { "AWS_PROFILE": "default", "AWS_REGION": "eu-west-1" }
}
```

[Docs](https://awslabs.github.io/mcp/servers/timestream-for-influxdb-mcp-server)

### Amazon Redshift

Data warehouse queries.

```json
{
  "command": "uvx",
  "args": ["awslabs.redshift-mcp-server@latest"],
  "env": { "AWS_PROFILE": "default", "AWS_REGION": "eu-west-1" }
}
```

[Docs](https://awslabs.github.io/mcp/servers/redshift-mcp-server)

### AWS S3 Tables

Query S3-based tables with SQL.

```json
{
  "command": "uvx",
  "args": ["awslabs.s3-tables-mcp-server@latest"],
  "env": { "AWS_PROFILE": "default", "AWS_REGION": "eu-west-1" }
}
```

[Docs](https://awslabs.github.io/mcp/servers/s3-tables-mcp-server)

---

## 💾 Caching

### Amazon ElastiCache

Complete ElastiCache operations.

```json
{
  "command": "uvx",
  "args": ["awslabs.elasticache-mcp-server@latest"],
  "env": { "AWS_PROFILE": "default", "AWS_REGION": "eu-west-1" }
}
```

[Docs](https://awslabs.github.io/mcp/servers/elasticache-mcp-server)

### ElastiCache/MemoryDB for Valkey

Advanced caching with Valkey.

```json
{
  "command": "uvx",
  "args": ["awslabs.valkey-mcp-server@latest"],
  "env": { "AWS_PROFILE": "default", "AWS_REGION": "eu-west-1" }
}
```

[Docs](https://awslabs.github.io/mcp/servers/valkey-mcp-server)

### ElastiCache for Memcached

High-speed caching.

```json
{
  "command": "uvx",
  "args": ["awslabs.memcached-mcp-server@latest"],
  "env": { "AWS_PROFILE": "default", "AWS_REGION": "eu-west-1" }
}
```

[Docs](https://awslabs.github.io/mcp/servers/memcached-mcp-server)

---

## 🤖 AI & Machine Learning

### Amazon Bedrock Knowledge Bases

Query knowledge bases with RAG.

```json
{
  "command": "uvx",
  "args": ["awslabs.bedrock-kb-retrieval-mcp-server@latest"],
  "env": { "AWS_PROFILE": "default", "AWS_REGION": "us-east-1" }
}
```

[Docs](https://awslabs.github.io/mcp/servers/bedrock-kb-retrieval-mcp-server)

### Amazon Bedrock Data Automation

Analyze documents, images, videos, audio.

```json
{
  "command": "uvx",
  "args": ["awslabs.aws-bedrock-data-automation-mcp-server@latest"],
  "env": { "AWS_PROFILE": "default", "AWS_REGION": "us-east-1" }
}
```

[Docs](https://awslabs.github.io/mcp/servers/aws-bedrock-data-automation-mcp-server)

### Amazon Bedrock Custom Model Import

Manage custom models for inference.

```json
{
  "command": "uvx",
  "args": ["awslabs.aws-bedrock-custom-model-import-mcp-server@latest"],
  "env": { "AWS_PROFILE": "default", "AWS_REGION": "us-east-1" }
}
```

[Docs](https://awslabs.github.io/mcp/servers/aws-bedrock-custom-model-import-mcp-server)

### Amazon Bedrock AgentCore

Build and deploy intelligent agents.

```json
{
  "command": "uvx",
  "args": ["awslabs.amazon-bedrock-agentcore-mcp-server@latest"],
  "env": { "AWS_PROFILE": "default", "AWS_REGION": "us-east-1" }
}
```

[Docs](https://awslabs.github.io/mcp/servers/amazon-bedrock-agentcore-mcp-server)

### Amazon Nova Canvas

AI image generation.

```json
{
  "command": "uvx",
  "args": ["awslabs.nova-canvas-mcp-server@latest"],
  "env": { "AWS_PROFILE": "default", "AWS_REGION": "us-east-1" }
}
```

[Docs](https://awslabs.github.io/mcp/servers/nova-canvas-mcp-server)

### Amazon SageMaker AI

Model development and deployment.

```json
{
  "command": "uvx",
  "args": ["awslabs.sagemaker-ai-mcp-server@latest"],
  "env": { "AWS_PROFILE": "default", "AWS_REGION": "us-east-1" }
}
```

[Docs](https://awslabs.github.io/mcp/servers/sagemaker-ai-mcp-server)

### SageMaker Spark Troubleshooting

Spark debugging and recommendations.

```json
{
  "command": "uvx",
  "args": [
    "awslabs.sagemaker-unified-studio-spark-troubleshooting-mcp-server@latest"
  ],
  "env": { "AWS_PROFILE": "default", "AWS_REGION": "us-east-1" }
}
```

[Docs](https://awslabs.github.io/mcp/servers/sagemaker-unified-studio-spark-troubleshooting-mcp-server)

### Amazon Kendra

Enterprise search and RAG.

```json
{
  "command": "uvx",
  "args": ["awslabs.amazon-kendra-index-mcp-server@latest"],
  "env": { "AWS_PROFILE": "default", "AWS_REGION": "us-east-1" }
}
```

[Docs](https://awslabs.github.io/mcp/servers/amazon-kendra-index-mcp-server)

### Amazon Q Business

AI assistant with anonymous access.

```json
{
  "command": "uvx",
  "args": ["awslabs.amazon-qbusiness-anonymous-mcp-server@latest"],
  "env": { "AWS_PROFILE": "default", "AWS_REGION": "us-east-1" }
}
```

[Docs](https://awslabs.github.io/mcp/servers/amazon-qbusiness-anonymous-mcp-server)

### Amazon Q Index

Search enterprise Q index.

```json
{
  "command": "uvx",
  "args": ["awslabs.amazon-qindex-mcp-server@latest"],
  "env": { "AWS_PROFILE": "default", "AWS_REGION": "us-east-1" }
}
```

[Docs](https://awslabs.github.io/mcp/servers/amazon-qindex-mcp-server)

---

## 📊 Observability & Monitoring

### Amazon CloudWatch

Metrics, alarms, and logs.

```json
{
  "command": "uvx",
  "args": ["awslabs.cloudwatch-mcp-server@latest"],
  "env": { "AWS_PROFILE": "default", "AWS_REGION": "eu-west-1" }
}
```

[Docs](https://awslabs.github.io/mcp/servers/cloudwatch-mcp-server)

### CloudWatch Application Signals

Application performance monitoring.

```json
{
  "command": "uvx",
  "args": ["awslabs.cloudwatch-applicationsignals-mcp-server@latest"],
  "env": { "AWS_PROFILE": "default", "AWS_REGION": "eu-west-1" }
}
```

[Docs](https://awslabs.github.io/mcp/servers/cloudwatch-applicationsignals-mcp-server)

### AWS CloudTrail

API activity and audit logs.

```json
{
  "command": "uvx",
  "args": ["awslabs.cloudtrail-mcp-server@latest"],
  "env": { "AWS_PROFILE": "default", "AWS_REGION": "eu-west-1" }
}
```

[Docs](https://awslabs.github.io/mcp/servers/cloudtrail-mcp-server)

### AWS Managed Prometheus

Prometheus-compatible monitoring.

```json
{
  "command": "uvx",
  "args": ["awslabs.prometheus-mcp-server@latest"],
  "env": { "AWS_PROFILE": "default", "AWS_REGION": "eu-west-1" }
}
```

[Docs](https://awslabs.github.io/mcp/servers/prometheus-mcp-server)

---

## 🌐 Networking

### AWS Network

VPC, Transit Gateway, Cloud WAN troubleshooting.

```json
{
  "command": "uvx",
  "args": ["awslabs.aws-network-mcp-server@latest"],
  "env": { "AWS_PROFILE": "default", "AWS_REGION": "eu-west-1" }
}
```

[Docs](https://awslabs.github.io/mcp/servers/aws-network-mcp-server)

---

## 📨 Messaging & Integration

### Amazon SNS/SQS

Event-driven messaging and queues.

```json
{
  "command": "uvx",
  "args": ["awslabs.amazon-sns-sqs-mcp-server@latest"],
  "env": { "AWS_PROFILE": "default", "AWS_REGION": "eu-west-1" }
}
```

[Docs](https://awslabs.github.io/mcp/servers/amazon-sns-sqs-mcp-server)

### Amazon MQ

RabbitMQ and ActiveMQ brokers.

```json
{
  "command": "uvx",
  "args": ["awslabs.amazon-mq-mcp-server@latest"],
  "env": { "AWS_PROFILE": "default", "AWS_REGION": "eu-west-1" }
}
```

[Docs](https://awslabs.github.io/mcp/servers/amazon-mq-mcp-server)

### AWS MSK

Kafka cluster management.

```json
{
  "command": "uvx",
  "args": ["awslabs.aws-msk-mcp-server@latest"],
  "env": { "AWS_PROFILE": "default", "AWS_REGION": "eu-west-1" }
}
```

[Docs](https://awslabs.github.io/mcp/servers/aws-msk-mcp-server)

### AWS AppSync

GraphQL API management.

```json
{
  "command": "uvx",
  "args": ["awslabs.aws-appsync-mcp-server@latest"],
  "env": { "AWS_PROFILE": "default", "AWS_REGION": "eu-west-1" }
}
```

[Docs](https://awslabs.github.io/mcp/servers/aws-appsync-mcp-server)

### OpenAPI

Dynamic API integration.

```json
{ "command": "uvx", "args": ["awslabs.openapi-mcp-server@latest"] }
```

[Docs](https://awslabs.github.io/mcp/servers/openapi-mcp-server)

---

## 💰 Cost & Billing

### AWS Pricing

Pre-deployment cost estimation.

```json
{
  "command": "uvx",
  "args": ["awslabs.aws-pricing-mcp-server@latest"],
  "env": { "AWS_PROFILE": "default", "AWS_REGION": "us-east-1" }
}
```

[Docs](https://awslabs.github.io/mcp/servers/aws-pricing-mcp-server)

### AWS Cost Explorer

Actual cost analysis and forecasting.

```json
{
  "command": "uvx",
  "args": ["awslabs.cost-explorer-mcp-server@latest"],
  "env": { "AWS_PROFILE": "default", "AWS_REGION": "us-east-1" }
}
```

[Docs](https://awslabs.github.io/mcp/servers/cost-explorer-mcp-server)

### AWS Billing

Billing and cost management.

```json
{
  "command": "uvx",
  "args": ["awslabs.billing-cost-management-mcp-server@latest"],
  "env": { "AWS_PROFILE": "default", "AWS_REGION": "us-east-1" }
}
```

[Docs](https://awslabs.github.io/mcp/servers/billing-cost-management-mcp-server)

---

## 🔐 Security & IAM

### AWS IAM

User, role, group, policy management.

```json
{
  "command": "uvx",
  "args": ["awslabs.iam-mcp-server@latest"],
  "env": { "AWS_PROFILE": "default", "AWS_REGION": "us-east-1" }
}
```

[Docs](https://awslabs.github.io/mcp/servers/iam-mcp-server)

### AWS Well-Architected Security

Security Pillar assessment.

```json
{
  "command": "uvx",
  "args": ["awslabs.well-architected-security-mcp-server@latest"],
  "env": { "AWS_PROFILE": "default", "AWS_REGION": "us-east-1" }
}
```

[Docs](https://awslabs.github.io/mcp/servers/well-architected-security-mcp-server)

---

## 📚 Documentation & Knowledge

### AWS Documentation

Latest AWS docs and APIs.

```json
{
  "command": "uvx",
  "args": ["awslabs.aws-documentation-mcp-server@latest"],
  "env": { "FASTMCP_LOG_LEVEL": "ERROR" }
}
```

[Docs](https://awslabs.github.io/mcp/servers/aws-documentation-mcp-server)

### AWS Knowledge (Remote)

Search docs, code samples, regional availability.

```json
{ "url": "https://knowledge-mcp.global.api.aws", "type": "http" }
```

[Docs](https://awslabs.github.io/mcp/servers/aws-knowledge-mcp-server)

### AWS Support

Create and manage support cases.

```json
{
  "command": "uvx",
  "args": ["awslabs.aws-support-mcp-server@latest"],
  "env": { "AWS_PROFILE": "default", "AWS_REGION": "us-east-1" }
}
```

[Docs](https://awslabs.github.io/mcp/servers/aws-support-mcp-server)

---

## 🛠️ Developer Tools

### AWS Diagram

Generate architecture diagrams.

```json
{ "command": "uvx", "args": ["awslabs.aws-diagram-mcp-server@latest"] }
```

[Docs](https://awslabs.github.io/mcp/servers/aws-diagram-mcp-server)

### Frontend

React and web development guidance.

```json
{ "command": "uvx", "args": ["awslabs.frontend-mcp-server@latest"] }
```

[Docs](https://awslabs.github.io/mcp/servers/frontend-mcp-server)

### Git Repo Research

Semantic code search.

```json
{ "command": "uvx", "args": ["awslabs.git-repo-research-mcp-server@latest"] }
```

[Docs](https://awslabs.github.io/mcp/servers/git-repo-research-mcp-server)

### Code Documentation Generation

Auto-generate docs from code.

```json
{ "command": "uvx", "args": ["awslabs.code-doc-gen-mcp-server@latest"] }
```

[Docs](https://awslabs.github.io/mcp/servers/code-doc-gen-mcp-server)

### Document Loader

Parse and extract document content.

```json
{ "command": "uvx", "args": ["awslabs.document-loader-mcp-server@latest"] }
```

[Docs](https://awslabs.github.io/mcp/servers/document-loader-mcp-server)

### Synthetic Data

Generate test data for dev/ML.

```json
{ "command": "uvx", "args": ["awslabs.syntheticdata-mcp-server@latest"] }
```

[Docs](https://awslabs.github.io/mcp/servers/syntheticdata-mcp-server)

---

## 📍 Location & IoT

### Amazon Location Service

Geocoding and route optimization.

```json
{
  "command": "uvx",
  "args": ["awslabs.aws-location-mcp-server@latest"],
  "env": { "AWS_PROFILE": "default", "AWS_REGION": "eu-west-1" }
}
```

[Docs](https://awslabs.github.io/mcp/servers/aws-location-mcp-server)

### AWS IoT SiteWise

Industrial IoT asset management.

```json
{
  "command": "uvx",
  "args": ["awslabs.aws-iot-sitewise-mcp-server@latest"],
  "env": { "AWS_PROFILE": "default", "AWS_REGION": "eu-west-1" }
}
```

[Docs](https://awslabs.github.io/mcp/servers/aws-iot-sitewise-mcp-server)

---

## 🏥 Healthcare & Life Sciences

### AWS HealthOmics

Genomics and lifescience workflows.

```json
{
  "command": "uvx",
  "args": ["awslabs.aws-healthomics-mcp-server@latest"],
  "env": { "AWS_PROFILE": "default", "AWS_REGION": "us-east-1" }
}
```

[Docs](https://awslabs.github.io/mcp/servers/aws-healthomics-mcp-server)

### AWS HealthLake

FHIR-compatible healthcare data.

```json
{
  "command": "uvx",
  "args": ["awslabs.healthlake-mcp-server@latest"],
  "env": { "AWS_PROFILE": "default", "AWS_REGION": "us-east-1" }
}
```

[Docs](https://awslabs.github.io/mcp/servers/healthlake-mcp-server)

---

## 📈 Data Processing

### Amazon Data Processing

AWS Glue and EMR pipelines.

```json
{
  "command": "uvx",
  "args": ["awslabs.aws-dataprocessing-mcp-server@latest"],
  "env": { "AWS_PROFILE": "default", "AWS_REGION": "eu-west-1" }
}
```

[Docs](https://awslabs.github.io/mcp/servers/aws-dataprocessing-mcp-server)

---

## 🔗 Full MCP Configuration Example

```json
{
  "mcpServers": {
    "aws-api": {
      "command": "uvx",
      "args": ["awslabs.aws-api-mcp-server@latest"],
      "env": { "AWS_PROFILE": "default", "AWS_REGION": "eu-west-1" }
    },
    "aws-knowledge": {
      "url": "https://knowledge-mcp.global.api.aws",
      "type": "http"
    },
    "cloudwatch": {
      "command": "uvx",
      "args": ["awslabs.cloudwatch-mcp-server@latest"],
      "env": { "AWS_PROFILE": "default", "AWS_REGION": "eu-west-1" }
    },
    "dynamodb": {
      "command": "uvx",
      "args": ["awslabs.dynamodb-mcp-server@latest"],
      "env": { "AWS_PROFILE": "default", "AWS_REGION": "eu-west-1" }
    }
  }
}
```

---

## References

- [AWS MCP Servers Home](https://awslabs.github.io/mcp/)
- [GitHub: awslabs/mcp](https://github.com/awslabs/mcp)
