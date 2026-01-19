---
name: aws-cli
description: Manage AWS CLI profiles for authentication and credential management. Use when creating new AWS profiles, listing existing profiles, switching between profiles, configuring SSO access, or setting up cross-account role assumption. Essential for any AWS operation requiring specific credentials or multi-account access.
---

# AWS CLI Profile Skill

> Part of the [AWS skill family](../aws/SKILL.md). For EKS operations, see [aws-eks](../aws-eks/SKILL.md).

Manage AWS CLI profiles for authentication across AWS operations.

## Quick Reference

| Task                       | Command                                                                                           |
| -------------------------- | ------------------------------------------------------------------------------------------------- |
| List profiles              | `python scripts/list_profiles.py`                                                                 |
| Validate profiles          | `python scripts/list_profiles.py --validate`                                                      |
| Create standard profile    | `python scripts/create_profile.py --profile <name> --access-key <key> --secret-key <secret>`      |
| Create assume-role profile | `python scripts/create_profile.py --profile <name> --assume-role <arn> --source-profile <source>` |
| Switch profile             | `eval $(python scripts/switch_profile.py --profile <name>)`                                       |

## Workflows

### 1. Create Standard IAM Profile

```
1. Gather credentials (access key ID and secret access key)
2. Run create_profile.py:
   python scripts/create_profile.py \
     --profile myprofile \
     --access-key AKIA... \
     --secret-key ... \
     --region us-east-1
3. Validate: python scripts/list_profiles.py --profile myprofile --validate
```

### 2. Create Cross-Account Profile

```
1. Ensure source profile exists and is valid
2. Get target role ARN from administrator
3. Run create_profile.py:
   python scripts/create_profile.py \
     --profile cross-account \
     --assume-role arn:aws:iam::123456789012:role/MyRole \
     --source-profile default
4. Validate: python scripts/list_profiles.py --profile cross-account --validate
```

**With MFA:**

```
python scripts/create_profile.py \
  --profile secure-admin \
  --assume-role arn:aws:iam::123456789012:role/AdminRole \
  --source-profile default \
  --mfa-serial arn:aws:iam::111111111111:mfa/my-user
```

### 3. Configure SSO Profile

SSO requires interactive browser authentication:

```
1. Run: aws configure sso --profile <name>
2. Enter SSO start URL and region when prompted
3. Complete browser authentication
4. Login: aws sso login --profile <name>
5. Validate: aws sts get-caller-identity --profile <name>
```

See [references/sso_configuration.md](references/sso_configuration.md) for detailed SSO setup.

### 4. Switch Active Profile

For current shell session:

```bash
# Generate and apply export commands
eval $(python scripts/switch_profile.py --profile myprofile)

# With validation first
eval $(python scripts/switch_profile.py --profile myprofile --validate)

# For fish shell
eval (python scripts/switch_profile.py --profile myprofile --shell fish)
```

### 5. List and Validate All Profiles

```bash
# List all profiles
python scripts/list_profiles.py

# Validate credentials (slower, makes API calls)
python scripts/list_profiles.py --validate

# JSON output for scripting
python scripts/list_profiles.py --validate --json
```

## Integration with Other Skills

### EKS Integration

Set the correct profile before EKS operations:

```bash
# Switch to profile with EKS access
eval $(python skills/aws-cli-profile/scripts/switch_profile.py --profile eks-admin)

# Then use EKS skill
aws eks list-clusters
```

Or configure MCP server with specific profile:

```json
{
  "mcpServers": {
    "eks": {
      "command": "uvx",
      "args": ["awslabs.eks-mcp-server@latest"],
      "env": {
        "AWS_PROFILE": "eks-admin"
      }
    }
  }
}
```

## Scripts

| Script                      | Purpose                                             |
| --------------------------- | --------------------------------------------------- |
| `scripts/create_profile.py` | Create/update profiles (standard, SSO, assume-role) |
| `scripts/list_profiles.py`  | List profiles with optional validation              |
| `scripts/switch_profile.py` | Generate shell commands to switch profile           |

## References

- [references/sso_configuration.md](references/sso_configuration.md) — SSO/IAM Identity Center setup
- [references/assume_role.md](references/assume_role.md) — Cross-account role assumption

## Fallback: AWS CLI Direct

If scripts are unavailable, use AWS CLI directly:

```bash
# Configure profile interactively
aws configure --profile myprofile

# List profiles (parse config files)
cat ~/.aws/credentials
cat ~/.aws/config

# Test profile
aws sts get-caller-identity --profile myprofile

# Set profile for session
export AWS_PROFILE=myprofile
```

## Troubleshooting

| Issue                    | Solution                                                |
| ------------------------ | ------------------------------------------------------- |
| "Profile not found"      | Check spelling; run `list_profiles.py` to see available |
| "Invalid credentials"    | Credentials may be expired; regenerate in IAM console   |
| "Access Denied"          | Profile lacks required permissions                      |
| SSO token expired        | Run `aws sso login --profile <name>`                    |
| MFA prompt not appearing | Ensure `mfa_serial` is set in config                    |
