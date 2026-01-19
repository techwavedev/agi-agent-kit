# Skills Catalog

> **Auto-generated Documentation** — Last updated: 2026-01-20 00:02
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

**Description:** Comprehensive AWS MCP skill covering ALL AWS services. Use for any AWS-related task - infrastructure, databases, AI/ML, observability, networking, serverless, and more. This single skill provides access to 60+ AWS MCP servers organized by category.

**References:**
- `references/common_patterns.md`
- `references/mcp_servers.md`

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
