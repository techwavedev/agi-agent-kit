# GitLab CI/CD for Kubernetes - Complete A-to-Z Learning Guide

> **Purpose:** Comprehensive tutorial explaining every file and concept so you can replicate this setup for any new project.

---

## Table of Contents

1. [Overview: What Is This Project?](#1-overview-what-is-this-project)
2. [Branch Strategy](#2-branch-strategy)
3. [Project Structure Explained](#3-project-structure-explained)
4. [File-by-File Deep Dive](#4-file-by-file-deep-dive)
5. [How GitLab Agent Works](#5-how-gitlab-agent-works)
6. [Step-by-Step: Create This From Scratch](#6-step-by-step-create-this-from-scratch)
7. [Kustomize Explained](#7-kustomize-explained)
8. [Pipeline Stages Explained](#8-pipeline-stages-explained)
9. [Common Patterns to Reuse](#9-common-patterns-to-reuse)
10. [Security Best Practices](#10-security-best-practices)
11. [Troubleshooting Guide](#11-troubleshooting-guide)

---

## 1. Overview: What Is This Project?

This project (`gitlab-ec/`) is a **Proof of Concept (POC)** that demonstrates how to deploy applications to AWS EKS (Elastic Kubernetes Service) using GitLab's built-in CI/CD pipelines and the GitLab Agent for Kubernetes.

### The Problem It Solves

Traditional Kubernetes deployments require direct access to the cluster:

- You need `kubectl` access from your machine
- CI/CD systems need firewall rules to reach the cluster
- Managing credentials across systems is complex

### The Solution: GitLab Agent

The GitLab Agent for Kubernetes solves this by:

1. **Running inside your cluster** as a pod
2. **Connecting outbound** to GitLab (no inbound firewall rules needed!)
3. **Receiving commands** from your CI/CD pipelines
4. **Executing kubectl** commands on your behalf

```
┌─────────────────────┐              ┌─────────────────────┐
│     GitLab          │              │    EKS Cluster      │
│  (sdlc.webcloud...) │◄─────────────│  GitLab Agent Pod   │
│                     │  Outbound    │  (initiates conn)   │
│  Runs CI/CD Jobs    │  gRPC/WSS    │                     │
└─────────────────────┘              └─────────────────────┘
                                              │
                                              ▼
                                     Deploys to cluster
```

---

## 2. Branch Strategy

This project uses environment-based branches to control deployments.

### Branch Overview

| Branch   | Purpose                          | Pipeline Trigger | Target Environment |
| -------- | -------------------------------- | ---------------- | ------------------ |
| `master` | Main development branch          | Automatic        | Development        |
| `tst`    | POC/Test environment deployments | Automatic        | Test/POC cluster   |
| `prod`   | Production deployments           | Manual approval  | Production cluster |

### How It Works

```
master (development)
   │
   ├──► tst (test/POC)
   │      │
   │      └──► Deploys to test cluster
   │
   └──► prod (production)
          │
          └──► Deploys to production cluster (manual)
```

### Workflow Rules in `.gitlab-ci.yml`

```yaml
workflow:
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    - if: $CI_COMMIT_BRANCH == "master"
    - if: $CI_COMMIT_BRANCH == "tst"
    - if: $CI_COMMIT_BRANCH == "prod"
    - if: $CI_COMMIT_TAG
    - when: manual
```

### Creating Environment Branches

```bash
# Create test branch (inherits from master)
git checkout master
git checkout -b tst
git push -u origin tst

# Create empty production branch (orphan - no history)
git checkout --orphan prod
git rm -rf .
git commit --allow-empty -m "Initial prod branch"
git push -u origin prod
```

### Using Branches for Deployments

**Test deployment:**

```bash
git checkout tst
git merge master           # Get latest changes
git push                   # Triggers test pipeline
```

**Production deployment:**

```bash
git checkout prod
git merge tst              # Promote tested code
git push                   # Triggers production pipeline (may require approval)
```

### Branch Protection (Recommended)

In GitLab, configure branch protection:

1. Go to **Settings** → **Repository** → **Protected branches**
2. Protect `prod` branch:
   - Allowed to merge: Maintainers only
   - Allowed to push: No one (force merge requests)
3. Protect `tst` branch:
   - Allowed to merge: Developers + Maintainers
   - Allowed to push: Developers + Maintainers

---

## 3. Project Structure Explained

```
gitlab-ec/
├── .gitignore              # Prevents secrets from being committed
├── .gitlab-ci.yml          # CI/CD pipeline definition (THE BRAIN)
├── LICENCE                 # License file
├── README.md               # Project documentation
├── k8s/                    # Kubernetes manifests
│   ├── base/               # Base resources (used everywhere)
│   │   ├── kustomization.yaml  # Ties all resources together
│   │   ├── namespace.yaml      # Creates the namespace
│   │   ├── configmap.yaml      # Application configuration
│   │   ├── deployment.yaml     # The application pods
│   │   └── service.yaml        # Network access to pods
│   └── overlays/           # Environment-specific variations
│       ├── tst/            # Test environment overrides
│       └── prod/           # Production environment overrides
└── templates/              # GitLab CI component templates
    └── my-component.yml    # Reusable CI job template
```

### Git Branches

```
Branches:
├── master                  # Main development (default)
├── tst                     # Test/POC environment
└── prod                    # Production environment (protected)
```

### Why This Structure?

| Directory/File   | Purpose                                                            |
| ---------------- | ------------------------------------------------------------------ |
| `.gitlab-ci.yml` | **Entry point** - GitLab reads this automatically to run pipelines |
| `k8s/base/`      | **Base manifests** - Common Kubernetes resources                   |
| `k8s/overlays/`  | **Environment variations** - Override base for tst/prod            |
| `.gitignore`     | **Security** - Blocks credentials from version control             |
| `tst` branch     | **Test deployments** - POC and integration testing                 |
| `prod` branch    | **Production deployments** - Protected, requires approval          |

---

## 3. File-by-File Deep Dive

### 3.1 `.gitlab-ci.yml` - The Pipeline Definition

**What it is:** The CI/CD pipeline configuration. GitLab reads this file from your repo and executes the defined jobs.

**Location:** Root of the repository (required name!)

```yaml
# ====== VARIABLES SECTION ======
# Define reusable values at the top
variables:
  KUBE_CONTEXT: "apim/poc-aws-shared:eks-nonprod-agent" # Agent reference
  NAMESPACE: "poc-nginx-test" # Where to deploy
  APP_NAME: "nginx" # For selectors
  KUBECTL_IMAGE: "alpine/k8s:1.29.0" # Container for jobs

# ====== WORKFLOW RULES ======
# Control WHEN pipelines run
workflow:
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event" # On MRs
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH # On main branch
    - if: $CI_COMMIT_TAG # On tags
    - when: manual # Or manually

# ====== STAGES ======
# Order of execution (LEFT to RIGHT)
stages:
  - validate # First: Check manifests
  - deploy # Second: Apply to cluster
  - verify # Third: Confirm success
  - cleanup # Fourth: Remove resources
```

**Key Concepts:**

| Concept           | Explanation                                                   |
| ----------------- | ------------------------------------------------------------- |
| `variables:`      | Global values accessible in all jobs via `$VARIABLE_NAME`     |
| `stages:`         | Ordered list of phases. Jobs in same stage run in parallel    |
| `workflow:rules:` | Conditions for when the entire pipeline should run            |
| `KUBE_CONTEXT`    | Format: `<project-path>:<agent-name>` - References your agent |

---

### 3.2 `k8s/base/kustomization.yaml` - The Manifest Orchestrator

**What it is:** Kustomize configuration that ties all Kubernetes resources together.

**Why use Kustomize?** Instead of running `kubectl apply -f file1.yaml -f file2.yaml ...`, you run `kubectl apply -k .` and Kustomize handles everything.

```yaml
---
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

namespace: poc-nginx-test # Apply this namespace to ALL resources

resources: # Files to include (ORDER MATTERS!)
  - namespace.yaml # 1. Create namespace first
  - configmap.yaml # 2. Create config
  - deployment.yaml # 3. Create deployment
  - service.yaml # 4. Create service

commonLabels: # Labels added to ALL resources
  app.kubernetes.io/part-of: poc-aws-shared
  app.kubernetes.io/version: "1.0.0"
```

**Why Order Matters:**

- Namespace must exist before you create resources in it
- ConfigMaps must exist before Deployments that reference them

---

### 3.3 `k8s/base/namespace.yaml` - The Isolation Boundary

**What it is:** Creates a Kubernetes namespace to isolate this application.

```yaml
---
apiVersion: v1
kind: Namespace
metadata:
  name: poc-nginx-test # The namespace name
  labels:
    app.kubernetes.io/name: poc-nginx-test
    app.kubernetes.io/managed-by: gitlab-ci # Indicates how it's managed
    environment: poc # Indicates environment type
```

**Why Namespaces?**

- **Isolation:** Resources in different namespaces don't interfere
- **RBAC:** You can limit access per namespace
- **Cleanup:** Delete namespace = delete everything in it
- **Quotas:** Apply resource limits per namespace

---

### 3.4 `k8s/base/deployment.yaml` - The Application Definition

**What it is:** Defines how your application runs - containers, replicas, health checks.

```yaml
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx
  namespace: poc-nginx-test
  labels:
    app.kubernetes.io/name: nginx # Standard labels
    app.kubernetes.io/instance: poc-test
    app.kubernetes.io/managed-by: gitlab-ci
spec:
  replicas: 2 # Run 2 copies for HA
  selector:
    matchLabels: # How deployment finds its pods
      app.kubernetes.io/name: nginx
      app.kubernetes.io/instance: poc-test
  template:
    metadata:
      labels: # Labels ON the pods
        app.kubernetes.io/name: nginx
        app.kubernetes.io/instance: poc-test
    spec:
      containers:
        - name: nginx
          image: nginx:1.25-alpine # Official nginx image (NOT Bitnami!)
          ports:
            - name: http # Named port
              containerPort: 80
              protocol: TCP
          volumeMounts: # Mount ConfigMap as files
            - name: html
              mountPath: /usr/share/nginx/html
              readOnly: true
          resources: # CPU/Memory limits (ALWAYS SET!)
            requests:
              cpu: 10m # Minimum needed
              memory: 32Mi
            limits:
              cpu: 100m # Maximum allowed
              memory: 64Mi
          livenessProbe: # Is the container alive?
            httpGet:
              path: /
              port: http
            initialDelaySeconds: 5 # Wait before first check
            periodSeconds: 10 # Check every 10s
          readinessProbe: # Is it ready for traffic?
            httpGet:
              path: /
              port: http
            initialDelaySeconds: 3
            periodSeconds: 5
      volumes:
        - name: html # Volume from ConfigMap
          configMap:
            name: nginx-html
```

**Critical Concepts:**

| Concept                | Why It Matters                                                |
| ---------------------- | ------------------------------------------------------------- |
| `replicas: 2`          | High availability - if one pod dies, the other serves traffic |
| `selector.matchLabels` | Must EXACTLY match `template.metadata.labels`                 |
| `resources.requests`   | Scheduler uses this to place pods on nodes                    |
| `resources.limits`     | Prevents runaway processes from killing the node              |
| `livenessProbe`        | Kubernetes restarts pod if probe fails                        |
| `readinessProbe`       | Traffic only sent to pod if probe passes                      |

---

### 3.5 `k8s/base/configmap.yaml` - Application Configuration

**What it is:** Stores configuration data (not secrets!) that pods can use.

```yaml
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: nginx-html
  namespace: poc-nginx-test
  labels:
    app.kubernetes.io/name: nginx
    app.kubernetes.io/component: content # Indicates this is content config
data:
  index.html: | # File name -> content mapping
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <title>EKS POC - GitLab Agent Test</title>
        ...
    </head>
    <body>
        ...
    </body>
    </html>
```

**How It Works:**

1. ConfigMap stores key-value pairs (key = filename, value = content)
2. Deployment mounts ConfigMap as a volume
3. Files appear in the container at the mount path
4. nginx serves files from that directory

**ConfigMap vs Secret:**

| ConfigMap            | Secret                             |
| -------------------- | ---------------------------------- |
| Non-sensitive data   | Sensitive data (passwords, tokens) |
| Stored as plain text | Stored as base64 (not encrypted!)  |
| Visible in logs      | Should never be logged             |

---

### 3.6 `k8s/base/service.yaml` - Network Access

**What it is:** Creates a stable network endpoint to access your pods.

```yaml
---
apiVersion: v1
kind: Service
metadata:
  name: nginx
  namespace: poc-nginx-test
  labels:
    app.kubernetes.io/name: nginx
    app.kubernetes.io/instance: poc-test
spec:
  type: ClusterIP # Internal only (default)
  ports:
    - name: http
      port: 80 # Service listens on this port
      targetPort: http # Forward to pod port named "http"
      protocol: TCP
  selector: # Find pods with these labels
    app.kubernetes.io/name: nginx
    app.kubernetes.io/instance: poc-test
```

**Service Types:**

| Type           | Access                    | Use Case                       |
| -------------- | ------------------------- | ------------------------------ |
| `ClusterIP`    | Internal only             | Default, microservices         |
| `NodePort`     | External via node IP:port | Development, testing           |
| `LoadBalancer` | External via cloud LB     | Production with cloud provider |

**Why Services?**

- Pods get random IPs that change when they restart
- Services provide a stable DNS name: `nginx.poc-nginx-test.svc.cluster.local`
- Services load-balance across all matching pods

---

### 3.7 `.gitignore` - Security Guard

**What it is:** Tells git which files to NEVER commit.

**Why Critical:** Accidentally committing credentials is one of the most common security mistakes!

Our `.gitignore` blocks:

- Environment files (`.env`, `.env.*`)
- Private keys (`*.pem`, `*.key`, `id_rsa*`)
- Tokens (`*token*`, `token.json`)
- Kubernetes secrets (`*-secret.yaml`)
- AWS credentials (`.aws/`, `credentials.csv`)
- Terraform state (`*.tfstate`, `*.tfvars`)
- And much more...

---

## 4. How GitLab Agent Works

### The Architecture

```
┌───────────────────────────────────────────────────────────────┐
│                     GitLab Instance                           │
│                 sdlc.webcloud.ec.europa.eu                    │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │  GitLab KAS (Kubernetes Agent Server)                    │ │
│  │  - Manages agent connections                             │ │
│  │  - Routes CI/CD commands to agents                       │ │
│  └─────────────────────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │  Your Project: apim/poc-aws-shared                       │ │
│  │  - .gitlab-ci.yml (pipeline runs here)                   │ │
│  │  - .gitlab/agents/<name>/config.yaml                     │ │
│  └─────────────────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────────────┘
                           ▲
                           │ gRPC over WebSocket (Outbound!)
                           │
┌───────────────────────────────────────────────────────────────┐
│                       AWS EKS Cluster                         │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │  gitlab-agent namespace                                  │ │
│  │  ┌─────────────────────────────────────────────────────┐│ │
│  │  │  GitLab Agent Pod (agentk)                          ││ │
│  │  │  - Connects TO GitLab (not from!)                   ││ │
│  │  │  - Receives kubectl commands                        ││ │
│  │  │  - Has ServiceAccount with RBAC permissions         ││ │
│  │  └─────────────────────────────────────────────────────┘│ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │  poc-nginx-test namespace (YOUR APPLICATION)            │ │
│  │  - Deployment, Service, ConfigMap created by agent      │ │
│  └─────────────────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────────────┘
```

### Why Outbound Connection?

**Traditional approach (problematic):**

- GitLab needs to reach your cluster
- Requires inbound firewall rules
- Cluster must be publicly accessible

**Agent approach (better):**

- Agent initiates connection FROM cluster TO GitLab
- No inbound rules needed
- Cluster can be completely private
- Works through NAT, proxies, firewalls

---

## 5. Step-by-Step: Create This From Scratch

Follow these steps to create this setup for a NEW project.

### Step 1: Create GitLab Project

1. Go to your GitLab instance
2. Create new project or navigate to existing
3. Clone locally:
   ```bash
   git clone https://sdlc.webcloud.ec.europa.eu/apim/your-project.git
   cd your-project
   ```

### Step 2: Create .gitignore

```bash
# Create comprehensive .gitignore FIRST
# (Copy the one from gitlab-ec/.gitignore)
```

### Step 3: Create Directory Structure

```bash
mkdir -p k8s/base
mkdir -p k8s/overlays/nonprod
mkdir -p k8s/overlays/prod
mkdir -p .gitlab/agents/YOUR-AGENT-NAME
```

### Step 4: Register GitLab Agent

1. In GitLab, go to: **Operate** → **Kubernetes clusters** → **Connect a cluster**
2. Enter agent name (e.g., `eks-nonprod-agent`)
3. **SAVE THE TOKEN IMMEDIATELY** - shown only once!
4. Create agent config file:

```yaml
# .gitlab/agents/eks-nonprod-agent/config.yaml
ci_access:
  projects:
    - id: apim/your-project
      default_namespace: your-app-namespace
      access_as:
        agent: {}
```

### Step 5: Install Agent on EKS

```bash
# Add Helm repo
helm repo add gitlab https://charts.gitlab.io
helm repo update

# Install agent
helm upgrade --install gitlab-agent gitlab/gitlab-agent \
  --namespace gitlab-agent \
  --create-namespace \
  --set config.token=YOUR-TOKEN-HERE \
  --set config.kasAddress=wss://kas.sdlc.webcloud.ec.europa.eu
```

### Step 6: Create Kubernetes Manifests

Create each file in `k8s/base/`:

1. **namespace.yaml** - Your app's namespace
2. **configmap.yaml** - Any configuration
3. **deployment.yaml** - Your application pods
4. **service.yaml** - Network access
5. **kustomization.yaml** - Ties them together

### Step 7: Create .gitlab-ci.yml

Copy and modify the pipeline from this project, updating:

- `KUBE_CONTEXT` - Your project path and agent name
- `NAMESPACE` - Your namespace
- `APP_NAME` - Your app name

### Step 8: Push and Trigger

```bash
git add .
git commit -m "Initial GitLab Agent setup"
git push
```

Pipeline triggers automatically!

---

## 6. Kustomize Explained

### What Is Kustomize?

Kustomize is a Kubernetes configuration management tool that:

- Combines multiple manifest files
- Applies transformations (namespace, labels)
- Supports environment overlays
- Built into kubectl (`kubectl apply -k`)

### Base vs Overlays Pattern

```
k8s/
├── base/                  # Common resources
│   ├── kustomization.yaml
│   ├── deployment.yaml    # replicas: 2
│   └── ...
└── overlays/
    ├── nonprod/
    │   └── kustomization.yaml  # Uses base, changes replicas to 1
    └── prod/
        └── kustomization.yaml  # Uses base, changes replicas to 5
```

**Base kustomization:**

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - namespace.yaml
  - configmap.yaml
  - deployment.yaml
  - service.yaml
```

**Overlay kustomization (nonprod):**

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - ../../base # Reference base
patches:
  - path: replica-patch.yaml # Override replicas
```

**replica-patch.yaml:**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx
spec:
  replicas: 1 # Override to 1 for nonprod
```

### Common Kustomize Commands

```bash
# Preview what will be applied
kubectl kustomize k8s/base

# Apply directly
kubectl apply -k k8s/base

# Apply overlay
kubectl apply -k k8s/overlays/prod
```

---

## 7. Pipeline Stages Explained

### Stage: validate

**Purpose:** Catch errors before deployment

```yaml
validate:manifests:
  stage: validate
  image: $KUBECTL_IMAGE
  script:
    - kubectl kustomize k8s/base --enable-helm # Test manifests are valid
```

**Why?**

- Catches YAML syntax errors
- Catches missing required fields
- Fails fast before deploying broken manifests

```yaml
validate:agent-connectivity:
  stage: validate
  script:
    - kubectl config use-context "$KUBE_CONTEXT" # Switch to agent
    - kubectl cluster-info # Test we can reach cluster
```

**Why?**

- Confirms agent is connected
- Confirms RBAC is working
- Fast feedback before long deployment

### Stage: deploy

**Purpose:** Apply resources to cluster

```yaml
deploy:nonprod:
  stage: deploy
  script:
    - kubectl apply -k k8s/base # Apply all resources
    - kubectl rollout status deployment/$APP_NAME # Wait for completion
  environment:
    name: nonprod
    url: https://nonprod.eks.example.com
    on_stop: cleanup:nonprod # Link to cleanup job
```

**Key concepts:**

- `kubectl apply -k` - Uses Kustomize
- `kubectl rollout status` - Waits for pods to be ready (important!)
- `environment:` - GitLab tracks deployments to this environment

### Stage: verify

**Purpose:** Confirm deployment is healthy

```yaml
verify:deployment:
  stage: verify
  script:
    - kubectl get pods -n $NAMESPACE # List pods
    - kubectl get svc -n $NAMESPACE # List services
    - kubectl exec ... -- wget localhost # Health check
```

**Why?**

- Pods can start but be unhealthy
- Services might not route correctly
- Catches issues missed by rollout status

### Stage: cleanup

**Purpose:** Remove all resources

```yaml
cleanup:nonprod:
  stage: cleanup
  script:
    - kubectl delete -k k8s/base --ignore-not-found=true
  environment:
    name: nonprod
    action: stop # Marks environment stopped
  rules:
    - when: manual # Only run manually
```

---

## 8. Common Patterns to Reuse

### Pattern 1: Multi-Environment Deployment

```yaml
deploy:nonprod:
  variables:
    KUBE_CONTEXT: "project:nonprod-agent"
  environment:
    name: nonprod
  script:
    - kubectl apply -k k8s/overlays/nonprod

deploy:prod:
  variables:
    KUBE_CONTEXT: "project:prod-agent"
  environment:
    name: production
  script:
    - kubectl apply -k k8s/overlays/prod
  when: manual # Require manual approval
```

### Pattern 2: Reusable Job Template

```yaml
.kubectl_base: # Starts with dot = template, not a job
  image: $KUBECTL_IMAGE
  before_script:
    - kubectl config use-context "$KUBE_CONTEXT"

my-job:
  extends: .kubectl_base # Inherit template
  script:
    - kubectl get pods
```

### Pattern 3: Conditional Execution

```yaml
deploy:
  rules:
    - if: $CI_COMMIT_BRANCH == "main" # Only on main branch
    - if: $CI_COMMIT_TAG =~ /^v.*/ # Or on version tags
    - when: never # Otherwise skip
```

---

## 9. Security Best Practices

### Never Commit Secrets

✅ Use `.gitignore` (provided)
✅ Use GitLab CI/CD Variables for secrets
✅ Use Kubernetes Secrets (created by hand or Sealed Secrets)

### Agent Token Management

✅ Store token in GitLab CI/CD Variables (masked!)
✅ Rotate tokens periodically
✅ Use different agents per environment

### RBAC Principle of Least Privilege

```yaml
# .gitlab/agents/<name>/config.yaml
ci_access:
  projects:
    - id: apim/your-project
      default_namespace: your-namespace # Only THIS namespace
      access_as:
        agent: {} # Use agent's ServiceAccount
```

### Network Isolation

- Agent connects outbound (no inbound rules)
- Application in its own namespace
- Use NetworkPolicies to restrict pod-to-pod traffic

---

## 10. Troubleshooting Guide

### Issue: Agent Not Connecting

```bash
# Check agent pod
kubectl get pods -n gitlab-agent
kubectl logs -n gitlab-agent -l app=gitlab-agent --tail=100
```

**Common causes:**

- Token expired/invalid → Regenerate in GitLab
- Wrong KAS address → Check `config.kasAddress`
- Network blocked → Check egress firewall rules

### Issue: Pipeline Fails at kubectl

```
error: context "project:agent" does not exist
```

**Fix:**

1. Verify agent name in GitLab matches `KUBE_CONTEXT`
2. Check agent config file exists: `.gitlab/agents/<name>/config.yaml`

### Issue: Deployment Pending

```bash
kubectl describe pod <pod-name> -n <namespace>
kubectl get events -n <namespace> --sort-by='.lastTimestamp'
```

**Common causes:**

- Resource limits too high → Reduce requests
- Image pull failed → Check image name
- Node selector doesn't match → Check labels

---

## Diagrams

See the `diagrams/` folder for PlantUML diagrams:

- `gitlab-agent-architecture.png` - System architecture
- `gitlab-agent-installation-flow.png` - Step-by-step installation

---

## Summary

| What You Learned         | File/Concept       |
| ------------------------ | ------------------ |
| Pipeline definition      | `.gitlab-ci.yml`   |
| Kubernetes resources     | `k8s/base/*.yaml`  |
| Configuration management | Kustomize          |
| Secure deployments       | GitLab Agent       |
| Environment isolation    | Namespaces         |
| Health monitoring        | Probes             |
| Security                 | `.gitignore`, RBAC |

**Next time you need this:**

1. Copy the `gitlab-ec/` structure
2. Modify variables for your project
3. Register agent in GitLab
4. Install agent on cluster
5. Push and deploy!

---

**Created:** 2026-01-21 | **Author:** Agent | **Status:** Complete Reference Guide
