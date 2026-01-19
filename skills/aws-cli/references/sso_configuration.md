# AWS SSO Profile Configuration

## Overview

AWS IAM Identity Center (successor to AWS SSO) provides a streamlined way to manage access across multiple AWS accounts without managing long-term credentials.

## Interactive SSO Setup

```bash
# Start SSO configuration wizard
aws configure sso --profile <profile-name>

# You'll be prompted for:
# - SSO session name (optional)
# - SSO start URL (e.g., https://my-org.awsapps.com/start)
# - SSO region
# - SSO registration scopes (accept default or customize)
```

## Manual Config File Setup

Add to `~/.aws/config`:

```ini
[profile my-sso-profile]
sso_session = my-session
sso_account_id = 123456789012
sso_role_name = AdministratorAccess
region = us-east-1
output = json

[sso-session my-session]
sso_start_url = https://my-org.awsapps.com/start
sso_region = us-east-1
sso_registration_scopes = sso:account:access
```

## Login and Usage

```bash
# Initial login (opens browser)
aws sso login --profile my-sso-profile

# Verify identity
aws sts get-caller-identity --profile my-sso-profile

# Use profile for commands
aws s3 ls --profile my-sso-profile

# Or export for session
export AWS_PROFILE=my-sso-profile
```

## Session Management

```bash
# Check session status
aws sts get-caller-identity --profile my-sso-profile

# Logout (invalidate cached credentials)
aws sso logout --profile my-sso-profile

# Re-login when session expires
aws sso login --profile my-sso-profile
```

## Multiple Accounts from Same SSO

```ini
# Production account
[profile prod]
sso_session = my-company
sso_account_id = 111111111111
sso_role_name = AdministratorAccess
region = us-east-1

# Development account
[profile dev]
sso_session = my-company
sso_account_id = 222222222222
sso_role_name = PowerUserAccess
region = us-east-1

# Shared SSO session
[sso-session my-company]
sso_start_url = https://my-company.awsapps.com/start
sso_region = us-east-1
```

## Token Caching

SSO tokens are cached in `~/.aws/sso/cache/`. These are automatically refreshed within their validity period (typically 8-12 hours).

## Troubleshooting

| Issue                | Solution                                                          |
| -------------------- | ----------------------------------------------------------------- |
| "Token has expired"  | Run `aws sso login --profile <profile>`                           |
| "No access"          | Verify sso_role_name matches your IAM Identity Center permissions |
| Browser doesn't open | Copy the URL from terminal and open manually                      |
| Wrong account        | Check sso_account_id in config                                    |
