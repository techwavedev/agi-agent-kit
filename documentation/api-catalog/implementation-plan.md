# API Catalogue Backend - EKS Migration Implementation Plan

> **Project**: `apim/api-catalogue-backend-tests`  
> **GitLab URL**: `https://sdlc.webcloud.ec.europa.eu/apim/api-catalogue-backend-tests`  
> **Target Environment**: EKS (Non-Prod using same agent as `poc-aws-shared`)  
> **Reference Implementation**: `apim/poc-aws-shared` (`gitlab-ec`)  
> **Status**: Planning Phase - No Deployments  
> **Date**: 2026-01-21

---

## Executive Summary

This document outlines the required changes to align the `api-catalogue-backend-tests` project with the EKS deployment patterns established in `poc-aws-shared`. The objective is to:

1. Use the **same GitLab Agent** (`apim/poc-aws-shared:eks-nonprod-agent`) for Kubernetes access
2. Align the **environment strategy** with `gitlab-ec` (master/tst/prod branches)
3. Update the **container registry** from `code.europa.eu:4567` to `sdlc.webcloud.ec.europa.eu` if needed

> [!CAUTION]
> This is a **live application** with active users. This plan documents what changes are needed - **no deployments will be executed**.

---

## 1. Current State Analysis

### 1.1 Repository Details

| Attribute              | Current Value                                                         |
| ---------------------- | --------------------------------------------------------------------- |
| **GitLab URL**         | `https://sdlc.webcloud.ec.europa.eu/apim/api-catalogue-backend-tests` |
| **Container Registry** | `code.europa.eu:4567/api-gateway/api-catalogue-backend`               |
| **Default Branch**     | `develop` (almost empty - only SAST config)                           |
| **Active Branch**      | `acc` (full application code)                                         |
| **Branches**           | `develop`, `acc`                                                      |
| **Deployment Method**  | Direct `kubectl config use-context`                                   |

### 1.2 Current Pipeline Summary (acc branch)

```yaml
# Current approach - uses direct kubeconfig
stages: [setup-ci, check-lint-format, test, build, deploy-prod, deploy-acc]

deploy-acc:
  script:
    - kubectl config use-context api-catalogue-nonprod # ❌ Direct kubeconfig
    - helm upgrade --install ...
  only:
    - acc
  tags:
    - api-catalogue-acc # ❌ Specific runner
```

### 1.3 Reference: gitlab-ec (poc-aws-shared) Pattern

```yaml
# Target approach - uses GitLab Agent
variables:
  KUBE_CONTEXT: "apim/poc-aws-shared:eks-nonprod-agent" # ✅ Agent tunnel

workflow:
  rules:
    - if: $CI_COMMIT_BRANCH == "master"
    - if: $CI_COMMIT_BRANCH == "tst"
    - if: $CI_COMMIT_BRANCH == "prod"

stages: [validate, deploy, verify, cleanup]

deploy:nonprod:
  extends: .kubectl_base
  script:
    - kubectl config use-context "$KUBE_CONTEXT" # ✅ Uses agent
    - kubectl apply -k k8s/base
  environment:
    name: nonprod
    on_stop: cleanup:nonprod
```

---

## 2. Proposed Changes

### 2.1 Environment Alignment (Confirmed)

Branch strategy for this project (Non-Prod only for now):

| Branch           | Environment | Agent               | Notes                 |
| ---------------- | ----------- | ------------------- | --------------------- |
| `acc`            | Non-Prod    | `eks-nonprod-agent` | Current active branch |
| `develop`        | Non-Prod    | `eks-nonprod-agent` | Default branch        |
| `main`           | Non-Prod    | `eks-nonprod-agent` | If used               |
| Feature branches | Non-Prod    | `eks-nonprod-agent` | MR pipelines          |

> [!NOTE]
> Production deployment (`prod` branch) will be addressed separately in a future phase.

### 2.1.1 Branch-Environment File Isolation

**Each branch should only contain files relevant to its environment.**

| Branch        | Values File                    | Files to REMOVE         |
| ------------- | ------------------------------ | ----------------------- |
| `acc`         | `helm/values-acc.yaml`         | `helm/values-prod.yaml` |
| `develop`     | `helm/values.yaml` (base only) | `helm/values-prod.yaml` |
| Future `prod` | `helm/values-prod.yaml`        | `helm/values-acc.yaml`  |

