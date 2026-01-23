# NodePool Configuration Reference

Comprehensive NodePool configuration patterns and examples.

---

## NodePool Structure

```yaml
apiVersion: karpenter.sh/v1
kind: NodePool
metadata:
  name: <name>
  annotations:
    # Optional: Prevent disruption
    karpenter.sh/do-not-disrupt: "true"
spec:
  template:
    metadata:
      labels: {}
      annotations: {}
    spec:
      nodeClassRef:
        group: karpenter.k8s.aws
        kind: EC2NodeClass
        name: <ec2nodeclass-name>
      requirements: []
      taints: []
      startupTaints: []
      expireAfter: 720h
      terminationGracePeriod: 24h
  limits:
    cpu: 1000
    memory: 1000Gi
  disruption:
    consolidationPolicy: WhenEmptyOrUnderutilized
    consolidateAfter: 1m
    budgets: []
  weight: 10
```

---

## Requirement Keys

### Kubernetes Standard Labels

| Key                                | Values             | Description             |
| ---------------------------------- | ------------------ | ----------------------- |
| `kubernetes.io/arch`               | `amd64`, `arm64`   | CPU architecture        |
| `kubernetes.io/os`                 | `linux`, `windows` | Operating system        |
| `node.kubernetes.io/instance-type` | EC2 types          | Specific instance types |
| `topology.kubernetes.io/zone`      | AZ names           | Availability zones      |

### Karpenter Labels

| Key                                           | Values                       | Description              |
| --------------------------------------------- | ---------------------------- | ------------------------ |
| `karpenter.sh/capacity-type`                  | `spot`, `on-demand`          | Capacity type            |
| `karpenter.k8s.aws/instance-category`         | `c`, `m`, `r`, `t`, `g`, `p` | Instance family category |
| `karpenter.k8s.aws/instance-generation`       | `5`, `6`, `7`                | Instance generation      |
| `karpenter.k8s.aws/instance-size`             | `medium`, `large`, `xlarge`  | Instance size            |
| `karpenter.k8s.aws/instance-cpu`              | Number                       | vCPU count               |
| `karpenter.k8s.aws/instance-memory`           | Number                       | Memory in Mi             |
| `karpenter.k8s.aws/instance-hypervisor`       | `nitro`, `xen`               | Hypervisor type          |
| `karpenter.k8s.aws/instance-gpu-count`        | Number                       | GPU count                |
| `karpenter.k8s.aws/instance-gpu-manufacturer` | `nvidia`, `amd`              | GPU manufacturer         |
| `karpenter.k8s.aws/instance-local-nvme`       | Number                       | Local NVMe storage in GB |

---

## Example NodePools

### General Purpose (Cost-Optimized)

```yaml
apiVersion: karpenter.sh/v1
kind: NodePool
metadata:
  name: general-purpose
spec:
  template:
    spec:
      nodeClassRef:
        group: karpenter.k8s.aws
        kind: EC2NodeClass
        name: default
      requirements:
        - key: kubernetes.io/arch
          operator: In
          values: ["amd64"]
        - key: kubernetes.io/os
          operator: In
          values: ["linux"]
        - key: karpenter.sh/capacity-type
          operator: In
          values: ["spot", "on-demand"]
        - key: karpenter.k8s.aws/instance-category
          operator: In
          values: ["c", "m", "r"]
        - key: karpenter.k8s.aws/instance-generation
          operator: Gt
          values: ["5"]
  limits:
    cpu: 1000
    memory: 2000Gi
  disruption:
    consolidationPolicy: WhenEmptyOrUnderutilized
    consolidateAfter: 30s
```

### ARM64 Workloads (Graviton)

```yaml
apiVersion: karpenter.sh/v1
kind: NodePool
metadata:
  name: graviton
spec:
  template:
    spec:
      nodeClassRef:
        group: karpenter.k8s.aws
        kind: EC2NodeClass
        name: graviton
      requirements:
        - key: kubernetes.io/arch
          operator: In
          values: ["arm64"]
        - key: karpenter.sh/capacity-type
          operator: In
          values: ["spot", "on-demand"]
        - key: karpenter.k8s.aws/instance-category
          operator: In
          values: ["c", "m", "r"]
        - key: karpenter.k8s.aws/instance-generation
          operator: Gt
          values: ["6"]
  limits:
    cpu: 500
  disruption:
    consolidationPolicy: WhenEmptyOrUnderutilized
    consolidateAfter: 1m
  weight: 100 # Prefer Graviton over x86
```

### GPU Workloads

