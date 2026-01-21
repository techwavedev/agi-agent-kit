# GitLab Agent Upgrade Guide

Instructions for upgrading the GitLab Agent for Kubernetes.

## Check Current Version

```bash
# Get current agent version
kubectl get deployment -n gitlab-agent -o jsonpath='{.items[*].spec.template.spec.containers[*].image}'

# Check agent pod status
kubectl get pods -n gitlab-agent
```

## Available Versions

Check latest versions:

```bash
helm repo update gitlab
helm search repo gitlab/gitlab-agent --versions | head -10
```

Current latest: **v18.8.0** (Chart 2.23.0)

## Upgrade Agent

```bash
# Upgrade to latest version
helm upgrade gitlab-agent gitlab/gitlab-agent \
  --namespace gitlab-agent \
  --reuse-values

# Or upgrade to specific version
helm upgrade gitlab-agent gitlab/gitlab-agent \
  --namespace gitlab-agent \
  --reuse-values \
  --version 2.23.0
```

The `--reuse-values` flag preserves your existing token and kasAddress configuration.

## Verify Upgrade

```bash
# Check new pod is running
kubectl get pods -n gitlab-agent -w

# Check agent logs for successful connection
kubectl logs -n gitlab-agent -l app=gitlab-agent --tail=50

# Verify in GitLab UI
# Navigate to: Operate → Kubernetes clusters
# Agent should show "Connected" status
```

## Rollback (if needed)

```bash
# List release history
helm history gitlab-agent -n gitlab-agent

# Rollback to previous version
helm rollback gitlab-agent -n gitlab-agent
```

## Version Compatibility

The GitLab Agent should be within 4 minor versions of your GitLab instance. Check your GitLab version:

- GitLab UI → Help (bottom left) → shows version
- Match agent version accordingly

| GitLab Version | Recommended Agent |
| -------------- | ----------------- |
| 18.x           | v18.x             |
| 17.x           | v17.x             |
