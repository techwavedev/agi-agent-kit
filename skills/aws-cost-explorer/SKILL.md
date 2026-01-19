---
name: aws-cost-explorer
description: Analyze actual AWS costs and usage data via Cost Explorer MCP. Use for cost breakdowns by service/region, comparing costs between periods, forecasting future costs, and identifying cost drivers. Queries your actual AWS billing data.
---

# AWS Cost Explorer Skill

> Part of the [AWS skill family](../aws/SKILL.md). For pricing info, see [aws-pricing](../aws-pricing/SKILL.md).

Analyze actual AWS costs and usage from your account.

## MCP Server Setup

```json
{
  "mcpServers": {
    "cost-explorer": {
      "command": "uvx",
      "args": ["awslabs.cost-explorer-mcp-server@latest"],
      "env": {
        "AWS_PROFILE": "default",
        "AWS_REGION": "us-east-1"
      }
    }
  }
}
```

## Features

- **Cost Analysis** — Breakdown by service, region, tags
- **Period Comparison** — Compare costs between time periods
- **Cost Forecasting** — Predict future spending
- **Driver Analysis** — Top 10 cost change drivers
- **Natural Language** — Query costs in plain English

## MCP Tools

| Tool                             | Description                                      |
| -------------------------------- | ------------------------------------------------ |
| `get_today_date`                 | Current date for relative queries                |
| `get_dimension_values`           | Available values for dimension (SERVICE, REGION) |
| `get_tag_values`                 | Available values for tag key                     |
| `get_cost_and_usage`             | Cost data with filtering and grouping            |
| `get_cost_and_usage_comparisons` | Compare two time periods                         |
| `get_cost_comparison_drivers`    | Top 10 cost change drivers                       |
| `get_cost_forecast`              | Predict future costs                             |

## Workflows

### 1. Analyze Current Costs

```
Ask: "What are my AWS costs this month by service?"
→ get_cost_and_usage grouped by SERVICE
→ Returns breakdown table
```

### 2. Compare Periods

```
Ask: "Compare my costs this month vs last month"
→ get_cost_and_usage_comparisons
→ Shows delta and percentage change
```

### 3. Identify Cost Drivers

```
Ask: "Why did my costs increase?"
→ get_cost_comparison_drivers
→ Top 10 drivers with explanations
```

### 4. Forecast Costs

```
Ask: "What will I spend next month?"
→ get_cost_forecast
→ Prediction with confidence intervals
```

## Example Queries

| Query                         | Tool                             |
| ----------------------------- | -------------------------------- |
| "Costs by service this month" | `get_cost_and_usage`             |
| "EC2 costs in eu-west-1"      | `get_cost_and_usage` filtered    |
| "Month-over-month comparison" | `get_cost_and_usage_comparisons` |
| "What caused the spike?"      | `get_cost_comparison_drivers`    |
| "Forecast next quarter"       | `get_cost_forecast`              |

## Pricing vs Cost Explorer

| Skill               | Data Source       | Use For                               |
| ------------------- | ----------------- | ------------------------------------- |
| `aws-pricing`       | AWS Pricing API   | Lookup prices, estimate new resources |
| `aws-cost-explorer` | Your billing data | Analyze actual spending               |

## Scripts

| Script                     | Purpose                   |
| -------------------------- | ------------------------- |
| `scripts/configure_mcp.py` | Auto-configure MCP client |

## References

- [Cost Explorer MCP Server](https://awslabs.github.io/mcp/servers/cost-explorer-mcp-server)
- [AWS Cost Explorer](https://docs.aws.amazon.com/cost-management/latest/userguide/)
