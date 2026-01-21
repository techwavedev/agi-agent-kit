# API Catalogue Backend - EKS Migration Implementation Plan

> **Project**: `apim/api-catalogue-backend-tests`  
> **Target Environment**: EKS (Non-Prod/Prod)  
> **Reference Implementation**: `apim/poc-aws-shared` (`gitlab-ec`)  
> **Status**: Documentation Phase (No Deployments)  
> **Date**: 2026-01-21

---

## Executive Summary

This document outlines the required changes to align the `api-catalogue-backend-tests` project with the EKS deployment patterns established in the `poc-aws-shared` project. The objective is to leverage the **GitLab Agent for Kubernetes** instead of direct `kubectl` context switching, while preserving the existing application functionality.

> **CRITICAL**: This is a live application with active users. All changes should be validated with dry-run modes before any deployment is executed.

---

## 1. Current State Analysis

### 1.1 Repository Structure (acc branch)

```text
api-catalogue-backend-tests/
├── .gitlab-ci.yml          # Current pipeline (needs refactoring)
├── Dockerfile              # Multi-stage build (ci, build, prod)
├── docker-compose.yml      # Local development
├── docker-compose.ci.yml   # CI testing with MongoDB
├── helm/                   # Helm chart for Kubernetes deployment
│   ├── Chart.yaml
│   ├── values.yaml         # Base values
│   ├── values-acc.yaml     # Acceptance environment
│   ├── values-prod.yaml    # Production environment
│   └── templates/
│       ├── deployment.yaml
│       ├── service.yaml
│       ├── ingress.yaml
│       ├── hpa.yaml
│       ├── import-cronjob.yaml
│       └── serviceaccount.yaml
├── src/                    # Application source
├── test/                   # Test suites
└── docs/                   # Documentation
```

### 1.2 Current Pipeline Issues

The current `.gitlab-ci.yml` has the following problems:

| Issue                      | Description                                                                            | Impact                                         |
| -------------------------- | -------------------------------------------------------------------------------------- | ---------------------------------------------- |
| **Direct kubectl context** | Uses `kubectl config use-context api-catalogue-prod`                                   | Requires runner-level kubeconfig, not portable |
| **No GitLab Agent**        | Pipeline doesn't use GitLab Agent tunnel                                               | Missing centralized access control             |
| **Tag-based runners**      | Uses specific runner tags (`api-catalogue`, `api-catalogue-prod`, `api-catalogue-acc`) | Tight coupling to infrastructure               |
| **No workflow rules**      | Uses `only:` instead of `workflow:rules`                                               | Outdated GitLab CI syntax                      |
| **No validation stage**    | Missing manifest validation before deploy                                              | Risk of invalid deployments                    |
| **No dry-run option**      | Direct `helm upgrade --install` without validation                                     | Risk of accidental changes                     |

### 1.3 Current Branches

| Branch    | Purpose                                             |
| --------- | --------------------------------------------------- |
| `develop` | Default branch (minimal content - only SAST config) |
| `acc`     | Acceptance environment with full application code   |

**Note**: The `develop` branch appears to be almost empty (only GitLab security scanning config), while `acc` contains the actual application.

---

## 2. Required Changes

### 2.1 Pipeline Refactoring (.gitlab-ci.yml)

The pipeline needs to be updated to use the GitLab Agent for Kubernetes pattern:

#### 2.1.1 Add KUBE_CONTEXT Variable

```yaml
variables:
  # GitLab Agent configuration
  # Format: path/to/agent/project:agent-name
  KUBE_CONTEXT_NONPROD: "apim/poc-aws-shared:eks-nonprod-agent"
  KUBE_CONTEXT_PROD: "apim/poc-aws-shared:eks-prod-agent"

  # Existing variables (keep these)
  GITLAB_REGISTRY: "code.europa.eu:4567/api-gateway/api-catalogue-backend"
```

#### 2.1.2 Add Workflow Rules

Replace `only:` blocks with proper workflow rules:

```yaml
workflow:
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    - if: $CI_COMMIT_BRANCH == "main"
    - if: $CI_COMMIT_BRANCH == "acc"
    - if: $CI_COMMIT_BRANCH == "develop"
    - if: $CI_COMMIT_TAG
```

#### 2.1.3 Add kubectl Base Template

```yaml
.kubectl_base:
  image: alpine/k8s:1.29.0 # No Bitnami policy
  before_script:
    - echo "Configuring kubectl with GitLab Agent..."
    - kubectl config use-context "$KUBE_CONTEXT"
    - kubectl config current-context
    - echo "kubectl configured successfully"
```

#### 2.1.4 Add Validation Stage

