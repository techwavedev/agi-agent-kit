#!/usr/bin/env python3
"""
Script: cluster_info.py
Purpose: Get comprehensive EKS cluster information

Usage:
    python cluster_info.py --cluster <name> --region <region> [--json]

Exit Codes: 0=success, 1=args, 2=not found, 3=aws error, 4=kubectl error
"""

import argparse
import json
import subprocess
import sys


def run_cmd(cmd: list, capture: bool = True) -> tuple[int, str]:
    """Run command and return exit code and output."""
    try:
        result = subprocess.run(cmd, capture_output=capture, text=True)
        return result.returncode, result.stdout + result.stderr
    except FileNotFoundError:
        return 127, f"Command not found: {cmd[0]}"


def get_cluster_info(cluster_name: str, region: str) -> dict:
    """Get EKS cluster details from AWS."""
    code, output = run_cmd([
        "aws", "eks", "describe-cluster",
        "--name", cluster_name,
        "--region", region,
        "--output", "json"
    ])
    
    if code != 0:
        return {"error": output, "code": code}
    
    try:
        return json.loads(output)
    except json.JSONDecodeError:
        return {"error": "Failed to parse AWS response", "raw": output}


def get_nodegroups(cluster_name: str, region: str) -> list:
    """List node groups for cluster."""
    code, output = run_cmd([
        "aws", "eks", "list-nodegroups",
        "--cluster-name", cluster_name,
        "--region", region,
        "--output", "json"
    ])
    
    if code != 0:
        return []
    
    try:
        data = json.loads(output)
        return data.get("nodegroups", [])
    except json.JSONDecodeError:
        return []


def get_nodegroup_details(cluster_name: str, nodegroup_name: str, region: str) -> dict:
    """Get node group details."""
    code, output = run_cmd([
        "aws", "eks", "describe-nodegroup",
        "--cluster-name", cluster_name,
        "--nodegroup-name", nodegroup_name,
        "--region", region,
        "--output", "json"
    ])
    
    if code != 0:
        return {"error": output}
    
    try:
        return json.loads(output)
    except json.JSONDecodeError:
        return {"error": "Failed to parse response"}


def get_kubectl_info() -> dict:
    """Get kubectl cluster info if configured."""
    info = {"connected": False}
    
    # Check current context
    code, output = run_cmd(["kubectl", "config", "current-context"])
    if code == 0:
        info["context"] = output.strip()
        info["connected"] = True
    
    # Get nodes
    code, output = run_cmd(["kubectl", "get", "nodes", "-o", "json"])
    if code == 0:
        try:
            nodes_data = json.loads(output)
            info["nodes"] = [
                {
                    "name": n["metadata"]["name"],
                    "status": next(
                        (c["status"] for c in n["status"]["conditions"] if c["type"] == "Ready"),
                        "Unknown"
                    ),
                    "instance_type": n["metadata"]["labels"].get("node.kubernetes.io/instance-type", "unknown"),
                    "zone": n["metadata"]["labels"].get("topology.kubernetes.io/zone", "unknown")
                }
                for n in nodes_data.get("items", [])
            ]
        except (json.JSONDecodeError, KeyError):
            pass
    
    # Get namespaces
    code, output = run_cmd(["kubectl", "get", "namespaces", "-o", "json"])
    if code == 0:
        try:
            ns_data = json.loads(output)
            info["namespaces"] = [n["metadata"]["name"] for n in ns_data.get("items", [])]
        except (json.JSONDecodeError, KeyError):
            pass
    
    return info


def main():
    parser = argparse.ArgumentParser(description="Get EKS cluster information")
    parser.add_argument("--cluster", "-c", required=True, help="Cluster name")
    parser.add_argument("--region", "-r", required=True, help="AWS region")
    parser.add_argument("--json", action="store_true", help="JSON output")
    
    args = parser.parse_args()
    
    result = {
        "cluster_name": args.cluster,
        "region": args.region,
        "status": "gathering"
    }
    
    # Get cluster info
    cluster = get_cluster_info(args.cluster, args.region)
    if "error" in cluster:
        result["status"] = "error"
        result["error"] = cluster["error"]
        print(json.dumps(result, indent=2) if args.json else f"Error: {cluster['error']}")
        sys.exit(3)
    
    result["cluster"] = {
        "arn": cluster["cluster"]["arn"],
        "status": cluster["cluster"]["status"],
        "version": cluster["cluster"]["version"],
        "endpoint": cluster["cluster"]["endpoint"],
        "platform_version": cluster["cluster"].get("platformVersion"),
        "created_at": str(cluster["cluster"].get("createdAt", ""))
    }
    
    # Get node groups
    nodegroups = get_nodegroups(args.cluster, args.region)
    result["nodegroups"] = []
    for ng in nodegroups:
        ng_details = get_nodegroup_details(args.cluster, ng, args.region)
        if "nodegroup" in ng_details:
            ng_info = ng_details["nodegroup"]
            result["nodegroups"].append({
                "name": ng,
                "status": ng_info.get("status"),
                "instance_types": ng_info.get("instanceTypes", []),
                "scaling": ng_info.get("scalingConfig", {}),
                "ami_type": ng_info.get("amiType")
            })
    
    # Get kubectl info
    result["kubectl"] = get_kubectl_info()
    result["status"] = "success"
    
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"Cluster: {args.cluster} ({args.region})")
        print(f"Status: {result['cluster']['status']}")
        print(f"Version: {result['cluster']['version']}")
        print(f"Endpoint: {result['cluster']['endpoint']}")
        print(f"\nNode Groups ({len(result['nodegroups'])}):")
        for ng in result["nodegroups"]:
            scaling = ng.get("scaling", {})
            print(f"  - {ng['name']}: {ng['status']} ({scaling.get('desiredSize', '?')} nodes)")
        
        if result["kubectl"]["connected"]:
            print(f"\nKubectl Context: {result['kubectl'].get('context', 'N/A')}")
            if "nodes" in result["kubectl"]:
                print(f"Nodes ({len(result['kubectl']['nodes'])}):")
                for node in result["kubectl"]["nodes"]:
                    print(f"  - {node['name']}: {node['status']} ({node['instance_type']})")
    
    sys.exit(0)


if __name__ == "__main__":
    main()
