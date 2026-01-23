#!/usr/bin/env python3
"""
Script: generate_agent_values.py
Purpose: Generate Helm values file for GitLab agent installation

Usage:
    python generate_agent_values.py \
        --gitlab-url https://gitlab.example.com \
        --agent-name eks-nonprod-agent \
        --output agent-values.yaml

    python generate_agent_values.py \
        --gitlab-url https://gitlab.example.com \
        --agent-name eks-prod-agent \
        --production \
        --ca-cert ./gitlab-ca.pem \
        --output prod-agent-values.yaml

Arguments:
    --gitlab-url      GitLab instance URL (required)
    --agent-name      Name of the agent (required)
    --output, -o      Output file path (default: agent-values.yaml)
    --production      Enable production settings (HA, resource limits)
    --ca-cert         Path to CA certificate for self-signed GitLab
    --replicas        Number of replicas (default: 1, 2 for production)
    --version         Agent version tag (e.g., v17.6.0)
    --token           Agent token (will prompt if not provided)

Exit Codes:
    0 - Success
    1 - Invalid arguments
    2 - File error
"""

import argparse
import os
import sys
from pathlib import Path


def generate_values(
    gitlab_url: str,
    agent_name: str,
    production: bool = False,
    ca_cert: str = None,
    replicas: int = None,
    version: str = None,
    token: str = None
) -> str:
    """Generate Helm values YAML content"""
    
    # Ensure URL has proper format
    if not gitlab_url.startswith("http"):
        gitlab_url = f"https://{gitlab_url}"
    
    # Build KAS address
    kas_address = f"wss://{gitlab_url.replace('https://', '').replace('http://', '')}/-/kubernetes-agent/"
    
    # Determine replica count
    if replicas is None:
        replicas = 2 if production else 1
    
    lines = [
        f"# GitLab Agent Helm Values",
        f"# Agent: {agent_name}",
        f"# GitLab: {gitlab_url}",
        f"# Generated for: {'production' if production else 'non-production'}",
        f"",
    ]
    
    # Replica count
    lines.append(f"replicaCount: {replicas}")
    lines.append("")
    
    # Image configuration
    if version:
        lines.extend([
            "image:",
            "  repository: registry.gitlab.com/gitlab-org/cluster-integration/gitlab-agent/agentk",
            f"  tag: \"{version}\"",
            "  pullPolicy: IfNotPresent",
            "",
        ])
    
    # Config section
    lines.append("config:")
    if token:
        lines.append(f"  token: \"{token}\"")
    else:
        lines.append("  token: \"\"  # Set via --set config.token=<token>")
    lines.append(f"  kasAddress: \"{kas_address}\"")
    
    # CA certificate reference
    if ca_cert:
        lines.append("  # CA certificate for self-signed GitLab")
        lines.append("  # Install with: --set-file config.kasCaCert=./gitlab-ca.pem")
        lines.append("  kasCaCert: \"\"  # Populated by --set-file")
    
    lines.extend([
        "  observability:",
        "    logging:",
        f"      level: {'warn' if production else 'info'}",
        "",
    ])
    
    # RBAC configuration
    lines.extend([
        "rbac:",
        "  create: true",
    ])
    if production:
        lines.append("  # Use pre-created role with minimal permissions")
        lines.append("  # useExistingRole: gitlab-agent-role")
    lines.append("")
    
    # Service account
    lines.extend([
        "serviceAccount:",
        "  create: true",
        f"  name: \"gitlab-agent-{agent_name}\"",
        "  annotations: {}",
        "",
    ])
    
    # Resources
    if production:
        lines.extend([
            "resources:",
            "  requests:",
            "    cpu: 100m",
            "    memory: 128Mi",
            "  limits:",
            "    cpu: 500m",
            "    memory: 256Mi",
            "",
        ])
    else:
        lines.extend([
            "resources:",
            "  requests:",
            "    cpu: 50m",
            "    memory: 64Mi",
            "  limits:",
            "    cpu: 200m",
            "    memory: 128Mi",
            "",
        ])
    
    # Pod Disruption Budget (production only)
    if production:
        lines.extend([
            "podDisruptionBudget:",
            "  enabled: true",
            "  minAvailable: 1",
            "",
        ])
    
    # Affinity (production only)
    if production and replicas > 1:
        lines.extend([
            "affinity:",
            "  podAntiAffinity:",
            "    preferredDuringSchedulingIgnoredDuringExecution:",
            "      - weight: 100",
            "        podAffinityTerm:",
            "          labelSelector:",
            "            matchLabels:",
            "              app.kubernetes.io/name: gitlab-agent",
            "          topologyKey: topology.kubernetes.io/zone",
            "",
        ])
    
    # Node selector (example)
    lines.extend([
        "nodeSelector: {}",
        "  # kubernetes.io/os: linux",
        "",
    ])
    
    # Tolerations (example)
    lines.extend([
        "tolerations: []",
        "  # - key: \"dedicated\"",
        "  #   operator: \"Equal\"",
        "  #   value: \"gitlab\"",
        "  #   effect: \"NoSchedule\"",
        "",
    ])
    
    # Additional env vars (example)
    lines.extend([
        "extraEnv: []",
        "  # - name: HTTPS_PROXY",
        "  #   value: \"http://proxy.example.com:8080\"",
        "",
    ])
    
    return "\n".join(lines)