```yaml
validate:manifests:
  stage: validate
  image: alpine/k8s:1.29.0
  script:
    - echo "Validating Helm chart..."
    - helm template api-catalogue ./helm -f ./helm/values-acc.yaml --debug
    - echo "Manifests are valid"
  rules:
    - if: $CI_COMMIT_BRANCH == "acc"
    - if: $CI_COMMIT_BRANCH == "main"
    - when: manual

validate:agent-connectivity:
  stage: validate
  extends: .kubectl_base
  variables:
    KUBE_CONTEXT: $KUBE_CONTEXT_NONPROD
  script:
    - echo "Testing GitLab Agent connectivity..."
    - kubectl cluster-info
    - kubectl get nodes --no-headers | head -3
    - echo "Agent connectivity verified"
  rules:
    - if: $CI_COMMIT_BRANCH == "acc"
    - when: manual
```

#### 2.1.5 Refactor Deploy Jobs

**Before (current):**

```yaml
deploy-acc:
  stage: deploy-acc
  script:
    - kubectl config use-context api-catalogue-nonprod # Direct kubeconfig
    - helm upgrade --install ...
  only:
    - acc
  tags:
    - api-catalogue-acc # Specific runner
```

**After (new pattern):**

```yaml
deploy:acc:
  stage: deploy
  extends: .kubectl_base
  variables:
    KUBE_CONTEXT: $KUBE_CONTEXT_NONPROD
  needs:
    - build
    - validate:manifests
  script:
    - export VERSION=$(cat VERSION.txt)
    - echo "Deploying version $VERSION to nonprod cluster"
    - |
      helm upgrade --install api-catalogue ./helm \
        --namespace api-catalog \
        --set image.tag=${VERSION} \
        --set ingress.securityGroups=${ACC_SECURITY_GROUPS} \
        --set ingress.subnets="${ACC_SUBNETS}" \
        --set ingress.certificateArn=${ACC_SSL_CERT_ARN} \
        -f ./helm/values-acc.yaml
    - kubectl -n api-catalog wait --for=condition=available --timeout=300s deployment/api-catalogue
  environment:
    name: acceptance
    url: https://api-catalogue-acc.shared-services.aws.cloud.tech.ec.europa.eu
  rules:
    - if: $CI_COMMIT_BRANCH == "acc"
    - when: manual
```

### 2.2 GitLab Agent Configuration

The project needs to be **authorized** to use the GitLab Agent registered in `apim/poc-aws-shared`.

#### 2.2.1 Update Agent Configuration

In the `apim/poc-aws-shared` repository, update the agent config file:

**File**: `.gitlab/agents/eks-nonprod-agent/config.yaml`

```yaml
ci_access:
  projects:
    - id: apim/poc-aws-shared
    - id: apim/api-catalogue-backend-tests # Add this line
```

Similarly for `eks-prod-agent` if production access is needed.

### 2.3 Stage Reorganization

**Current stages (6):**

```yaml
stages:
  - setup-ci
  - check-lint-format
  - test
  - build
  - deploy-prod
  - deploy-acc
```

**Recommended stages (7):**

```yaml
stages:
  - setup-ci
  - check-lint-format
  - test
  - build
  - validate # NEW: manifest validation
  - deploy # RENAMED: unified deploy stage
  - verify # NEW: post-deployment verification
```

---

## 3. Image Standards Alignment

### 3.1 No Bitnami Policy

| Current Usage           | Replacement         | Location                           |
| ----------------------- | ------------------- | ---------------------------------- |
| N/A (already compliant) | N/A                 | Dockerfile uses official `node:20` |
| N/A                     | `alpine/k8s:1.29.0` | Pipeline kubectl jobs              |

The project is already using official Node.js images, which is compliant with the "No Bitnami" policy.

---

## 4. Environment Variables Required

The following CI/CD variables must be configured in GitLab (Settings > CI/CD > Variables):

| Variable               | Environment | Description                       |
| ---------------------- | ----------- | --------------------------------- |
| `ACC_SECURITY_GROUPS`  | acc         | Security group IDs for ALB        |
| `ACC_SUBNETS`          | acc         | Subnet IDs for ALB                |
| `ACC_SSL_CERT_ARN`     | acc         | ACM certificate ARN               |
| `PROD_SECURITY_GROUPS` | prod        | Security group IDs for ALB        |
| `PROD_SUBNETS`         | prod        | Subnet IDs for ALB                |
| `PROD_SSL_CERT_ARN`    | prod        | ACM certificate ARN               |
| `REGISTRY_USER`        | all         | Docker registry username          |
| `REGISTRY_PASSWORD`    | all         | Docker registry password (masked) |

