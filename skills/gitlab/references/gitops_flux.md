# GitOps with Flux

GitLab recommends Flux for GitOps deployments. This guide covers setting up Flux with GitLab Agent for continuous deployment to EKS clusters.

---

## Overview

### Why Flux?

| Feature                | Flux (GitOps)                  | CI/CD (kubectl)           |
| ---------------------- | ------------------------------ | ------------------------- |
| **Deployment Trigger** | Git push → automatic           | Pipeline trigger → manual |
| **Security Model**     | Pull-based, no credentials out | Push-based, tokens in CI  |
| **Drift Detection**    | Automatic remediation          | Manual checks needed      |
| **Audit Trail**        | Git history = deploy history   | Pipeline logs             |
| **Recommended For**    | Production environments        | Dev/test, migrations      |

### Architecture

```
┌───────────────────────────────────────────────────────────────┐
│  GitLab                                                        │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │  flux-config repository                                 │  │
│  │  ├── clusters/                                          │  │
│  │  │   ├── eks-nonprod/                                   │  │
│  │  │   │   ├── flux-system/                               │  │
│  │  │   │   ├── apps/                                      │  │
│  │  │   │   └── infrastructure/                            │  │
│  │  │   └── eks-prod/                                      │  │
│  │  └── apps/                                              │  │
│  │      └── my-app/                                        │  │
│  └─────────────────────────────────────────────────────────┘  │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │  application repositories (source of manifests)        │  │
│  └─────────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────────┘
                              │
                         Git pull
                              │
┌───────────────────────────────────────────────────────────────┐
│  EKS Cluster                                                   │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │  flux-system namespace                                  │  │
│  │  ├── source-controller (fetches Git repos)             │  │
│  │  ├── kustomize-controller (applies manifests)          │  │
│  │  ├── helm-controller (manages Helm releases)           │  │
│  │  └── notification-controller (sends events)            │  │
│  └─────────────────────────────────────────────────────────┘  │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │  gitlab-agent namespace                                 │  │
│  │  └── agentk (provides cluster connectivity to GitLab)   │  │
│  └─────────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────────┘
```

---

## Setup

### Prerequisites

- GitLab Agent installed and connected
- `flux` CLI installed: `brew install fluxcd/tap/flux`
- GitLab access token with `api` and `write_repository` scopes

### Step 1: Enable Flux in Agent Config

Update `.gitlab/agents/<agent-name>/config.yaml`:

```yaml
# Enable Flux integration
flux:
  resource_inclusions:
    - api_groups:
        - "*"
      resources:
        - "*"
```

### Step 2: Bootstrap Flux

```bash
# Set environment
export GITLAB_HOST="gitlab.example.com"
export GITLAB_TOKEN="glpat-xxxx"
export GITLAB_GROUP="path/to/group"
export FLUX_REPO="flux-config"

# Verify prerequisites
flux check --pre

# Bootstrap (creates flux-config repo if needed)
flux bootstrap gitlab \
  --hostname=${GITLAB_HOST} \
  --token-auth \
  --owner=${GITLAB_GROUP} \
  --repository=${FLUX_REPO} \
  --branch=main \
  --path=clusters/eks-nonprod \
  --components-extra=image-reflector-controller,image-automation-controller

# Verify installation
flux check
kubectl get pods -n flux-system
```

### Step 3: Create GitLab Token Secret

```bash
# Create secret for Flux to access GitLab repos
kubectl create secret generic gitlab-token \
  --namespace=flux-system \
  --from-literal=username=git \
  --from-literal=password=${GITLAB_TOKEN}
```

For self-signed certificates:

```bash
# Create CA secret
kubectl create secret generic gitlab-ca \
  --namespace=flux-system \
  --from-file=ca.crt=./gitlab-ca.pem
```

---

## Configuration

### GitRepository Source

```yaml
# clusters/eks-nonprod/apps/my-app-source.yaml
apiVersion: source.toolkit.fluxcd.io/v1
kind: GitRepository
metadata:
  name: my-app
  namespace: flux-system
spec:
  interval: 1m0s
  url: https://gitlab.example.com/path/to/my-app.git
  ref:
    branch: main
  secretRef:
    name: gitlab-token
  # For self-signed certs
  certSecretRef:
    name: gitlab-ca
```

### Kustomization

```yaml
# clusters/eks-nonprod/apps/my-app-kustomization.yaml
apiVersion: kustomize.toolkit.fluxcd.io/v1
kind: Kustomization
metadata:
  name: my-app
  namespace: flux-system
spec:
  interval: 5m0s
  path: ./manifests
  prune: true # Delete resources removed from Git
  sourceRef:
    kind: GitRepository
    name: my-app
  targetNamespace: production
  healthChecks:
    - apiVersion: apps/v1
      kind: Deployment
      name: my-app
      namespace: production
  timeout: 3m0s
```

### HelmRelease

```yaml
# clusters/eks-nonprod/infrastructure/cert-manager.yaml
apiVersion: source.toolkit.fluxcd.io/v1
kind: HelmRepository
metadata:
  name: jetstack
  namespace: flux-system
spec:
  interval: 1h0m0s
  url: https://charts.jetstack.io
---
apiVersion: helm.toolkit.fluxcd.io/v2
kind: HelmRelease
metadata:
  name: cert-manager
  namespace: flux-system
spec:
  interval: 1h0m0s
  chart:
    spec:
      chart: cert-manager
      version: "1.13.x"
      sourceRef:
        kind: HelmRepository
        name: jetstack
  targetNamespace: cert-manager
  install:
    createNamespace: true
  values:
    installCRDs: true
```

---

## Repository Structure

