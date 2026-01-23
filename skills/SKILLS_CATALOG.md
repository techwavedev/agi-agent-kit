# Skills Catalog

> **Auto-generated Documentation** — Last updated: 2026-01-23 12:47
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
  - [Aws Terraform](#aws-terraform)
  - [Confluent Kafka](#confluent-kafka)
  - [Consul](#consul)
  - [Gitlab](#gitlab)
  - [Karpenter](#karpenter)
  - [Opensearch](#opensearch)
  - [Pdf Reader](#pdf-reader)
  - [Qdrant Memory](#qdrant-memory)
  - [Victoriametrics](#victoriametrics)
  - [Webcrawler](#webcrawler)
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

**Description:** Comprehensive AWS MCP skill covering ALL AWS services. Use for any AWS-related task - infrastructure, databases, AI/ML, observability, networking, serverless, and more. This single skill provides access to 60+ AWS MCP servers organized by category.

**References:**
- `references/common_patterns.md`
- `references/mcp_servers.md`

---

### Confluent Kafka

| Property | Value |
| -------- | ----- |
| **Name** | `confluent-kafka` |
| **Location** | `skills/confluent-kafka/` |
| **Parent** | [Aws](#aws) |

**Description:** Confluent Kafka specialist for tarball/Ansible custom installations. Expert in updating, maintaining, checking health, troubleshooting, documenting, analyzing metrics, and upgrading Confluent Kafka deployments from 7.x to 8.x versions. Covers KRaft mode (ZooKeeper-less), broker configuration, Schema Registry, Connect, ksqlDB, Control Center, and production-grade operations. Use when working with Confluent Platform installations, migrations to KRaft, performance tuning, health monitoring, and infrastructure-as-code with Ansible.

**Scripts:**

| Script | Purpose |
| ------ | ------- |
| `scripts/kafka_health_check.py` | *[See script for details]* |
| `scripts/upgrade_preflight.py` | *[See script for details]* |
| `scripts/validate_config.py` | *[See script for details]* |

**References:**
- `references/ansible_playbooks.md`
- `references/ec_deployment.md`
- `references/kraft_migration.md`
- `references/troubleshooting.md`
- `references/upgrade_7x_to_8x.md`

---

### Consul

| Property | Value |
| -------- | ----- |
| **Name** | `consul` |
| **Location** | `skills/consul/` |
| **Parent** | [Aws](#aws) |

**Description:** HashiCorp Consul specialist for EKS clusters. Use for Consul service mesh installation, configuration, HA setup, maintenance, updates, upgrades, troubleshooting, and optimization. Covers Consul Connect, intentions, health checks, ACLs, gossip encryption, TLS configuration, federation, and Kubernetes integration via consul-k8s Helm chart. Requires kubectl and helm access to target EKS cluster.

**Scripts:**

| Script | Purpose |
| ------ | ------- |
| `scripts/consul_health_report.py` | *[See script for details]* |
| `scripts/consul_status.py` | *[See script for details]* |
| `scripts/generate_values.py` | *[See script for details]* |

**References:**
- `references/acl_setup.md`
- `references/ha_config.md`
- `references/troubleshooting.md`
- `references/upgrades.md`

---

### Gitlab

| Property | Value |
| -------- | ----- |
| **Name** | `gitlab` |
| **Location** | `skills/gitlab/` |
| **Parent** | [Aws](#aws) |

**Description:** GitLab specialist for Kubernetes agent management on EKS clusters. Use for GitLab agent (agentk) installation, configuration, upgrades, GitOps with Flux, CI/CD pipeline integration, project management via API, token management, and troubleshooting connectivity issues. Covers agent registration, Helm deployments, KAS configuration (self-managed on-prem), impersonation, and multi-cluster setups. Requires kubectl/helm access to target EKS cluster and GitLab API token.

**Scripts:**

| Script | Purpose |
| ------ | ------- |
| `scripts/generate_agent_values.py` | *[See script for details]* |
| `scripts/gitlab_agent_status.py` | *[See script for details]* |

**References:**
- `references/agent_installation.md`
- `references/api_reference.md`
- `references/gitops_flux.md`
- `references/troubleshooting.md`

---

### Karpenter

| Property | Value |
| -------- | ----- |
| **Name** | `karpenter` |
| **Location** | `skills/karpenter/` |
| **Parent** | [Aws](#aws) |

**Description:** Karpenter Kubernetes autoscaler specialist for EKS clusters. Use for troubleshooting, documenting, managing, creating, updating, upgrading Karpenter deployments, and obtaining live cluster information. Covers NodePool/EC2NodeClass configuration, cost optimization, node consolidation, drift detection, Spot interruption handling, and migration from Cluster Autoscaler. Requires kubectl access to target EKS cluster.

**Scripts:**

| Script | Purpose |
| ------ | ------- |
| `scripts/generate_ec2nodeclass.py` | *[See script for details]* |
| `scripts/generate_nodepool.py` | *[See script for details]* |
| `scripts/karpenter_status.py` | *[See script for details]* |

**References:**
- `references/ec2nodeclasses.md`
- `references/migration.md`
- `references/nodepools.md`
- `references/troubleshooting.md`

---

### Aws Terraform

| Property | Value |
| -------- | ----- |
| **Name** | `aws-terraform` |
| **Location** | `skills/aws-terraform/` |
| **Type** | Standalone |

**Description:** AWS infrastructure deployments using Terraform and Terragrunt. Use for any task involving: (1) Writing, validating, or deploying Terraform/HCL code for AWS, (2) Security scanning with Checkov, (3) AWS provider documentation lookup, (4) Terraform Registry module analysis, (5) Terragrunt multi-environment orchestration, (6) Infrastructure as Code best practices for AWS. Parent skill: aws.

**Scripts:**

| Script | Purpose |
| ------ | ------- |
| `scripts/configure_mcp.py` | *[See script for details]* |

**References:**
- `references/best_practices.md`
- `references/checkov_reference.md`

---

### Opensearch

| Property | Value |
| -------- | ----- |
| **Name** | `opensearch` |
| **Location** | `skills/opensearch/` |
| **Type** | Standalone |

**Description:** OpenSearch specialist covering querying (Query DSL, SQL), performance optimization, cluster management, monitoring, OpenSearch Dashboards, ML/AI (neural search, embeddings, ML Commons), data ingestion (Logstash, Fluent Bit, Data Prepper), OpenSearch Operator for Kubernetes, and MCP integration. Use for any task involving: (1) Writing or optimizing OpenSearch queries, (2) Index design and mapping, (3) Cluster health and performance tuning, (4) OpenSearch Dashboards visualization, (5) Neural/semantic search with vectors, (6) Log and data ingestion pipelines, (7) Kubernetes deployments with OpenSearch Operator.

**Scripts:**

| Script | Purpose |
| ------ | ------- |
| `scripts/configure_mcp.py` | *[See script for details]* |

**References:**
- `references/ml_neural_search.md`
- `references/operator.md`
- `references/query_dsl.md`

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

### Qdrant Memory

| Property | Value |
| -------- | ----- |
| **Name** | `qdrant-memory` |
| **Location** | `skills/qdrant-memory/` |
| **Type** | Standalone |

**Description:** "Intelligent token optimization through Qdrant-powered semantic caching and long-term memory. Use for (1) Semantic Cache - avoid LLM calls entirely for semantically similar queries with 100% token savings, (2) Long-Term Memory - retrieve only relevant context chunks instead of full conversation history with 80-95% context reduction, (3) Hybrid Search - combine vector similarity with keyword filtering for technical queries, (4) Memory Management - store and retrieve conversation memories, decisions, and code patterns with metadata filtering. Triggers when needing to cache responses, remember past interactions, optimize context windows, or implement RAG patterns."

**Scripts:**

| Script | Purpose |
| ------ | ------- |
| `scripts/benchmark_token_savings.py` | *[See script for details]* |
| `scripts/embedding_utils.py` | *[See script for details]* |
| `scripts/hybrid_search.py` | *[See script for details]* |
| `scripts/init_collection.py` | *[See script for details]* |
| `scripts/memory_retrieval.py` | *[See script for details]* |
| `scripts/semantic_cache.py` | *[See script for details]* |
| `scripts/test_skill.py` | *[See script for details]* |

**References:**
- `references/advanced_patterns.md`
- `references/collection_schemas.md`
- `references/complete_guide.md`
- `references/embedding_models.md`

---

### Victoriametrics

| Property | Value |
| -------- | ----- |
| **Name** | `victoriametrics` |
| **Location** | `skills/victoriametrics/` |
| **Type** | Standalone |

**Description:** VictoriaMetrics time-series database specialist covering deployment (bare metal, Docker, EKS/Kubernetes), cluster architecture (vminsert/vmselect/vmstorage), vmagent configuration, performance optimization, capacity planning, troubleshooting, monitoring, and Prometheus migration/compatibility. Use for any task involving: (1) Installing or upgrading VictoriaMetrics (single-node or cluster), (2) vmagent scraping and remote write configuration, (3) Capacity planning and resource optimization, (4) Prometheus to VictoriaMetrics migration with vmctl, (5) High availability and replication setup, (6) Kubernetes/EKS deployments with Helm or Operator, (7) MetricsQL queries and optimization, (8) Troubleshooting performance issues.

**References:**
- `references/kubernetes.md`
- `references/prometheus_migration.md`
- `references/troubleshooting.md`

---

### Webcrawler

| Property | Value |
| -------- | ----- |
| **Name** | `webcrawler` |
| **Location** | `skills/webcrawler/` |
| **Type** | Standalone |

**Description:** "Documentation harvesting agent for crawling and extracting content from documentation websites. Use for crawling documentation sites and extracting all pages about a subject, building offline knowledge bases from online docs, harvesting API references, tutorials, or guides from documentation portals, creating structured markdown exports from multi-page documentation, and downloading and organizing technical docs for embedding or RAG pipelines. Supports recursive crawling with depth control, content filtering, and structured output."

**Scripts:**

| Script | Purpose |
| ------ | ------- |
| `scripts/crawl_docs.py` | *[See script for details]* |
| `scripts/extract_page.py` | *[See script for details]* |
| `scripts/filter_docs.py` | *[See script for details]* |

**References:**
- `references/advanced_crawling.md`

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