> [!IMPORTANT]
> **No mixing**: The `acc` branch should NOT contain `values-prod.yaml`. This prevents accidental production deployments and keeps each branch clean.

### 2.2 Container Registry Migration (Confirmed)

Migrate from `code.europa.eu` to `sdlc.webcloud.ec.europa.eu`:

| Aspect       | Current                                                 | New                                                                |
| ------------ | ------------------------------------------------------- | ------------------------------------------------------------------ |
| **Registry** | `code.europa.eu:4567/api-gateway/api-catalogue-backend` | `sdlc.webcloud.ec.europa.eu:4567/apim/api-catalogue-backend-tests` |
| **Login**    | `docker login code.europa.eu:4567`                      | `docker login sdlc.webcloud.ec.europa.eu:4567`                     |
| **Variable** | `REGISTRY_USER` / `REGISTRY_PASSWORD`                   | Update CI/CD variables                                             |

> [!NOTE]
> This aligns the container registry with the same GitLab instance as the repository, simplifying authentication and access control.

### 2.3 GitLab Agent Configuration

Use the **same agent** as `poc-aws-shared`:

```yaml
variables:
  # Non-prod agent for all branches
  KUBE_CONTEXT: "apim/poc-aws-shared:eks-nonprod-agent"
```

**Required**: Update agent config in `poc-aws-shared` to authorize this project:

```yaml
# File: .gitlab/agents/eks-nonprod-agent/config.yaml
ci_access:
  projects:
    - id: apim/poc-aws-shared
    - id: apim/api-catalogue-backend-tests # ADD THIS
```

**Required**: Update agent config in `poc-aws-shared` to authorize this project:

```yaml
# File: .gitlab/agents/eks-nonprod-agent/config.yaml
ci_access:
  projects:
    - id: apim/poc-aws-shared
    - id: apim/api-catalogue-backend-tests # ADD THIS
```

---

## 3. Pipeline Refactoring Summary

### 3.1 Key Insight: Hybrid Runner Approach

The current pipeline has two distinct types of jobs:

| Job Type                                        | Current Runner          | Proposed Runner              | Reason                    |
| ----------------------------------------------- | ----------------------- | ---------------------------- | ------------------------- |
| **CI/Build Jobs** (setup-ci, lint, test, build) | `api-catalogue` tag     | **Keep `api-catalogue` tag** | Requires Docker-in-Docker |
| **Deploy Jobs** (deploy-acc)                    | `api-catalogue-acc` tag | **Switch to GitLab Agent**   | Only needs kubectl        |

> [!IMPORTANT]
> **The build stages MUST keep the `api-catalogue` runner tag** because they require Docker-in-Docker capabilities for building multi-arch images. Only the deploy stages should switch to using the GitLab Agent.

### 3.2 Current vs Proposed - Stage by Stage

#### CI/Build Stages (KEEP EXISTING RUNNER TAGS)

```yaml
# These stages remain largely unchanged - they need Docker-in-Docker
setup-ci:
  tags:
    - api-catalogue # KEEP - needs Docker

check-lint-format:
  tags:
    - api-catalogue # KEEP - needs Docker compose

test:
  tags:
    - api-catalogue # KEEP - needs Docker compose + MongoDB

build:
  tags:
    - api-catalogue # KEEP - needs Docker buildx
```

#### Deploy Stages (CHANGE TO GITLAB AGENT)

```yaml
# Before (current)
deploy-acc:
  script:
    - kubectl config use-context api-catalogue-nonprod # ❌ Direct kubeconfig
  tags:
    - api-catalogue-acc # ❌ Specific runner

# After (proposed)
deploy:acc:
  image: alpine/k8s:1.29.0
  script:
    - kubectl config use-context "$KUBE_CONTEXT_NONPROD" # ✅ GitLab Agent
  # No tags: - uses any runner with agent access
```

### 3.3 Summary of Changes