def generate_install_command(
    agent_name: str,
    values_file: str,
    ca_cert: str = None,
    namespace: str = "gitlab-agent"
) -> str:
    """Generate the Helm install command"""
    
    lines = [
        "# Installation command:",
        "#",
        "# helm repo add gitlab https://charts.gitlab.io",
        "# helm repo update",
        "#",
    ]
    
    cmd = f"# helm upgrade --install gitlab-agent gitlab/gitlab-agent \\\n"
    cmd += f"#   --namespace {namespace} \\\n"
    cmd += f"#   --create-namespace \\\n"
    cmd += f"#   -f {values_file} \\\n"
    cmd += f"#   --set config.token=\"<YOUR_AGENT_TOKEN>\""
    
    if ca_cert:
        cmd += f" \\\n#   --set-file config.kasCaCert={ca_cert}"
    
    lines.append(cmd)
    lines.append("")
    
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Generate Helm values file for GitLab agent installation",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--gitlab-url",
        required=True,
        help="GitLab instance URL"
    )
    parser.add_argument(
        "--agent-name",
        required=True,
        help="Name of the agent"
    )
    parser.add_argument(
        "--output", "-o",
        default="agent-values.yaml",
        help="Output file path (default: agent-values.yaml)"
    )
    parser.add_argument(
        "--production",
        action="store_true",
        help="Enable production settings (HA, resource limits)"
    )
    parser.add_argument(
        "--ca-cert",
        help="Path to CA certificate for self-signed GitLab"
    )
    parser.add_argument(
        "--replicas",
        type=int,
        help="Number of replicas"
    )
    parser.add_argument(
        "--version",
        help="Agent version tag (e.g., v17.6.0)"
    )
    parser.add_argument(
        "--token",
        help="Agent token (will be included in values file)"
    )
    
    args = parser.parse_args()
    
    # Validate CA cert file if provided
    if args.ca_cert and not Path(args.ca_cert).exists():
        print(f"Warning: CA certificate file not found: {args.ca_cert}")
        print("The path will be included in the output, but verify it exists before installation.")
    
    # Generate values
    values_content = generate_values(
        gitlab_url=args.gitlab_url,
        agent_name=args.agent_name,
        production=args.production,
        ca_cert=args.ca_cert,
        replicas=args.replicas,
        version=args.version,
        token=args.token
    )
    
    # Generate install command
    install_cmd = generate_install_command(
        agent_name=args.agent_name,
        values_file=args.output,
        ca_cert=args.ca_cert
    )
    
    # Combine content
    full_content = install_cmd + values_content
    
    # Write to file
    try:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, "w") as f:
            f.write(full_content)
        
        print(f"✅ Generated values file: {output_path}")
        print("")
        print("Next steps:")
        print(f"  1. Review and customize: {output_path}")
        print(f"  2. Register agent in GitLab (UI or API)")
        print(f"  3. Create agent token and save it")
        if args.ca_cert:
            print(f"  4. Ensure CA cert exists: {args.ca_cert}")
        print(f"  5. Run Helm install command (shown at top of values file)")
        
        sys.exit(0)
        
    except IOError as e:
        print(f"Error writing file: {e}")
        sys.exit(2)


if __name__ == "__main__":
    main()
