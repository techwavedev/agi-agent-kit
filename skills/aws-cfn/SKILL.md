---
name: aws-cfn
description: Manage AWS CloudFormation resources and templates via MCP Server. Use for creating, reading, updating, and deleting resources through Cloud Control API, getting resource schemas, and generating CloudFormation templates from existing resources.
---

# AWS CloudFormation Skill

> Part of the [AWS skill family](../aws/SKILL.md). For full IaC, see [aws-iac](../aws-iac/SKILL.md).

Manage CloudFormation resources and templates via MCP.

## MCP Server Setup

```json
{
  "mcpServers": {
    "cloudformation": {
      "command": "uvx",
      "args": ["awslabs.cfn-mcp-server@latest"],
      "env": {
        "AWS_PROFILE": "default",
        "AWS_REGION": "eu-west-1"
      }
    }
  }
}
```

### Auto-Configure

```bash
python scripts/configure_mcp.py --profile default --region eu-west-1
```

## MCP Tools

| Tool                              | Description                               |
| --------------------------------- | ----------------------------------------- |
| `create_resource`                 | Create AWS resource via Cloud Control API |
| `get_resource`                    | Get resource configuration                |
| `update_resource`                 | Update resource properties                |
| `delete_resource`                 | Delete resource                           |
| `list_resources`                  | List resources by type                    |
| `get_resource_schema_information` | Get CFN schema for resource type          |
| `get_request_status`              | Check async operation status              |
| `create_template`                 | Generate CFN template from resources      |

## Workflows

### 1. Create Resource

```
Ask: "Create an S3 bucket with versioning enabled"
→ Uses create_resource with AWS::S3::Bucket
→ Returns resource identifier
```

### 2. Export to Template

```
Ask: "Create a CloudFormation template from my existing resources"
→ List resources with list_resources
→ Use create_template to generate YAML template
```

### 3. Understand Resource Schema

```
Ask: "What properties can I set on AWS::S3::Bucket?"
→ Uses get_resource_schema_information
→ Returns all available properties
```

### 4. Update Resource

```
Ask: "Enable encryption on my S3 bucket"
→ Uses update_resource with property changes
→ Applies declarative update
```

## Example Commands

| Task               | Tool                                       |
| ------------------ | ------------------------------------------ |
| Create S3 bucket   | `create_resource` with `AWS::S3::Bucket`   |
| List EC2 instances | `list_resources` with `AWS::EC2::Instance` |
| Get bucket config  | `get_resource` with bucket identifier      |
| Generate template  | `create_template` from listed resources    |

## Scripts

| Script                     | Purpose                   |
| -------------------------- | ------------------------- |
| `scripts/configure_mcp.py` | Auto-configure MCP client |

## References

- [CloudFormation MCP Server](https://awslabs.github.io/mcp/servers/cfn-mcp-server)
- [CloudFormation Resource Types](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-template-resource-type-ref.html)
