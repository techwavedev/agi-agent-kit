#!/usr/bin/env python3
"""
Script: generate_nodepool.py
Purpose: Generate Karpenter NodePool YAML configuration

Usage:
    python generate_nodepool.py --name <name> [options]

Arguments:
    --name              NodePool name (required)
    --nodeclass         EC2NodeClass name (default: default)
    --instance-types    Comma-separated instance types (e.g., "m5.large,m5.xlarge")
    --instance-category Comma-separated categories (e.g., "c,m,r")
    --instance-gen      Minimum instance generation (default: 5)
    --capacity-type     Capacity type: spot, on-demand, both (default: both)
    --arch              Architecture: amd64, arm64, both (default: amd64)
    --cpu-limit         CPU limit for the pool (default: 1000)
    --memory-limit      Memory limit in Gi (default: 2000)
    --consolidation     Consolidation policy: WhenEmpty, WhenEmptyOrUnderutilized (default: WhenEmptyOrUnderutilized)
    --consolidate-after Time before consolidation (default: 1m)
    --expire-after      Node expiration time (default: 720h)
    --taints            Comma-separated taints (format: key=value:effect)
    --labels            Comma-separated labels (format: key=value)
    --output            Output file (default: stdout)

Exit Codes:
    0 - Success
    1 - Invalid arguments
"""

import argparse
import json
import sys
from typing import Any

import yaml


def parse_taints(taints_str: str) -> list[dict]:
    """Parse taint string into list of taint dicts."""
    if not taints_str:
        return []

    taints = []
    for taint in taints_str.split(","):
        taint = taint.strip()
        if ":" not in taint:
            continue

        key_value, effect = taint.rsplit(":", 1)
        if "=" in key_value:
            key, value = key_value.split("=", 1)
        else:
            key, value = key_value, ""

        taints.append({
            "key": key,
            "value": value,
            "effect": effect
        })

    return taints


def parse_labels(labels_str: str) -> dict:
    """Parse label string into dict."""
    if not labels_str:
        return {}

    labels = {}
    for label in labels_str.split(","):
        label = label.strip()
        if "=" in label:
            key, value = label.split("=", 1)
            labels[key] = value

    return labels


def generate_nodepool(args: argparse.Namespace) -> dict:
    """Generate NodePool configuration."""
    # Build requirements
    requirements = []

    # Architecture
    if args.arch == "both":
        requirements.append({
            "key": "kubernetes.io/arch",
            "operator": "In",
            "values": ["amd64", "arm64"]
        })
    else:
        requirements.append({
            "key": "kubernetes.io/arch",
            "operator": "In",
            "values": [args.arch]
        })

    # OS (always Linux for now)
    requirements.append({
        "key": "kubernetes.io/os",
        "operator": "In",
        "values": ["linux"]
    })

    # Capacity type
    if args.capacity_type == "both":
        requirements.append({
            "key": "karpenter.sh/capacity-type",
            "operator": "In",
            "values": ["spot", "on-demand"]
        })
    else:
        requirements.append({
            "key": "karpenter.sh/capacity-type",
            "operator": "In",
            "values": [args.capacity_type]
        })

    # Instance types or categories
    if args.instance_types:
        requirements.append({
            "key": "node.kubernetes.io/instance-type",
            "operator": "In",
            "values": [t.strip() for t in args.instance_types.split(",")]
        })
    elif args.instance_category:
        requirements.append({
            "key": "karpenter.k8s.aws/instance-category",
            "operator": "In",
            "values": [c.strip() for c in args.instance_category.split(",")]
        })
        requirements.append({
            "key": "karpenter.k8s.aws/instance-generation",
            "operator": "Gt",
            "values": [str(args.instance_gen)]
        })

    # Build spec.template
    template_spec: dict[str, Any] = {
        "nodeClassRef": {
            "group": "karpenter.k8s.aws",
            "kind": "EC2NodeClass",
            "name": args.nodeclass
        },
        "requirements": requirements
    }

    # Add expireAfter
    if args.expire_after:
        template_spec["expireAfter"] = args.expire_after

    # Add taints
    taints = parse_taints(args.taints)
    if taints:
        template_spec["taints"] = taints

    # Build template metadata
    template_metadata = {}
    labels = parse_labels(args.labels)
    if labels:
        template_metadata["labels"] = labels

    # Build limits
    limits = {}
    if args.cpu_limit:
        limits["cpu"] = args.cpu_limit
    if args.memory_limit:
        limits["memory"] = f"{args.memory_limit}Gi"

    # Build disruption
    disruption = {
        "consolidationPolicy": args.consolidation,
        "consolidateAfter": args.consolidate_after
    }

    # Assemble NodePool
    nodepool = {
        "apiVersion": "karpenter.sh/v1",
        "kind": "NodePool",
        "metadata": {
            "name": args.name
        },
        "spec": {
            "template": {
                "spec": template_spec
            },
            "limits": limits,
            "disruption": disruption
        }
    }

    # Add template metadata if present
    if template_metadata:
        nodepool["spec"]["template"]["metadata"] = template_metadata

    return nodepool


def main():
    parser = argparse.ArgumentParser(description="Generate Karpenter NodePool YAML")
    parser.add_argument("--name", required=True, help="NodePool name")
    parser.add_argument("--nodeclass", default="default", help="EC2NodeClass name")
    parser.add_argument("--instance-types", help="Comma-separated instance types")
    parser.add_argument("--instance-category", default="c,m,r", help="Instance categories")
    parser.add_argument("--instance-gen", type=int, default=5, help="Minimum instance generation")
    parser.add_argument("--capacity-type", choices=["spot", "on-demand", "both"], default="both")
    parser.add_argument("--arch", choices=["amd64", "arm64", "both"], default="amd64")
    parser.add_argument("--cpu-limit", type=int, default=1000, help="CPU limit")
    parser.add_argument("--memory-limit", type=int, default=2000, help="Memory limit in Gi")
    parser.add_argument("--consolidation", default="WhenEmptyOrUnderutilized",
                        choices=["WhenEmpty", "WhenEmptyOrUnderutilized"])
    parser.add_argument("--consolidate-after", default="1m", help="Consolidation delay")
    parser.add_argument("--expire-after", default="720h", help="Node expiration")
    parser.add_argument("--taints", help="Comma-separated taints: key=value:effect")
    parser.add_argument("--labels", help="Comma-separated labels: key=value")
    parser.add_argument("--output", help="Output file (default: stdout)")
    parser.add_argument("--format", choices=["yaml", "json"], default="yaml", help="Output format")

    args = parser.parse_args()

    try:
        nodepool = generate_nodepool(args)

        if args.format == "json":
            output = json.dumps(nodepool, indent=2)
        else:
            output = yaml.dump(nodepool, default_flow_style=False, sort_keys=False)

        if args.output:
            with open(args.output, "w") as f:
                f.write(output)
            print(f"NodePool configuration written to: {args.output}")
        else:
            print(output)

        sys.exit(0)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
