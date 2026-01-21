# GitLab Agent Troubleshooting

Troubleshooting guide for GitLab Agent for Kubernetes from a **project owner/operator perspective** — focusing on cluster-side diagnostics and fixes you can perform without GitLab server admin access.

---

## Quick Diagnostics

### First Steps

```bash
# 1. Check agent pod status
kubectl get pods -n gitlab-agent

# 2. View agent logs (most issues show here)
kubectl logs -f -l=app.kubernetes.io/name=gitlab-agent -n gitlab-agent

# 3. Check events for errors
kubectl get events -n gitlab-agent --sort-by='.lastTimestamp'

# 4. Describe pod for detailed status
kubectl describe pod -l=app.kubernetes.io/name=gitlab-agent -n gitlab-agent
```

### Agent Status in GitLab UI

Navigate to: **Project → Operate → Kubernetes clusters**

- ✅ **Connected** — Agent is healthy
- ⚠️ **Never connected** — Token or network issue
- ❌ **Not connected** — Agent was connected but lost connection

---

## Connection Issues

### Error: "failed to WebSocket dial"

**Symptom in logs:**

```json
{
  "level": "warn",
  "msg": "GetConfiguration failed",
  "error": "transport: Error while dialing failed to WebSocket dial: ... no such host"
}
```

**Causes & Solutions:**

| Cause                   | Solution                                           |
| ----------------------- | -------------------------------------------------- |
| Wrong KAS address       | Verify `config.kasAddress` in Helm values          |
| DNS resolution failure  | Check cluster DNS, verify GitLab hostname resolves |
| Network policy blocking | Allow egress to GitLab on port 443                 |
| Proxy/Firewall blocking | Whitelist GitLab host, allow WebSocket upgrade     |

**Fix:**

```bash
# Verify DNS from cluster
kubectl run dns-test --rm -it --restart=Never --image=busybox -- \
  nslookup gitlab.example.com

# Test connectivity
kubectl run curl-test --rm -it --restart=Never --image=curlimages/curl -- \
  curl -v "https://gitlab.example.com/-/kubernetes-agent/"

# Check/update Helm values
helm get values gitlab-agent -n gitlab-agent
```

---

### Error: "HTTP 301" on Handshake

**Symptom in logs:**

```json
{
  "error": "expected handshake response status code 101 but got 301"
}
```

**Cause:** Missing trailing slash in KAS address.

**Fix:**

```bash
# WRONG
--set config.kasAddress="wss://gitlab.example.com/-/kubernetes-agent"

# CORRECT (with trailing slash)
--set config.kasAddress="wss://gitlab.example.com/-/kubernetes-agent/"
```

```bash
helm upgrade gitlab-agent gitlab/gitlab-agent \
  --namespace gitlab-agent \
  --reuse-values \
  --set config.kasAddress="wss://gitlab.example.com/-/kubernetes-agent/"
```

---

### Error: "certificate signed by unknown authority"

**Symptom in logs:**

```json
{
  "error": "x509: certificate signed by unknown authority"
}
```

**Cause:** GitLab uses a self-signed certificate or internal CA that the agent doesn't trust.

**Fix:**

```bash
# 1. Get the CA certificate from GitLab
openssl s_client -connect gitlab.example.com:443 -showcerts </dev/null 2>/dev/null | \
  openssl x509 -outform PEM > gitlab-ca.pem

# 2. Verify it's the right cert
openssl x509 -in gitlab-ca.pem -text -noout | head -20

# 3. Reinstall agent with CA
helm upgrade --install gitlab-agent gitlab/gitlab-agent \
  --namespace gitlab-agent \
  --set config.token="${AGENT_TOKEN}" \
  --set config.kasAddress="wss://gitlab.example.com/-/kubernetes-agent/" \
  --set-file config.kasCaCert=./gitlab-ca.pem
```

**Verify CA is mounted:**

```bash
kubectl get configmap -l=app=gitlab-agent -n gitlab-agent -o yaml | grep -A20 "ca.crt"
```

---

### Error: "Decompressor not installed for grpc-encoding"

**Symptom in logs:**

```json
{
  "error": "grpc: Decompressor is not installed for grpc-encoding \"gzip\""
}
```

**Cause:** Agent version is newer than KAS server version.

**Fix:** Downgrade agent to match GitLab version:

```bash
# Check current agent version
kubectl get deployment gitlab-agent -n gitlab-agent -o jsonpath='{.spec.template.spec.containers[0].image}'

# Ask GitLab admin for GitLab version, or check in GitLab UI (Help → GitLab version)
# Agent should match major.minor version

helm upgrade gitlab-agent gitlab/gitlab-agent \
  --namespace gitlab-agent \
  --reuse-values \
  --set image.tag=v17.6.0  # Match your GitLab version
```

