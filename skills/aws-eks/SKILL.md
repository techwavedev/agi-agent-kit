---
name: aws-eks
description: Manage AWS EKS (Elastic Kubernetes Service) clusters via AWS EKS MCP Server. Use for creating, updating, or deleting EKS clusters, managing node groups, configuring kubectl access, deploying workloads, and troubleshooting Kubernetes issues. Integrates with Amazon EKS MCP Server for AI-assisted cluster management.
---

# AWS EKS Skill

> Part of the [AWS skill family](../aws/SKILL.md). For profile management, see [aws-cli](../aws-cli/SKILL.md).

Manage AWS EKS clusters via AWS MCP Server integration.

## MCP Server Setup

The Amazon EKS MCP Server provides AI-assisted Kubernetes cluster management.

### Quick Setup (Recommended)

Auto-configure your MCP client with region from AWS CLI:

```bash
python scripts/configure_mcp.py --allow-write
```

Options:

- `--client claude|cursor|vscode` — Specify client (auto-detects if not set)
- `--region eu-west-1` — Override region (prompts if not in AWS config)
- `--allow-sensitive` — Enable access to logs and secrets
- `--dry-run` — Preview config without writing

### Manual Setup

Add to your MCP client configuration (e.g., Claude Desktop, Cursor):

```json
{
  "mcpServers": {
    "eks": {
      "command": "uvx",
      "args": ["awslabs.eks-mcp-server@latest", "--allow-write"],
      "env": {
        "AWS_PROFILE": "default",
        "AWS_REGION": "eu-west-1"
      }
    }
  }
}
```

**Flags:**

- `--allow-write` — Enable create/update/delete operations
- `--allow-sensitive-data-access` — Allow access to logs and secrets

### Prerequisites

- AWS CLI configured with valid credentials
- kubectl installed
- Python 3.10+ with uvx (`pip install uvx`)

## MCP Tools Available

When the EKS MCP server is connected, these tools become available:

| Tool                 | Description                               |
| -------------------- | ----------------------------------------- |
| `list_clusters`      | List all EKS clusters in region           |
| `describe_cluster`   | Get cluster details and status            |
| `create_cluster`     | Create new EKS cluster                    |
| `delete_cluster`     | Delete an EKS cluster                     |
| `list_nodegroups`    | List node groups for cluster              |
| `describe_nodegroup` | Get node group details                    |
| `scale_nodegroup`    | Adjust node group scaling                 |
| `get_pod_logs`       | Retrieve pod logs                         |
| `apply_manifest`     | Apply Kubernetes manifest                 |
| `get_resources`      | List K8s resources (pods, services, etc.) |

## Workflows

### 1. Connect to Existing Cluster

```
1. Use `list_clusters` to find clusters
2. Use `describe_cluster` to get endpoint details
3. Update kubeconfig: aws eks update-kubeconfig --name <cluster> --region <region>
4. Use `get_resources` to explore cluster state
```

### 2. Deploy Application

```
1. Use `describe_cluster` to verify cluster is ACTIVE
2. Prepare Kubernetes manifests (deployment, service, etc.)
3. Use `apply_manifest` to deploy
4. Use `get_resources` to verify deployment status
5. Use `get_pod_logs` to check application logs
```

### 3. Troubleshoot Issues

```
1. Use `get_resources` to find problematic pods
2. Use `get_pod_logs` to check error messages
3. Use `describe_cluster` to verify cluster health
4. Consult references/troubleshooting.md for common fixes
```

### 4. Scale Workloads

```
1. Use `list_nodegroups` to see current node groups
2. Use `scale_nodegroup` to adjust capacity
3. Use `get_resources` to verify pods are scheduled
```

## Fallback: AWS CLI

When MCP server is not available, use AWS CLI directly:

```bash
# List clusters
aws eks list-clusters --region <region>

# Get cluster details
aws eks describe-cluster --name <cluster-name> --region <region>

# Update kubeconfig
aws eks update-kubeconfig --name <cluster-name> --region <region>

# Scale node group
aws eks update-nodegroup-config \
  --cluster-name <cluster-name> \
  --nodegroup-name <nodegroup-name> \
  --scaling-config minSize=<min>,maxSize=<max>,desiredSize=<desired>
```

## Scripts

| Script                     | Purpose                                     |
| -------------------------- | ------------------------------------------- |
| `scripts/configure_mcp.py` | Auto-configure MCP client with EKS server   |
| `scripts/cluster_info.py`  | Comprehensive cluster status (CLI fallback) |

## References

- [references/cluster_operations.md](references/cluster_operations.md) — Create, update, delete clusters
- [references/troubleshooting.md](references/troubleshooting.md) — Common issues and fixes
- [references/iam_roles.md](references/iam_roles.md) — IAM roles and service accounts
- [references/mcp_setup.md](references/mcp_setup.md) — Detailed MCP configuration
