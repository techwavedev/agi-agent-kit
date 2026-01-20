#!/usr/bin/env python3
"""
Script: consul_status.py
Purpose: Get comprehensive status of Consul cluster on Kubernetes

Usage:
    python consul_status.py --namespace consul [--context <context>]

Arguments:
    --namespace   Kubernetes namespace where Consul is installed (default: consul)
    --context     Kubernetes context to use (optional)
    --json        Output in JSON format

Exit Codes:
    0 - Success
    1 - Invalid arguments
    2 - kubectl/cluster not accessible
    3 - Consul not found
"""

import argparse
import json
import subprocess
import sys
from typing import Dict, Any, Optional


def run_kubectl(args: list, context: Optional[str] = None) -> tuple:
    """Run kubectl command and return (success, output)."""
    cmd = ["kubectl"]
    if context:
        cmd.extend(["--context", context])
    cmd.extend(args)
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
    except subprocess.TimeoutExpired:
        return False, "", "Command timed out"
    except Exception as e:
        return False, "", str(e)


def get_bootstrap_token(namespace: str, context: Optional[str] = None) -> Optional[str]:
    """Retrieve bootstrap ACL token from Kubernetes secret."""
    cmd = ["kubectl"]
    if context:
        cmd.extend(["--context", context])
    cmd.extend([
        "get", "secret", "consul-bootstrap-acl-token",
        "-n", namespace,
        "-o", "jsonpath={.data.token}"
    ])
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if result.returncode == 0 and result.stdout:
            import base64
            return base64.b64decode(result.stdout).decode('utf-8').strip()
    except Exception:
        pass
    return None


def run_consul_cmd(namespace: str, cmd: str, context: Optional[str] = None, token: Optional[str] = None) -> tuple:
    """Run consul command inside server pod with optional ACL token."""
    consul_cmd = cmd.split()
    if token:
        consul_cmd.extend(["-token", token])
    
    kubectl_args = [
        "exec", "-n", namespace, "consul-server-0", "--",
        "consul"
    ] + consul_cmd
    return run_kubectl(kubectl_args, context)


def get_pods_status(namespace: str, context: Optional[str] = None) -> Dict[str, Any]:
    """Get status of Consul pods."""
    success, output, _ = run_kubectl(
        ["get", "pods", "-n", namespace, "-l", "app=consul", 
         "-o", "json"],
        context
    )
    
    if not success:
        return {"error": "Failed to get pods"}
    
    try:
        pods_data = json.loads(output)
        pods = []
        for pod in pods_data.get("items", []):
            pod_info = {
                "name": pod["metadata"]["name"],
                "status": pod["status"]["phase"],
                "ready": all(c.get("ready", False) 
                           for c in pod["status"].get("containerStatuses", [])),
                "restarts": sum(c.get("restartCount", 0) 
                               for c in pod["status"].get("containerStatuses", [])),
                "node": pod["spec"].get("nodeName", "unknown")
            }
            pods.append(pod_info)
        return {"pods": pods, "total": len(pods)}
    except json.JSONDecodeError:
        return {"error": "Failed to parse pods JSON"}


def get_cluster_members(namespace: str, context: Optional[str] = None, token: Optional[str] = None) -> Dict[str, Any]:
    """Get Consul cluster members."""
    success, output, error = run_consul_cmd(namespace, "members", context, token)
    
    if not success:
        return {"error": f"Failed to get members: {error}"}
    
    members = []
    lines = output.strip().split("\n")
    for line in lines[1:]:  # Skip header
        parts = line.split()
        if len(parts) >= 4:
            members.append({
                "name": parts[0],
                "address": parts[1],
                "status": parts[2],
                "type": parts[3]
            })
    
    return {"members": members, "total": len(members)}


