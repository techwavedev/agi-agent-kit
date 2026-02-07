#!/usr/bin/env python3
"""
Script: gitlab_agent_status.py
Purpose: Check GitLab agent health and generate status report

Usage:
    python gitlab_agent_status.py --namespace gitlab-agent \
        --gitlab-url https://gitlab.example.com \
        --project-id 123 \
        --output reports/gitlab/

Arguments:
    --namespace, -n   Kubernetes namespace (default: gitlab-agent)
    --gitlab-url      GitLab instance URL (or GITLAB_HOST env var)
    --project-id      GitLab project ID (or PROJECT_ID env var)
    --agent-id        Specific agent ID (optional, checks all if omitted)
    --output, -o      Output directory for reports (default: current)
    --format, -f      Output format: json, markdown, or both (default: both)

Exit Codes:
    0 - Success, all agents healthy
    1 - Invalid arguments
    2 - Connection error
    3 - Unhealthy agents detected
    4 - Processing error

Environment Variables:
    GITLAB_HOST   - GitLab hostname
    GITLAB_TOKEN  - GitLab personal/project access token
    PROJECT_ID    - Default project ID
    KUBECONFIG    - Kubernetes config path
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def run_kubectl(args: list) -> tuple:
    """Run kubectl command and return (success, output)"""
    try:
        result = subprocess.run(
            ["kubectl"] + args,
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.returncode == 0, result.stdout.strip()
    except subprocess.TimeoutExpired:
        return False, "Command timed out"
    except FileNotFoundError:
        return False, "kubectl not found"


def get_agent_pods(namespace: str) -> dict:
    """Get agent pod status from Kubernetes"""
    success, output = run_kubectl([
        "get", "pods", "-n", namespace,
        "-l", "app.kubernetes.io/name=gitlab-agent",
        "-o", "json"
    ])
    
    if not success:
        return {"error": output, "pods": []}
    
    try:
        data = json.loads(output)
        pods = []
        for item in data.get("items", []):
            pod = {
                "name": item["metadata"]["name"],
                "status": item["status"]["phase"],
                "ready": all(
                    c.get("ready", False) 
                    for c in item["status"].get("containerStatuses", [])
                ),
                "restarts": sum(
                    c.get("restartCount", 0) 
                    for c in item["status"].get("containerStatuses", [])
                ),
                "node": item["spec"].get("nodeName", "unknown"),
                "image": item["spec"]["containers"][0]["image"] if item["spec"].get("containers") else "unknown"
            }
            pods.append(pod)
        return {"error": None, "pods": pods}
    except json.JSONDecodeError as e:
        return {"error": f"JSON parse error: {e}", "pods": []}


def get_agent_logs(namespace: str, lines: int = 50) -> str:
    """Get recent agent logs"""
    success, output = run_kubectl([
        "logs", "-n", namespace,
        "-l", "app.kubernetes.io/name=gitlab-agent",
        "--tail", str(lines)
    ])
    return output if success else f"Error getting logs: {output}"


def get_helm_status(namespace: str) -> dict:
    """Get Helm release status"""
    try:
        result = subprocess.run(
            ["helm", "list", "-n", namespace, "-o", "json"],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode != 0:
            return {"error": result.stderr, "releases": []}
        
        releases = json.loads(result.stdout)
        return {"error": None, "releases": releases}
    except Exception as e:
        return {"error": str(e), "releases": []}


def get_gitlab_agents(gitlab_url: str, token: str, project_id: str) -> dict:
    """Get agents from GitLab API"""
    import urllib.request
    import ssl
    
    url = f"{gitlab_url}/api/v4/projects/{project_id}/cluster_agents"
    
    # Create request with token
    req = urllib.request.Request(url)
    req.add_header("PRIVATE-TOKEN", token)
    
    # Allow self-signed certs (common in on-prem)
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=30) as response:
            data = json.loads(response.read().decode())
            return {"error": None, "agents": data}
    except urllib.error.HTTPError as e:
        return {"error": f"HTTP {e.code}: {e.reason}", "agents": []}
    except urllib.error.URLError as e:
        return {"error": f"Connection error: {e.reason}", "agents": []}
    except Exception as e:
        return {"error": str(e), "agents": []}


def get_agent_tokens(gitlab_url: str, token: str, project_id: str, agent_id: int) -> dict:
    """Get tokens for an agent from GitLab API"""
    import urllib.request
    import ssl
    
    url = f"{gitlab_url}/api/v4/projects/{project_id}/cluster_agents/{agent_id}/tokens"
    
    req = urllib.request.Request(url)
    req.add_header("PRIVATE-TOKEN", token)
    
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=30) as response:
            data = json.loads(response.read().decode())
            return {"error": None, "tokens": data}
    except Exception as e:
        return {"error": str(e), "tokens": []}


def generate_report(data: dict, output_format: str, output_dir: str):
    """Generate status report in requested format(s)"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    if output_format in ("json", "both"):
        json_file = output_path / f"gitlab_agent_status_{timestamp}.json"
        with open(json_file, "w") as f:
            json.dump(data, f, indent=2, default=str)
        print(f"JSON report: {json_file}")
    
    if output_format in ("markdown", "both"):
        md_file = output_path / f"gitlab_agent_status_{timestamp}.md"
        md_content = generate_markdown(data)
        with open(md_file, "w") as f:
            f.write(md_content)
        print(f"Markdown report: {md_file}")


