#!/usr/bin/env python3
"""
Script: create_profile.py
Purpose: Create or update an AWS CLI profile in ~/.aws/credentials and ~/.aws/config

Usage:
    python create_profile.py --profile <name> --access-key <key> --secret-key <secret> [--region <region>] [--output <format>]
    python create_profile.py --profile <name> --sso  # Interactive SSO setup
    python create_profile.py --profile <name> --assume-role <role-arn> --source-profile <source>

Arguments:
    --profile       Profile name to create/update (required)
    --access-key    AWS Access Key ID
    --secret-key    AWS Secret Access Key
    --region        AWS region (default: us-east-1)
    --output        Output format: json, yaml, text, table (default: json)
    --sso           Configure SSO profile (interactive)
    --assume-role   ARN of role to assume
    --source-profile Source profile for role assumption
    --mfa-serial    MFA device ARN (optional)

Exit Codes:
    0 - Success
    1 - Invalid arguments
    2 - File access error
    3 - Configuration error
"""

import argparse
import configparser
import json
import os
import sys
from pathlib import Path


def get_aws_dir():
    """Get the AWS config directory path."""
    return Path.home() / ".aws"


def ensure_aws_dir():
    """Ensure ~/.aws directory exists."""
    aws_dir = get_aws_dir()
    aws_dir.mkdir(mode=0o700, exist_ok=True)
    return aws_dir


def read_config(filepath):
    """Read an AWS config file."""
    config = configparser.ConfigParser()
    if filepath.exists():
        config.read(filepath)
    return config


def write_config(config, filepath):
    """Write an AWS config file with secure permissions."""
    with open(filepath, 'w') as f:
        config.write(f)
    os.chmod(filepath, 0o600)


def create_standard_profile(args):
    """Create a standard IAM credentials profile."""
    aws_dir = ensure_aws_dir()
    credentials_file = aws_dir / "credentials"
    config_file = aws_dir / "config"

    # Update credentials file
    credentials = read_config(credentials_file)
    if args.profile not in credentials:
        credentials[args.profile] = {}
    
    credentials[args.profile]['aws_access_key_id'] = args.access_key
    credentials[args.profile]['aws_secret_access_key'] = args.secret_key
    
    write_config(credentials, credentials_file)

    # Update config file
    config = read_config(config_file)
    profile_section = f"profile {args.profile}" if args.profile != "default" else "default"
    
    if profile_section not in config:
        config[profile_section] = {}
    
    config[profile_section]['region'] = args.region
    config[profile_section]['output'] = args.output
    
    write_config(config, config_file)

    return {
        "status": "success",
        "profile": args.profile,
        "type": "standard",
        "region": args.region,
        "credentials_file": str(credentials_file),
        "config_file": str(config_file)
    }


def create_assume_role_profile(args):
    """Create an assume-role profile."""
    aws_dir = ensure_aws_dir()
    config_file = aws_dir / "config"

    config = read_config(config_file)
    profile_section = f"profile {args.profile}" if args.profile != "default" else "default"
    
    if profile_section not in config:
        config[profile_section] = {}
    
    config[profile_section]['role_arn'] = args.assume_role
    config[profile_section]['source_profile'] = args.source_profile
    config[profile_section]['region'] = args.region
    config[profile_section]['output'] = args.output
    
    if args.mfa_serial:
        config[profile_section]['mfa_serial'] = args.mfa_serial
    
    write_config(config, config_file)

    return {
        "status": "success",
        "profile": args.profile,
        "type": "assume_role",
        "role_arn": args.assume_role,
        "source_profile": args.source_profile,
        "region": args.region,
        "mfa_required": bool(args.mfa_serial)
    }


def create_sso_profile(args):
    """Create an SSO profile (outputs instructions for manual completion)."""
    aws_dir = ensure_aws_dir()
    config_file = aws_dir / "config"

    # We can't fully automate SSO as it requires browser interaction
    # But we can prepare the config structure
    return {
        "status": "pending_sso_login",
        "profile": args.profile,
        "type": "sso",
        "message": "SSO profile requires interactive setup",
        "next_steps": [
            f"Run: aws configure sso --profile {args.profile}",
            "Follow the browser prompts to authenticate",
            f"Then run: aws sso login --profile {args.profile}"
        ]
    }


def main():
    parser = argparse.ArgumentParser(
        description="Create or update an AWS CLI profile",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument('--profile', required=True, help='Profile name')
    parser.add_argument('--access-key', help='AWS Access Key ID')
    parser.add_argument('--secret-key', help='AWS Secret Access Key')
    parser.add_argument('--region', default='us-east-1', help='AWS region')
    parser.add_argument('--output', default='json', choices=['json', 'yaml', 'text', 'table'])
    parser.add_argument('--sso', action='store_true', help='Configure SSO profile')
    parser.add_argument('--assume-role', help='ARN of role to assume')
    parser.add_argument('--source-profile', help='Source profile for role assumption')
    parser.add_argument('--mfa-serial', help='MFA device ARN')

    args = parser.parse_args()

    try:
        # Determine profile type and create accordingly
        if args.sso:
            result = create_sso_profile(args)
        elif args.assume_role:
            if not args.source_profile:
                print(json.dumps({
                    "status": "error",
                    "message": "--source-profile required when using --assume-role"
                }), file=sys.stderr)
                sys.exit(1)
            result = create_assume_role_profile(args)
        elif args.access_key and args.secret_key:
            result = create_standard_profile(args)
        else:
            print(json.dumps({
                "status": "error",
                "message": "Must provide --access-key and --secret-key, --sso, or --assume-role"
            }), file=sys.stderr)
            sys.exit(1)

        print(json.dumps(result, indent=2))
        sys.exit(0)

    except PermissionError as e:
        print(json.dumps({
            "status": "error",
            "type": "permission_error",
            "message": str(e)
        }), file=sys.stderr)
        sys.exit(2)
    except Exception as e:
        print(json.dumps({
            "status": "error",
            "type": type(e).__name__,
            "message": str(e)
        }), file=sys.stderr)
        sys.exit(3)


if __name__ == '__main__':
    main()