| Aspect               | Current                       | Proposed                        |
| -------------------- | ----------------------------- | ------------------------------- |
| **CI/Build Runners** | `api-catalogue` tag           | **No change** - keep tag        |
| **Deploy Runners**   | `api-catalogue-acc/prod` tags | **Remove** - use agent          |
| **Deploy Context**   | Direct kubeconfig             | GitLab Agent tunnel             |
| **Workflow**         | `only:` blocks                | `workflow:rules`                |
| **Stages**           | 6 stages                      | 7 stages (add validate, verify) |
| **Environments**     | None defined                  | GitLab environments with URLs   |

### 3.4 New Stage Structure

```yaml
stages:
  - setup-ci # Docker build for CI (KEEP api-catalogue tag)
  - check-lint-format # Linting (KEEP api-catalogue tag)
  - test # Unit tests (KEEP api-catalogue tag)
  - build # Docker build + push (KEEP api-catalogue tag)
  - validate # NEW: Helm validation + agent connectivity (uses agent)
  - deploy # Helm upgrade (uses agent)
  - verify # NEW: Post-deploy checks (uses agent)
```

### 3.5 Environment Configuration

```yaml
deploy:acc:
  image: alpine/k8s:1.29.0 # Uses lightweight kubectl image
  variables:
    KUBE_CONTEXT: $KUBE_CONTEXT
  environment:
    name: acceptance
    url: https://api-catalogue-acc.shared-services.aws.cloud.tech.ec.europa.eu
    on_stop: cleanup:acc
  rules:
    - if: $CI_COMMIT_BRANCH == "acc"
  # No tags: - can run on any runner
```

---

## 4. Files to Modify

| File                                                          | Action     | Description                                                                                     |
| ------------------------------------------------------------- | ---------- | ----------------------------------------------------------------------------------------------- |
| `.gitlab-ci.yml`                                              | Refactor   | Add agent context, workflow rules, validation stages, remove deploy-prod                        |
| `poc-aws-shared/.gitlab/agents/eks-nonprod-agent/config.yaml` | Update     | Authorize api-catalogue project                                                                 |
| `helm/values.yaml`                                            | Update     | Change `image.repository` to `sdlc.webcloud.ec.europa.eu:4567/apim/api-catalogue-backend-tests` |
| `helm/values-prod.yaml`                                       | **Delete** | Remove from `acc` branch (branch-environment isolation)                                         |

### 4.4 Secrets, Variables & Configuration Checklist

#### GitLab CI/CD Variables (Pipeline Level)

Update these in **GitLab → Settings → CI/CD → Variables**:

| Variable              | Current              | Action     | Notes                             |
| --------------------- | -------------------- | ---------- | --------------------------------- |
| `REGISTRY_USER`       | For `code.europa.eu` | **Update** | New registry credentials          |
| `REGISTRY_PASSWORD`   | For `code.europa.eu` | **Update** | New registry credentials (masked) |
| `ACC_SECURITY_GROUPS` | Existing             | **Verify** | ALB security group IDs            |
| `ACC_SUBNETS`         | Existing             | **Verify** | ALB subnet IDs                    |
| `ACC_SSL_CERT_ARN`    | Existing             | **Verify** | ACM certificate ARN               |

#### Kubernetes Secrets (Cluster Level)

These secrets must exist in the `api-catalog` namespace:

| Secret Name             | Purpose                   | Action            |
| ----------------------- | ------------------------- | ----------------- |
| `api-catalogue-secrets` | App environment variables | **Verify exists** |
| `mongodb-certificate`   | MongoDB TLS certificate   | **Verify exists** |

**Contents of `api-catalogue-secrets`:**

```yaml
# Required environment variables in the K8s secret:
MONGODB_URI: "mongodb://..."
AUTH_TRUSTED_ISSUERS: "[...]"
IMPORT_SCRIPT_TOKEN: "..."
WSO2_SERVICES_APIKEY: "..."
APIM_SERVICE_URL: "..."
APIM_EXTRA_CLIENT_ID: "..."
APIM_EXTRA_CLIENT_SECRET: "..."
APIM_INTRA_CLIENT_ID: "..."
APIM_INTRA_CLIENT_SECRET: "..."
KIBANA_SERVICE_URL: "..."
KIBANA_APIKEY: "..."
CONSUL_SERVICE_URL: "..."
CONSUL_TOKEN: "..."
FCP_SERVICE_URL: "..."
```

#### ServiceAccount & IRSA

