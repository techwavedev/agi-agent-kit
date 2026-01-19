#!/usr/bin/env python3
"""
Script: generate_ec2nodeclass.py
Purpose: Generate Karpenter EC2NodeClass YAML configuration

Usage:
    python generate_ec2nodeclass.py --name <name> --cluster <cluster-name> [options]

Arguments:
    --name              EC2NodeClass name (required)
    --cluster           EKS cluster name (required, used for discovery tags)
    --role              IAM role name (default: KarpenterNodeRole-<cluster>)
    --ami-family        AMI family: AL2, AL2023, Bottlerocket, Ubuntu, Windows2019, Windows2022
    --ami-selector      AMI selector type: alias, tag, id (default: alias)
    --volume-size       Root volume size in Gi (default: 100)
    --volume-type       Volume type: gp2, gp3, io1, io2 (default: gp3)
    --encrypted         Encrypt volumes (default: true)
    --imdsv2            Require IMDSv2 (default: true)
    --user-data         Path to user data script file
    --tags              Comma-separated tags: key=value
    --output            Output file (default: stdout)

Exit Codes:
    0 - Success
    1 - Invalid arguments
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import yaml


def generate_ec2nodeclass(args: argparse.Namespace) -> dict:
    """Generate EC2NodeClass configuration."""
    # Determine role name
    role = args.role or f"KarpenterNodeRole-{args.cluster}"

    # Build AMI selector
    ami_selector_terms = []
    if args.ami_selector == "alias":
        ami_family_aliases = {
            "AL2": "al2@latest",
            "AL2023": "al2023@latest",
            "Bottlerocket": "bottlerocket@latest"
        }
        alias = ami_family_aliases.get(args.ami_family, "al2023@latest")
        ami_selector_terms.append({"alias": alias})
    elif args.ami_selector == "tag":
        ami_selector_terms.append({
            "tags": {
                "karpenter.sh/discovery": args.cluster
            }
        })

    # Build subnet and security group selectors
    subnet_selector_terms = [{
        "tags": {
            "karpenter.sh/discovery": args.cluster
        }
    }]

    security_group_selector_terms = [{
        "tags": {
            "karpenter.sh/discovery": args.cluster
        }
    }]

    # Build block device mappings
    device_name = "/dev/xvda"
    if args.ami_family in ["Windows2019", "Windows2022"]:
        device_name = "/dev/sda1"

    block_device_mappings = [{
        "deviceName": device_name,
        "ebs": {
            "volumeSize": f"{args.volume_size}Gi",
            "volumeType": args.volume_type,
            "encrypted": args.encrypted,
            "deleteOnTermination": True
        }
    }]

    # Add IOPS and throughput for gp3
    if args.volume_type == "gp3":
        block_device_mappings[0]["ebs"]["iops"] = 3000
        block_device_mappings[0]["ebs"]["throughput"] = 125

    # Build metadata options
    metadata_options = {
        "httpEndpoint": "enabled",
        "httpProtocolIPv6": "disabled",
        "httpPutResponseHopLimit": 1,
        "httpTokens": "required" if args.imdsv2 else "optional"
    }

    # Build tags
    tags = {
        "Environment": "production",
        "ManagedBy": "karpenter",
        f"kubernetes.io/cluster/{args.cluster}": "owned"
    }

    if args.tags:
        for tag in args.tags.split(","):
            tag = tag.strip()
            if "=" in tag:
                key, value = tag.split("=", 1)
                tags[key] = value

    # Assemble EC2NodeClass
    ec2nodeclass: dict[str, Any] = {
        "apiVersion": "karpenter.k8s.aws/v1",
        "kind": "EC2NodeClass",
        "metadata": {
            "name": args.name
        },
        "spec": {
            "role": role,
            "amiSelectorTerms": ami_selector_terms,
            "subnetSelectorTerms": subnet_selector_terms,
            "securityGroupSelectorTerms": security_group_selector_terms,
            "blockDeviceMappings": block_device_mappings,
            "metadataOptions": metadata_options,
            "tags": tags
        }
    }

    # Add AMI family if not using alias
    if args.ami_selector != "alias" and args.ami_family:
        ec2nodeclass["spec"]["amiFamily"] = args.ami_family

    # Add user data if specified
    if args.user_data:
        user_data_path = Path(args.user_data)
        if user_data_path.exists():
            ec2nodeclass["spec"]["userData"] = user_data_path.read_text()

    return ec2nodeclass


def main():
    parser = argparse.ArgumentParser(description="Generate Karpenter EC2NodeClass YAML")
    parser.add_argument("--name", required=True, help="EC2NodeClass name")
    parser.add_argument("--cluster", required=True, help="EKS cluster name")
    parser.add_argument("--role", help="IAM role name")
    parser.add_argument("--ami-family", default="AL2023",
                        choices=["AL2", "AL2023", "Bottlerocket", "Ubuntu", "Windows2019", "Windows2022"])
    parser.add_argument("--ami-selector", default="alias", choices=["alias", "tag", "id"])
    parser.add_argument("--volume-size", type=int, default=100, help="Volume size in Gi")
    parser.add_argument("--volume-type", default="gp3", choices=["gp2", "gp3", "io1", "io2"])
    parser.add_argument("--encrypted", type=bool, default=True, help="Encrypt volumes")
    parser.add_argument("--imdsv2", type=bool, default=True, help="Require IMDSv2")
    parser.add_argument("--user-data", help="Path to user data script")
    parser.add_argument("--tags", help="Comma-separated tags: key=value")
    parser.add_argument("--output", help="Output file (default: stdout)")
    parser.add_argument("--format", choices=["yaml", "json"], default="yaml", help="Output format")

    args = parser.parse_args()

    try:
        ec2nodeclass = generate_ec2nodeclass(args)

        if args.format == "json":
            output = json.dumps(ec2nodeclass, indent=2)
        else:
            output = yaml.dump(ec2nodeclass, default_flow_style=False, sort_keys=False)

        if args.output:
            with open(args.output, "w") as f:
                f.write(output)
            print(f"EC2NodeClass configuration written to: {args.output}")
        else:
            print(output)

        sys.exit(0)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
