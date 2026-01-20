# Consul Upgrade Guide

## Table of Contents

- [Pre-Upgrade Checklist](#pre-upgrade-checklist)
- [Upgrade Paths](#upgrade-paths)
- [Upgrade Procedures](#upgrade-procedures)
- [Post-Upgrade Validation](#post-upgrade-validation)
- [Rollback Procedures](#rollback-procedures)
- [Breaking Changes by Version](#breaking-changes-by-version)

---

## Pre-Upgrade Checklist

### Before Any Upgrade

- [ ] Review [release notes](https://developer.hashicorp.com/consul/docs/release-notes)
- [ ] Check for breaking changes
- [ ] Create snapshot backup
- [ ] Verify cluster is healthy
- [ ] Test upgrade in non-prod first
- [ ] Plan maintenance window

### Backup Commands

```bash
# Create snapshot
kubectl exec -n consul consul-server-0 -- consul snapshot save /tmp/backup.snap
kubectl cp consul/consul-server-0:/tmp/backup.snap ./consul-backup-$(date +%Y%m%d-%H%M).snap

# Verify backup
consul snapshot inspect ./consul-backup-*.snap
```

### Health Verification

```bash
# All servers healthy
kubectl exec -n consul consul-server-0 -- consul members

# Raft consensus
kubectl exec -n consul consul-server-0 -- consul operator raft list-peers

# No critical services down
kubectl exec -n consul consul-server-0 -- consul catalog services
```

---

## Upgrade Paths

### Consul Version Compatibility

| From   | To     | Notes                                           |
| ------ | ------ | ----------------------------------------------- |
| 1.15.x | 1.16.x | Direct upgrade supported                        |
| 1.16.x | 1.17.x | Direct upgrade supported                        |
| 1.17.x | 1.18.x | Direct upgrade supported                        |
| 1.15.x | 1.18.x | **Step upgrade required** (1.15→1.16→1.17→1.18) |

### consul-k8s Helm Chart Versions

| Helm Chart | Consul Version | Notes  |
| ---------- | -------------- | ------ |
| 1.0.x      | 1.14.x         | Legacy |
| 1.1.x      | 1.15.x         |        |
| 1.2.x      | 1.16.x         |        |
| 1.3.x      | 1.17.x         |        |
| 1.4.x      | 1.18.x         | Latest |

---

## Upgrade Procedures

### Standard Helm Upgrade

```bash
# 1. Check current version
helm list -n consul
kubectl exec -n consul consul-server-0 -- consul version

# 2. Update Helm repo
helm repo update hashicorp

# 3. Check available versions
helm search repo hashicorp/consul --versions

# 4. Dry-run upgrade
helm upgrade consul hashicorp/consul \
  --namespace consul \
  --values consul-values.yaml \
  --version <NEW_VERSION> \
  --dry-run

# 5. Perform upgrade
helm upgrade consul hashicorp/consul \
  --namespace consul \
  --values consul-values.yaml \
  --version <NEW_VERSION>

# 6. Watch rollout
kubectl rollout status statefulset/consul-server -n consul --timeout=10m
```

### Zero-Downtime Upgrade Strategy

```bash
# Upgrade servers one at a time
for i in 2 1 0; do
  echo "Upgrading consul-server-$i..."
  kubectl delete pod consul-server-$i -n consul
  kubectl wait --for=condition=Ready pod/consul-server-$i -n consul --timeout=300s
  sleep 30
done

# Verify leader election
kubectl exec -n consul consul-server-0 -- consul operator raft list-peers
```

### Multi-Datacenter Upgrade Order

1. **Upgrade secondary datacenters first**
2. Verify federation health
3. **Upgrade primary datacenter last**

---

## Post-Upgrade Validation

### Immediate Checks

```bash
# Server health
kubectl exec -n consul consul-server-0 -- consul members

# Version verification
kubectl exec -n consul consul-server-0 -- consul version

# Raft status
kubectl exec -n consul consul-server-0 -- consul operator raft list-peers

# Connect CA
kubectl exec -n consul consul-server-0 -- consul connect ca get-config
```

### Service Mesh Validation

```bash
# Check service registrations
kubectl exec -n consul consul-server-0 -- consul catalog services

# Verify sidecar injection still works
kubectl rollout restart deployment/test-app -n test

# Check intentions
kubectl get serviceintentions -A
```

---

## Rollback Procedures

### Helm Rollback

```bash
# List revisions
helm history consul -n consul

# Rollback to previous
helm rollback consul <REVISION> -n consul

# Watch rollout
kubectl rollout status statefulset/consul-server -n consul
```

### Snapshot Restore (Data Recovery)

```bash
# Copy backup to server
kubectl cp ./consul-backup.snap consul/consul-server-0:/tmp/restore.snap

# Restore snapshot
kubectl exec -n consul consul-server-0 -- consul snapshot restore /tmp/restore.snap

# Restart servers
kubectl rollout restart statefulset/consul-server -n consul
```

---

## Breaking Changes by Version

### 1.17.x → 1.18.x

- Consul Dataplane is now default (replaces client agents)
- Update sidecar annotations if customized

### 1.16.x → 1.17.x

- ACL token migration completed
- Legacy ACL tokens no longer supported

### 1.15.x → 1.16.x

- Catalog API v2 introduced (opt-in)
- Some deprecated flags removed

### General Guidance

- Always check the official [upgrading documentation](https://developer.hashicorp.com/consul/docs/upgrading)
- Test CRD changes in non-prod
- Monitor Envoy proxy compatibility
