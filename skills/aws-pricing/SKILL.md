---
name: aws-pricing
description: AWS pricing discovery, cost analysis, and planning via MCP. Use for querying service prices, comparing regions, analyzing CDK/Terraform project costs, and getting cost optimization recommendations aligned with Well-Architected Framework.
---

# AWS Pricing Skill

> Part of the [AWS skill family](../aws/SKILL.md). For IaC costs, see [aws-iac](../aws-iac/SKILL.md).

AWS pricing discovery and cost analysis.

## MCP Server Setup

```json
{
  "mcpServers": {
    "pricing": {
      "command": "uvx",
      "args": ["awslabs.aws-pricing-mcp-server@latest"],
      "env": {
        "AWS_PROFILE": "default",
        "AWS_REGION": "us-east-1"
      }
    }
  }
}
```

## Features

- **Service Catalog** — Discover all AWS services with pricing
- **Real-Time Pricing** — Current prices with filtering
- **Multi-Region Compare** — Compare prices across regions
- **Cost Reports** — Detailed analysis with breakdowns
- **IaC Analysis** — Scan CDK/Terraform for costs
- **Natural Language** — Query pricing in plain English

## Capabilities

### Pricing Discovery

- Explore all AWS services with pricing
- Discover pricing attributes (instance types, regions, etc.)
- Real-time pricing queries with filtering
- Multi-region comparisons
- Download bulk pricing data (CSV/JSON)

### Cost Analysis

- Detailed cost reports with breakdowns
- Infrastructure project analysis (CDK, Terraform)
- Architecture pattern guidance
- Well-Architected cost optimization

## Workflows

### 1. Query Service Pricing

```
Ask: "What's the price of m6i.large EC2 in eu-west-1?"
→ Returns on-demand and reserved pricing
```

### 2. Compare Regions

```
Ask: "Compare S3 storage costs: us-east-1 vs eu-west-1"
→ Returns pricing comparison table
```

### 3. Analyze Project Costs

```
Ask: "Estimate costs for my Terraform project"
→ Scans .tf files
→ Identifies resources
→ Returns cost breakdown
```

### 4. Optimize Costs

```
Ask: "How can I reduce my Lambda costs?"
→ Returns Well-Architected recommendations
→ Suggests optimization strategies
```

## Example Queries

| Query                     | Result                       |
| ------------------------- | ---------------------------- |
| "List EC2 instance types" | Available types with pricing |
| "RDS PostgreSQL pricing"  | Database pricing by size     |
| "Bedrock model costs"     | Per-token pricing            |
| "Compare EBS volumes"     | GP3 vs IO2 pricing           |

## Scripts

| Script                     | Purpose                   |
| -------------------------- | ------------------------- |
| `scripts/configure_mcp.py` | Auto-configure MCP client |

## References

- [AWS Pricing MCP Server](https://awslabs.github.io/mcp/servers/aws-pricing-mcp-server)
- [AWS Pricing Calculator](https://calculator.aws/)