def get_raft_status(namespace: str, context: Optional[str] = None, token: Optional[str] = None) -> Dict[str, Any]:
    """Get Raft consensus status."""
    success, output, error = run_consul_cmd(
        namespace, "operator raft list-peers", context, token
    )
    
    if not success:
        return {"error": f"Failed to get raft status: {error}"}
    
    peers = []
    leader = None
    lines = output.strip().split("\n")
    for line in lines[1:]:  # Skip header
        parts = line.split()
        if len(parts) >= 4:
            peer = {
                "node": parts[0],
                "id": parts[1] if len(parts) > 1 else "",
                "address": parts[2] if len(parts) > 2 else "",
                "state": parts[3] if len(parts) > 3 else "",
                "voter": parts[4] if len(parts) > 4 else ""
            }
            peers.append(peer)
            if peer["state"] == "leader":
                leader = peer["node"]
    
    return {"peers": peers, "leader": leader, "total": len(peers)}


def get_helm_info(namespace: str, context: Optional[str] = None) -> Dict[str, Any]:
    """Get Helm release info."""
    cmd = ["helm", "list", "-n", namespace, "-o", "json"]
    if context:
        cmd.extend(["--kube-context", context])
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            releases = json.loads(result.stdout)
            for release in releases:
                if release.get("name") == "consul":
                    return {
                        "name": release["name"],
                        "version": release.get("chart", ""),
                        "app_version": release.get("app_version", ""),
                        "status": release.get("status", ""),
                        "updated": release.get("updated", "")
                    }
            return {"error": "Consul release not found"}
        return {"error": result.stderr}
    except Exception as e:
        return {"error": str(e)}


def main():
    parser = argparse.ArgumentParser(description="Get Consul cluster status")
    parser.add_argument("--namespace", "-n", default="consul",
                       help="Kubernetes namespace (default: consul)")
    parser.add_argument("--context", "-c", default=None,
                       help="Kubernetes context")
    parser.add_argument("--json", action="store_true",
                       help="Output in JSON format")
    args = parser.parse_args()
    
    # Retrieve bootstrap token for ACL-enabled clusters
    token = get_bootstrap_token(args.namespace, args.context)
    
    status = {
        "namespace": args.namespace,
        "acl_token_found": token is not None,
        "helm": get_helm_info(args.namespace, args.context),
        "pods": get_pods_status(args.namespace, args.context),
        "members": get_cluster_members(args.namespace, args.context, token),
        "raft": get_raft_status(args.namespace, args.context, token)
    }
    
    if args.json:
        print(json.dumps(status, indent=2))
    else:
        print(f"\n{'='*60}")
        print(f"CONSUL STATUS - Namespace: {args.namespace}")
        print(f"{'='*60}\n")
        
        # Helm info
        helm = status["helm"]
        if "error" not in helm:
            print(f"📦 Helm Release: {helm.get('name', 'N/A')}")
            print(f"   Chart: {helm.get('version', 'N/A')}")
            print(f"   App Version: {helm.get('app_version', 'N/A')}")
            print(f"   Status: {helm.get('status', 'N/A')}")
        else:
            print(f"❌ Helm: {helm['error']}")
        print()
        
        # Pods
        pods = status["pods"]
        if "error" not in pods:
            print(f"🔵 Pods ({pods['total']} total):")
            for pod in pods.get("pods", []):
                icon = "✅" if pod["ready"] else "❌"
                print(f"   {icon} {pod['name']}: {pod['status']} (restarts: {pod['restarts']})")
        else:
            print(f"❌ Pods: {pods['error']}")
        print()
        
        # Raft
        raft = status["raft"]
        if "error" not in raft:
            print(f"🗳️  Raft Consensus ({raft['total']} peers):")
            print(f"   Leader: {raft.get('leader', 'NONE')}")
            for peer in raft.get("peers", []):
                icon = "👑" if peer["state"] == "leader" else "  "
                print(f"   {icon} {peer['node']}: {peer['state']}")
        else:
            print(f"❌ Raft: {raft['error']}")
        print()
        
        # Summary
        healthy = (
            "error" not in pods and
            "error" not in raft and
            raft.get("leader") is not None
        )
        print(f"{'='*60}")
        if healthy:
            print("✅ Cluster Status: HEALTHY")
        else:
            print("❌ Cluster Status: UNHEALTHY")
        print(f"{'='*60}\n")
    
    sys.exit(0)


if __name__ == "__main__":
    main()