---

## Authentication Issues

### Error: "Failed to register agent pod"

**Symptom in logs:**

```json
{
  "msg": "Failed to register agent pod. Please make sure the agent version matches the server version"
}
```

**Causes:**

1. Version mismatch between agent and GitLab
2. Invalid or expired token
3. KAS service not running (GitLab server issue)

**Fixes you can try:**

```bash
# 1. Verify token is active via API
curl --header "PRIVATE-TOKEN: ${GITLAB_TOKEN}" \
  "https://${GITLAB_HOST}/api/v4/projects/${PROJECT_ID}/cluster_agents/${AGENT_ID}/tokens" | jq

# 2. Create new token if needed
NEW_TOKEN=$(curl --silent --request POST \
  --header "PRIVATE-TOKEN: ${GITLAB_TOKEN}" \
  --header "Content-Type: application/json" \
  --url "https://${GITLAB_HOST}/api/v4/projects/${PROJECT_ID}/cluster_agents/${AGENT_ID}/tokens" \
  --data '{"name":"refresh-token"}' | jq -r '.token')

# 3. Update agent with new token
helm upgrade gitlab-agent gitlab/gitlab-agent \
  --namespace gitlab-agent \
  --reuse-values \
  --set config.token="${NEW_TOKEN}"

# 4. Match agent version to GitLab
helm upgrade gitlab-agent gitlab/gitlab-agent \
  --namespace gitlab-agent \
  --reuse-values \
  --set image.tag=v17.6.0
```

**If still failing:** Contact GitLab admin to verify KAS is running:

```bash
# GitLab admin command (not accessible to project owners)
gitlab-ctl status gitlab-kas
```

---

### Agent Shows "Never Connected" in UI

**Checklist:**

- [ ] Token was created and saved correctly
- [ ] Token is active (not revoked): Check via API
- [ ] Helm install completed successfully
- [ ] Pod is Running: `kubectl get pods -n gitlab-agent`
- [ ] No errors in logs: `kubectl logs -f -l=app.kubernetes.io/name=gitlab-agent -n gitlab-agent`
- [ ] Network allows outbound to GitLab on 443

**Debug:**

```bash
# Check pod status
kubectl get pods -n gitlab-agent -o wide

# Check for crashloops
kubectl describe pod -l=app.kubernetes.io/name=gitlab-agent -n gitlab-agent | grep -A5 "State:"

# Verify token in secret
kubectl get secret -n gitlab-agent gitlab-agent-token -o jsonpath='{.data.token}' | base64 -d
```

---

## CI/CD Issues

### Error: "kubectl config use-context: context not found"

**Symptom in pipeline:**

```
error: no context exists with the name: "my-project/my-agent:agent-name"
```

**Causes:**

1. Agent name mismatch
2. Project path format incorrect
3. CI/CD access not configured

**Fix:**

```bash
# 1. List available contexts in pipeline
kubectl config get-contexts

# 2. Use correct format: <path/with/namespace>:<agent-name>
kubectl config use-context "group/project:eks-nonprod-agent"
```

**Configure CI/CD access in agent config:**

```yaml
# .gitlab/agents/eks-nonprod-agent/config.yaml
ci_access:
  projects:
    - id: path/to/your/project
  groups:
    - id: path/to/your/group
```

---

### Error: "x509: certificate signed by unknown authority" in Pipeline

**Symptom:** kubectl commands fail in CI/CD with certificate errors.

**Fix:** Configure KAS CA in gitlab-ci.yml:

```yaml
deploy:
  image: bitnami/kubectl:latest
  before_script:
    # Trust the GitLab CA
    - echo "$KUBE_CA_CERT" > /tmp/gitlab-ca.crt
    - export SSL_CERT_FILE=/tmp/gitlab-ca.crt
  script:
    - kubectl config use-context path/to/project:agent-name
    - kubectl get pods
  variables:
    KUBE_CA_CERT: |
      -----BEGIN CERTIFICATE-----
      ... your CA certificate ...
      -----END CERTIFICATE-----
```

Or use a CI/CD variable for the certificate:

1. Go to **Project → Settings → CI/CD → Variables**
2. Add `KUBE_CA_CERT` with the CA certificate content
3. Set as "File" type

---

### Error: "permission denied" in kubectl Commands

**Cause:** Agent service account lacks permissions.

**Fix:** Expand RBAC for agent (you control this in EKS):

```yaml
# cluster-role-expansion.yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: gitlab-agent-role
rules:
  - apiGroups: [""]
    resources: ["pods", "services", "configmaps", "secrets"]
    verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]
  - apiGroups: ["apps"]
    resources: ["deployments", "statefulsets", "daemonsets"]
    verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]
  # Add more as needed
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
kubectl apply -f cluster-role-expansion.yaml

# Update Helm to use custom role
helm upgrade gitlab-agent gitlab/gitlab-agent \
  --namespace gitlab-agent \
  --reuse-values \
  --set rbac.useExistingRole=gitlab-agent-role
```

