# Skills Catalog

> **Auto-generated Documentation** — Last updated: 2026-01-19 23:15
>
> This catalog is automatically maintained. Update it by running:
>
> ```bash
> python3 skill-creator/scripts/update_catalog.py --skills-dir skills/
> ```

This document provides comprehensive documentation on available skills, how to use them, and when each skill should be triggered. It serves as the central reference for understanding and leveraging the modular capabilities of this AI agent system.

---

## Table of Contents

- [What Are Skills?](#what-are-skills)
- [How Skills Work](#how-skills-work)
- [Available Skills](#available-skills)
  - [AWS (Hub)](#aws-hub)
  - [AWS CLI](#aws-cli)
  - [AWS Documentation](#aws-documentation)
  - [AWS EKS](#aws-eks)
  - [PDF Reader](#pdf-reader)
- [Skill Relationships](#skill-relationships)
- [Using Skills](#using-skills)
- [Creating New Skills](#creating-new-skills)
- [Maintenance](#maintenance)

---

## What Are Skills?

**Skills** are modular, self-contained packages that extend the AI agent's capabilities with specialized knowledge, workflows, and tools. Think of them as "onboarding guides" for specific domains or tasks—they transform a general-purpose agent into a specialized one equipped with procedural knowledge.

### What Skills Provide

| Component             | Description                                               |
| --------------------- | --------------------------------------------------------- |
| **Workflows**         | Multi-step procedures for specific domains                |
| **Tool Integrations** | Instructions for working with specific file formats, APIs |
| **Domain Expertise**  | Company-specific knowledge, schemas, business logic       |
| **Bundled Resources** | Scripts, references, and assets for repetitive tasks      |

### Skill Structure

Every skill follows this structure:

```
skill-name/
├── SKILL.md           # (required) Main instruction file with YAML frontmatter
├── scripts/           # (optional) Executable Python/Bash scripts
├── references/        # (optional) Documentation to be loaded as needed
└── assets/            # (optional) Files used in output (templates, images, etc.)
```

---

## How Skills Work

### Progressive Disclosure System

Skills use a three-level loading system to manage context efficiently:

1. **Metadata (name + description)** — Always in context (~100 words)
   - The agent sees skill names and descriptions at all times
   - This triggers skill activation when relevant

2. **SKILL.md body** — Loaded when skill triggers (<5k words)
   - Procedural instructions and workflow guidance
   - References to bundled resources

3. **Bundled resources** — Loaded as needed (unlimited)
   - Scripts can be executed without loading into context
   - References loaded only when specifically required

### Triggering a Skill

Skills are triggered automatically when the user's request matches the skill's description. You can also explicitly reference a skill:

```
"Use the pdf-reader skill to extract text from this document"
"I need to set up AWS credentials" → triggers aws-cli skill
"Help me deploy to EKS" → triggers aws-eks skill
```

---

## Available Skills

### AWS (Hub)

| Property     | Value         |
| ------------ | ------------- |
| **Name**     | `aws`         |
| **Location** | `skills/aws/` |
| **Type**     | Router / Hub  |

**Description:** Central hub for AWS cloud operations. Routes to specialized sub-skills for specific AWS services. Start here for any AWS-related work.

**When to Use:**

- Any AWS-related task
- Need to determine which AWS sub-skill to use
- General AWS questions or operations
- Setting up MCP servers for AWS services

**Sub-Skills:**

| Skill                          | Purpose                         | Trigger                         |
| ------------------------------ | ------------------------------- | ------------------------------- |
| [aws-cli](#aws-cli)            | Profile & credential management | Credentials, profiles, SSO      |
| [aws-docs](#aws-documentation) | Documentation lookup            | Best practices, troubleshooting |
| [aws-eks](#aws-eks)            | EKS cluster management          | Kubernetes on AWS               |

**Quick Start:**

```bash
# List AWS profiles
python3 skills/aws-cli/scripts/list_profiles.py

# Switch profile
eval $(python3 skills/aws-cli/scripts/switch_profile.py --profile myprofile)
```

**References:**

- `references/mcp_servers.md` — All AWS MCP servers configuration
- `references/common_patterns.md` — Shared patterns across AWS skills

---

### AWS CLI

| Property     | Value                 |
| ------------ | --------------------- |
| **Name**     | `aws-cli`             |
| **Location** | `skills/aws-cli/`     |
| **Parent**   | [AWS (Hub)](#aws-hub) |

**Description:** Manage AWS CLI profiles for authentication and credential management.

**When to Use:**

- Creating new AWS profiles
- Listing existing profiles
- Switching between profiles
- Configuring SSO access
- Setting up cross-account role assumption
- Any AWS operation requiring specific credentials

**Scripts:**

| Script                      | Purpose                                             |
| --------------------------- | --------------------------------------------------- |
| `scripts/create_profile.py` | Create/update profiles (standard, SSO, assume-role) |
| `scripts/list_profiles.py`  | List profiles with optional validation              |
| `scripts/switch_profile.py` | Generate shell commands to switch profile           |

**Quick Reference:**

```bash
# List profiles
python3 skills/aws-cli/scripts/list_profiles.py

# Validate profiles
python3 skills/aws-cli/scripts/list_profiles.py --validate

# Create standard profile
python3 skills/aws-cli/scripts/create_profile.py \
  --profile <name> \
  --access-key <key> \
  --secret-key <secret>

# Switch profile (apply to current shell)
eval $(python3 skills/aws-cli/scripts/switch_profile.py --profile <name>)
```

**References:**

- `references/sso_configuration.md` — SSO/IAM Identity Center setup
- `references/assume_role.md` — Cross-account role assumption

---

### AWS Documentation

| Property     | Value                 |
| ------------ | --------------------- |
| **Name**     | `aws-docs`            |
| **Location** | `skills/aws-docs/`    |
| **Parent**   | [AWS (Hub)](#aws-hub) |

**Description:** Look up AWS documentation, best practices, and troubleshooting guidance using the AWS Documentation MCP server.

**When to Use:**

- Looking up AWS documentation
- Searching for best practices and guidelines
- Getting service recommendations
- Troubleshooting AWS issues
- Finding API references and examples

**MCP Server Configuration:**

```json
{
  "mcpServers": {
    "aws-docs": {
      "command": "uvx",
      "args": ["awslabs.aws-documentation-mcp-server@latest"],
      "env": {
        "FASTMCP_LOG_LEVEL": "ERROR",
        "AWS_DOCUMENTATION_PARTITION": "aws"
      }
    }
  }
}
```

**Available Tools (via MCP):**

- `search_documentation` — Search AWS documentation
- `get_page_content` — Retrieve specific documentation pages
- `recommend` — Get service recommendations

**References:**

- `references/common_searches.md` — Common documentation search patterns
- `references/documentation_urls.md` — Key AWS documentation URLs

---

### AWS EKS

| Property     | Value                 |
| ------------ | --------------------- |
| **Name**     | `aws-eks`             |
| **Location** | `skills/aws-eks/`     |
| **Parent**   | [AWS (Hub)](#aws-hub) |

**Description:** Manage Amazon EKS (Elastic Kubernetes Service) clusters, including cluster operations, node groups, deployments, and troubleshooting.

**When to Use:**

- EKS cluster creation/management
- Node group scaling
- Kubernetes deployments on AWS
- Pod logs and troubleshooting
- Helm chart operations
- kubectl commands for EKS

**Scripts:**

| Script                     | Purpose                        |
| -------------------------- | ------------------------------ |
| `scripts/configure_mcp.py` | Auto-configure EKS MCP server  |
| `scripts/cluster_info.py`  | Get cluster details and status |

**MCP Server Configuration:**

```json
{
  "mcpServers": {
    "eks": {
      "command": "uvx",
      "args": ["awslabs.eks-mcp-server@latest", "--allow-write"],
      "env": {
        "AWS_PROFILE": "default",
        "AWS_REGION": "eu-west-1"
      }
    }
  }
}
```

**Quick Start:**

```bash
# Configure MCP with write access
python3 skills/aws-eks/scripts/configure_mcp.py --allow-write

# Get cluster info
python3 skills/aws-eks/scripts/cluster_info.py --cluster my-cluster
```

**References:**

- `references/mcp_setup.md` — MCP server configuration
- `references/cluster_operations.md` — Cluster management patterns
- `references/iam_roles.md` — IAM role requirements
- `references/troubleshooting.md` — Common issues and solutions

---

### PDF Reader

| Property     | Value                |
| ------------ | -------------------- |
| **Name**     | `pdf-reader`         |
| **Location** | `skills/pdf-reader/` |
| **Type**     | Standalone           |

**Description:** Extract text from PDF files for manipulation, search, and reference.

**When to Use:**

- Reading PDF content
- Extracting text from documents
- Searching within PDFs
- Converting PDF to text for further processing
- Documents with tables (use pdfplumber method)
- Scanned/image PDFs (use pymupdf for OCR)

**Scripts:**

| Script                    | Purpose                          |
| ------------------------- | -------------------------------- |
| `scripts/extract_text.py` | Multi-method PDF text extraction |

**Quick Reference:**

```bash
# Extract all text
python3 skills/pdf-reader/scripts/extract_text.py document.pdf

# Save to file
python3 skills/pdf-reader/scripts/extract_text.py document.pdf -o .tmp/output.txt

# Extract specific pages
python3 skills/pdf-reader/scripts/extract_text.py document.pdf -p 1-10

# Extract with specific method
python3 skills/pdf-reader/scripts/extract_text.py document.pdf -m pdfplumber
```

**Options:**

| Option                | Description                         |
| --------------------- | ----------------------------------- |
| `-o, --output FILE`   | Save to file (default: stdout)      |
| `-m, --method METHOD` | auto\|pdfplumber\|pymupdf\|pdfminer |
| `-p, --pages RANGE`   | Page range: "1-5" or "1,3,5"        |
| `--preserve-layout`   | Keep spatial arrangement of text    |
| `--json`              | Output with metadata                |

**Method Selection Guide:**

| Scenario                 | Recommended Method  |
| ------------------------ | ------------------- |
| General use              | `auto` (default)    |
| Documents with tables    | `pdfplumber`        |
| Large PDFs, speed needed | `pymupdf`           |
| Maximum text accuracy    | `pdfminer`          |
| Scanned/image PDFs       | `pymupdf` (has OCR) |

**Dependencies:**

```bash
pip install pdfplumber pymupdf pdfminer.six
```

**References:**

- `references/pdf_libraries.md` — Library comparison and selection guide

---

## Skill Relationships

```
┌─────────────────────────────────────────────────────────────────┐
│                        AWS Hub (aws)                            │
│        Central router for all AWS-related operations            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │   aws-cli   │  │  aws-docs   │  │        aws-eks          │  │
│  │  Profiles   │  │Documentation│  │ Kubernetes Operations   │  │
│  │ Credentials │  │Best Practices│  │ Cluster Management      │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                   Standalone Skills                             │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                      pdf-reader                             ││
│  │              PDF text extraction & processing               ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

---

## Using Skills

### Automatic Triggering

Skills are automatically triggered based on the user's request matching the skill description:

| User Request                                  | Triggered Skill |
| --------------------------------------------- | --------------- |
| "Set up my AWS credentials"                   | aws-cli         |
| "Deploy my app to EKS"                        | aws-eks         |
| "What's the best practice for S3 encryption?" | aws-docs        |
| "Extract text from this PDF"                  | pdf-reader      |

### Explicit Reference

You can explicitly invoke a skill:

```
"Use the aws-cli skill to create a new profile"
"Apply the pdf-reader skill to extract tables from report.pdf"
```

### Workflow Pattern

For complex tasks involving multiple skills:

1. **Start with the hub skill** (e.g., `aws`) for routing guidance
2. **Follow references** to specific sub-skills
3. **Use scripts** for deterministic operations
4. **Check references** for detailed documentation

### Best Practices

1. **Check existing skills first** — Before writing custom code, check if a skill handles the task
2. **Use scripts over inline code** — Bundled scripts are tested and reliable
3. **Follow skill workflows** — Skills often define optimal step sequences
4. **Update skills as you learn** — Add edge cases and troubleshooting tips

---

## Creating New Skills

### Quick Start

```bash
# Initialize a new skill
python3 skill-creator/scripts/init_skill.py my-new-skill --path skills/

# Edit the generated SKILL.md
# Customize scripts/, references/, assets/ as needed

# Package the skill
python3 skill-creator/scripts/package_skill.py skills/my-new-skill

# Update the catalog (MANDATORY)
python3 skill-creator/scripts/update_catalog.py --skills-dir skills/
```

### Skill Creation Checklist

- [ ] Clear, comprehensive description in YAML frontmatter
- [ ] "When to use" scenarios documented
- [ ] Quick start / common usage examples
- [ ] Scripts tested and documented
- [ ] References linked for detailed docs
- [ ] **Catalog updated after creation**

For detailed skill creation guidance, read: `skill-creator/SKILL_skillcreator.md`

---

## Maintenance

### Updating This Catalog

**IMPORTANT:** This catalog must be updated whenever skills are:

- Created
- Modified (description, scripts, or major functionality)
- Deleted

Update command:

```bash
python3 skill-creator/scripts/update_catalog.py --skills-dir skills/
```

Or manually update the relevant skill section following the template pattern.

### Adding a New Skill to the Catalog

When adding a new skill via the update script, verify:

1. **Entry in Table of Contents** — Link appears correctly
2. **Skill Section** contains:
   - Property table (name, location, type/parent)
   - Description from SKILL.md
   - Scripts table (if applicable)
   - References list
3. **Skill Relationships** diagram updated if needed
4. **Using Skills** triggering table updated

### Catalog Template for Manual Additions

````markdown
### Skill Name

| Property     | Value                |
| ------------ | -------------------- |
| **Name**     | `skill-name`         |
| **Location** | `skills/skill-name/` |
| **Type**     | Standalone           |

<!-- OR -->

| **Parent** | [Parent Skill](#parent-skill) |

**Description:** [Copy from SKILL.md description]

**When to Use:**

- [Trigger scenario 1]
- [Trigger scenario 2]

**Scripts:**

| Script                   | Purpose   |
| ------------------------ | --------- |
| `scripts/script_name.py` | [Purpose] |

**Quick Reference:**

\```bash

# Example command

python3 skills/skill-name/scripts/script.py --arg value
\```

**References:**

- `references/doc.md` — [Description]

---
````

---

_This catalog is part of the [3-Layer Architecture](../AGENTS.md) for reliable AI agent operations._
