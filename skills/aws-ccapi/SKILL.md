---
name: aws-ccapi
description: Manage 1,100+ AWS resources via Cloud Control API with integrated security scanning. Use for declarative resource creation, reading, updating, deleting, and listing. Features security-first workflow with Checkov scanning, credential awareness, and template generation.
---

# AWS Cloud Control API Skill

> Part of the [AWS skill family](../aws/SKILL.md). For CLI commands, see [aws-api](../aws-api/SKILL.md).

Manage AWS resources declaratively via Cloud Control API with security scanning.

## MCP Server Setup

```json
{
  "mcpServers": {
    "ccapi": {
      "command": "uvx",
      "args": ["awslabs.ccapi-mcp-server@latest"],
      "env": {
        "AWS_PROFILE": "default",
        "AWS_REGION": "eu-west-1",
        "SECURITY_SCANNING": "enabled"
      }
    }
  }
}
```

### Auto-Configure

```bash
python scripts/configure_mcp.py --profile default --region eu-west-1
```

## Features

- **1,100+ Resource Types** — All AWS and partner resources
- **Security Scanning** — Checkov integration before deployment
- **Credential Awareness** — Shows account/region before changes
- **Token Workflow** — AI cannot bypass security steps
- **Template Generation** — Export to CloudFormation

## MCP Tools

### Core Tools

| Tool                           | Description                               |
| ------------------------------ | ----------------------------------------- |
| `check_environment_variables`  | Verify AWS credentials configured         |
| `get_aws_session_info`         | Get account ID, region, credential source |
| `get_aws_account_info`         | Quick one-step account info               |
| `generate_infrastructure_code` | Prepare properties and CF template        |
| `explain`                      | Show what will be created/modified        |
| `run_checkov`                  | Security scan the template                |

### Resource Tools (CRUDL)

| Tool              | Description                           |
| ----------------- | ------------------------------------- |
| `create_resource` | Create any AWS resource declaratively |
| `get_resource`    | Read resource properties              |
| `update_resource` | Update with JSON Patch operations     |
| `delete_resource` | Remove resource with confirmation     |
| `list_resources`  | List all resources of a type          |

### Utility Tools

| Tool                              | Description                            |
| --------------------------------- | -------------------------------------- |
| `get_resource_schema_information` | Get CloudFormation schema for resource |
| `create_template`                 | Generate CFN template from resources   |

## Secure Workflow

The server enforces this workflow:

```
1. check_environment_variables() → environment_token
2. get_aws_session_info() → credentials_token
3. generate_infrastructure_code() → generated_code_token
4. explain() → explained_token
5. run_checkov() → security_scan_token (if enabled)
6. create_resource() → resource created
```

**Security guarantees:**

- Cannot skip credential checks
- Cannot bypass security scans
- Full transparency before changes
- Audit trail via token chain

## Configuration

| Variable             | Default   | Description                  |
| -------------------- | --------- | ---------------------------- |
| `AWS_PROFILE`        | default   | AWS profile to use           |
| `AWS_REGION`         | us-east-1 | Target region                |
| `SECURITY_SCANNING`  | enabled   | Enable Checkov scanning      |
| `CCAPI_DEFAULT_TAGS` | -         | Auto-apply tags to resources |

## Example Operations

### Create S3 Bucket

```
Ask: "Create an encrypted S3 bucket with versioning"
→ Workflow runs through all security steps
→ Shows exactly what will be created
→ Runs Checkov security scan
→ Creates bucket with properties shown
```

### List EC2 Instances

```
Ask: "List all EC2 instances"
→ Uses list_resources with AWS::EC2::Instance
→ Returns all instances with properties
```

### Get Resource Schema

```
Ask: "What properties can I set on an RDS instance?"
→ Uses get_resource_schema_information
→ Returns full CloudFormation schema
```

## Scripts

| Script                     | Purpose                   |
| -------------------------- | ------------------------- |
| `scripts/configure_mcp.py` | Auto-configure MCP client |

## References

- [AWS Cloud Control API MCP Server](https://awslabs.github.io/mcp/servers/ccapi-mcp-server)
- [Cloud Control API Docs](https://docs.aws.amazon.com/cloudcontrolapi/latest/userguide/)
- [Supported Resource Types](https://docs.aws.amazon.com/cloudcontrolapi/latest/userguide/supported-resources.html)
