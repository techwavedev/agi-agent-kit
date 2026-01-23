#!/usr/bin/env python3
"""
Script: karpenter_status.py
Purpose: Get comprehensive status of Karpenter deployment and resources in an EKS cluster

Usage:
    python karpenter_status.py --cluster <cluster-name> [--region <region>] [--namespace karpenter]

Arguments:
    --cluster    EKS cluster name (required)
    --region     AWS region (default: eu-west-1)
    --namespace  Karpenter namespace (default: karpenter)
    --output     Output format: text, json, yaml (default: text)

Exit Codes:
    0 - Success
    1 - Invalid arguments
    2 - kubectl not available or cluster not accessible
    3 - Karpenter not installed
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime


def run_kubectl(args: list, namespace: str = None) -> tuple[bool, str]:
    """Run kubectl command and return success status and output."""
    cmd = ["kubectl"]
    if namespace:
        cmd.extend(["-n", namespace])
    cmd.extend(args)

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return result.returncode == 0, result.stdout.strip() if result.returncode == 0 else result.stderr.strip()
    except subprocess.TimeoutExpired:
        return False, "Command timed out"
    except FileNotFoundError:
        return False, "kubectl not found"


def get_karpenter_status(namespace: str) -> dict:
    """Get Karpenter controller status."""
    success, output = run_kubectl(
        ["get", "pods", "-l", "app.kubernetes.io/name=karpenter", "-o", "json"],
        namespace=namespace
    )

    if not success:
        return {"status": "not_found", "error": output}

    try:
        pods = json.loads(output)
        pod_list = pods.get("items", [])

        if not pod_list:
            return {"status": "not_installed", "pods": []}

        status = {
            "status": "running",
            "pods": [],
            "total": len(pod_list),
            "ready": 0
        }

        for pod in pod_list:
            name = pod["metadata"]["name"]
            phase = pod["status"].get("phase", "Unknown")
            container_statuses = pod["status"].get("containerStatuses", [])

            ready = all(cs.get("ready", False) for cs in container_statuses)
            restarts = sum(cs.get("restartCount", 0) for cs in container_statuses)

            if ready and phase == "Running":
                status["ready"] += 1

            status["pods"].append({
                "name": name,
                "phase": phase,
                "ready": ready,
                "restarts": restarts
            })

        if status["ready"] < status["total"]:
            status["status"] = "degraded"
        if status["ready"] == 0:
            status["status"] = "unhealthy"

        return status

    except json.JSONDecodeError:
        return {"status": "error", "error": "Failed to parse pod output"}


def get_nodepools() -> dict:
    """Get all NodePools and their status."""
    success, output = run_kubectl(["get", "nodepools", "-o", "json"])

    if not success:
        return {"count": 0, "error": output, "pools": []}

    try:
        data = json.loads(output)
        pools = []

        for item in data.get("items", []):
            name = item["metadata"]["name"]
            spec = item.get("spec", {})
            status = item.get("status", {})

            limits = spec.get("limits", {})
            resources = status.get("resources", {})

            # Get conditions
            conditions = {c["type"]: c["status"] for c in status.get("conditions", [])}

            pools.append({
                "name": name,
                "limits": limits,
                "current_resources": resources,
                "conditions": conditions,
                "disruption_policy": spec.get("disruption", {}).get("consolidationPolicy", "Unknown")
            })

        return {"count": len(pools), "pools": pools}

    except json.JSONDecodeError:
        return {"count": 0, "error": "Failed to parse output", "pools": []}


def get_ec2nodeclasses() -> dict:
    """Get all EC2NodeClasses and their status."""
    success, output = run_kubectl(["get", "ec2nodeclasses", "-o", "json"])

    if not success:
        return {"count": 0, "error": output, "classes": []}

    try:
        data = json.loads(output)
        classes = []

        for item in data.get("items", []):
            name = item["metadata"]["name"]
            spec = item.get("spec", {})
            status = item.get("status", {})

            classes.append({
                "name": name,
                "role": spec.get("role", "N/A"),
                "ami_family": spec.get("amiFamily", "Default"),
                "instance_profile": spec.get("instanceProfile", "N/A"),
                "subnets": len(status.get("subnets", [])),
                "security_groups": len(status.get("securityGroups", [])),
                "amis": len(status.get("amis", []))
            })

        return {"count": len(classes), "classes": classes}

    except json.JSONDecodeError:
        return {"count": 0, "error": "Failed to parse output", "classes": []}


def get_nodeclaims() -> dict:
    """Get all NodeClaims and their status."""
    success, output = run_kubectl(["get", "nodeclaims", "-o", "json"])

    if not success:
        return {"count": 0, "error": output, "claims": []}

    try:
        data = json.loads(output)
        claims = []

        for item in data.get("items", []):
            name = item["metadata"]["name"]
            spec = item.get("spec", {})
            status = item.get("status", {})

            conditions = {c["type"]: c["status"] for c in status.get("conditions", [])}

            claims.append({
                "name": name,
                "nodepool": item["metadata"].get("labels", {}).get("karpenter.sh/nodepool", "Unknown"),
                "instance_type": status.get("instanceType", "Pending"),
                "capacity_type": status.get("capacity", "Unknown"),
                "zone": status.get("zone", "Unknown"),
                "node_name": status.get("nodeName", "Pending"),
                "conditions": conditions
            })

        return {"count": len(claims), "claims": claims}

    except json.JSONDecodeError:
        return {"count": 0, "error": "Failed to parse output", "claims": []}


def get_karpenter_nodes() -> dict:
    """Get all nodes managed by Karpenter."""
    success, output = run_kubectl(["get", "nodes", "-l", "karpenter.sh/nodepool", "-o", "json"])

    if not success:
        return {"count": 0, "error": output, "nodes": []}

    try:
        data = json.loads(output)
        nodes = []

        for item in data.get("items", []):
            name = item["metadata"]["name"]
            labels = item["metadata"].get("labels", {})
            status = item.get("status", {})

            # Get node conditions
            conditions = {c["type"]: c["status"] for c in status.get("conditions", [])}
            ready = conditions.get("Ready", "Unknown")

            # Get capacity
            capacity = status.get("capacity", {})
            allocatable = status.get("allocatable", {})

            nodes.append({
                "name": name,
                "nodepool": labels.get("karpenter.sh/nodepool", "Unknown"),
                "instance_type": labels.get("node.kubernetes.io/instance-type", "Unknown"),
                "capacity_type": labels.get("karpenter.sh/capacity-type", "Unknown"),
                "zone": labels.get("topology.kubernetes.io/zone", "Unknown"),
                "ready": ready,
                "cpu_capacity": capacity.get("cpu", "0"),
                "memory_capacity": capacity.get("memory", "0"),
                "pods_capacity": capacity.get("pods", "0")
            })

        return {"count": len(nodes), "nodes": nodes}

    except json.JSONDecodeError:
        return {"count": 0, "error": "Failed to parse output", "nodes": []}


def format_text_output(status: dict) -> str:
    """Format status as human-readable text."""
    lines = []
    lines.append("=" * 60)
    lines.append(f"KARPENTER STATUS REPORT - {status['timestamp']}")
    lines.append(f"Cluster: {status['cluster']}")
    lines.append("=" * 60)

    # Controller Status
    controller = status["controller"]
    lines.append(f"\n📦 CONTROLLER STATUS: {controller['status'].upper()}")
    if controller.get("pods"):
        for pod in controller["pods"]:
            status_icon = "✅" if pod["ready"] else "❌"
            lines.append(f"   {status_icon} {pod['name']} - {pod['phase']} (restarts: {pod['restarts']})")

    # NodePools
    nodepools = status["nodepools"]
    lines.append(f"\n🎯 NODEPOOLS ({nodepools['count']})")
    if nodepools.get("pools"):
        for pool in nodepools["pools"]:
            lines.append(f"\n   Pool: {pool['name']}")
            lines.append(f"   ├─ Disruption: {pool['disruption_policy']}")
            if pool.get("limits"):
                lines.append(f"   ├─ Limits: {pool['limits']}")
            if pool.get("current_resources"):
                lines.append(f"   └─ Current: {pool['current_resources']}")

    # EC2NodeClasses
    classes = status["ec2nodeclasses"]
    lines.append(f"\n🔧 EC2NODECLASSES ({classes['count']})")
    if classes.get("classes"):
        for nc in classes["classes"]:
            lines.append(f"\n   Class: {nc['name']}")
            lines.append(f"   ├─ Role: {nc['role']}")
            lines.append(f"   ├─ AMI Family: {nc['ami_family']}")
            lines.append(f"   └─ Subnets: {nc['subnets']}, SGs: {nc['security_groups']}, AMIs: {nc['amis']}")

    # NodeClaims
    claims = status["nodeclaims"]
    lines.append(f"\n📋 NODECLAIMS ({claims['count']})")
    if claims.get("claims"):
        for claim in claims["claims"]:
            lines.append(f"\n   Claim: {claim['name']}")
            lines.append(f"   ├─ NodePool: {claim['nodepool']}")
            lines.append(f"   ├─ Instance: {claim['instance_type']} ({claim['capacity_type']})")
            lines.append(f"   ├─ Zone: {claim['zone']}")
            lines.append(f"   └─ Node: {claim['node_name']}")

    # Nodes
    nodes = status["nodes"]
    lines.append(f"\n🖥️  KARPENTER NODES ({nodes['count']})")
    if nodes.get("nodes"):
        for node in nodes["nodes"]:
            ready_icon = "✅" if node["ready"] == "True" else "❌"
            lines.append(f"\n   {ready_icon} {node['name']}")
            lines.append(f"   ├─ Type: {node['instance_type']} ({node['capacity_type']})")
            lines.append(f"   ├─ Zone: {node['zone']}")
            lines.append(f"   └─ Capacity: {node['cpu_capacity']} CPU, {node['memory_capacity']} Memory")

    lines.append("\n" + "=" * 60)
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Get Karpenter status in an EKS cluster")
    parser.add_argument("--cluster", required=True, help="EKS cluster name")
    parser.add_argument("--region", default="eu-west-1", help="AWS region")
    parser.add_argument("--namespace", default="karpenter", help="Karpenter namespace")
    parser.add_argument("--output", choices=["text", "json", "yaml"], default="text", help="Output format")
    args = parser.parse_args()

    # Update kubeconfig for the cluster
    update_cmd = ["aws", "eks", "update-kubeconfig", "--name", args.cluster, "--region", args.region]
    try:
        subprocess.run(update_cmd, capture_output=True, check=True, timeout=30)
    except subprocess.CalledProcessError as e:
        print(json.dumps({"status": "error", "message": f"Failed to update kubeconfig: {e.stderr}"}))
        sys.exit(2)
    except FileNotFoundError:
        print(json.dumps({"status": "error", "message": "AWS CLI not found"}))
        sys.exit(2)

    # Collect all status information
    status = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "cluster": args.cluster,
        "region": args.region,
        "controller": get_karpenter_status(args.namespace),
        "nodepools": get_nodepools(),
        "ec2nodeclasses": get_ec2nodeclasses(),
        "nodeclaims": get_nodeclaims(),
        "nodes": get_karpenter_nodes()
    }

    # Output based on format
    if args.output == "json":
        print(json.dumps(status, indent=2))
    elif args.output == "yaml":
        try:
            import yaml
            print(yaml.dump(status, default_flow_style=False))
        except ImportError:
            print(json.dumps(status, indent=2))
    else:
        print(format_text_output(status))

    # Exit with appropriate code
    if status["controller"]["status"] == "not_installed":
        sys.exit(3)
    elif status["controller"]["status"] in ["unhealthy", "error"]:
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
