# AWS Assume Role Configuration

## Overview

Role assumption allows a profile to temporarily acquire permissions from another AWS account or role. This is essential for cross-account access and privilege escalation patterns.

## Basic Assume Role Profile

Add to `~/.aws/config`:

```ini
[profile source-account]
region = us-east-1
output = json

[profile cross-account-admin]
role_arn = arn:aws:iam::TARGET_ACCOUNT_ID:role/AdminRole
source_profile = source-account
region = us-east-1
```

## With MFA Required

```ini
[profile secure-admin]
role_arn = arn:aws:iam::123456789012:role/AdminRole
source_profile = my-base-profile
mfa_serial = arn:aws:iam::111111111111:mfa/my-user
region = us-east-1
```

When using this profile, you'll be prompted for your MFA code.

## Role Chaining

Assume a role, then assume another role from that context:

```ini
[profile base]
# Standard credentials

[profile intermediate]
role_arn = arn:aws:iam::222222222222:role/IntermediateRole
source_profile = base

[profile final]
role_arn = arn:aws:iam::333333333333:role/FinalRole
source_profile = intermediate
```

**Note:** Role chaining has a maximum of 1 hour session duration.

## Session Duration

```ini
[profile long-session]
role_arn = arn:aws:iam::123456789012:role/DevRole
source_profile = base
duration_seconds = 3600  # 1 hour (max depends on role config)
```

## External ID (for third-party access)

```ini
[profile vendor-access]
role_arn = arn:aws:iam::VENDOR_ACCOUNT:role/VendorRole
source_profile = my-profile
external_id = unique-external-id-12345
```

## Using with create_profile.py

```bash
# Create assume-role profile
python scripts/create_profile.py \
  --profile cross-account \
  --assume-role arn:aws:iam::123456789012:role/MyRole \
  --source-profile default \
  --region us-east-1

# With MFA
python scripts/create_profile.py \
  --profile secure-profile \
  --assume-role arn:aws:iam::123456789012:role/SecureRole \
  --source-profile default \
  --mfa-serial arn:aws:iam::111111111111:mfa/my-user
```

## Credential Process (Advanced)

For custom credential retrieval:

```ini
[profile custom]
credential_process = /path/to/credential-script.sh
region = us-east-1
```

The script must output JSON:

```json
{
  "Version": 1,
  "AccessKeyId": "AKIA...",
  "SecretAccessKey": "...",
  "SessionToken": "...",
  "Expiration": "2024-01-01T00:00:00Z"
}
```

## Troubleshooting

| Issue                                      | Solution                                                       |
| ------------------------------------------ | -------------------------------------------------------------- |
| "Access Denied" assuming role              | Check trust policy on target role includes source account/user |
| "MFA required" error                       | Add mfa_serial to profile config                               |
| Session expires quickly                    | Check role's maximum session duration in IAM                   |
| "Not authorized to perform sts:AssumeRole" | Source credentials lack sts:AssumeRole permission              |
