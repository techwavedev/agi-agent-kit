# GitLab Agent Installation Guide

Detailed guide for installing and configuring the GitLab Agent for Kubernetes on EKS clusters with on-prem self-managed GitLab.

---

## Prerequisites

### GitLab Requirements

- GitLab version 15.0+ (for API-based token management)
- KAS (Kubernetes Agent Server) enabled on your GitLab instance
- Personal Access Token or Project Access Token with:
  - `api` scope (for agent management)
  - `read_repository` scope (for GitOps)

### Cluster Requirements

- Kubernetes 1.32-1.34 (check GitLab version compatibility)
- Helm 3.x compatible with your Kubernetes version
- kubectl access to target cluster
- Network connectivity from cluster to GitLab KAS endpoint

### Verify KAS Availability

```bash
# KAS should respond on this endpoint (self-managed)
curl -v "https://${GITLAB_HOST}/-/kubernetes-agent/"

# Expected: HTTP 101 Switching Protocols (WebSocket upgrade) or HTTP 400
# Error: Connection refused means KAS is not properly configured
```

---

## Installation Methods

### Method 1: Helm with API Registration (Recommended)

**Step 1: Set Environment Variables**

```bash
export GITLAB_HOST="gitlab.example.com"
export GITLAB_TOKEN="glpat-xxxxxxxxxxxxxxxxxxxx"
export PROJECT_ID="123"  # Your project ID
export AGENT_NAME="eks-nonprod-agent"
```

**Step 2: Register Agent via API**

```bash
AGENT_RESPONSE=$(curl --silent --request POST \
  --header "PRIVATE-TOKEN: ${GITLAB_TOKEN}" \
  --header "Content-Type: application/json" \
  --url "https://${GITLAB_HOST}/api/v4/projects/${PROJECT_ID}/cluster_agents" \
  --data "{\"name\":\"${AGENT_NAME}\"}")

export AGENT_ID=$(echo $AGENT_RESPONSE | jq -r '.id')
echo "Agent ID: ${AGENT_ID}"
```

**Step 3: Create Agent Token**

```bash
TOKEN_RESPONSE=$(curl --silent --request POST \
  --header "PRIVATE-TOKEN: ${GITLAB_TOKEN}" \
  --header "Content-Type: application/json" \
  --url "https://${GITLAB_HOST}/api/v4/projects/${PROJECT_ID}/cluster_agents/${AGENT_ID}/tokens" \
  --data '{"name":"initial-token","description":"Initial installation token"}')

export AGENT_TOKEN=$(echo $TOKEN_RESPONSE | jq -r '.token')
echo "Token created (save this, it cannot be retrieved again!)"
```

**Step 4: Get CA Certificate (for self-signed)**

```bash
# Extract CA certificate
openssl s_client -connect ${GITLAB_HOST}:443 -showcerts </dev/null 2>/dev/null | \
  openssl x509 -outform PEM > gitlab-ca.pem
```

**Step 5: Install with Helm**

```bash
# Add repo
helm repo add gitlab https://charts.gitlab.io
helm repo update

# Install
helm upgrade --install gitlab-agent gitlab/gitlab-agent \
  --namespace gitlab-agent \
  --create-namespace \
  --set config.token="${AGENT_TOKEN}" \
  --set config.kasAddress="wss://${GITLAB_HOST}/-/kubernetes-agent/" \
  --set-file config.kasCaCert=./gitlab-ca.pem \
  --set image.tag=v17.6.0

# Verify
kubectl get pods -n gitlab-agent
```

### Method 2: GitLab UI Registration

1. Navigate to your project → **Operate** → **Kubernetes clusters**
2. Click **Connect a cluster**
3. Enter agent name (e.g., `eks-nonprod-agent`)
4. Click **Register**
5. Copy the generated Helm install command
6. Modify for self-signed certificates:

```bash
# Add --set-file config.kasCaCert=./gitlab-ca.pem to the command
```

---

## Configuration Options

### Agent Configuration File

Create `.gitlab/agents/<agent-name>/config.yaml` in your project:

```yaml
# Full configuration reference

# CI/CD workflow access
ci_access:
  # Projects that can use this agent in CI/CD
  projects:
    - id: path/to/project1
    - id: path/to/project2
  # Groups - all projects in group can access
  groups:
    - id: path/to/group

# User access for Kubernetes dashboard (Premium/Ultimate)
user_access:
  projects:
    - id: path/to/project
  groups:
    - id: path/to/group
  access_as:
    agent: {}

# GitOps with Flux integration
flux:
  # Resources Flux can manage
  resource_inclusions:
    - api_groups:
        - "*"
      resources:
        - "*"

# Observability settings
observability:
  logging:
    level: info # debug, info, warn, error
  metrics:
    enabled: true
    address: ":8080"

# Remote development workspaces (Premium/Ultimate)
remote_development:
  enabled: false
```

### Helm Values Reference

