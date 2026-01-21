# GitLab CI/CD Troubleshooting Guide

Common issues and solutions for GitLab CI/CD pipelines with Kubernetes.

---

## Pipeline Syntax Errors

### Error: `workflow:rules:rule when unknown value: manual`

**Cause:** Using `when: manual` in `workflow:rules` is invalid. The `when: manual` keyword is only valid at the job level, not in workflow rules.

**Wrong:**

```yaml
workflow:
  rules:
    - if: $CI_COMMIT_BRANCH == "master"
    - when: manual # INVALID!
```

**Correct:**

```yaml
workflow:
  rules:
    - if: $CI_COMMIT_BRANCH == "master"
    - if: $CI_COMMIT_BRANCH == "tst"
    - if: $CI_COMMIT_BRANCH == "prod"
    - if: $CI_COMMIT_TAG

# Use 'when: manual' at job level instead:
deploy:prod:
  rules:
    - if: $CI_COMMIT_BRANCH == "prod"
      when: manual # Valid at job level
```

**Difference:**

- `workflow:rules` - Controls when the pipeline runs at all
- Job `rules:` - Controls when individual jobs run within the pipeline

---

## Agent Connectivity Issues

### Error: `KUBE_CONTEXT not found`

**Cause:** Agent name in `KUBE_CONTEXT` doesn't match registered agent.

**Fix:**

1. Go to GitLab → Operate → Kubernetes clusters
2. Copy the exact agent name
3. Update `.gitlab-ci.yml`:
   ```yaml
   variables:
     KUBE_CONTEXT: "project-path:exact-agent-name"
   ```

### Error: Agent not connecting

**Check agent status:**

```bash
kubectl get pods -n gitlab-agent
kubectl logs -n gitlab-agent -l app=gitlab-agent --tail=100
```

**Common causes:**

- Expired token → Regenerate in GitLab
- Wrong KAS address → Check `config.kasAddress`
- Network blocked → Check egress firewall

---

## Deployment Issues

### Error: Namespace not found

**Cause:** Trying to deploy before namespace exists.

**Fix:** Ensure `namespace.yaml` is listed first in `kustomization.yaml`:

```yaml
resources:
  - namespace.yaml # Must be first!
  - configmap.yaml
  - deployment.yaml
  - service.yaml
```

### Error: ImagePullBackOff

**Cause:** Can't pull container image.

**Check:**

```bash
kubectl describe pod <pod-name> -n <namespace>
```

**Common causes:**

- Image doesn't exist
- Private registry without credentials
- Typo in image name

---

## Permission Issues

### Error: Cannot push to protected branch

**Cause:** Branch is protected and requires merge request.

**Options:**

1. Create MR instead of direct push
2. Ask maintainer to unprotect temporarily
3. Use `--force` if you have permission (not recommended)

### Error: RBAC access denied

**Cause:** Agent ServiceAccount lacks permissions.

**Fix:** Update agent configuration or ClusterRole.

---

## Validation Tips

### Test pipeline syntax locally

```bash
# Validate YAML syntax
python -c "import yaml; yaml.safe_load(open('.gitlab-ci.yml'))"

# Validate Kubernetes manifests
kubectl kustomize k8s/base --enable-helm
```

### Check CI/CD lint in GitLab

Go to: CI/CD → Editor → Validate

---

## Quick Reference

| Error                  | Likely Cause        | Quick Fix                        |
| ---------------------- | ------------------- | -------------------------------- |
| `when: manual` invalid | Wrong location      | Move to job rules                |
| Context not found      | Agent name mismatch | Check agent registration         |
| Namespace error        | Resource order      | Namespace first in kustomization |
| ImagePullBackOff       | Image access        | Check image name/registry        |
| Push rejected          | Protected branch    | Use merge request                |
