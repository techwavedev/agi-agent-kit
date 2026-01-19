#!/usr/bin/env python3
"""
Script: list_profiles.py
Purpose: List all AWS CLI profiles and optionally validate their credentials

Usage:
    python list_profiles.py [--validate] [--profile <name>] [--json]

Arguments:
    --validate      Test credentials for each profile (slower, requires network)
    --profile       Only check a specific profile
    --json          Output in JSON format (default: table format)

Exit Codes:
    0 - Success
    1 - Invalid arguments
    2 - File access error
    3 - No profiles found
"""

import argparse
import configparser
import json
import subprocess
import sys
from pathlib import Path


def get_aws_dir():
    """Get the AWS config directory path."""
    return Path.home() / ".aws"


def read_profiles():
    """Read all profiles from credentials and config files."""
    aws_dir = get_aws_dir()
    credentials_file = aws_dir / "credentials"
    config_file = aws_dir / "config"
    
    profiles = {}
    
    # Read credentials file
    if credentials_file.exists():
        creds = configparser.ConfigParser()
        creds.read(credentials_file)
        for section in creds.sections():
            profiles[section] = {
                "name": section,
                "type": "standard",
                "has_credentials": True,
                "access_key_id": creds[section].get('aws_access_key_id', '')[:8] + '...' if creds[section].get('aws_access_key_id') else None
            }
    
    # Read config file (may override or add profiles)
    if config_file.exists():
        config = configparser.ConfigParser()
        config.read(config_file)
        for section in config.sections():
            # Config file uses "profile <name>" format except for default
            profile_name = section.replace("profile ", "") if section.startswith("profile ") else section
            
            if profile_name not in profiles:
                profiles[profile_name] = {
                    "name": profile_name,
                    "type": "unknown",
                    "has_credentials": False
                }
            
            # Determine profile type from config
            if config[section].get('role_arn'):
                profiles[profile_name]["type"] = "assume_role"
                profiles[profile_name]["role_arn"] = config[section].get('role_arn')
                profiles[profile_name]["source_profile"] = config[section].get('source_profile')
            elif config[section].get('sso_start_url'):
                profiles[profile_name]["type"] = "sso"
                profiles[profile_name]["sso_start_url"] = config[section].get('sso_start_url')
                profiles[profile_name]["sso_account_id"] = config[section].get('sso_account_id')
            
            # Add region and output if present
            profiles[profile_name]["region"] = config[section].get('region')
            profiles[profile_name]["output"] = config[section].get('output')
    
    return profiles


def validate_profile(profile_name):
    """Validate a profile by attempting to get caller identity."""
    try:
        result = subprocess.run(
            ['aws', 'sts', 'get-caller-identity', '--profile', profile_name],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            identity = json.loads(result.stdout)
            return {
                "valid": True,
                "account": identity.get("Account"),
                "arn": identity.get("Arn"),
                "user_id": identity.get("UserId")
            }
        else:
            return {
                "valid": False,
                "error": result.stderr.strip()
            }
    except subprocess.TimeoutExpired:
        return {"valid": False, "error": "Timeout"}
    except FileNotFoundError:
        return {"valid": False, "error": "AWS CLI not installed"}
    except Exception as e:
        return {"valid": False, "error": str(e)}


def format_table(profiles, validated=False):
    """Format profiles as a readable table."""
    if not profiles:
        return "No AWS profiles found."
    
    lines = []
    lines.append("")
    
    if validated:
        header = f"{'Profile':<20} {'Type':<12} {'Region':<15} {'Status':<10} {'Account':<15}"
        lines.append(header)
        lines.append("-" * len(header))
        
        for name, info in sorted(profiles.items()):
            status = "✓ Valid" if info.get("validation", {}).get("valid") else "✗ Invalid"
            account = info.get("validation", {}).get("account", "-")
            lines.append(f"{name:<20} {info.get('type', '-'):<12} {info.get('region', '-') or '-':<15} {status:<10} {account:<15}")
    else:
        header = f"{'Profile':<20} {'Type':<12} {'Region':<15} {'Credentials':<12}"
        lines.append(header)
        lines.append("-" * len(header))
        
        for name, info in sorted(profiles.items()):
            has_creds = "Yes" if info.get("has_credentials") else "No"
            lines.append(f"{name:<20} {info.get('type', '-'):<12} {info.get('region', '-') or '-':<15} {has_creds:<12}")
    
    lines.append("")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="List AWS CLI profiles",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('--validate', action='store_true', help='Validate credentials')
    parser.add_argument('--profile', help='Check specific profile only')
    parser.add_argument('--json', action='store_true', help='Output as JSON')

    args = parser.parse_args()

    try:
        profiles = read_profiles()
        
        if not profiles:
            if args.json:
                print(json.dumps({"status": "error", "message": "No profiles found"}))
            else:
                print("No AWS profiles found in ~/.aws/")
            sys.exit(3)
        
        # Filter to specific profile if requested
        if args.profile:
            if args.profile not in profiles:
                if args.json:
                    print(json.dumps({"status": "error", "message": f"Profile '{args.profile}' not found"}))
                else:
                    print(f"Profile '{args.profile}' not found")
                sys.exit(1)
            profiles = {args.profile: profiles[args.profile]}
        
        # Validate if requested
        if args.validate:
            for name in profiles:
                profiles[name]["validation"] = validate_profile(name)
        
        # Output
        if args.json:
            print(json.dumps({
                "status": "success",
                "profiles": profiles,
                "count": len(profiles)
            }, indent=2))
        else:
            print(format_table(profiles, validated=args.validate))
        
        sys.exit(0)

    except PermissionError as e:
        print(json.dumps({
            "status": "error",
            "type": "permission_error",
            "message": str(e)
        }) if args.json else f"Permission error: {e}", file=sys.stderr)
        sys.exit(2)
    except Exception as e:
        print(json.dumps({
            "status": "error",
            "type": type(e).__name__,
            "message": str(e)
        }) if args.json else f"Error: {e}", file=sys.stderr)
        sys.exit(3)


if __name__ == '__main__':
    main()
