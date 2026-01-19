# Skills Catalog

> **Auto-generated Documentation** — Last updated: 2026-01-19 23:36
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
  - [Aws Appsync](#aws-appsync)
  - [Aws Aurora Dsql](#aws-aurora-dsql)
  - [Aws Aurora Mysql](#aws-aurora-mysql)
  - [Aws Aurora Postgresql](#aws-aurora-postgresql)
  - [Aws Bedrock Agentcore](#aws-bedrock-agentcore)
  - [Aws Bedrock Custom Model](#aws-bedrock-custom-model)
  - [Aws Bedrock Data Automation](#aws-bedrock-data-automation)
  - [Aws Bedrock Kb](#aws-bedrock-kb)
  - [Aws Billing](#aws-billing)
  - [Aws Ccapi](#aws-ccapi)
  - [Aws Cdk](#aws-cdk)
  - [Aws Cfn](#aws-cfn)
  - [Aws Cli](#aws-cli)
  - [Aws Cloudtrail](#aws-cloudtrail)
  - [Aws Cloudwatch](#aws-cloudwatch)
  - [Aws Cloudwatch Signals](#aws-cloudwatch-signals)
  - [Aws Code Doc Gen](#aws-code-doc-gen)
  - [Aws Core](#aws-core)
  - [Aws Cost Explorer](#aws-cost-explorer)
  - [Aws Data Processing](#aws-data-processing)
  - [Aws Diagram](#aws-diagram)
  - [Aws Docs](#aws-docs)
  - [Aws Document Loader](#aws-document-loader)
  - [Aws Documentdb](#aws-documentdb)
  - [Aws Dynamodb](#aws-dynamodb)
  - [Aws Ecs](#aws-ecs)
  - [Aws Eks](#aws-eks)
  - [Aws Elasticache](#aws-elasticache)
  - [Aws Finch](#aws-finch)
  - [Aws Frontend](#aws-frontend)
  - [Aws Git Repo](#aws-git-repo)
  - [Aws Healthlake](#aws-healthlake)
  - [Aws Healthomics](#aws-healthomics)
  - [Aws Iac](#aws-iac)
  - [Aws Iam](#aws-iam)
  - [Aws Iot Sitewise](#aws-iot-sitewise)
  - [Aws Kendra](#aws-kendra)
  - [Aws Keyspaces](#aws-keyspaces)
  - [Aws Knowledge](#aws-knowledge)
  - [Aws Lambda](#aws-lambda)
  - [Aws Location](#aws-location)
  - [Aws Memcached](#aws-memcached)
  - [Aws Mq](#aws-mq)
  - [Aws Msk](#aws-msk)
  - [Aws Neptune](#aws-neptune)
  - [Aws Network](#aws-network)
  - [Aws Nova Canvas](#aws-nova-canvas)
  - [Aws Openapi](#aws-openapi)
  - [Aws Pricing](#aws-pricing)
  - [Aws Prometheus](#aws-prometheus)
  - [Aws Q Business](#aws-q-business)
  - [Aws Q Index](#aws-q-index)
  - [Aws Redshift](#aws-redshift)
  - [Aws S3 Tables](#aws-s3-tables)
  - [Aws Sagemaker](#aws-sagemaker)
  - [Aws Sagemaker Spark](#aws-sagemaker-spark)
  - [Aws Serverless](#aws-serverless)
  - [Aws Sns Sqs](#aws-sns-sqs)
  - [Aws Stepfunctions](#aws-stepfunctions)
  - [Aws Support](#aws-support)
  - [Aws Synthetic Data](#aws-synthetic-data)
  - [Aws Terraform](#aws-terraform)
  - [Aws Timestream](#aws-timestream)
  - [Aws Valkey](#aws-valkey)
  - [Aws Well Architected](#aws-well-architected)
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

### Aws Appsync

| Property | Value |
| -------- | ----- |
| **Name** | `aws-appsync` |
| **Location** | `skills/aws-appsync/` |
| **Type** | Standalone |

**Description:** AWS AppSync via MCP. Use for backend API management and GraphQL operations.

---

### Aws Aurora Dsql

| Property | Value |
| -------- | ----- |
| **Name** | `aws-aurora-dsql` |
| **Location** | `skills/aws-aurora-dsql/` |
| **Type** | Standalone |

**Description:** Amazon Aurora DSQL distributed SQL via MCP. Use for PostgreSQL-compatible distributed SQL operations.

---

### Aws Aurora Mysql

| Property | Value |
| -------- | ----- |
| **Name** | `aws-aurora-mysql` |
| **Location** | `skills/aws-aurora-mysql/` |
| **Type** | Standalone |

**Description:** Amazon Aurora MySQL via RDS Data API. Use for MySQL database operations.

---

### Aws Aurora Postgresql

| Property | Value |
| -------- | ----- |
| **Name** | `aws-aurora-postgresql` |
| **Location** | `skills/aws-aurora-postgresql/` |
| **Type** | Standalone |

**Description:** Amazon Aurora PostgreSQL via RDS Data API. Use for PostgreSQL database operations.

---

### Aws Bedrock Agentcore

| Property | Value |
| -------- | ----- |
| **Name** | `aws-bedrock-agentcore` |
| **Location** | `skills/aws-bedrock-agentcore/` |
| **Type** | Standalone |

**Description:** Amazon Bedrock AgentCore via MCP. Use for building, deploying, and managing intelligent agents.

---

### Aws Bedrock Custom Model

| Property | Value |
| -------- | ----- |
| **Name** | `aws-bedrock-custom-model` |
| **Location** | `skills/aws-bedrock-custom-model/` |
| **Type** | Standalone |

**Description:** Amazon Bedrock Custom Model Import via MCP. Use for managing custom models in Bedrock for on-demand inference.

---

### Aws Bedrock Data Automation

| Property | Value |
| -------- | ----- |
| **Name** | `aws-bedrock-data-automation` |
| **Location** | `skills/aws-bedrock-data-automation/` |
| **Type** | Standalone |

**Description:** Amazon Bedrock Data Automation via MCP. Use for analyzing documents, images, videos, and audio files.

---

### Aws Bedrock Kb

| Property | Value |
| -------- | ----- |
| **Name** | `aws-bedrock-kb` |
| **Location** | `skills/aws-bedrock-kb/` |
| **Type** | Standalone |

**Description:** Amazon Bedrock Knowledge Bases retrieval via MCP. Use for querying enterprise knowledge bases with citation support and RAG.

---

### Aws Billing

| Property | Value |
| -------- | ----- |
| **Name** | `aws-billing` |
| **Location** | `skills/aws-billing/` |
| **Type** | Standalone |

**Description:** AWS Billing and Cost Management via MCP. Use for billing management and cost analysis.

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

### Aws Cdk

| Property | Value |
| -------- | ----- |
| **Name** | `aws-cdk` |
| **Location** | `skills/aws-cdk/` |
| **Type** | Standalone |

**Description:** AWS CDK via MCP. Use for CDK development with security compliance using CDK-nag.

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

### Aws Cloudtrail

| Property | Value |
| -------- | ----- |
| **Name** | `aws-cloudtrail` |
| **Location** | `skills/aws-cloudtrail/` |
| **Type** | Standalone |

**Description:** AWS CloudTrail via MCP. Use for API activity, user, and resource analysis.

---

### Aws Cloudwatch

| Property | Value |
| -------- | ----- |
| **Name** | `aws-cloudwatch` |
| **Location** | `skills/aws-cloudwatch/` |
| **Type** | Standalone |

**Description:** Amazon CloudWatch via MCP. Use for metrics, alarms, and logs analysis.

---

### Aws Cloudwatch Signals

| Property | Value |
| -------- | ----- |
| **Name** | `aws-cloudwatch-signals` |
| **Location** | `skills/aws-cloudwatch-signals/` |
| **Type** | Standalone |

**Description:** Amazon CloudWatch Application Signals via MCP. Use for application monitoring and performance insights.

---

### Aws Code Doc Gen

| Property | Value |
| -------- | ----- |
| **Name** | `aws-code-doc-gen` |
| **Location** | `skills/aws-code-doc-gen/` |
| **Type** | Standalone |

**Description:** Code Documentation Generation via MCP. Use for automated documentation from code analysis.

---

### Aws Core

| Property | Value |
| -------- | ----- |
| **Name** | `aws-core` |
| **Location** | `skills/aws-core/` |
| **Type** | Standalone |

**Description:** AWS Core MCP Server. Use for intelligent planning and AWS MCP server orchestration.

---

### Aws Cost Explorer

| Property | Value |
| -------- | ----- |
| **Name** | `aws-cost-explorer` |
| **Location** | `skills/aws-cost-explorer/` |
| **Type** | Standalone |

**Description:** Analyze actual AWS costs and usage data via Cost Explorer MCP. Use for cost breakdowns by service/region, comparing costs between periods, forecasting future costs, and identifying cost drivers. Queries your actual AWS billing data.

---

### Aws Data Processing

| Property | Value |
| -------- | ----- |
| **Name** | `aws-data-processing` |
| **Location** | `skills/aws-data-processing/` |
| **Type** | Standalone |

**Description:** Amazon Data Processing via MCP. Use for AWS Glue and EMR data processing pipelines.

---

### Aws Diagram

| Property | Value |
| -------- | ----- |
| **Name** | `aws-diagram` |
| **Location** | `skills/aws-diagram/` |
| **Type** | Standalone |

**Description:** AWS Diagram via MCP. Use for generating architecture diagrams and technical illustrations.

---

### Aws Document Loader

| Property | Value |
| -------- | ----- |
| **Name** | `aws-document-loader` |
| **Location** | `skills/aws-document-loader/` |
| **Type** | Standalone |

**Description:** Document parsing and content extraction via MCP. Use for loading and parsing documents for AI processing.

---

### Aws Documentdb

| Property | Value |
| -------- | ----- |
| **Name** | `aws-documentdb` |
| **Location** | `skills/aws-documentdb/` |
| **Type** | Standalone |

**Description:** Amazon DocumentDB via MCP. Use for MongoDB-compatible document database operations.

---

### Aws Dynamodb

| Property | Value |
| -------- | ----- |
| **Name** | `aws-dynamodb` |
| **Location** | `skills/aws-dynamodb/` |
| **Type** | Standalone |

**Description:** Amazon DynamoDB operations via MCP. Use for complete DynamoDB operations and table management.

---

### Aws Ecs

| Property | Value |
| -------- | ----- |
| **Name** | `aws-ecs` |
| **Location** | `skills/aws-ecs/` |
| **Type** | Standalone |

**Description:** Amazon ECS container orchestration and application deployment via MCP. Use for deploying containers, managing services, task definitions, and cluster operations.

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

### Aws Elasticache

| Property | Value |
| -------- | ----- |
| **Name** | `aws-elasticache` |
| **Location** | `skills/aws-elasticache/` |
| **Type** | Standalone |

**Description:** Amazon ElastiCache via MCP. Use for complete ElastiCache operations.

---

### Aws Finch

| Property | Value |
| -------- | ----- |
| **Name** | `aws-finch` |
| **Location** | `skills/aws-finch/` |
| **Type** | Standalone |

**Description:** Local container building with ECR integration via Finch MCP. Use for building containers locally and pushing to Amazon ECR.

---

### Aws Frontend

| Property | Value |
| -------- | ----- |
| **Name** | `aws-frontend` |
| **Location** | `skills/aws-frontend/` |
| **Type** | Standalone |

**Description:** Frontend MCP Server. Use for React and modern web development guidance.

---

### Aws Git Repo

| Property | Value |
| -------- | ----- |
| **Name** | `aws-git-repo` |
| **Location** | `skills/aws-git-repo/` |
| **Type** | Standalone |

**Description:** Git Repo Research via MCP. Use for semantic code search and repository analysis.

---

### Aws Healthlake

| Property | Value |
| -------- | ----- |
| **Name** | `aws-healthlake` |
| **Location** | `skills/aws-healthlake/` |
| **Type** | Standalone |

**Description:** AWS HealthLake via MCP. Use for FHIR interactions and healthcare datastore management.

---

### Aws Healthomics

| Property | Value |
| -------- | ----- |
| **Name** | `aws-healthomics` |
| **Location** | `skills/aws-healthomics/` |
| **Type** | Standalone |

**Description:** AWS HealthOmics via MCP. Use for lifescience workflows and genomic analysis.

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

### Aws Iam

| Property | Value |
| -------- | ----- |
| **Name** | `aws-iam` |
| **Location** | `skills/aws-iam/` |
| **Type** | Standalone |

**Description:** AWS IAM via MCP. Use for user, role, group, and policy management.

---

### Aws Iot Sitewise

| Property | Value |
| -------- | ----- |
| **Name** | `aws-iot-sitewise` |
| **Location** | `skills/aws-iot-sitewise/` |
| **Type** | Standalone |

**Description:** AWS IoT SiteWise via MCP. Use for industrial IoT asset management, data ingestion, monitoring, and analytics.

---

### Aws Kendra

| Property | Value |
| -------- | ----- |
| **Name** | `aws-kendra` |
| **Location** | `skills/aws-kendra/` |
| **Type** | Standalone |

**Description:** Amazon Kendra enterprise search via MCP. Use for enterprise search and RAG enhancement.

---

### Aws Keyspaces

| Property | Value |
| -------- | ----- |
| **Name** | `aws-keyspaces` |
| **Location** | `skills/aws-keyspaces/` |
| **Type** | Standalone |

**Description:** Amazon Keyspaces via MCP. Use for Apache Cassandra-compatible operations.

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

### Aws Location

| Property | Value |
| -------- | ----- |
| **Name** | `aws-location` |
| **Location** | `skills/aws-location/` |
| **Type** | Standalone |

**Description:** Amazon Location Service via MCP. Use for place search, geocoding, and route optimization.

---

### Aws Memcached

| Property | Value |
| -------- | ----- |
| **Name** | `aws-memcached` |
| **Location** | `skills/aws-memcached/` |
| **Type** | Standalone |

**Description:** Amazon ElastiCache for Memcached via MCP. Use for high-speed caching operations.

---

### Aws Mq

| Property | Value |
| -------- | ----- |
| **Name** | `aws-mq` |
| **Location** | `skills/aws-mq/` |
| **Type** | Standalone |

**Description:** Amazon MQ via MCP. Use for message broker management with RabbitMQ and ActiveMQ.

---

### Aws Msk

| Property | Value |
| -------- | ----- |
| **Name** | `aws-msk` |
| **Location** | `skills/aws-msk/` |
| **Type** | Standalone |

**Description:** AWS MSK via MCP. Use for managing, monitoring, and optimizing Amazon MSK clusters.

---

### Aws Neptune

| Property | Value |
| -------- | ----- |
| **Name** | `aws-neptune` |
| **Location** | `skills/aws-neptune/` |
| **Type** | Standalone |

**Description:** Amazon Neptune graph database via MCP. Use for graph queries with openCypher and Gremlin.

---

### Aws Network

| Property | Value |
| -------- | ----- |
| **Name** | `aws-network` |
| **Location** | `skills/aws-network/` |
| **Type** | Standalone |

**Description:** AWS network troubleshooting and analysis via MCP. Use for path tracing, flow log analysis, Transit Gateway/Cloud WAN routing, VPC connectivity issues, Network Firewall rules, and VPN connections. Read-only operations for safe troubleshooting.

---

### Aws Nova Canvas

| Property | Value |
| -------- | ----- |
| **Name** | `aws-nova-canvas` |
| **Location** | `skills/aws-nova-canvas/` |
| **Type** | Standalone |

**Description:** Amazon Nova Canvas AI image generation via MCP. Use for generating images with text and color guidance.

---

### Aws Openapi

| Property | Value |
| -------- | ----- |
| **Name** | `aws-openapi` |
| **Location** | `skills/aws-openapi/` |
| **Type** | Standalone |

**Description:** OpenAPI via MCP. Use for dynamic API integration through OpenAPI specifications.

---

### Aws Pricing

| Property | Value |
| -------- | ----- |
| **Name** | `aws-pricing` |
| **Location** | `skills/aws-pricing/` |
| **Type** | Standalone |

**Description:** AWS pricing discovery, cost analysis, and planning via MCP. Use for querying service prices, comparing regions, analyzing CDK/Terraform project costs, and getting cost optimization recommendations aligned with Well-Architected Framework.

---

### Aws Prometheus

| Property | Value |
| -------- | ----- |
| **Name** | `aws-prometheus` |
| **Location** | `skills/aws-prometheus/` |
| **Type** | Standalone |

**Description:** AWS Managed Prometheus via MCP. Use for Prometheus-compatible monitoring operations.

---

### Aws Q Business

| Property | Value |
| -------- | ----- |
| **Name** | `aws-q-business` |
| **Location** | `skills/aws-q-business/` |
| **Type** | Standalone |

**Description:** Amazon Q Business anonymous access via MCP. Use for AI assistant based on knowledge base with anonymous access.

---

### Aws Q Index

| Property | Value |
| -------- | ----- |
| **Name** | `aws-q-index` |
| **Location** | `skills/aws-q-index/` |
| **Type** | Standalone |

**Description:** Amazon Q Index search via MCP. Use for searching through enterprise's Q index.

---

### Aws Redshift

| Property | Value |
| -------- | ----- |
| **Name** | `aws-redshift` |
| **Location** | `skills/aws-redshift/` |
| **Type** | Standalone |

**Description:** Amazon Redshift via MCP. Use for discovering, exploring, and querying Redshift clusters and serverless workgroups.

---

### Aws S3 Tables

| Property | Value |
| -------- | ----- |
| **Name** | `aws-s3-tables` |
| **Location** | `skills/aws-s3-tables/` |
| **Type** | Standalone |

**Description:** AWS S3 Tables via MCP. Use for managing, querying, and ingesting S3-based tables with SQL support.

---

### Aws Sagemaker

| Property | Value |
| -------- | ----- |
| **Name** | `aws-sagemaker` |
| **Location** | `skills/aws-sagemaker/` |
| **Type** | Standalone |

**Description:** Amazon SageMaker AI resource management via MCP. Use for model development, training, and deployment.

---

### Aws Sagemaker Spark

| Property | Value |
| -------- | ----- |
| **Name** | `aws-sagemaker-spark` |
| **Location** | `skills/aws-sagemaker-spark/` |
| **Type** | Standalone |

**Description:** SageMaker Unified Studio Spark via MCP. Use for Spark troubleshooting, code recommendation, and upgrades.

---

### Aws Serverless

| Property | Value |
| -------- | ----- |
| **Name** | `aws-serverless` |
| **Location** | `skills/aws-serverless/` |
| **Type** | Standalone |

**Description:** Complete serverless application lifecycle with SAM CLI. Use for initializing, building, deploying SAM apps, deploying web apps (Express, Next.js) to Lambda, managing domains, viewing logs/metrics, and getting Lambda event schemas.

---

### Aws Sns Sqs

| Property | Value |
| -------- | ----- |
| **Name** | `aws-sns-sqs` |
| **Location** | `skills/aws-sns-sqs/` |
| **Type** | Standalone |

**Description:** Amazon SNS/SQS via MCP. Use for event-driven messaging and queue management.

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

### Aws Support

| Property | Value |
| -------- | ----- |
| **Name** | `aws-support` |
| **Location** | `skills/aws-support/` |
| **Type** | Standalone |

**Description:** AWS Support case management via MCP. Use for creating and managing AWS Support cases.

---

### Aws Synthetic Data

| Property | Value |
| -------- | ----- |
| **Name** | `aws-synthetic-data` |
| **Location** | `skills/aws-synthetic-data/` |
| **Type** | Standalone |

**Description:** Synthetic Data via MCP. Use for generating realistic test data for development and ML.

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

### Aws Timestream

| Property | Value |
| -------- | ----- |
| **Name** | `aws-timestream` |
| **Location** | `skills/aws-timestream/` |
| **Type** | Standalone |

**Description:** Amazon Timestream for InfluxDB via MCP. Use for InfluxDB-compatible time series operations.

---

### Aws Valkey

| Property | Value |
| -------- | ----- |
| **Name** | `aws-valkey` |
| **Location** | `skills/aws-valkey/` |
| **Type** | Standalone |

**Description:** Amazon ElastiCache/MemoryDB for Valkey via MCP. Use for advanced data structures and caching with Valkey.

---

### Aws Well Architected

| Property | Value |
| -------- | ----- |
| **Name** | `aws-well-architected` |
| **Location** | `skills/aws-well-architected/` |
| **Type** | Standalone |

**Description:** AWS Well-Architected Security Assessment via MCP. Use for assessing environments against Security Pillar.

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
