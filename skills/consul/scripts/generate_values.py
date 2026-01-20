#!/usr/bin/env python3
"""
Script: generate_values.py
Purpose: Generate Consul Helm values file based on configuration options

Usage:
    python generate_values.py --datacenter dc1 --replicas 3 [options]

Arguments:
    --datacenter    Datacenter name (required)
    --replicas      Number of server replicas (3 or 5)
    --connect-inject Enable Connect sidecar injection
    --acls          Enable ACL system
    --tls           Enable TLS
    --mesh-gateway  Enable mesh gateway
    --ingress-gateway Enable ingress gateway
    --output        Output file path (default: stdout)

Exit Codes:
    0 - Success
    1 - Invalid arguments
"""

import argparse
import sys
import yaml


def generate_values(args) -> dict:
    """Generate Consul Helm values based on arguments."""
    
    values = {
        "global": {
            "name": "consul",
            "datacenter": args.datacenter,
        },
        "server": {
            "replicas": args.replicas,
            "bootstrapExpect": args.replicas,
            "resources": {
                "requests": {
                    "memory": "200Mi",
                    "cpu": "100m"
                },
                "limits": {
                    "memory": "500Mi",
                    "cpu": "500m"
                }
            },
            "storageClass": "gp3",
            "storage": "10Gi"
        },
        "connectInject": {
            "enabled": args.connect_inject,
            "default": False
        },
        "controller": {
            "enabled": args.connect_inject
        }
    }
    
    # Server anti-affinity for HA
    if args.replicas >= 3:
        values["server"]["affinity"] = """
podAntiAffinity:
  requiredDuringSchedulingIgnoredDuringExecution:
    - labelSelector:
        matchLabels:
          app: consul
          component: server
      topologyKey: kubernetes.io/hostname"""
    
    # ACLs
    if args.acls:
        values["global"]["acls"] = {
            "manageSystemACLs": True
        }
    
    # TLS
    if args.tls:
        values["global"]["tls"] = {
            "enabled": True,
            "enableAutoEncrypt": True
        }
        values["global"]["gossipEncryption"] = {
            "autoGenerate": True
        }
    
    # Mesh Gateway
    if args.mesh_gateway:
        values["meshGateway"] = {
            "enabled": True,
            "replicas": 2
        }
    
    # Ingress Gateway
    if args.ingress_gateway:
        values["ingressGateway"] = {
            "enabled": True,
            "defaults": {
                "replicas": 2
            }
        }
    
    # Scale resources for larger clusters
    if args.replicas >= 5:
        values["server"]["resources"]["requests"]["memory"] = "500Mi"
        values["server"]["resources"]["requests"]["cpu"] = "200m"
        values["server"]["resources"]["limits"]["memory"] = "1Gi"
        values["server"]["resources"]["limits"]["cpu"] = "1000m"
        values["server"]["storage"] = "20Gi"
    
    return values


def main():
    parser = argparse.ArgumentParser(
        description="Generate Consul Helm values file"
    )
    parser.add_argument("--datacenter", "-d", required=True,
                       help="Datacenter name")
    parser.add_argument("--replicas", "-r", type=int, default=3,
                       choices=[1, 3, 5],
                       help="Number of server replicas (default: 3)")
    parser.add_argument("--connect-inject", action="store_true",
                       help="Enable Connect sidecar injection")
    parser.add_argument("--acls", action="store_true",
                       help="Enable ACL system")
    parser.add_argument("--tls", action="store_true",
                       help="Enable TLS")
    parser.add_argument("--mesh-gateway", action="store_true",
                       help="Enable mesh gateway")
    parser.add_argument("--ingress-gateway", action="store_true",
                       help="Enable ingress gateway")
    parser.add_argument("--output", "-o", default=None,
                       help="Output file path (default: stdout)")
    
    args = parser.parse_args()
    
    # Validate
    if args.replicas == 1:
        print("⚠️  Warning: Single server mode is not suitable for production",
              file=sys.stderr)
    
    values = generate_values(args)
    
    # Add header comment
    output = f"""# Consul Helm Values
# Generated for datacenter: {args.datacenter}
# Replicas: {args.replicas}
# Features: {'ACLs ' if args.acls else ''}{'TLS ' if args.tls else ''}{'Connect ' if args.connect_inject else ''}
#
# Install with:
#   helm install consul hashicorp/consul -n consul -f <this-file>
#
"""
    output += yaml.dump(values, default_flow_style=False, sort_keys=False)
    
    if args.output:
        with open(args.output, 'w') as f:
            f.write(output)
        print(f"✅ Values written to {args.output}")
    else:
        print(output)
    
    sys.exit(0)


if __name__ == "__main__":
    main()
