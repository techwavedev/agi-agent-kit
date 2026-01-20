# Consul Troubleshooting Guide

## Table of Contents

- [Cluster Formation Issues](#cluster-formation-issues)
- [Connect Sidecar Issues](#connect-sidecar-issues)
- [Performance Issues](#performance-issues)
- [TLS/Certificate Issues](#tlscertificate-issues)
- [ACL Issues](#acl-issues)
- [Upgrade Issues](#upgrade-issues)

---

## Cluster Formation Issues

### Servers Not Joining Cluster

**Symptoms:**

- `consul members` shows fewer than expected servers
- Servers stuck in `left` or `failed` state

**Diagnosis:**

```bash
# Check server logs
kubectl logs -n consul consul-server-0 | grep -i "join\|gossip\|serf"

# Check gossip key
kubectl get secret consul-gossip-encryption-key -n consul -o jsonpath='{.data.key}' | base64 -d
```

**Solutions:**

1. **Gossip key mismatch** — Ensure all servers use same key
2. **Network policies** — Allow ports 8301 (LAN gossip), 8300 (RPC)
3. **DNS resolution** — Check headless service resolves correctly

### Raft Quorum Lost

**Symptoms:**

- `No cluster leader`
- Only 1 server responding

**Recovery:**

```bash
# Check raft peers
kubectl exec -n consul consul-server-0 -- consul operator raft list-peers

# Remove failed peer
kubectl exec -n consul consul-server-0 -- consul operator raft remove-peer -address=<failed-peer-ip>:8300

# If single node recovery needed (DANGEROUS - data loss possible)
kubectl exec -n consul consul-server-0 -- consul operator raft remove-peer -address=<peer-address>
```

---

## Connect Sidecar Issues

### Sidecar Not Injecting

**Symptoms:**

- Pods start without `consul-dataplane` container
- No Envoy sidecar

**Diagnosis:**

```bash
# Check webhook
kubectl get mutatingwebhookconfigurations | grep consul

# Check injector logs
kubectl logs -n consul -l app=consul,component=connect-injector

# Check pod annotations
kubectl get pod <pod-name> -o yaml | grep consul
```

**Solutions:**

1. **Missing annotation** — Add `consul.hashicorp.com/connect-inject: "true"`
2. **Namespace not labeled** — `kubectl label namespace myapp consul.hashicorp.com/connect-inject=true`
3. **Webhook certificate expired** — Restart injector deployment

### Sidecar CrashLoopBackOff

**Symptoms:**

- `consul-dataplane` container crashes
- Pod restarts repeatedly

**Diagnosis:**

```bash
# Check dataplane logs
kubectl logs <pod-name> -c consul-dataplane

# Check Envoy config
kubectl exec <pod-name> -c consul-dataplane -- wget -qO- localhost:19000/config_dump
```

**Solutions:**

1. **ACL token issues** — Verify service token exists
2. **Upstream not found** — Check service registration
3. **Resource limits** — Increase CPU/memory for dataplane

---

## Performance Issues

### High Latency Between Services

**Diagnosis:**

```bash
# Check Envoy stats
kubectl exec <pod-name> -c consul-dataplane -- wget -qO- localhost:19000/stats | grep upstream

# Check connect intentions
kubectl get serviceintentions -A
```

**Solutions:**

1. **Increase Envoy resources**

```yaml
annotations:
  consul.hashicorp.com/sidecar-proxy-cpu-request: "100m"
  consul.hashicorp.com/sidecar-proxy-memory-request: "128Mi"
```

2. **Check network policies** — Ensure direct pod-to-pod traffic allowed
3. **Locality-aware routing** — Enable mesh gateway mode

### Server High CPU

**Diagnosis:**

```bash
# Check leader
kubectl exec -n consul consul-server-0 -- consul operator raft list-peers | grep leader

# Check catalog size
kubectl exec -n consul consul-server-0 -- consul catalog services | wc -l
```

**Solutions:**

1. Scale to 5 servers for read distribution
2. Increase server resources
3. Review service registration churn

---

## TLS/Certificate Issues

### Certificate Errors

**Symptoms:**

- `x509: certificate signed by unknown authority`
- Connect handshake failures

**Diagnosis:**

```bash
# Check CA config
kubectl exec -n consul consul-server-0 -- consul connect ca get-config

# Check certificate expiry
kubectl exec -n consul consul-server-0 -- consul tls cert-show
```

**Solutions:**

1. **CA mismatch** — Ensure all clients trust the CA
2. **Certificate rotation** — Trigger CA rotation
3. **Auto-encrypt issues** — Verify `enableAutoEncrypt: true`

### Gossip Encryption Failures

**Symptoms:**

- Servers can't communicate
- `memberlist: Encrypt message failed`

**Diagnosis:**

```bash
# Check keyring
kubectl exec -n consul consul-server-0 -- consul keyring -list
```

**Solutions:**

1. Ensure all nodes have the same gossip key
2. If rotating keys, follow proper key rotation procedure

---

## ACL Issues

### Permission Denied Errors

**Diagnosis:**

```bash
# Check token
kubectl exec -n consul consul-server-0 -- consul acl token list

# Check policy
kubectl exec -n consul consul-server-0 -- consul acl policy list
```

**Solutions:**

1. Create appropriate policy for the service
2. Attach policy to token
3. Verify token is being used correctly

### Bootstrap Token Lost

**Recovery:**

```bash
# Reset bootstrap (requires server access)
kubectl exec -n consul consul-server-0 -- consul acl bootstrap -reset
```

---

## Upgrade Issues

### Pods Stuck in Pending

**Cause:** Volume affinity conflicts

**Solution:**

```bash
# Check PVC binding
kubectl get pvc -n consul

# Delete stuck pod (statefulset will recreate)
kubectl delete pod consul-server-X -n consul
```

### Version Incompatibility

**Prevention:**

- Always check [upgrade notes](https://developer.hashicorp.com/consul/docs/upgrading)
- Upgrade one minor version at a time
- Test in non-prod first

**Recovery:**

```bash
# Rollback Helm release
helm rollback consul <previous-revision> -n consul
```
