# Consul HA Configuration Patterns

## Table of Contents

- [3-Server HA (Standard)](#3-server-ha-standard)
- [5-Server HA (High Availability)](#5-server-ha-high-availability)
- [Multi-Datacenter Federation](#multi-datacenter-federation)
- [Resource Sizing](#resource-sizing)
- [Storage Configuration](#storage-configuration)

---

## 3-Server HA (Standard)

Minimum HA configuration tolerating 1 server failure.

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
  bootstrapExpect: 3
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
  topologySpreadConstraints: |
    - maxSkew: 1
      topologyKey: topology.kubernetes.io/zone
      whenUnsatisfiable: DoNotSchedule
      labelSelector:
        matchLabels:
          app: consul
          component: server

connectInject:
  enabled: true
  default: false

controller:
  enabled: true
```

---

## 5-Server HA (High Availability)

Enhanced HA configuration tolerating 2 server failures.

```yaml
server:
  replicas: 5
  bootstrapExpect: 5
  resources:
    requests:
      memory: "500Mi"
      cpu: "200m"
    limits:
      memory: "1Gi"
      cpu: "1000m"
  storageClass: gp3
  storage: 20Gi
  affinity: |
    podAntiAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
        - labelSelector:
            matchLabels:
              app: consul
              component: server
          topologyKey: topology.kubernetes.io/zone
```

---

## Multi-Datacenter Federation

### Primary Datacenter

```yaml
global:
  name: consul
  datacenter: dc1
  tls:
    enabled: true
    enableAutoEncrypt: true
  acls:
    manageSystemACLs: true
  federation:
    enabled: true
    createFederationSecret: true

meshGateway:
  enabled: true
  replicas: 2

server:
  replicas: 3
```

### Secondary Datacenter

```yaml
global:
  name: consul
  datacenter: dc2
  tls:
    enabled: true
    enableAutoEncrypt: true
    caCert:
      secretName: consul-federation
      secretKey: caCert
  acls:
    manageSystemACLs: true
    replicationToken:
      secretName: consul-federation
      secretKey: replicationToken
  federation:
    enabled: true
    primaryDatacenter: dc1
    primaryGateways:
      - "mesh-gateway-dc1.example.com:443"

meshGateway:
  enabled: true
  replicas: 2

server:
  replicas: 3
  extraConfig: |
    {
      "primary_datacenter": "dc1",
      "retry_join_wan": ["mesh-gateway-dc1.example.com:443"]
    }
```

---

## Resource Sizing

| Cluster Size             | Servers | CPU Request | Memory Request | Storage |
| ------------------------ | ------- | ----------- | -------------- | ------- |
| Small (<50 services)     | 3       | 100m        | 200Mi          | 10Gi    |
| Medium (50-200 services) | 3       | 200m        | 500Mi          | 20Gi    |
| Large (200+ services)    | 5       | 500m        | 1Gi            | 50Gi    |

---

## Storage Configuration

### AWS gp3 StorageClass

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: consul-storage
provisioner: ebs.csi.aws.com
parameters:
  type: gp3
  iops: "3000"
  throughput: "125"
  encrypted: "true"
reclaimPolicy: Retain
allowVolumeExpansion: true
volumeBindingMode: WaitForFirstConsumer
```

### Consul Helm Values for Custom Storage

```yaml
server:
  storageClass: consul-storage
  storage: 20Gi
```