---

## Agent Version Issues

### "Agent version mismatch" Warning in UI

**Meaning:** Multiple agent pods with different versions, or version cache issue.

**Fixes:**

```bash
# 1. Check all agent pods have same version
kubectl get pods -n gitlab-agent -o jsonpath='{.items[*].spec.containers[*].image}'

# 2. Force single replica during upgrade
helm upgrade gitlab-agent gitlab/gitlab-agent \
  --namespace gitlab-agent \
  --reuse-values \
  --set replicaCount=1 \
  --set image.tag=v17.6.0

# 3. Wait for rollout
kubectl rollout status deployment/gitlab-agent -n gitlab-agent

# 4. Scale back up (if needed)
helm upgrade gitlab-agent gitlab/gitlab-agent \
  --namespace gitlab-agent \
  --reuse-values \
  --set replicaCount=2
```

**Note:** Wait ~20 minutes for GitLab's agent version cache to update.

---

## Pod Issues

### CrashLoopBackOff

```bash
# Check events
kubectl describe pod -l=app.kubernetes.io/name=gitlab-agent -n gitlab-agent

# Check logs from crashed container
kubectl logs -l=app.kubernetes.io/name=gitlab-agent -n gitlab-agent --previous

# Common causes:
# - Invalid token (check token is correctly set)
# - Invalid KAS address
# - OOM (increase memory limits)
```

### OOMKilled

```bash
# Check current limits
kubectl get deployment gitlab-agent -n gitlab-agent -o jsonpath='{.spec.template.spec.containers[0].resources}'

# Increase limits
helm upgrade gitlab-agent gitlab/gitlab-agent \
  --namespace gitlab-agent \
  --reuse-values \
  --set resources.limits.memory=512Mi \
  --set resources.requests.memory=256Mi
```

---

## Flux/GitOps Issues

### Flux Not Syncing

```bash
# Check Flux sources
flux get sources git

# Check Flux kustomizations
flux get kustomization

# Force reconciliation
flux reconcile source git my-app --with-source
```

### "Unable to clone repository" in Flux

**Check GitLab secret:**

```bash
kubectl get secret gitlab-token -n flux-system -o yaml
```

**Recreate if needed:**

```bash
kubectl delete secret gitlab-token -n flux-system
kubectl create secret generic gitlab-token \
  --namespace=flux-system \
  --from-literal=username=git \
  --from-literal=password=${GITLAB_TOKEN}
```

---

## Diagnostic Commands Summary

```bash
# Agent status
kubectl get pods -n gitlab-agent
kubectl logs -f -l=app.kubernetes.io/name=gitlab-agent -n gitlab-agent
kubectl describe pod -l=app.kubernetes.io/name=gitlab-agent -n gitlab-agent

# Helm status
helm list -n gitlab-agent
helm get values gitlab-agent -n gitlab-agent
helm history gitlab-agent -n gitlab-agent

# API checks
curl --header "PRIVATE-TOKEN: ${GITLAB_TOKEN}" \
  "https://${GITLAB_HOST}/api/v4/projects/${PROJECT_ID}/cluster_agents" | jq
curl --header "PRIVATE-TOKEN: ${GITLAB_TOKEN}" \
  "https://${GITLAB_HOST}/api/v4/projects/${PROJECT_ID}/cluster_agents/${AGENT_ID}/tokens" | jq

# Network tests
kubectl run curl-test --rm -it --restart=Never --image=curlimages/curl -- \
  curl -v "https://${GITLAB_HOST}/-/kubernetes-agent/"

# Config verification
kubectl get configmap -l=app=gitlab-agent -n gitlab-agent -o yaml
kubectl get secret -n gitlab-agent -o yaml
```

---

## When to Escalate to GitLab Admin

Escalate these issues — they require GitLab server access:

| Issue                               | Why Admin Needed             |
| ----------------------------------- | ---------------------------- |
| KAS not responding at all           | Server-side service issue    |
| "KAS internal error" in agent logs  | Server-side configuration    |
| GitLab upgrade broke agents         | Server version change        |
| Need higher token limits            | License/configuration change |
| Certificate issues at GitLab server | Server TLS configuration     |

**Information to provide:**

1. Agent logs: `kubectl logs -l=app.kubernetes.io/name=gitlab-agent -n gitlab-agent --tail=100`
2. Agent version: `kubectl get deployment gitlab-agent -n gitlab-agent -o jsonpath='{.spec.template.spec.containers[0].image}'`
3. Error messages (exact JSON from logs)
4. Project path and agent name
