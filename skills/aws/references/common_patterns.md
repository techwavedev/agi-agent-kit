# Common AWS Patterns

Shared patterns used across all AWS sub-skills.

## Profile Management

All AWS commands should respect the active profile:

```bash
# Check current identity
aws sts get-caller-identity

# With specific profile
aws sts get-caller-identity --profile myprofile
```

## Region Handling

Priority order for region:

1. `--region` flag on command
2. `AWS_REGION` environment variable
3. `AWS_DEFAULT_REGION` environment variable
4. Profile's configured region in `~/.aws/config`

```bash
# Get current region
aws configure get region

# Set for session
export AWS_REGION=eu-west-1
```

## Error Handling

Common AWS errors and solutions:

| Error                     | Cause               | Solution                       |
| ------------------------- | ------------------- | ------------------------------ |
| `ExpiredToken`            | Credentials expired | Refresh SSO or regenerate keys |
| `AccessDenied`            | Missing permissions | Check IAM policies             |
| `InvalidClientTokenId`    | Bad credentials     | Verify access key ID           |
| `SignatureDoesNotMatch`   | Bad secret key      | Regenerate credentials         |
| `RegionDisabledException` | Region not enabled  | Enable in account settings     |

## Pagination

For commands returning many results:

```bash
# Use --max-items and --starting-token
aws s3api list-objects-v2 --bucket mybucket --max-items 100

# Or let AWS CLI handle pagination
aws s3api list-objects-v2 --bucket mybucket --no-paginate
```

## Output Formatting

```bash
# JSON (default)
aws eks list-clusters --output json

# Table (human readable)
aws eks list-clusters --output table

# Text (scripting)
aws eks list-clusters --output text

# Query specific fields
aws eks describe-cluster --name mycluster --query 'cluster.status' --output text
```

## Tagging Convention

Consistent tagging across resources:

```bash
--tags Key=Environment,Value=production Key=Project,Value=myapp Key=Owner,Value=team@example.com
```
