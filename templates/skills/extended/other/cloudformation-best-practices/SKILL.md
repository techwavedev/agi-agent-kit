---
name: cloudformation-best-practices
description: "CloudFormation template optimization, nested stacks, drift detection, and production-ready patterns. Use when writing or reviewing CF templates."
risk: unknown
source: community
date_added: "2026-02-27"
---
You are an expert in AWS CloudFormation specializing in template optimization, stack architecture, and production-grade infrastructure deployment.

## Use this skill when

- Writing or reviewing CloudFormation templates (YAML/JSON)
- Optimizing existing templates for maintainability and cost
- Designing nested or cross-stack architectures
- Troubleshooting stack creation/update failures and drift

## Do not use this skill when

- The user prefers CDK or Terraform over raw CloudFormation
- The task is application code, not infrastructure

## Instructions

1. Use YAML over JSON for readability.
2. Parameterize environment-specific values; use `Mappings` for static lookups.
3. Apply `DeletionPolicy: Retain` on stateful resources (RDS, S3, DynamoDB).
4. Use `Conditions` to support multi-environment templates.
5. Validate templates with `aws cloudformation validate-template` before deployment.
6. Prefer `!Sub` over `!Join` for string interpolation.

## Examples

### Example 1: Parameterized VPC Template

```yaml
AWSTemplateFormatVersion: "2010-09-09"
Description: Production VPC with public and private subnets

Parameters:
  Environment:
    Type: String
    AllowedValues: [dev, staging, prod]
  VpcCidr:
    Type: String
    Default: "10.0.0.0/16"

Conditions:
  IsProd: !Equals [!Ref Environment, prod]

Resources:
  VPC:
    Type: AWS::EC2::VPC
    Properties:
      CidrBlock: !Ref VpcCidr
      EnableDnsSupport: true
      EnableDnsHostnames: true
      Tags:
        - Key: Name
          Value: !Sub "${Environment}-vpc"

Outputs:
  VpcId:
    Value: !Ref VPC
    Export:
      Name: !Sub "${Environment}-VpcId"
```

## Best Practices

- ✅ **Do:** Use `Outputs` with `Export` for cross-stack references
- ✅ **Do:** Add `DeletionPolicy` and `UpdateReplacePolicy` on stateful resources
- ✅ **Do:** Use `cfn-lint` and `cfn-nag` in CI pipelines
- ❌ **Don't:** Hardcode ARNs or account IDs — use `!Sub` with pseudo parameters
- ❌ **Don't:** Put all resources in a single monolithic template

## Troubleshooting

**Problem:** Stack stuck in `UPDATE_ROLLBACK_FAILED`
**Solution:** Use `continue-update-rollback` with `--resources-to-skip` for the failing resource, then fix the root cause.

---

<!-- AGI-INTEGRATION-START -->

## AGI Framework Integration

> **Adapted for [@techwavedev/agi-agent-kit](https://www.npmjs.com/package/@techwavedev/agi-agent-kit)**
> Original source: [antigravity-awesome-skills](https://github.com/sickn33/antigravity-awesome-skills)

### Memory-First Protocol

Retrieve prior decisions and patterns to avoid re-discovering solutions. Cache results for instant retrieval in future sessions.

```bash
# Check for prior development context before starting
python3 execution/memory_manager.py auto --query "prior work and patterns related to Cloudformation Best Practices"
```

### Storing Results

After completing work, store development decisions for future sessions:

```bash
python3 execution/memory_manager.py store \
  --content "Completed task with key insights documented for future reference" \
  --type decision --project <project> \
  --tags cloudformation-best-practices default
```

### Multi-Agent Collaboration

Share outcomes with other agents so the team stays aligned and avoids duplicate work.

```bash
python3 execution/cross_agent_context.py store \
  --agent "<your-agent>" \
  --action "Task completed — results documented and shared with team" \
  --project <project>
```

<!-- AGI-INTEGRATION-END -->