def generate_markdown(data: dict) -> str:
    """Generate markdown report from data"""
    lines = [
        f"# GitLab Agent Status Report",
        f"",
        f"**Generated:** {data['timestamp']}",
        f"**Environment:** {data['environment']}",
        f"",
    ]
    
    # Summary
    healthy = data.get("healthy", False)
    status_emoji = "✅" if healthy else "❌"
    lines.append(f"## Summary: {status_emoji} {'Healthy' if healthy else 'Issues Detected'}")
    lines.append("")
    
    # Kubernetes Status
    lines.append("## Kubernetes Status")
    lines.append("")
    k8s = data.get("kubernetes", {})
    pods = k8s.get("pods", {}).get("pods", [])
    
    if pods:
        lines.append("| Pod | Status | Ready | Restarts | Node |")
        lines.append("|-----|--------|-------|----------|------|")
        for pod in pods:
            ready = "✅" if pod["ready"] else "❌"
            lines.append(f"| {pod['name']} | {pod['status']} | {ready} | {pod['restarts']} | {pod['node']} |")
    else:
        lines.append("No agent pods found.")
    lines.append("")
    
    # Helm Status
    helm = k8s.get("helm", {}).get("releases", [])
    if helm:
        lines.append("### Helm Release")
        lines.append("")
        for release in helm:
            lines.append(f"- **Name:** {release.get('name')}")
            lines.append(f"- **Chart:** {release.get('chart')}")
            lines.append(f"- **Status:** {release.get('status')}")
            lines.append(f"- **Revision:** {release.get('revision')}")
    lines.append("")
    
    # GitLab API Status
    lines.append("## GitLab API Status")
    lines.append("")
    gitlab = data.get("gitlab", {})
    agents = gitlab.get("agents", {}).get("agents", [])
    
    if agents:
        lines.append("### Registered Agents")
        lines.append("")
        lines.append("| ID | Name | Created |")
        lines.append("|----|------|---------|")
        for agent in agents:
            lines.append(f"| {agent['id']} | {agent['name']} | {agent.get('created_at', 'N/A')} |")
        lines.append("")
        
        # Tokens
        tokens = gitlab.get("tokens", [])
        if tokens:
            lines.append("### Agent Tokens")
            lines.append("")
            lines.append("| Agent | Token ID | Name | Status | Created |")
            lines.append("|-------|----------|------|--------|---------|")
            for token_info in tokens:
                for token in token_info.get("tokens", []):
                    lines.append(f"| {token_info['agent_id']} | {token['id']} | {token['name']} | {token['status']} | {token.get('created_at', 'N/A')} |")
    else:
        api_error = gitlab.get("agents", {}).get("error")
        if api_error:
            lines.append(f"**Error:** {api_error}")
        else:
            lines.append("No agents found.")
    lines.append("")
    
    # Issues
    issues = data.get("issues", [])
    if issues:
        lines.append("## Issues Detected")
        lines.append("")
        for issue in issues:
            lines.append(f"- ⚠️ {issue}")
    lines.append("")
    
    # Recent Logs
    lines.append("## Recent Logs")
    lines.append("")
    lines.append("```")
    logs = data.get("kubernetes", {}).get("logs", "No logs available")
    lines.append(logs[-3000:] if len(logs) > 3000 else logs)  # Limit log size
    lines.append("```")
    
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Check GitLab agent health and generate status report",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        "--namespace", "-n",
        default="gitlab-agent",
        help="Kubernetes namespace (default: gitlab-agent)"
    )
    parser.add_argument(
        "--gitlab-url",
        default=os.environ.get("GITLAB_HOST", ""),
        help="GitLab instance URL"
    )
    parser.add_argument(
        "--project-id",
        default=os.environ.get("PROJECT_ID", ""),
        help="GitLab project ID"
    )
    parser.add_argument(
        "--agent-id",
        help="Specific agent ID (optional)"
    )
    parser.add_argument(
        "--output", "-o",
        default=".",
        help="Output directory (default: current)"
    )
    parser.add_argument(
        "--format", "-f",
        choices=["json", "markdown", "both"],
        default="both",
        help="Output format (default: both)"
    )
    
    args = parser.parse_args()
    
    # Get GitLab token from environment
    gitlab_token = os.environ.get("GITLAB_TOKEN", "")
    
    # Normalize GitLab URL
    gitlab_url = args.gitlab_url
    if gitlab_url and not gitlab_url.startswith("http"):
        gitlab_url = f"https://{gitlab_url}"
    
    # Collect data
    data = {
        "timestamp": datetime.now().isoformat(),
        "environment": {
            "namespace": args.namespace,
            "gitlab_url": gitlab_url,
            "project_id": args.project_id
        },
        "kubernetes": {},
        "gitlab": {},
        "issues": [],
        "healthy": True
    }
    
    print(f"Checking GitLab agent status in namespace: {args.namespace}")
    
    # Kubernetes checks
    print("  - Checking pods...")
    data["kubernetes"]["pods"] = get_agent_pods(args.namespace)
    
    print("  - Checking Helm release...")
    data["kubernetes"]["helm"] = get_helm_status(args.namespace)
    
    print("  - Getting recent logs...")
    data["kubernetes"]["logs"] = get_agent_logs(args.namespace)
    
    # GitLab API checks (if configured)
    if gitlab_url and gitlab_token and args.project_id:
        print(f"  - Checking GitLab API ({gitlab_url})...")
        data["gitlab"]["agents"] = get_gitlab_agents(gitlab_url, gitlab_token, args.project_id)
        
        # Get tokens for each agent
        agents = data["gitlab"]["agents"].get("agents", [])
        data["gitlab"]["tokens"] = []
        for agent in agents:
            token_data = get_agent_tokens(gitlab_url, gitlab_token, args.project_id, agent["id"])
            token_data["agent_id"] = agent["id"]
            data["gitlab"]["tokens"].append(token_data)
    else:
        print("  - Skipping GitLab API (missing URL, token, or project ID)")
    
    # Analyze for issues
    pods = data["kubernetes"]["pods"].get("pods", [])
    if not pods:
        data["issues"].append("No agent pods found in namespace")
        data["healthy"] = False
    else:
        for pod in pods:
            if pod["status"] != "Running":
                data["issues"].append(f"Pod {pod['name']} is {pod['status']}")
                data["healthy"] = False
            if not pod["ready"]:
                data["issues"].append(f"Pod {pod['name']} is not ready")
                data["healthy"] = False
            if pod["restarts"] > 5:
                data["issues"].append(f"Pod {pod['name']} has {pod['restarts']} restarts")
    
    # Check for errors in logs
    logs = data["kubernetes"].get("logs", "")
    if '"level":"error"' in logs or '"level":"warn"' in logs:
        data["issues"].append("Errors or warnings found in agent logs")
    
    # Generate report
    generate_report(data, args.format, args.output)
    
    # Print summary
    print("")
    if data["healthy"]:
        print("✅ All agents healthy")
        sys.exit(0)
    else:
        print("❌ Issues detected:")
        for issue in data["issues"]:
            print(f"  - {issue}")
        sys.exit(3)


if __name__ == "__main__":
    main()
