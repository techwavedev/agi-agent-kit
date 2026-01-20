---
name: consul
description: HashiCorp Consul specialist for EKS clusters. Use for Consul service mesh installation, configuration, HA setup, maintenance, updates, upgrades, troubleshooting, and optimization. Covers Consul Connect, intentions, health checks, ACLs, gossip encryption, TLS configuration, federation, and Kubernetes integration via consul-k8s Helm chart. Requires kubectl and helm access to target EKS cluster.
---

# Consul Skill

Comprehensive skill for managing HashiCorp Consul—the service mesh and service discovery solution—on Amazon EKS.

> **Last Updated:** 2026-01-20 from [consul.io](https://developer.hashicorp.com/consul)

---

## Quick Start

```bash
# Set cluster context
export CLUSTER_NAME=eks-nonprod
aws eks update-kubeconfig --name $CLUSTER_NAME --region eu-west-1

# Verify Consul is running
kubectl get pods -n consul
helm list -n consul

# Check Consul cluster status
kubectl exec -n consul consul-server-0 -- consul members
kubectl exec -n consul consul-server-0 -- consul operator raft list-peers
```

---

## Core Concepts

### Key Components

| Component           | Description                                                   |
| ------------------- | ------------------------------------------------------------- |
| **Consul Server**   | Maintains cluster state, handles queries, replicates data     |
| **Consul Client**   | Runs on each node, registers services, performs health checks |
| **Connect Sidecar** | Envoy proxy for mTLS and service mesh traffic                 |
| **Mesh Gateway**    | Routes traffic between datacenters/clusters                   |
| **Ingress Gateway** | External traffic entry point                                  |

### Architecture on EKS

```
┌─────────────────────────────────────────────────┐
│  EKS Cluster                                    │
│  ┌─────────────────────────────────────────────┐│
│  │ consul namespace                            ││
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐       ││
│  │  │Server 0 │ │Server 1 │ │Server 2 │ (HA)  ││
│  │  └─────────┘ └─────────┘ └─────────┘       ││
│  │  ┌──────────────┐ ┌──────────────┐         ││
│  │  │Mesh Gateway  │ │Ingress GW    │         ││
│  │  └──────────────┘ └──────────────┘         ││
│  └─────────────────────────────────────────────┘│
│  ┌─────────────────────────────────────────────┐│
│  │ Application namespaces                      ││
│  │  Pod + Envoy Sidecar (auto-injected)        ││
│  └─────────────────────────────────────────────┘│
└─────────────────────────────────────────────────┘
```

---

## Common Workflows

### 1. Check Consul Health

```bash
# Server status
kubectl exec -n consul consul-server-0 -- consul members

# Raft consensus (HA health)
kubectl exec -n consul consul-server-0 -- consul operator raft list-peers

# Server logs
kubectl logs -n consul -l app=consul,component=server --tail=100

# Connect CA status
kubectl exec -n consul consul-server-0 -- consul connect ca get-config
```

### 2. Install Consul on EKS (HA)

```bash
# Add Helm repo
helm repo add hashicorp https://helm.releases.hashicorp.com
helm repo update

# Create namespace
kubectl create namespace consul

# Install with HA configuration
helm install consul hashicorp/consul \
  --namespace consul \
  --values consul-values.yaml \
  --version 1.3.0
```

**Minimal HA values (`consul-values.yaml`):**

```yaml
global:
  name: consul
  datacenter: dc1
  gossipEncryption:
    autoGenerate: true
  tls:
    enabled: true
    enableAutoEncrypt: true
  acls:
    manageSystemACLs: true

server:
  replicas: 3
  resources:
    requests:
      memory: "200Mi"
      cpu: "100m"
    limits:
      memory: "500Mi"
      cpu: "500m"
  storageClass: gp3
  storage: 10Gi
  affinity: |
    podAntiAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
        - labelSelector:
            matchLabels:
              app: consul
              component: server
          topologyKey: kubernetes.io/hostname

connectInject:
  enabled: true
  default: false

controller:
  enabled: true

meshGateway:
  enabled: false

ingressGateway:
  enabled: false
```

### 3. Upgrade Consul

```bash
# Check current version
helm list -n consul

# Review release notes first!
# https://developer.hashicorp.com/consul/docs/release-notes

# Dry-run upgrade
helm upgrade consul hashicorp/consul \
  --namespace consul \
  --values consul-values.yaml \
  --version <NEW_VERSION> \
  --dry-run

# Perform upgrade
helm upgrade consul hashicorp/consul \
  --namespace consul \
  --values consul-values.yaml \
  --version <NEW_VERSION>

# Watch rollout
kubectl rollout status statefulset/consul-server -n consul
```

### 4. Configure Service Intentions

```yaml
# allow-api-to-db.yaml
apiVersion: consul.hashicorp.com/v1alpha1
kind: ServiceIntentions
metadata:
  name: api-to-database
  namespace: consul
spec:
  destination:
    name: database
  sources:
    - name: api
      action: allow
    - name: "*"
      action: deny
```

```bash
kubectl apply -f allow-api-to-db.yaml
```

### 5. Enable Connect Sidecar Injection

Add annotation to deployments:

```yaml
annotations:
  consul.hashicorp.com/connect-inject: "true"
```

Or enable namespace-wide:

```bash
kubectl label namespace myapp consul.hashicorp.com/connect-inject=true
```

---

## Troubleshooting Guide

### Common Issues

| Issue                           | Diagnosis                           | Solution                                      |
| ------------------------------- | ----------------------------------- | --------------------------------------------- |
| **Servers not forming cluster** | `consul members` shows < 3          | Check gossip encryption key, network policies |
| **Sidecar not injecting**       | Pods missing envoy container        | Verify webhook, check labels/annotations      |
| **ACL denied**                  | `permission denied` errors          | Bootstrap ACLs, create proper tokens          |
| **TLS handshake failures**      | Connection refused between services | Verify CA, check certificate rotation         |
| **High latency**                | Services slow to respond            | Check Envoy resource limits, xDS updates      |

### Debug Commands

```bash
# Check sidecar injection webhook
kubectl get mutatingwebhookconfigurations | grep consul

# View injector logs
kubectl logs -n consul -l app=consul,component=connect-injector

# Check service registration
kubectl exec -n consul consul-server-0 -- consul catalog services

# Debug Envoy proxy
kubectl exec -n <namespace> <pod> -c consul-dataplane -- wget -qO- localhost:19000/config_dump

# Check intentions
kubectl get serviceintentions -A

# ACL token details
kubectl exec -n consul consul-server-0 -- consul acl token list
```

### Reference Files

- **[references/ha_config.md](references/ha_config.md)** — HA configuration patterns
- **[references/acl_setup.md](references/acl_setup.md)** — ACL bootstrap and token management
- **[references/troubleshooting.md](references/troubleshooting.md)** — Detailed troubleshooting scenarios
- **[references/upgrades.md](references/upgrades.md)** — Version upgrade paths and breaking changes

---

## High Availability (HA)

### Requirements

- **Minimum 3 servers** for quorum (tolerates 1 failure)
- **5 servers** for higher availability (tolerates 2 failures)
- **Anti-affinity** to spread across nodes/AZs

### HA Configuration

```yaml
server:
  replicas: 3
  affinity: |
    podAntiAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
        - labelSelector:
            matchLabels:
              app: consul
              component: server
          topologyKey: topology.kubernetes.io/zone
```

### Quorum Loss Recovery

```bash
# Check peer status
kubectl exec -n consul consul-server-0 -- consul operator raft list-peers

# If quorum lost and need to recover with single node:
kubectl exec -n consul consul-server-0 -- consul operator raft remove-peer -address=<failed-peer>
```

---

## Maintenance Tasks

### Backup and Restore

```bash
# Snapshot (backup)
kubectl exec -n consul consul-server-0 -- consul snapshot save /tmp/backup.snap
kubectl cp consul/consul-server-0:/tmp/backup.snap ./consul-backup-$(date +%Y%m%d).snap

# Restore
kubectl cp ./backup.snap consul/consul-server-0:/tmp/restore.snap
kubectl exec -n consul consul-server-0 -- consul snapshot restore /tmp/restore.snap
```

### Certificate Rotation

```bash
# Check certificate expiry
kubectl exec -n consul consul-server-0 -- consul connect ca get-config

# Force CA rotation (with new root)
kubectl exec -n consul consul-server-0 -- consul connect ca set-config -config-file=/tmp/ca-config.json
```

### Gossip Key Rotation

```bash
# Generate new key
consul keygen

# Install new key (phase 1: add to all nodes)
kubectl exec -n consul consul-server-0 -- consul keyring -install <new-key>

# Make primary (phase 2)
kubectl exec -n consul consul-server-0 -- consul keyring -use <new-key>

# Remove old key (phase 3)
kubectl exec -n consul consul-server-0 -- consul keyring -remove <old-key>
```

---

## Scripts

### Get Consul Status

```bash
# Run from skill directory
python scripts/consul_status.py --namespace consul
```

### Generate Helm Values

```bash
python scripts/generate_values.py \
  --datacenter dc1 \
  --replicas 3 \
  --connect-inject \
  --acls \
  --tls
```

---

## Best Practices

### Security

1. **Enable ACLs** — Always use `manageSystemACLs: true`
2. **Enable TLS** — Use `tls.enabled: true`
3. **Gossip encryption** — Use `gossipEncryption.autoGenerate: true`
4. **Network policies** — Restrict traffic to Consul ports

### Performance

1. **Resource limits** — Set appropriate CPU/memory for servers
2. **Storage class** — Use fast SSD storage (gp3)
3. **Anti-affinity** — Spread servers across AZs

### Reliability

1. **3+ servers** — Never run fewer than 3 for production
2. **Regular backups** — Schedule snapshot backups
3. **Monitoring** — Export metrics to Prometheus

---

## Related Skills

- **[karpenter](../karpenter/SKILL.md)** — Node autoscaling for Consul workloads
- **[aws](../aws/SKILL.md)** — Parent AWS skill for broader AWS operations

---

## External Resources

- [Consul Documentation](https://developer.hashicorp.com/consul/docs)
- [Consul on Kubernetes](https://developer.hashicorp.com/consul/docs/k8s)
- [consul-k8s Helm Chart](https://github.com/hashicorp/consul-k8s)
- [Consul Connect (Service Mesh)](https://developer.hashicorp.com/consul/docs/connect)