```yaml
apiVersion: karpenter.sh/v1
kind: NodePool
metadata:
  name: gpu
spec:
  template:
    metadata:
      labels:
        workload-type: gpu
    spec:
      nodeClassRef:
        group: karpenter.k8s.aws
        kind: EC2NodeClass
        name: gpu
      requirements:
        - key: node.kubernetes.io/instance-type
          operator: In
          values:
            - "p3.2xlarge"
            - "p3.8xlarge"
            - "p3.16xlarge"
            - "g4dn.xlarge"
            - "g4dn.2xlarge"
            - "g5.xlarge"
            - "g5.2xlarge"
        - key: karpenter.sh/capacity-type
          operator: In
          values: ["spot", "on-demand"]
      taints:
        - key: nvidia.com/gpu
          value: "true"
          effect: NoSchedule
  limits:
    nvidia.com/gpu: 20
  disruption:
    consolidationPolicy: WhenEmpty
    consolidateAfter: 5m
```

### High-Memory Workloads

```yaml
apiVersion: karpenter.sh/v1
kind: NodePool
metadata:
  name: high-memory
spec:
  template:
    spec:
      nodeClassRef:
        group: karpenter.k8s.aws
        kind: EC2NodeClass
        name: default
      requirements:
        - key: karpenter.k8s.aws/instance-category
          operator: In
          values: ["r", "x"]
        - key: karpenter.k8s.aws/instance-memory
          operator: Gt
          values: ["65536"] # > 64Gi
        - key: karpenter.sh/capacity-type
          operator: In
          values: ["on-demand"]
  limits:
    memory: 4000Gi
  disruption:
    consolidationPolicy: WhenEmpty
    consolidateAfter: 10m
```

### Burst/Ephemeral Workloads

```yaml
apiVersion: karpenter.sh/v1
kind: NodePool
metadata:
  name: burst
spec:
  template:
    spec:
      nodeClassRef:
        group: karpenter.k8s.aws
        kind: EC2NodeClass
        name: default
      requirements:
        - key: karpenter.k8s.aws/instance-category
          operator: In
          values: ["t"] # Burstable instances
        - key: karpenter.sh/capacity-type
          operator: In
          values: ["spot"]
      expireAfter: 4h # Short-lived nodes
  limits:
    cpu: 200
  disruption:
    consolidationPolicy: WhenEmptyOrUnderutilized
    consolidateAfter: 10s
```

### Windows Workloads

```yaml
apiVersion: karpenter.sh/v1
kind: NodePool
metadata:
  name: windows
spec:
  template:
    spec:
      nodeClassRef:
        group: karpenter.k8s.aws
        kind: EC2NodeClass
        name: windows
      requirements:
        - key: kubernetes.io/os
          operator: In
          values: ["windows"]
        - key: kubernetes.io/arch
          operator: In
          values: ["amd64"]
        - key: karpenter.k8s.aws/instance-category
          operator: In
          values: ["c", "m"]
  limits:
    cpu: 200
  disruption:
    consolidationPolicy: WhenEmpty
    consolidateAfter: 30m
```

---

## Disruption Policies

### WhenEmpty

Consolidates only when node has no non-DaemonSet pods:

```yaml
disruption:
  consolidationPolicy: WhenEmpty
  consolidateAfter: 5m
```

### WhenEmptyOrUnderutilized

Consolidates when empty OR when pods can fit on other nodes:

```yaml
disruption:
  consolidationPolicy: WhenEmptyOrUnderutilized
  consolidateAfter: 30s
```

### Disruption Budgets

Limit simultaneous disruptions:

```yaml
disruption:
  budgets:
    - nodes: "10%"
    - nodes: "0"
      schedule: "0 9 * * 5" # No disruption Friday 9am
      duration: 8h
```

---

## Taints and Tolerations

### Dedicated NodePool

```yaml
spec:
  template:
    spec:
      taints:
        - key: team
          value: data-science
          effect: NoSchedule
```

Pods must tolerate:

```yaml
tolerations:
  - key: team
    operator: Equal
    value: data-science
    effect: NoSchedule
```

### Startup Taints

Temporary taints removed when node is ready:

```yaml
spec:
  template:
    spec:
      startupTaints:
        - key: node.kubernetes.io/not-ready
          effect: NoSchedule
```

---

## Weight-Based Selection

Higher weight = higher priority when multiple NodePools match:

```yaml
# Prefer Graviton (weight 100) over x86 (weight 10)
---
apiVersion: karpenter.sh/v1
kind: NodePool
metadata:
  name: graviton
spec:
  weight: 100
  # ...
---
apiVersion: karpenter.sh/v1
kind: NodePool
metadata:
  name: x86
spec:
  weight: 10
  # ...
```

---

## Resource Limits

Prevent runaway costs by limiting NodePool resources:

```yaml
limits:
  cpu: 1000 # Total vCPUs across all nodes
  memory: 2000Gi # Total memory
  nvidia.com/gpu: 10 # Total GPUs
```

Check current usage:

```bash
kubectl describe nodepool <name>
# Status.Resources shows current allocation
```
