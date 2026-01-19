---
name: aws
description: AWS cloud operations hub. Use for any AWS-related task including EKS cluster management, CLI profile configuration, S3, Lambda, and other AWS services. This skill routes to specialized sub-skills and provides shared context (profiles, regions) across all AWS operations. Start here for AWS work.
---

# AWS Skill

Central hub for AWS cloud operations. Routes to specialized sub-skills.

## Quick Start

### 1. Set up credentials

```bash
# List existing profiles
python aws-cli/scripts/list_profiles.py

# Create new profile
python aws-cli/scripts/create_profile.py --profile myprofile --access-key AKIA... --secret-key ...

# Switch profile
eval $(python aws-cli/scripts/switch_profile.py --profile myprofile)
```

### 2. Configure MCP servers

```bash
# Auto-configure EKS MCP
python aws-eks/scripts/configure_mcp.py --allow-write
```

## Sub-Skills

| Skill                            | Purpose                         | When to Use                                     |
| -------------------------------- | ------------------------------- | ----------------------------------------------- |
| [aws-cli](../aws-cli/SKILL.md)   | Profile & credential management | Setting up credentials, switching accounts, SSO |
| [aws-docs](../aws-docs/SKILL.md) | Documentation lookup            | AWS best practices, troubleshooting, guidance   |
| [aws-eks](../aws-eks/SKILL.md)   | EKS cluster management          | Kubernetes on AWS, cluster ops, deployments     |

## Routing Guide

**Authentication & Profiles:**
→ Use `aws-cli` skill

- Create/list/switch profiles
- SSO configuration
- Cross-account role assumption

**Documentation & Best Practices:**
→ Use `aws-docs` skill

- Look up AWS documentation
- Search for best practices and guidelines
- Get service recommendations
- Troubleshooting guidance
- API references and examples

**Kubernetes/EKS:**
→ Use `aws-eks` skill

- Cluster creation/management
- Node group scaling
- Pod logs, deployments, troubleshooting

**General AWS CLI:**
→ Use AWS CLI directly with the active profile

```bash
aws <service> <command> --profile <profile>
```

## Shared Context

All AWS sub-skills inherit from the active profile:

```bash
# Set profile for all subsequent operations
export AWS_PROFILE=myprofile
export AWS_REGION=eu-west-1

# Or use profile flag per command
--profile myprofile --region eu-west-1
```

## MCP Servers

Configure multiple AWS MCP servers for comprehensive access:

```json
{
  "mcpServers": {
    "aws-api": {
      "command": "uvx",
      "args": ["awslabs.aws-api-mcp-server@latest"],
      "env": { "AWS_PROFILE": "default", "AWS_REGION": "eu-west-1" }
    },
    "eks": {
      "command": "uvx",
      "args": ["awslabs.eks-mcp-server@latest", "--allow-write"],
      "env": { "AWS_PROFILE": "default", "AWS_REGION": "eu-west-1" }
    },
    "cloudformation": {
      "command": "uvx",
      "args": ["awslabs.cfn-mcp-server@latest"],
      "env": { "AWS_PROFILE": "default", "AWS_REGION": "eu-west-1" }
    }
  }
}
```

See [references/mcp_servers.md](references/mcp_servers.md) for full list of AWS MCP servers.

## Adding New AWS Sub-Skills

To add a new AWS service skill:

1. Create `skills/aws-<service>/` directory
2. Follow the skill-creator pattern
3. Add entry to this routing table
4. Share profile/region context via `AWS_PROFILE` and `AWS_REGION` env vars

## References

- [references/mcp_servers.md](references/mcp_servers.md) — All AWS MCP servers
- [references/common_patterns.md](references/common_patterns.md) — Shared patterns across AWS skills
