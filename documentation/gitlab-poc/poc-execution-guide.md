# POC Execution Guide: nginx EKS Deployment Test

> Step-by-step guide for executing the GitLab Agent POC on EKS Non-Prod

## POC Objectives

| #   | Objective                        | Validation                               |
| --- | -------------------------------- | ---------------------------------------- |
| 1   | Verify GitLab Agent connectivity | `validate:agent-connectivity` job passes |
| 2   | Test pipeline runners            | Jobs execute successfully                |
| 3   | Deploy to EKS via kubectl        | nginx pods running in cluster            |
| 4   | Confirm rollout and health       | Pods ready, endpoints active             |
| 5   | Clean up test resources          | Namespace removed cleanly                |

---

## Prerequisites Checklist

Before starting the POC:

- [ ] GitLab Agent installed on EKS Non-Prod cluster
- [ ] Agent connected to `sdlc.webcloud.ec.europa.eu`
- [ ] Agent token configured and active
- [ ] `.gitlab/agents/<agent-name>/config.yaml` committed to repo
- [ ] `KUBE_CONTEXT` in `.gitlab-ci.yml` matches agent name

---

## Execution Steps

### Step 1: Clone and Configure Locally

```bash
# Clone the project (already done)
cd /Users/elton/Library/CloudStorage/SynologyDrive-MacbookM3/gitlab-ec

# Verify files
ls -la k8s/base/
```

**Expected:** 5 YAML files (namespace, configmap, deployment, service, kustomization)

---

### Step 2: Update Agent Context (if needed)

Edit `.gitlab-ci.yml` line 14:

```yaml
KUBE_CONTEXT: "apim/poc-aws-shared:eks-nonprod-agent"
#                 └── project path ──┘:└── agent name ──┘
```

⚠️ **Important:** The agent name must exactly match what's registered in GitLab.

---

### Step 3: Commit and Push

```bash
# Add all new files
git add -A

# Commit with descriptive message
git commit -m "feat: Add nginx POC for EKS deployment testing

- Add k8s/base/ manifests (namespace, deployment, service, configmap)
- Update .gitlab-ci.yml with deploy pipeline
- Add kustomize configuration"

# Push to trigger pipeline
git push origin main
```

---

### Step 4: Monitor Pipeline

1. Open GitLab: `https://sdlc.webcloud.ec.europa.eu/apim/poc-aws-shared/-/pipelines`
2. Click on the running pipeline
3. Watch each stage complete:

| Stage      | Expected Duration | Success Criteria         |
| ---------- | ----------------- | ------------------------ |
| `validate` | ~30s              | Green checkmarks         |
| `deploy`   | ~60s              | "Deployment successful!" |
| `verify`   | ~30s              | Pod status shows 2/2     |

---

### Step 5: Verify Deployment Manually

After pipeline succeeds, verify from local machine:

```bash
# Switch to non-prod context
kubectl config use-context <your-nonprod-context>

# Check namespace created
kubectl get ns poc-nginx-test

# Check pods running
kubectl get pods -n poc-nginx-test
# Expected:
# NAME                    READY   STATUS    RESTARTS   AGE
# nginx-xxxxxxx-xxxxx     1/1     Running   0          1m
# nginx-xxxxxxx-xxxxx     1/1     Running   0          1m

# Check service
kubectl get svc -n poc-nginx-test
# Expected:
# NAME    TYPE        CLUSTER-IP     EXTERNAL-IP   PORT(S)   AGE
# nginx   ClusterIP   10.x.x.x       <none>        80/TCP    1m

# Test nginx response
kubectl port-forward -n poc-nginx-test svc/nginx 8080:80 &
curl http://localhost:8080 | head -10
# Expected: HTML content with "GitLab Agent POC"

# Stop port-forward
pkill -f "port-forward.*poc-nginx-test"
```

---

### Step 6: Review Results

**✅ POC Success Criteria:**

| Check           | How to Verify                     | Status |
| --------------- | --------------------------------- | ------ |
| Agent connected | Pipeline runs without auth errors | ☐      |
| kubectl works   | Manifests applied successfully    | ☐      |
| Pods healthy    | 2/2 Running, 0 restarts           | ☐      |
| Service active  | Endpoints populated               | ☐      |
| HTML served     | Custom page displays              | ☐      |

---

### Step 7: Cleanup (Optional)

Run the cleanup job manually from GitLab:

1. Go to pipeline page
2. Click on `cleanup:nonprod` job
3. Click **"Run"** (it's manual)
4. Wait for completion

Or cleanup manually:

```bash
kubectl delete ns poc-nginx-test
```

---

## Troubleshooting During POC

### Pipeline Stuck at "Pending"

**Cause:** No runners available

**Solution:**

1. Check if GitLab runners are registered for the project
2. Verify runner tags match job requirements

### `KUBE_CONTEXT` Error

**Cause:** Agent name mismatch

**Solution:**

```bash
# Check registered agents in GitLab
# Operate → Kubernetes clusters → View agents
# Copy exact agent name and update .gitlab-ci.yml
```

### Deployment Timeout

**Cause:** Image pull issues or resource constraints

**Solution:**

```bash
# Check pod events
kubectl describe pod -n poc-nginx-test -l app.kubernetes.io/name=nginx

# Check node resources
kubectl top nodes
```

### Pods in CrashLoopBackOff

**Cause:** Container startup failure

**Solution:**

```bash
# Check pod logs
kubectl logs -n poc-nginx-test -l app.kubernetes.io/name=nginx
```

---

## Recording Results

After completing the POC, document results:

| Metric                  | Value               |
| ----------------------- | ------------------- |
| **Date**                | 2026-01-21          |
| **Agent Name**          | `eks-nonprod-agent` |
| **Pipeline Run**        | `#___`              |
| **Total Duration**      | `___` minutes       |
| **All Jobs Passed**     | Yes / No            |
| **Manual Verification** | Yes / No            |
| **Issues Encountered**  | None / List         |

---

## Next Steps After Successful POC

1. **Document agent configuration** for team reference
2. **Configure prod agent** following same pattern
3. **Add env-specific overlays** (`k8s/overlays/nonprod/`, `k8s/overlays/prod/`)
4. **Set up Ingress** for external access if needed
5. **Integrate with existing GitOps** (Flux) workflow

---

**POC Owner:** Elton | **Environment:** Non-Prod Only | **Status:** Ready for Execution
