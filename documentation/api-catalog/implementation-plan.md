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

Branch strategy for this project:

| Branch           | Environment    | Agent                  | Notes                 |
| ---------------- | -------------- | ---------------------- | --------------------- |
| `prod`           | **Production** | `eks-prod-agent` (TBD) | Protected branch      |
| `acc`            | Non-Prod       | `eks-nonprod-agent`    | Current active branch |
| `develop`        | Non-Prod       | `eks-nonprod-agent`    | Default branch        |
| `main`           | Non-Prod       | `eks-nonprod-agent`    | If used               |
| Feature branches | Non-Prod       | `eks-nonprod-agent`    | MR pipelines          |

> [!NOTE]
> **Simple rule**: `prod` branch → Production cluster. Everything else → Non-Prod cluster.

### 2.2 Container Registry Decision

| Option               | Registry                                                           | Notes                        |
| -------------------- | ------------------------------------------------------------------ | ---------------------------- |
| **A** (Keep current) | `code.europa.eu:4567/api-gateway/api-catalogue-backend`            | Requires cross-registry auth |
| **B** (Migrate)      | `sdlc.webcloud.ec.europa.eu:4567/apim/api-catalogue-backend-tests` | Same instance as repo        |

> [!IMPORTANT]
> **Decision Required**: Should we keep using `code.europa.eu` registry or migrate images to `sdlc.webcloud.ec.europa.eu`?

### 2.3 GitLab Agent Configuration

Use the **same agents** as `poc-aws-shared`:

```yaml
variables:
  # Non-prod agent for all branches except prod
  KUBE_CONTEXT_NONPROD: "apim/poc-aws-shared:eks-nonprod-agent"
  # Prod agent only for prod branch (TBD)
  KUBE_CONTEXT_PROD: "apim/poc-aws-shared:eks-prod-agent"
```

**Required**: Update agent config in `poc-aws-shared` to authorize this project:

```yaml
# File: .gitlab/agents/eks-nonprod-agent/config.yaml
ci_access:
  projects:
    - id: apim/poc-aws-shared
    - id: apim/api-catalogue-backend-tests # ADD THIS
```

> [!NOTE]
> Production agent (`eks-prod-agent`) configuration will be defined separately when production deployment is ready.

---

## 3. Pipeline Refactoring Summary

### 3.1 Key Changes

| Aspect            | Current                       | Proposed                                |
| ----------------- | ----------------------------- | --------------------------------------- |
| **Agent**         | Direct kubeconfig             | `apim/poc-aws-shared:eks-nonprod-agent` |
| **Workflow**      | `only:` blocks                | `workflow:rules`                        |
| **Runners**       | Tag-based (`api-catalogue-*`) | Generic runners                         |
| **Stages**        | 6 stages                      | 7 stages (add validate, verify)         |
| **Environments**  | None defined                  | GitLab environments with URLs           |
| **kubectl Image** | (none - uses runner)          | `alpine/k8s:1.29.0`                     |

### 3.2 New Stage Structure

```yaml
stages:
  - setup-ci # Docker build for CI
  - check-lint-format # Linting
  - test # Unit tests
  - build # Docker build + push
  - validate # NEW: Helm validation + agent connectivity
  - deploy # Helm upgrade
  - verify # NEW: Post-deploy checks
```

### 3.3 Environment Configuration

```yaml
deploy:acc:
  environment:
    name: acceptance
    url: https://api-catalogue-acc.shared-services.aws.cloud.tech.ec.europa.eu
    on_stop: cleanup:acc

deploy:prod:
  environment:
    name: production
    url: https://api-catalogue-prod.shared-services.aws.cloud.tech.ec.europa.eu
    on_stop: cleanup:prod
```

---

## 4. Files to Modify

| File                                                          | Action   | Description                                          |
| ------------------------------------------------------------- | -------- | ---------------------------------------------------- |
| `.gitlab-ci.yml`                                              | Refactor | Add agent context, workflow rules, validation stages |
| `poc-aws-shared/.gitlab/agents/eks-nonprod-agent/config.yaml` | Update   | Authorize api-catalogue project                      |
| `helm/values.yaml`                                            | Review   | Verify image repository if changing registry         |

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

### Phase 4: Production Readiness

- [ ] Merge changes to `acc` branch
- [ ] Document rollback procedures
- [ ] Schedule maintenance window if needed

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

1. ~~**Branch Naming**: Keep `acc` or rename to `tst` for consistency?~~ → **Resolved**: Keep `acc`
2. **Registry**: Keep `code.europa.eu` or migrate to `sdlc.webcloud.ec.europa.eu`?
3. **Runner Tags**: Can we remove specific runner tags, or are they required for infrastructure access?
4. **Production Agent**: When will `eks-prod-agent` be configured for production deployments?

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
