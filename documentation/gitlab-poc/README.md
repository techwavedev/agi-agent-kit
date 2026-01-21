# GitLab Agent for Kubernetes - POC Installation

Documentation for the GitLab Kubernetes Agent installed on `eks-nonprod` cluster for the `poc-aws-shared` project.

**Installed:** 2026-01-21  
**Cluster:** eks-nonprod  
**Namespace:** gitlab-sdlc  
**GitLab Project:** apim/poc-aws-shared

---

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Installation Steps](#installation-steps)
4. [Verification](#verification)
5. [Configuration](#configuration)
6. [Maintenance](#maintenance)
7. [Troubleshooting](#troubleshooting)

---

## Overview

The GitLab Agent for Kubernetes (`agentk`) enables:

- **GitOps deployments** via Flux integration
- **CI/CD kubectl access** for pipelines
- **Cluster visibility** in GitLab UI

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  GitLab (sdlc.webcloud.ec.europa.eu)                        │
│  └── Project: apim/poc-aws-shared (ID: 7794)                │
│      └── Agent: eks-nonprod-agent (ID: 11)                  │
└─────────────────────────────────────────────────────────────┘
                              │
                    WebSocket (wss://)
                              │
┌─────────────────────────────────────────────────────────────┐
│  EKS Cluster: eks-nonprod                                   │
│  └── Namespace: gitlab-sdlc                                 │
│      └── Deployment: gitlab-agent (2 replicas)              │
└─────────────────────────────────────────────────────────────┘
```

---

## Prerequisites

### Access Requirements

| Requirement   | Details                                           |
| ------------- | ------------------------------------------------- |
| GitLab Access | Project Owner/Maintainer on `apim/poc-aws-shared` |
| AWS Access    | Profile `eks-kafka` with EKS access               |
| EKS Access    | kubectl access to `eks-nonprod`                   |
| Tools         | `kubectl`, `helm`, `aws` CLI, `curl`, `jq`        |

### Environment Setup

```bash
# GitLab credentials (stored in .env)
export GITLAB_HOST=sdlc.webcloud.ec.europa.eu
export GITLAB_TOKEN=<your-personal-access-token>
export PROJECT_ID=7794

# Kubernetes context
export KUBECONFIG=~/.kube/config
export AWS_PROFILE=eks-kafka
kubectl config use-context arn:aws:eks:eu-west-1:511383368449:cluster/eks-nonprod
```

---

## Installation Steps

### Step 1: Register Agent in GitLab

Register the agent via GitLab API:

```bash
curl --request POST \
  --header "PRIVATE-TOKEN: ${GITLAB_TOKEN}" \
  --header "Content-Type: application/json" \
  --url "https://${GITLAB_HOST}/api/v4/projects/${PROJECT_ID}/cluster_agents" \
  --data '{"name":"eks-nonprod-agent"}'
```

**Response:**

```json
{
  "id": 11,
  "name": "eks-nonprod-agent"
}
```

### Step 2: Create Agent Token

Create authentication token for the agent:

```bash
curl --request POST \
  --header "PRIVATE-TOKEN: ${GITLAB_TOKEN}" \
  --header "Content-Type: application/json" \
  --url "https://${GITLAB_HOST}/api/v4/projects/${PROJECT_ID}/cluster_agents/11/tokens" \
  --data '{"name":"initial-token","description":"EKS nonprod agent token"}'
```

> ⚠️ **Important:** Save the `token` value immediately - it cannot be retrieved again!

### Step 3: Install with Helm

```bash
# Add GitLab Helm repository
helm repo add gitlab https://charts.gitlab.io
helm repo update

# Install the agent
helm upgrade --install gitlab-agent gitlab/gitlab-agent \
  --namespace gitlab-sdlc \
  --create-namespace \
  --set config.token="<AGENT_TOKEN>" \
  --set config.kasAddress="wss://sdlc.webcloud.ec.europa.eu/-/kubernetes-agent/" \
  --set image.tag=v17.6.0 \
  --wait --timeout 120s
```

**Installation Output:**

```
NAME: gitlab-agent
LAST DEPLOYED: Wed Jan 21 13:44:22 2026
NAMESPACE: gitlab-sdlc
STATUS: deployed
REVISION: 1
```

---

## Verification

### Check Pod Status

```bash
kubectl get pods -n gitlab-sdlc
```

**Expected Output:**

```
NAME                               READY   STATUS    RESTARTS   AGE
gitlab-agent-v2-76c44d5799-4hjmr   1/1     Running   0          59s
gitlab-agent-v2-76c44d5799-spfgd   1/1     Running   0          59s
```

### Check Agent Logs

```bash
kubectl logs -n gitlab-sdlc -l app.kubernetes.io/name=gitlab-agent --tail=50
```

**Look for:**

- `"msg":"Starting"` — Agent modules initializing
- `"msg":"attempting to acquire leader lease"` — HA election
- No `"level":"ERROR"` messages

### Verify in GitLab UI

1. Navigate to: https://sdlc.webcloud.ec.europa.eu/apim/poc-aws-shared
2. Go to **Operate → Kubernetes clusters**
3. Agent should show as **Connected**

### Verify via API

```bash
curl --header "PRIVATE-TOKEN: ${GITLAB_TOKEN}" \
  "https://${GITLAB_HOST}/api/v4/projects/${PROJECT_ID}/cluster_agents" | jq
```

---

## Configuration

### Current Deployment Details

| Setting       | Value                                                  |
| ------------- | ------------------------------------------------------ |
| Namespace     | `gitlab-sdlc`                                          |
| Replicas      | 2 (HA)                                                 |
| Image Version | `v17.6.0`                                              |
| KAS Address   | `wss://sdlc.webcloud.ec.europa.eu/-/kubernetes-agent/` |
| Agent ID      | 11                                                     |
| Token Name    | `initial-token`                                        |

### Helm Values

To see current values:

```bash
helm get values gitlab-agent -n gitlab-sdlc
```

### Agent Configuration File

To enable CI/CD access, create agent config in GitLab repository:

**File:** `.gitlab/agents/eks-nonprod-agent/config.yaml`

```yaml
ci_access:
  projects:
    - id: apim/poc-aws-shared
  groups:
    - id: apim
```

---

## Maintenance

### Upgrade Agent

```bash
# Check current version
helm list -n gitlab-sdlc

# Upgrade to new version
helm upgrade gitlab-agent gitlab/gitlab-agent \
  --namespace gitlab-sdlc \
  --reuse-values \
  --set image.tag=v17.8.0

# Watch rollout
kubectl rollout status deployment/gitlab-agent-v2 -n gitlab-sdlc
```

### Token Rotation

```bash
# 1. Create new token (max 2 active)
curl --request POST \
  --header "PRIVATE-TOKEN: ${GITLAB_TOKEN}" \
  --header "Content-Type: application/json" \
  --url "https://${GITLAB_HOST}/api/v4/projects/${PROJECT_ID}/cluster_agents/11/tokens" \
  --data '{"name":"rotation-token"}'

# 2. Update Helm with new token
helm upgrade gitlab-agent gitlab/gitlab-agent \
  --namespace gitlab-sdlc \
  --reuse-values \
  --set config.token="<NEW_TOKEN>"

# 3. Revoke old token
curl --request DELETE \
  --header "PRIVATE-TOKEN: ${GITLAB_TOKEN}" \
  "https://${GITLAB_HOST}/api/v4/projects/${PROJECT_ID}/cluster_agents/11/tokens/<OLD_TOKEN_ID>"
```

### Uninstall

```bash
# Remove from cluster
helm uninstall gitlab-agent --namespace gitlab-sdlc
kubectl delete namespace gitlab-sdlc

# Remove from GitLab (optional)
curl --request DELETE \
  --header "PRIVATE-TOKEN: ${GITLAB_TOKEN}" \
  "https://${GITLAB_HOST}/api/v4/projects/${PROJECT_ID}/cluster_agents/11"
```

---

## Troubleshooting

### Check Agent Logs

```bash
kubectl logs -n gitlab-sdlc -l app.kubernetes.io/name=gitlab-agent --tail=100
```

### Common Issues

| Issue                       | Solution                                                   |
| --------------------------- | ---------------------------------------------------------- |
| Pod CrashLoopBackOff        | Check token is valid, check KAS address ends with `/`      |
| "Connection refused"        | Verify network allows outbound to GitLab on 443            |
| "Certificate error"         | Add `--set-file config.kasCaCert=./ca.pem` for self-signed |
| Agent not showing in GitLab | Wait 2-3 minutes, check logs for errors                    |

### Debug Commands

```bash
# Pod details
kubectl describe pod -n gitlab-sdlc -l app.kubernetes.io/name=gitlab-agent

# Events
kubectl get events -n gitlab-sdlc --sort-by='.lastTimestamp'

# Helm status
helm status gitlab-agent -n gitlab-sdlc
```

---

## Related Resources

- **Skill Documentation:** `skills/gitlab/SKILL.md`
- **GitLab Docs:** https://docs.gitlab.com/user/clusters/agent/
- **Project URL:** https://sdlc.webcloud.ec.europa.eu/apim/poc-aws-shared

---

## Appendix: Full Installation Commands

For quick reference, here's the complete installation sequence:

```bash
# 1. Set environment
source .env && export $(grep -v '^#' .env | xargs)
export KUBECONFIG=~/.kube/config
export AWS_PROFILE=eks-kafka

# 2. Register agent
AGENT_RESPONSE=$(curl --silent --request POST \
  --header "PRIVATE-TOKEN: ${GITLAB_TOKEN}" \
  --header "Content-Type: application/json" \
  --url "https://${GITLAB_HOST}/api/v4/projects/${PROJECT_ID}/cluster_agents" \
  --data '{"name":"eks-nonprod-agent"}')
AGENT_ID=$(echo $AGENT_RESPONSE | jq -r '.id')

# 3. Create token
TOKEN_RESPONSE=$(curl --silent --request POST \
  --header "PRIVATE-TOKEN: ${GITLAB_TOKEN}" \
  --header "Content-Type: application/json" \
  --url "https://${GITLAB_HOST}/api/v4/projects/${PROJECT_ID}/cluster_agents/${AGENT_ID}/tokens" \
  --data '{"name":"initial-token"}')
AGENT_TOKEN=$(echo $TOKEN_RESPONSE | jq -r '.token')

# 4. Install with Helm
helm repo add gitlab https://charts.gitlab.io
helm repo update
helm upgrade --install gitlab-agent gitlab/gitlab-agent \
  --namespace gitlab-sdlc \
  --create-namespace \
  --set config.token="${AGENT_TOKEN}" \
  --set config.kasAddress="wss://${GITLAB_HOST}/-/kubernetes-agent/" \
  --set image.tag=v17.6.0

# 5. Verify
kubectl get pods -n gitlab-sdlc
kubectl logs -n gitlab-sdlc -l app.kubernetes.io/name=gitlab-agent --tail=20
```
