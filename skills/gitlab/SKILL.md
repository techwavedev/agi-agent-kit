---
name: gitlab
description: GitLab specialist for Kubernetes agent management on EKS clusters. Use for GitLab agent (agentk) installation, configuration, upgrades, GitOps with Flux, CI/CD pipeline integration, project management via API, token management, and troubleshooting connectivity issues. Covers agent registration, Helm deployments, KAS configuration (self-managed on-prem), impersonation, and multi-cluster setups. Requires kubectl/helm access to target EKS cluster and GitLab API token.
---

# GitLab Skill

Comprehensive skill for managing GitLab Kubernetes agents and project integrations on Amazon EKS. This skill covers the full lifecycle of GitLab agent deployment, GitOps workflows with Flux, CI/CD pipeline configurations, and project management via the GitLab API.

> **Last Updated:** 2026-02-07 from [docs.gitlab.com](https://docs.gitlab.com/user/clusters/agent/)

---

## Quick Start

```bash
# Set cluster context
export CLUSTER_NAME=eks-nonprod
aws eks update-kubeconfig --name $CLUSTER_NAME --region eu-west-1

# Verify GitLab agent is running
kubectl get pods -n gitlab-agent
helm list -n gitlab-agent

# Check agent logs
kubectl logs -f -l=app.kubernetes.io/name=gitlab-agent -n gitlab-agent

# List agents via API
curl --header "PRIVATE-TOKEN: ${GITLAB_TOKEN}" \
  "https://${GITLAB_HOST}/api/v4/projects/${PROJECT_ID}/cluster_agents"
```

---

## Core Concepts

### Architecture Overview

```
┌────────────────────────────────────────────────────────────┐
│  GitLab Self-Managed (On-Prem)                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ GitLab Rails + KAS (Kubernetes Agent Server)         │  │
│  │  - Handles agent connections via WebSocket/gRPC      │  │
│  │  - Manages agent tokens and configuration            │  │
│  │  - Proxies kubectl requests from CI/CD               │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────┘
                           │
                    WebSocket (wss://)
                           │
┌────────────────────────────────────────────────────────────┐
│  EKS Cluster                                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ gitlab-agent namespace                               │  │
│  │  ┌─────────────────────────────────────────────┐     │  │
│  │  │ agentk (GitLab Agent for Kubernetes)        │     │  │
│  │  │  - Connects outbound to KAS                 │     │  │
│  │  │  - Watches for configuration changes        │     │  │
│  │  │  - Enables GitOps via Flux                  │     │  │
│  │  │  - Proxies K8s API for CI/CD jobs           │     │  │
│  │  └─────────────────────────────────────────────┘     │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ flux-system namespace (GitOps)                       │  │
│  │  - Flux controllers for continuous deployment        │  │
│  │  - Watches Git repositories for manifest changes     │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Application namespaces                               │  │
│  │  - Deployed workloads managed by GitOps/CI-CD        │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────┘
```

### Key Components

| Component       | Description                                                           |
| --------------- | --------------------------------------------------------------------- |
| **agentk**      | Agent running in cluster, connects outbound to KAS via WebSocket      |
| **KAS**         | Kubernetes Agent Server, runs on GitLab instance, manages connections |
| **Flux**        | GitLab-recommended GitOps solution for continuous deployment          |
| **Agent Token** | Authentication token for agent-KAS communication (max 2 active)       |
| **Config File** | `.gitlab/agents/<agent-name>/config.yaml` in the config project       |

### Deployment Workflows

GitLab supports two primary Kubernetes deployment workflows:

| Workflow            | Description                                               | Recommendation     |
| ------------------- | --------------------------------------------------------- | ------------------ |
| **GitOps (Flux)**   | Flux watches Git repos, auto-deploys on changes           | ✅ **Recommended** |
| **CI/CD (kubectl)** | Pipeline jobs run kubectl against cluster via agent proxy | ⚠️ For migrations  |

---

## Common Workflows

### 1. Install Agent on EKS

**Step 1: Register Agent in GitLab**

```bash
# Via API
curl --request POST \
  --header "PRIVATE-TOKEN: ${GITLAB_TOKEN}" \
  --header "Content-Type: application/json" \
  --url "https://${GITLAB_HOST}/api/v4/projects/${PROJECT_ID}/cluster_agents" \
  --data '{"name":"eks-nonprod-agent"}'

# Save the agent ID from response for token creation
```

Or use the GitLab UI: Project → Operate → Kubernetes clusters → Connect a cluster.

**Step 2: Create Agent Token**

```bash
curl --request POST \
  --header "PRIVATE-TOKEN: ${GITLAB_TOKEN}" \
  --header "Content-Type: application/json" \
  --url "https://${GITLAB_HOST}/api/v4/projects/${PROJECT_ID}/cluster_agents/${AGENT_ID}/tokens" \
  --data '{"name":"initial-token","description":"EKS nonprod agent token"}'

# IMPORTANT: Save the token from response - it cannot be retrieved again!
```

**Step 3: Create Agent Configuration**

In your GitLab project, create `.gitlab/agents/eks-nonprod-agent/config.yaml`:

```yaml
# Agent configuration for CI/CD access
ci_access:
  projects:
    - id: path/to/your/project
  groups:
    - id: path/to/your/group

# Enable GitOps with Flux (recommended)
flux:
  resource_inclusions:
    - api_groups:
        - "*"
      resources:
        - "*"
```

**Step 4: Install with Helm**

```bash
# Add GitLab Helm repo
helm repo add gitlab https://charts.gitlab.io
helm repo update

# Install agent (for self-managed GitLab with custom CA)
helm upgrade --install gitlab-agent gitlab/gitlab-agent \
  --namespace gitlab-agent \
  --create-namespace \
  --set config.token="${AGENT_TOKEN}" \
  --set config.kasAddress="wss://${GITLAB_HOST}/-/kubernetes-agent/" \
  --set-file config.kasCaCert=./gitlab-ca.pem \
  --set image.tag=v17.6.0

# Verify installation
kubectl get pods -n gitlab-agent
kubectl logs -f -l=app.kubernetes.io/name=gitlab-agent -n gitlab-agent
```

### 2. Upgrade Agent Version

```bash
# Check current version
helm list -n gitlab-agent
kubectl get deployment -n gitlab-agent -o jsonpath='{.items[*].spec.template.spec.containers[*].image}'

# Get current values (don't use --reuse-values)
helm get values gitlab-agent -n gitlab-agent > agent-values.yaml

# Review GitLab release notes for breaking changes
# https://gitlab.com/gitlab-org/cluster-integration/gitlab-agent/-/releases

# Upgrade to specific version
helm repo update
helm upgrade gitlab-agent gitlab/gitlab-agent \
  --namespace gitlab-agent \
  -f agent-values.yaml \
  --set image.tag=v17.8.0

# Watch rollout
kubectl rollout status deployment/gitlab-agent -n gitlab-agent
```

**Version Compatibility**: Agent version should match GitLab major.minor version. Previous and next minor versions are also supported.

### 3. Configure CI/CD Pipeline Access

Edit your `.gitlab-ci.yml`:

```yaml
deploy:
  image: bitnami/kubectl:latest
  script:
    # Use the agent's kubecontext
    - kubectl config get-contexts
    - kubectl config use-context path/to/project:eks-nonprod-agent
    - kubectl get pods -n production
    - kubectl apply -f manifests/
  environment:
    name: production
    kubernetes:
      agent: path/to/project:eks-nonprod-agent
```

### 4. Set Up GitOps with Flux

GitLab recommends Flux for GitOps deployments.

**Step 1: Bootstrap Flux**

```bash
# Install Flux CLI
brew install fluxcd/tap/flux

# Bootstrap Flux with GitLab
flux bootstrap gitlab \
  --hostname=${GITLAB_HOST} \
  --token-auth \
  --owner=path/to/group \
  --repository=flux-config \
  --branch=main \
  --path=clusters/eks-nonprod
```

**Step 2: Configure Flux Source**

```yaml
# clusters/eks-nonprod/app-source.yaml
apiVersion: source.toolkit.fluxcd.io/v1
kind: GitRepository
metadata:
  name: my-app
  namespace: flux-system
spec:
  interval: 1m
  url: https://gitlab.example.com/path/to/my-app.git
  ref:
    branch: main
  secretRef:
    name: gitlab-token
```

**Step 3: Configure Kustomization**

```yaml
# clusters/eks-nonprod/app-kustomization.yaml
apiVersion: kustomize.toolkit.fluxcd.io/v1
kind: Kustomization
metadata:
  name: my-app
  namespace: flux-system
spec:
  interval: 5m
  path: ./manifests
  prune: true
  sourceRef:
    kind: GitRepository
    name: my-app
  targetNamespace: production
```

### 5. Token Rotation

Agents can have maximum 2 active tokens. Rotate tokens without downtime:

```bash
# 1. Create new token (while old token is still active)
curl --request POST \
  --header "PRIVATE-TOKEN: ${GITLAB_TOKEN}" \
  --header "Content-Type: application/json" \
  --url "https://${GITLAB_HOST}/api/v4/projects/${PROJECT_ID}/cluster_agents/${AGENT_ID}/tokens" \
  --data '{"name":"rotation-token","description":"Token rotation $(date +%Y%m%d)"}'

# 2. Update agent with new token
helm upgrade gitlab-agent gitlab/gitlab-agent \
  --namespace gitlab-agent \
  -f agent-values.yaml \
  --set config.token="${NEW_TOKEN}"

# 3. Verify agent reconnects
kubectl logs -f -l=app.kubernetes.io/name=gitlab-agent -n gitlab-agent

# 4. Revoke old token
curl --request DELETE \
  --header "PRIVATE-TOKEN: ${GITLAB_TOKEN}" \
  --url "https://${GITLAB_HOST}/api/v4/projects/${PROJECT_ID}/cluster_agents/${AGENT_ID}/tokens/${OLD_TOKEN_ID}"
```

---

## Troubleshooting Guide

### Common Issues

| Issue                                       | Diagnosis                     | Solution                                                |
| ------------------------------------------- | ----------------------------- | ------------------------------------------------------- |
| **WebSocket dial failed**                   | `lookup gitlab-kas on...`     | Verify DNS resolution, check `kasAddress` configuration |
| **HTTP 301 on handshake**                   | Missing trailing slash        | Ensure `kasAddress` ends with `/`                       |
| **Certificate signed by unknown authority** | Self-signed CA not trusted    | Use `--set-file config.kasCaCert=ca.pem`                |
| **Agent version mismatch**                  | Version warning in UI         | Update agent to match GitLab version                    |
| **Decompressor not installed for gzip**     | Version incompatibility       | Ensure `agentk` and KAS versions match                  |
| **Failed to register agent pod**            | Version/connectivity mismatch | Verify KAS is running: `gitlab-ctl status gitlab-kas`   |

### Debug Commands

```bash
# View agent logs
kubectl logs -f -l=app.kubernetes.io/name=gitlab-agent -n gitlab-agent

# Check agent pod status
kubectl describe pod -l=app.kubernetes.io/name=gitlab-agent -n gitlab-agent

# Verify agent configuration
kubectl get configmap -l=app=gitlab-agent -n gitlab-agent -o yaml

# Test connectivity to KAS
kubectl run curl-test --rm -it --restart=Never --image=curlimages/curl -- \
  curl -v "https://${GITLAB_HOST}/-/kubernetes-agent/"

# List registered agents via API
curl --header "PRIVATE-TOKEN: ${GITLAB_TOKEN}" \
  "https://${GITLAB_HOST}/api/v4/projects/${PROJECT_ID}/cluster_agents" | jq

# Check token status
curl --header "PRIVATE-TOKEN: ${GITLAB_TOKEN}" \
  "https://${GITLAB_HOST}/api/v4/projects/${PROJECT_ID}/cluster_agents/${AGENT_ID}/tokens" | jq
```

### Self-Signed Certificate Fix

For on-prem GitLab with self-signed certificates:

```bash
# Get the CA certificate from GitLab server
openssl s_client -connect ${GITLAB_HOST}:443 -showcerts </dev/null 2>/dev/null | \
  openssl x509 -outform PEM > gitlab-ca.pem

# Install with CA
helm upgrade --install gitlab-agent gitlab/gitlab-agent \
  --namespace gitlab-agent \
  --set config.token="${AGENT_TOKEN}" \
  --set config.kasAddress="wss://${GITLAB_HOST}/-/kubernetes-agent/" \
  --set-file config.kasCaCert=./gitlab-ca.pem
```

### Reference Files

- **[references/agent_installation.md](references/agent_installation.md)** — Detailed installation and configuration guide
- **[references/gitops_flux.md](references/gitops_flux.md)** — Complete GitOps setup with Flux
- **[references/api_reference.md](references/api_reference.md)** — GitLab API endpoints for agent and project management
- **[references/troubleshooting.md](references/troubleshooting.md)** — Detailed troubleshooting scenarios

---

## GitLab API Quick Reference

### Agent Management

```bash
# List agents
GET /projects/:id/cluster_agents

# Get agent details
GET /projects/:id/cluster_agents/:agent_id

# Register agent
POST /projects/:id/cluster_agents
# Body: {"name":"agent-name"}

# Delete agent
DELETE /projects/:id/cluster_agents/:agent_id
```

### Token Management

```bash
# List tokens (max 2 active)
GET /projects/:id/cluster_agents/:agent_id/tokens

# Create token
POST /projects/:id/cluster_agents/:agent_id/tokens
# Body: {"name":"token-name","description":"optional"}

# Revoke token
DELETE /projects/:id/cluster_agents/:agent_id/tokens/:token_id
```

### Project Management

```bash
# List projects
GET /projects?search=keyword

# Get project details
GET /projects/:id

# Create project
POST /projects
# Body: {"name":"project-name","namespace_id":123}

# Edit project
PUT /projects/:id
```

---

## Scripts

### Check Agent Health

```bash
# Run agent health check
python skills/gitlab/scripts/gitlab_agent_status.py \
  --namespace gitlab-agent \
  --gitlab-url "https://${GITLAB_HOST}" \
  --project-id ${PROJECT_ID} \
  --output reports/gitlab/agent_health.json
```

### Generate Agent Values

```bash
# Generate Helm values file
python skills/gitlab/scripts/generate_agent_values.py \
  --gitlab-url "https://${GITLAB_HOST}" \
  --agent-name eks-nonprod-agent \
  --ca-cert ./gitlab-ca.pem \
  --output agent-values.yaml
```

---

## Best Practices

### Security

1. **Use dedicated service account** — Don't use `cluster-admin` in production
2. **Rotate tokens regularly** — Use the 2-token limit for zero-downtime rotation
3. **Restrict CI/CD access** — Use impersonation for fine-grained RBAC
4. **Enable TLS** — Required for self-managed GitLab with KAS

### Production Configuration

```yaml
# production-values.yaml
replicaCount: 2

resources:
  requests:
    cpu: 100m
    memory: 128Mi
  limits:
    cpu: 500m
    memory: 256Mi

rbac:
  create: true
  useExistingRole: gitlab-agent-role # Pre-created restricted role

serviceAccount:
  create: true
  name: gitlab-agent

podDisruptionBudget:
  enabled: true
  minAvailable: 1

affinity:
  podAntiAffinity:
    preferredDuringSchedulingIgnoredDuringExecution:
      - weight: 100
        podAffinityTerm:
          labelSelector:
            matchLabels:
              app.kubernetes.io/name: gitlab-agent
          topologyKey: kubernetes.io/hostname
```

### Reliability

1. **Match versions** — Keep agent version aligned with GitLab version
2. **Monitor connectivity** — Alert on agent connection failures
3. **Use GitOps** — Prefer Flux over CI/CD for production deployments
4. **Backup config** — Store agent values in version control

---

## Environment Configuration

Required environment variables for scripts:

```bash
export GITLAB_HOST="gitlab.example.com"          # Your on-prem GitLab host
export GITLAB_TOKEN="glpat-xxxx"                 # Personal/project access token
export PROJECT_ID="123"                          # Project ID containing agent config
export AGENT_ID="1"                              # Agent ID (from registration)
export KUBECONFIG="~/.kube/config"               # Kubernetes configuration
```

---

## Related Skills

- **[karpenter](../karpenter/SKILL.md)** — Node autoscaling for GitLab agent workloads
- **[aws](../aws/SKILL.md)** — Parent AWS skill for EKS cluster management
- **[consul](../consul/SKILL.md)** — Service mesh for applications deployed via GitOps

---

## External Resources

- [GitLab Agent for Kubernetes Documentation](https://docs.gitlab.com/user/clusters/agent/)
- [Installing the Agent](https://docs.gitlab.com/user/clusters/agent/install/)
- [GitOps with Flux](https://docs.gitlab.com/user/clusters/agent/gitops/)
- [CI/CD Workflow](https://docs.gitlab.com/user/clusters/agent/ci_cd_workflow/)
- [Kubernetes Agent API](https://docs.gitlab.com/api/cluster_agents/)
- [Troubleshooting Guide](https://docs.gitlab.com/user/clusters/agent/troubleshooting/)
- [GitLab Agent Helm Chart](https://gitlab.com/gitlab-org/charts/gitlab-agent)
- [FluxCD Documentation](https://fluxcd.io/flux/)