---

## 5. Deployment Safety Checklist

Since this is a **live application**, implement these safety measures:

### 5.1 Pre-Deployment Validation

```bash
# Local validation before pushing
helm template api-catalogue ./helm -f ./helm/values-acc.yaml | kubectl apply --dry-run=server -f -
```

### 5.2 Pipeline Dry-Run Stage (Optional Enhancement)

```yaml
deploy:acc:dry-run:
  stage: validate
  extends: .kubectl_base
  variables:
    KUBE_CONTEXT: $KUBE_CONTEXT_NONPROD
  script:
    - export VERSION=$(cat VERSION.txt)
    - |
      helm upgrade --install api-catalogue ./helm \
        --namespace api-catalog \
        --set image.tag=${VERSION} \
        -f ./helm/values-acc.yaml \
        --dry-run
  rules:
    - if: $CI_COMMIT_BRANCH == "acc"
```

### 5.3 Rollback Procedure

Document the rollback command for operators:

```bash
# Rollback to previous release
helm rollback api-catalogue -n api-catalog

# Or rollback to specific revision
helm history api-catalogue -n api-catalog
helm rollback api-catalogue <REVISION> -n api-catalog
```

---

## 6. Implementation Steps

### Phase 1: Preparation (No Deployment Risk)

1. [ ] **Fork/Branch Strategy**: Create a feature branch from `acc` for pipeline changes
2. [ ] **Agent Authorization**: Update `poc-aws-shared` agent config to allow this project
3. [ ] **Validate Agent Access**: Test agent connectivity manually

### Phase 2: Pipeline Refactoring

4. [ ] **Update `.gitlab-ci.yml`**: Apply all changes from Section 2.1
5. [ ] **Add Workflow Rules**: Replace `only:` with `rules:`
6. [ ] **Add Validation Stage**: Include manifest validation job
7. [ ] **Update Deploy Jobs**: Use GitLab Agent context

### Phase 3: Testing

8. [ ] **Run Validation Jobs**: Execute pipeline with manual triggers
9. [ ] **Test Agent Connectivity**: Verify `kubectl cluster-info` works
10. [ ] **Dry-Run Deployment**: Run Helm with `--dry-run` flag

### Phase 4: Production Readiness

11. [ ] **Merge to acc**: After successful validation
12. [ ] **Monitor Deployment**: Watch pod rollout status
13. [ ] **Update Documentation**: Add runbook for new pipeline

---

## 7. Files to Modify

| File                                                          | Action                         | Priority |
| ------------------------------------------------------------- | ------------------------------ | -------- |
| `.gitlab-ci.yml`                                              | Refactor                       | HIGH     |
| `poc-aws-shared/.gitlab/agents/eks-nonprod-agent/config.yaml` | Add project authorization      | HIGH     |
| `helm/values-acc.yaml`                                        | Verify values                  | MEDIUM   |
| `helm/values-prod.yaml`                                       | Verify values                  | MEDIUM   |
| `README.md`                                                   | Update deployment instructions | LOW      |

---

## 8. Reference: Complete Refactored Pipeline

See: [refactored-gitlab-ci.yml](./refactored-gitlab-ci.yml)

---

## 9. Comparison Summary

| Aspect                | Current (api-catalogue)       | Target (poc-aws-shared pattern) |
| --------------------- | ----------------------------- | ------------------------------- |
| **Deployment Method** | Direct kubeconfig             | GitLab Agent tunnel             |
| **Runner Coupling**   | Tag-based (`api-catalogue-*`) | Generic runners                 |
| **CI Syntax**         | `only:` blocks                | `workflow:rules`                |
| **Validation**        | None                          | Manifest + agent connectivity   |
| **Image Policy**      | Official Node.js              | Compliant                       |
| **Helm Usage**        | Direct upgrade                | With dry-run option             |
| **Rollback**          | Manual                        | Documented procedure            |

---

## 10. Next Steps

1. Review this implementation plan
2. Confirm agent authorization approach with platform team
3. Create feature branch for pipeline changes
4. Execute Phase 1-3 in sequence
5. Schedule maintenance window for Phase 4 if needed

---

## Appendix A: Agent Authorization Request Template

To request access to the GitLab Agent, send this to the `poc-aws-shared` maintainers:

```
Subject: Request GitLab Agent Access for api-catalogue-backend-tests

Project Path: apim/api-catalogue-backend-tests
Agent Required: eks-nonprod-agent (and eks-prod-agent for production)
Access Level: CI/CD pipeline deployment
Namespace: api-catalog

Justification: Migrating from direct kubeconfig to GitLab Agent pattern
for improved security and access control.
```
