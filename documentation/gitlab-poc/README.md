# GitLab Agent for Kubernetes - EKS POC

> Documentation for the POC deployment testing GitLab Agent connectivity to EKS clusters

## Overview

This POC validates the end-to-end integration between the EC GitLab instance (`sdlc.webcloud.ec.europa.eu`) and AWS EKS clusters using the GitLab Agent for Kubernetes.

| Attribute            | Value                        |
| -------------------- | ---------------------------- |
| **GitLab Instance**  | `sdlc.webcloud.ec.europa.eu` |
| **Project**          | `apim/poc-aws-shared`        |
| **Local Path**       | `gitlab-ec/`                 |
| **Target Cluster**   | EKS Non-Prod                 |
| **Test Application** | nginx (2 replicas)           |
| **Namespace**        | `poc-nginx-test`             |

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           EC GitLab Instance                                │
│                    sdlc.webcloud.ec.europa.eu                               │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Project: apim/poc-aws-shared                                        │   │
│  │  ├── .gitlab-ci.yml (CI/CD Pipeline)                                │   │
│  │  ├── k8s/base/ (Kubernetes manifests)                               │   │
│  │  └── .gitlab/agents/<agent-name>/config.yaml                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────┬───────────────────────────┘
                                              │
                                              │ gRPC (outbound from cluster)
                                              │ Agent pulls instructions
                                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              AWS EKS Cluster                                │
│                                 (Non-Prod)                                  │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  gitlab-agent namespace                                               │  │
│  │  ┌────────────────────────────────────────────────────────────────┐  │  │
│  │  │  GitLab Agent Pod                                               │  │  │
│  │  │  - Connects to GitLab via gRPC                                  │  │  │
│  │  │  - Receives kubectl commands from CI/CD                         │  │  │
│  │  │  - Executes deployments in authorized namespaces                │  │  │
│  │  └────────────────────────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  poc-nginx-test namespace                                             │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │  │
│  │  │  nginx pod  │  │  nginx pod  │  │   Service   │  │  ConfigMap  │  │  │
│  │  │  (replica 1)│  │  (replica 2)│  │  (ClusterIP)│  │  (HTML)     │  │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘  │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Components

### 1. GitLab Agent

The agent runs inside the EKS cluster and establishes an **outbound** connection to the GitLab instance. This is crucial for environments where inbound connections to the cluster are restricted.

**Key points:**

- Agent initiates connection (firewall-friendly)
- Uses gRPC over HTTPS
- Token-based authentication
- Can be configured for specific namespaces/resources

### 2. CI/CD Pipeline

The pipeline (`/.gitlab-ci.yml`) contains:

| Stage      | Jobs                                                | Purpose                       |
| ---------- | --------------------------------------------------- | ----------------------------- |
| `validate` | `validate:manifests`, `validate:agent-connectivity` | Pre-flight checks             |
| `deploy`   | `deploy:nonprod`                                    | Apply K8s manifests via agent |
| `verify`   | `verify:deployment`, `verify:resources`             | Health checks                 |
| `cleanup`  | `cleanup:nonprod`                                   | Remove test resources         |

### 3. Kubernetes Manifests

Located in `k8s/base/`:

| File                 | Resource      | Description                  |
| -------------------- | ------------- | ---------------------------- |
| `namespace.yaml`     | Namespace     | `poc-nginx-test` namespace   |
| `configmap.yaml`     | ConfigMap     | Custom HTML for nginx        |
| `deployment.yaml`    | Deployment    | 2 nginx replicas with probes |
| `service.yaml`       | Service       | ClusterIP on port 80         |
| `kustomization.yaml` | Kustomization | Ties all resources together  |

## Setup Instructions

### Step 1: Register GitLab Agent

1. Navigate to the project in GitLab
2. Go to **Operate** → **Kubernetes clusters** → **Connect a cluster**
3. Name your agent (e.g., `eks-nonprod-agent`)
4. Copy the agent token (displayed only once!)

### Step 2: Install Agent on EKS

```bash
# Add GitLab Helm repo
helm repo add gitlab https://charts.gitlab.io
helm repo update

# Install agent
helm upgrade --install gitlab-agent gitlab/gitlab-agent \
  --namespace gitlab-agent \
  --create-namespace \
  --set config.token=<AGENT_TOKEN> \
  --set config.kasAddress=wss://kas.sdlc.webcloud.ec.europa.eu
```

### Step 3: Configure Agent

Create `.gitlab/agents/<agent-name>/config.yaml` in the project:

```yaml
# Agent configuration
ci_access:
  projects:
    - id: apim/poc-aws-shared
      default_namespace: poc-nginx-test
      access_as:
        agent: {}
```

### Step 4: Update Pipeline Variable

Edit `.gitlab-ci.yml`:

```yaml
variables:
  KUBE_CONTEXT: "apim/poc-aws-shared:<agent-name>"
```

### Step 5: Run Pipeline

1. Commit and push changes
2. Pipeline triggers automatically
3. Monitor stages in GitLab CI/CD

## Verification

### Check Agent Status

```bash
# Agent pod
kubectl get pods -n gitlab-agent

# Agent logs
kubectl logs -n gitlab-agent -l app=gitlab-agent --tail=50

# Expected: Connected successfully, receiving instructions
```

### Check Deployment

```bash
# Pods
kubectl get pods -n poc-nginx-test
# Expected: 2/2 Running

# Service
kubectl get svc -n poc-nginx-test
# Expected: nginx ClusterIP 80/TCP

# Test locally
kubectl port-forward -n poc-nginx-test svc/nginx 8080:80
# Open http://localhost:8080
```

## Troubleshooting

| Issue                    | Cause                 | Solution                          |
| ------------------------ | --------------------- | --------------------------------- |
| Agent not connecting     | Token expired/invalid | Regenerate token in GitLab        |
| `KUBE_CONTEXT` not found | Agent name mismatch   | Verify agent name in config       |
| Deployment fails         | RBAC permissions      | Check agent's ServiceAccount RBAC |
| Pods pending             | Resource constraints  | Check node resources/quotas       |

See also: `/skills/gitlab/references/troubleshooting.md`

## Security Considerations

1. **Token Management**: Agent token should be rotated regularly
2. **Namespace Isolation**: Agent configured for specific namespaces only
3. **RBAC**: Minimum required permissions for deployments
4. **Network**: Agent uses outbound connection only

## Files Reference

| Path                        | Description                              |
| --------------------------- | ---------------------------------------- |
| `gitlab-ec/.gitlab-ci.yml`  | CI/CD pipeline configuration             |
| `gitlab-ec/k8s/base/`       | Kubernetes manifests                     |
| `gitlab-ec/README.md`       | Project README                           |
| `documentation/gitlab-poc/` | This documentation                       |
| `skills/gitlab/`            | GitLab skill with scripts and references |

## Next Steps

After successful POC validation:

1. [ ] Configure production agent for prod EKS cluster
2. [ ] Set up Ingress with TLS for external access
3. [ ] Integrate with GitOps (Flux) for declarative deployments
4. [ ] Add environment-specific overlays (nonprod/prod)
5. [ ] Configure monitoring and alerting

---

**Status:** POC | **Created:** 2026-01-21 | **Author:** Agent