### Recommended Layout

```
flux-config/
├── clusters/
│   ├── eks-nonprod/
│   │   ├── flux-system/           # Flux components (auto-generated)
│   │   │   └── gotk-*.yaml
│   │   ├── apps/                  # Application deployments
│   │   │   ├── kustomization.yaml
│   │   │   ├── my-app.yaml
│   │   │   └── other-app.yaml
│   │   └── infrastructure/        # Shared infrastructure
│   │       ├── kustomization.yaml
│   │       ├── cert-manager.yaml
│   │       └── ingress-nginx.yaml
│   └── eks-prod/
│       ├── flux-system/
│       ├── apps/
│       └── infrastructure/
├── apps/                          # Shared app definitions
│   ├── base/
│   │   └── my-app/
│   │       ├── deployment.yaml
│   │       ├── service.yaml
│   │       └── kustomization.yaml
│   ├── nonprod/
│   │   └── my-app/
│   │       └── kustomization.yaml
│   └── prod/
│       └── my-app/
│           └── kustomization.yaml
└── infrastructure/                # Shared infra definitions
    ├── cert-manager/
    └── ingress-nginx/
```

### Dependency Ordering

```yaml
# clusters/eks-nonprod/apps/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - my-app.yaml
  - other-app.yaml
```

```yaml
# clusters/eks-nonprod/infrastructure/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - cert-manager.yaml
  - ingress-nginx.yaml
```

Use `dependsOn` for ordering:

```yaml
apiVersion: kustomize.toolkit.fluxcd.io/v1
kind: Kustomization
metadata:
  name: apps
  namespace: flux-system
spec:
  dependsOn:
    - name: infrastructure # Apps wait for infra
  # ...
```

---

## Notifications

### Send Deployment Events to GitLab

```yaml
# clusters/eks-nonprod/flux-system/notifications.yaml
apiVersion: notification.toolkit.fluxcd.io/v1beta3
kind: Provider
metadata:
  name: gitlab
  namespace: flux-system
spec:
  type: gitlab
  address: https://gitlab.example.com
  secretRef:
    name: gitlab-token
---
apiVersion: notification.toolkit.fluxcd.io/v1beta3
kind: Alert
metadata:
  name: deployment-alerts
  namespace: flux-system
spec:
  providerRef:
    name: gitlab
  eventSeverity: info
  eventSources:
    - kind: Kustomization
      name: "*"
    - kind: HelmRelease
      name: "*"
```

### Webhook for Immediate Reconciliation

```yaml
# Trigger immediate sync on Git push
apiVersion: notification.toolkit.fluxcd.io/v1
kind: Receiver
metadata:
  name: gitlab-webhook
  namespace: flux-system
spec:
  type: gitlab
  secretRef:
    name: webhook-token
  resources:
    - kind: GitRepository
      name: "*"
```

Get webhook URL:

```bash
kubectl get receiver gitlab-webhook -n flux-system -o jsonpath='{.status.webhookPath}'
# Configure as webhook in GitLab project settings
```

---

## Operations

### Sync Status

```bash
# Check all Flux resources
flux get all

# Check specific app
flux get kustomization my-app

# Check source status
flux get sources git
```

### Manual Reconciliation

```bash
# Trigger immediate sync
flux reconcile source git my-app

# Reconcile kustomization
flux reconcile kustomization my-app
```

### Suspend/Resume

```bash
# Suspend (disable auto-sync)
flux suspend kustomization my-app

# Resume
flux resume kustomization my-app
```

### Rollback

```bash
# Git-based rollback (recommended)
git revert HEAD
git push

# Or rollback to specific commit
git reset --hard <commit>
git push --force-with-lease
```

### Logs

```bash
# Flux controller logs
kubectl logs -n flux-system deployment/source-controller
kubectl logs -n flux-system deployment/kustomize-controller
kubectl logs -n flux-system deployment/helm-controller

# Events
kubectl get events -n flux-system --sort-by='.lastTimestamp'
```

---

## Troubleshooting

### Common Issues

| Issue                     | Diagnosis                       | Solution                                |
| ------------------------- | ------------------------------- | --------------------------------------- |
| **Source not ready**      | `flux get sources git my-app`   | Check token, URL, branch name           |
| **Certificate error**     | x509 errors in logs             | Add `certSecretRef` with CA cert        |
| **Authentication failed** | 401/403 in source-controller    | Verify token has correct permissions    |
| **Kustomization stuck**   | `flux get kustomization my-app` | Check health checks, resource conflicts |
| **Drift not reconciled**  | Changes not applied             | Check `prune: true`, verify interval    |

### Debug Commands

```bash
# Describe resources
flux get sources git my-app
flux get kustomization my-app

# View events
flux events

# Force reconciliation
flux reconcile kustomization my-app --with-source

# Trace failures
flux trace kustomization my-app

# Preview changes (dry-run)
flux diff kustomization my-app
```

---

## Best Practices

### Security

1. **Use deploy tokens** — Create read-only tokens for Flux
2. **Limit permissions** — Only expose necessary namespaces
3. **Seal secrets** — Use Sealed Secrets or SOPS for encrypted secrets
4. **Audit access** — Use Git history as audit trail

### Operations

1. **Use health checks** — Define healthChecks in Kustomization
2. **Set proper timeouts** — Don't let failures hang forever
3. **Enable pruning** — `prune: true` cleans up removed resources
4. **Monitor with alerts** — Configure notification provider

### Structure

1. **Separate environments** — Different cluster paths
2. **Use Kustomize overlays** — Base + environment overlays
3. **Order dependencies** — Infrastructure before apps
4. **Version pin** — Pin chart and image versions
