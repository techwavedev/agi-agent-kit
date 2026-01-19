---
name: aws-stepfunctions
description: Execute AWS Step Functions state machines as AI tools. Use for running complex multi-step workflows, orchestrating AWS services, and executing business processes. Supports Standard and Express workflows with EventBridge Schema Registry integration.
---

# AWS Step Functions Skill

> Part of the [AWS skill family](../aws/SKILL.md). For Lambda, see [aws-lambda](../aws-lambda/SKILL.md).

Execute Step Functions state machines as AI tools.

## MCP Server Setup

```json
{
  "mcpServers": {
    "stepfunctions": {
      "command": "uvx",
      "args": ["awslabs.stepfunctions-tool-mcp-server@latest"],
      "env": {
        "AWS_PROFILE": "default",
        "AWS_REGION": "eu-west-1",
        "STATE_MACHINE_PREFIX": "ai-workflows-"
      }
    }
  }
}
```

### Auto-Configure

```bash
python scripts/configure_mcp.py --prefix ai-workflows-
```

## Features

- **State Machines as Tools** — AI invokes workflows directly
- **Standard & Express** — Long-running or high-volume workflows
- **Schema Support** — EventBridge Schema Registry integration
- **Orchestration** — Coordinate multiple AWS services
- **Security Isolation** — AI only invokes, workflows have permissions

## Architecture

```
Model → MCP Client → Step Functions MCP Server → State Machine
                                                      ↓
                                          ├── Other AWS Services
                                          ├── Lambda Functions
                                          └── External APIs
```

## Configuration

| Variable                                 | Description           |
| ---------------------------------------- | --------------------- |
| `STATE_MACHINE_PREFIX`                   | Filter by name prefix |
| `STATE_MACHINE_LIST`                     | Comma-separated ARNs  |
| `STATE_MACHINE_TAG_KEY`                  | Filter by tag key     |
| `STATE_MACHINE_TAG_VALUE`                | Filter by tag value   |
| `STATE_MACHINE_INPUT_SCHEMA_ARN_TAG_KEY` | Tag with schema ARN   |

## Workflow Types

| Type         | Use For                             |
| ------------ | ----------------------------------- |
| **Standard** | Long-running, needs status tracking |
| **Express**  | High-volume, short-duration, sync   |

## Tool Documentation

The server builds tool docs from:

1. **State Machine Description** — Base tool description
2. **Workflow Comment** — Context from definition
3. **Input Schema** — From EventBridge Schema Registry

## Workflows

### 1. Execute Business Process

```
Ask: "Process the new customer order"
→ Invokes order-processing state machine
→ Orchestrates inventory, payment, shipping
→ Returns execution result
```

### 2. Run Data Pipeline

```
Ask: "Run the daily ETL pipeline"
→ Invokes ETL state machine
→ Coordinates Glue, S3, Redshift
→ Tracks execution status
```

### 3. Orchestrate AI Workflow

```
Ask: "Analyze and summarize the uploaded document"
→ Invokes document-analysis state machine
→ Coordinates Textract, Comprehend, Bedrock
→ Returns analysis results
```

## Best Practices

1. **Descriptive Names** — Clear state machine descriptions
2. **Schema Validation** — Use EventBridge schemas
3. **Prefix Naming** — Consistent prefix for AI tools
4. **Idempotency** — Design for retry safety
5. **Error Handling** — Proper Catch/Retry in definitions

## Scripts

| Script                     | Purpose                   |
| -------------------------- | ------------------------- |
| `scripts/configure_mcp.py` | Auto-configure MCP client |

## References

- [Step Functions MCP Server](https://awslabs.github.io/mcp/servers/stepfunctions-tool-mcp-server)
- [Step Functions Docs](https://docs.aws.amazon.com/step-functions/)