```yaml
# Complete gitlab-agent Helm values

# Image configuration
image:
  repository: registry.gitlab.com/gitlab-org/cluster-integration/gitlab-agent/agentk
  tag: v17.6.0 # Should match GitLab version
  pullPolicy: IfNotPresent

# Replica count for HA
replicaCount: 1 # Use 2 for production

# Agent configuration
config:
  token: "" # Agent token (required)
  kasAddress: "" # KAS WebSocket URL (required)
  kasCaCert: "" # CA certificate for self-signed (optional)
  observability:
    logging:
      level: info

# RBAC configuration
rbac:
  create: true
  # Use existing role instead of cluster-admin
  useExistingRole: "" # e.g., gitlab-agent-role

# Service account
serviceAccount:
  create: true
  name: "" # Auto-generated if empty
  annotations: {}

# Resource limits
resources:
  requests:
    cpu: 100m
    memory: 128Mi
  limits:
    cpu: 500m
    memory: 512Mi

# Pod disruption budget
podDisruptionBudget:
  enabled: false
  minAvailable: 1

# Node selector
nodeSelector: {}

# Tolerations
tolerations: []

# Affinity rules
affinity: {}

# Additional environment variables
extraEnv: []

# Additional volumes
extraVolumes: []
extraVolumeMounts: []
```

---

## Production Installation

### Create Restricted RBAC Role

```yaml
# gitlab-agent-rbac.yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: gitlab-agent-role
rules:
  # Minimal permissions for GitOps
  - apiGroups: [""]
    resources:
      - namespaces
      - pods
      - services
      - configmaps
      - secrets
    verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]
  - apiGroups: ["apps"]
    resources:
      - deployments
      - statefulsets
      - daemonsets
      - replicasets
    verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]
  - apiGroups: ["networking.k8s.io"]
    resources:
      - ingresses
    verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]
  # Add more as needed for your workloads
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: gitlab-agent-binding
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: gitlab-agent-role
subjects:
  - kind: ServiceAccount
    name: gitlab-agent
    namespace: gitlab-agent
```

```bash
# Apply RBAC
kubectl apply -f gitlab-agent-rbac.yaml

# Install with restricted role
helm upgrade --install gitlab-agent gitlab/gitlab-agent \
  --namespace gitlab-agent \
  --create-namespace \
  -f production-values.yaml \
  --set rbac.useExistingRole=gitlab-agent-role \
  --set config.token="${AGENT_TOKEN}" \
  --set config.kasAddress="wss://${GITLAB_HOST}/-/kubernetes-agent/" \
  --set-file config.kasCaCert=./gitlab-ca.pem
```

### Production Values File

```yaml
# production-values.yaml
replicaCount: 2

image:
  tag: v17.6.0

resources:
  requests:
    cpu: 100m
    memory: 128Mi
  limits:
    cpu: 500m
    memory: 256Mi

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
          topologyKey: topology.kubernetes.io/zone

config:
  observability:
    logging:
      level: warn
```

---

## Multi-Cluster Setup

### One Agent Per Cluster

GitLab recommends running one agent per cluster with impersonation for multi-tenancy:

```
┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│  EKS-nonprod     │    │  EKS-staging     │    │  EKS-prod        │
│  ┌────────────┐  │    │  ┌────────────┐  │    │  ┌────────────┐  │
│  │  agentk    │  │    │  │  agentk    │  │    │  │  agentk    │  │
│  │ (nonprod)  │  │    │  │ (staging)  │  │    │  │ (prod)     │  │
│  └─────┬──────┘  │    │  └─────┬──────┘  │    │  └─────┬──────┘  │
└────────┼─────────┘    └────────┼─────────┘    └────────┼─────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌────────────┴────────────┐
                    │   GitLab KAS Server     │
                    │   (on-prem GitLab)      │
                    └─────────────────────────┘
```

### Register Multiple Agents

```bash
# Create agents for each environment
for ENV in nonprod staging prod; do
  curl --request POST \
    --header "PRIVATE-TOKEN: ${GITLAB_TOKEN}" \
    --header "Content-Type: application/json" \
    --url "https://${GITLAB_HOST}/api/v4/projects/${PROJECT_ID}/cluster_agents" \
    --data "{\"name\":\"eks-${ENV}-agent\"}"
done
```

### Use Different Release Names

```bash
# Non-prod cluster
helm upgrade --install gitlab-agent-nonprod gitlab/gitlab-agent \
  --namespace gitlab-agent \
  --set config.token="${NONPROD_TOKEN}" \
  ...

# Staging cluster (same namespace, different release)
helm upgrade --install gitlab-agent-staging gitlab/gitlab-agent \
  --namespace gitlab-agent \
  --set config.token="${STAGING_TOKEN}" \
  ...
```

---

## Uninstallation

```bash
# Uninstall Helm release
helm uninstall gitlab-agent --namespace gitlab-agent

# Delete namespace (optional)
kubectl delete namespace gitlab-agent

# Delete agent registration from GitLab
curl --request DELETE \
  --header "PRIVATE-TOKEN: ${GITLAB_TOKEN}" \
  --url "https://${GITLAB_HOST}/api/v4/projects/${PROJECT_ID}/cluster_agents/${AGENT_ID}"
```

---

## Verification Checklist

After installation, verify:

- [ ] Agent pod is Running: `kubectl get pods -n gitlab-agent`
- [ ] No errors in logs: `kubectl logs -f -l=app.kubernetes.io/name=gitlab-agent -n gitlab-agent`
- [ ] Agent shows "Connected" in GitLab UI: Project → Operate → Kubernetes clusters
- [ ] Token status is "active": Check via API
- [ ] CI/CD can access cluster: Run a test pipeline with `kubectl get pods`
