#!/usr/bin/env python3
"""
Script: switch_profile.py
Purpose: Generate shell commands to switch AWS CLI profile for current session

Usage:
    python switch_profile.py --profile <name> [--validate] [--shell <bash|zsh|fish>]
    eval $(python switch_profile.py --profile myprofile)

Arguments:
    --profile       Profile name to switch to (required)
    --validate      Validate profile before switching
    --shell         Shell type for export syntax (default: bash/zsh)
    --json          Output JSON with commands instead of shell commands

Exit Codes:
    0 - Success
    1 - Invalid arguments / Profile not found
    2 - Validation failed
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


def profile_exists(profile_name):
    """Check if a profile exists in credentials or config."""
    aws_dir = get_aws_dir()
    
    # Check credentials file
    credentials_file = aws_dir / "credentials"
    if credentials_file.exists():
        creds = configparser.ConfigParser()
        creds.read(credentials_file)
        if profile_name in creds.sections():
            return True
    
    # Check config file
    config_file = aws_dir / "config"
    if config_file.exists():
        config = configparser.ConfigParser()
        config.read(config_file)
        config_section = f"profile {profile_name}" if profile_name != "default" else "default"
        if config_section in config.sections() or profile_name in config.sections():
            return True
    
    return False


def get_profile_region(profile_name):
    """Get the region configured for a profile."""
    aws_dir = get_aws_dir()
    config_file = aws_dir / "config"
    
    if config_file.exists():
        config = configparser.ConfigParser()
        config.read(config_file)
        config_section = f"profile {profile_name}" if profile_name != "default" else "default"
        if config_section in config.sections():
            return config[config_section].get('region')
    
    return None


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
            return True, identity
        else:
            return False, result.stderr.strip()
    except Exception as e:
        return False, str(e)


def generate_shell_commands(profile_name, region=None, shell='bash'):
    """Generate shell commands to set AWS profile."""
    commands = []
    
    if shell == 'fish':
        commands.append(f'set -gx AWS_PROFILE {profile_name}')
        if region:
            commands.append(f'set -gx AWS_DEFAULT_REGION {region}')
    else:  # bash/zsh
        commands.append(f'export AWS_PROFILE={profile_name}')
        if region:
            commands.append(f'export AWS_DEFAULT_REGION={region}')
    
    return commands


def main():
    parser = argparse.ArgumentParser(
        description="Switch AWS CLI profile for current session",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('--profile', required=True, help='Profile name to switch to')
    parser.add_argument('--validate', action='store_true', help='Validate profile first')
    parser.add_argument('--shell', default='bash', choices=['bash', 'zsh', 'fish'])
    parser.add_argument('--json', action='store_true', help='Output as JSON')

    args = parser.parse_args()

    # Check profile exists
    if not profile_exists(args.profile):
        if args.json:
            print(json.dumps({
                "status": "error",
                "message": f"Profile '{args.profile}' not found"
            }))
        else:
            print(f"# Error: Profile '{args.profile}' not found", file=sys.stderr)
        sys.exit(1)
    
    # Validate if requested
    if args.validate:
        valid, result = validate_profile(args.profile)
        if not valid:
            if args.json:
                print(json.dumps({
                    "status": "error",
                    "message": f"Profile validation failed: {result}"
                }))
            else:
                print(f"# Error: Profile validation failed: {result}", file=sys.stderr)
            sys.exit(2)
    
    # Get region for profile
    region = get_profile_region(args.profile)
    
    # Generate commands
    commands = generate_shell_commands(args.profile, region, args.shell)
    
    if args.json:
        output = {
            "status": "success",
            "profile": args.profile,
            "region": region,
            "shell": args.shell,
            "commands": commands,
            "usage": f"eval $(python switch_profile.py --profile {args.profile})"
        }
        if args.validate:
            output["validation"] = result
        print(json.dumps(output, indent=2))
    else:
        # Output shell commands directly (can be eval'd)
        for cmd in commands:
            print(cmd)
        # Add a comment showing what was done
        print(f"# Switched to AWS profile: {args.profile}" + (f" (region: {region})" if region else ""))
    
    sys.exit(0)


if __name__ == '__main__':
    main()