| Config                                                  | Location            | Action                         |
| ------------------------------------------------------- | ------------------- | ------------------------------ |
| `serviceAccount.annotations.eks.amazonaws.com/role-arn` | `helm/values*.yaml` | **Verify** IAM role ARN is set |

#### Container Images

| Image                  | Current                                                 | New                                                                | Action                        |
| ---------------------- | ------------------------------------------------------- | ------------------------------------------------------------------ | ----------------------------- |
| **Application**        | `code.europa.eu:4567/api-gateway/api-catalogue-backend` | `sdlc.webcloud.ec.europa.eu:4567/apim/api-catalogue-backend-tests` | **Update** in pipeline & Helm |
| **Base (Dockerfile)**  | `node:20` / `node:20-alpine`                            | No change                                                          | ✅ Compliant                  |
| **kubectl (Pipeline)** | N/A                                                     | `alpine/k8s:1.29.0`                                                | **Add** for deploy jobs       |

#### Helm Values Files

| File                    | Key Settings                          | Action                                       |
| ----------------------- | ------------------------------------- | -------------------------------------------- |
| `helm/values.yaml`      | `image.repository`, `secretsConfig.*` | **Update** registry                          |
| `helm/values-acc.yaml`  | `ingress.hostname`, `resources`       | **Verify**                                   |
| `helm/values-prod.yaml` | N/A                                   | **Delete** from `acc` branch (env isolation) |

---

## 5. Implementation Phases

### Phase 1: Agent Authorization (No Risk)

- [ ] Update agent config in `poc-aws-shared` to authorize this project
- [ ] Verify agent access from CI pipeline (read-only test)

### Phase 2: Pipeline Refactoring (Branch-Level)

- [ ] Create feature branch from `acc`
- [ ] Update `.gitlab-ci.yml` with new structure
- [ ] Test pipeline execution (validation stages only)

### Phase 3: Deployment Testing

- [ ] Run `helm upgrade --dry-run` in pipeline
- [ ] Verify environment visibility in GitLab UI
- [ ] Test agent connectivity to EKS cluster

### Phase 4: Finalization

- [ ] Merge changes to `acc` branch
- [ ] Delete `helm/values-prod.yaml` from `acc` branch (branch-environment isolation)
- [ ] Document rollback procedures

---

## 6. Verification Plan

Since this is a **live application**, verification will be done without actual deployment:

### 6.1 Agent Connectivity Test

```bash
# Run in pipeline validation job
kubectl config use-context "apim/poc-aws-shared:eks-nonprod-agent"
kubectl cluster-info
kubectl get namespace api-catalog
```

### 6.2 Helm Template Validation

```bash
# Validate chart renders correctly
helm template api-catalogue ./helm -f ./helm/values-acc.yaml --debug
```

### 6.3 Dry-Run Deployment

```bash
# Verify what would change without applying
helm upgrade --install api-catalogue ./helm \
  --namespace api-catalog \
  -f ./helm/values-acc.yaml \
  --dry-run
```

---

## 7. Open Questions

1. ~~**Branch Naming**: Keep `acc` or rename?~~ → **Resolved**: Keep `acc`
2. ~~**Registry**: Keep `code.europa.eu` or migrate?~~ → **Resolved**: Migrate to `sdlc.webcloud.ec.europa.eu`
3. ~~**Runner Tags**: Can we remove specific runner tags?~~ → **Resolved**: Hybrid approach - keep for CI/Build, remove for deploy
4. ~~**Production deployment**~~ → **Deferred**: Will be addressed in a future phase

---

## 8. Risk Assessment

| Risk                           | Likelihood | Impact | Mitigation                                 |
| ------------------------------ | ---------- | ------ | ------------------------------------------ |
| Agent authorization fails      | Low        | High   | Test in POC project first                  |
| Pipeline syntax errors         | Medium     | Low    | Validate YAML locally                      |
| Registry authentication issues | Low        | Medium | Keep existing registry initially           |
| Deployment breaks live app     | Low        | High   | Use `--dry-run` exclusively until verified |

---

## Next Steps

1. **Review this plan** and provide feedback on open questions
2. **Authorize agent** in `poc-aws-shared` project
3. **Create feature branch** for pipeline changes
4. **Execute Phase 1-3** with dry-run mode only
