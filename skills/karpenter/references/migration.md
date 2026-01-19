# Migration from Cluster Autoscaler to Karpenter

Step-by-step guide to migrate from Kubernetes Cluster Autoscaler to Karpenter.

---

## Overview

### Why Migrate?

| Feature            | Cluster Autoscaler      | Karpenter                  |
| ------------------ | ----------------------- | -------------------------- |
| Provisioning speed | Minutes                 | Seconds                    |
| Instance selection | Pre-defined node groups | Dynamic, right-sized       |
| Spot handling      | Limited                 | Native, automatic failover |
| Consolidation      | None                    | Built-in                   |
| Configuration      | Node groups             | Kubernetes-native CRDs     |

### Migration Strategies

1. **Parallel** (Recommended): Run both, gradually shift workloads
2. **Big Bang**: Replace completely in one operation

---

## Pre-Migration Checklist

- [ ] Karpenter IAM role created with required permissions
- [ ] IRSA configured for Karpenter ServiceAccount
- [ ] SQS queue for spot interruptions (optional but recommended)
- [ ] Subnets and security groups tagged with `karpenter.sh/discovery: <cluster-name>`
- [ ] Test environment validated

---

## Step-by-Step Migration

### Step 1: Prepare Infrastructure

**Tag Subnets:**

```bash
aws ec2 create-tags --resources subnet-xxx subnet-yyy \
  --tags Key=karpenter.sh/discovery,Value=${CLUSTER_NAME}
```

**Tag Security Groups:**

```bash
aws ec2 create-tags --resources sg-xxx \
  --tags Key=karpenter.sh/discovery,Value=${CLUSTER_NAME}
```

**Create Karpenter IAM Role:**

```bash
# Use eksctl or Terraform - see Karpenter getting started guide
eksctl create iamserviceaccount \
  --cluster=${CLUSTER_NAME} \
  --namespace=karpenter \
  --name=karpenter \
  --role-name=${CLUSTER_NAME}-karpenter \
  --attach-policy-arn=arn:aws:iam::${AWS_ACCOUNT_ID}:policy/KarpenterControllerPolicy \
  --approve
```

### Step 2: Install Karpenter

```bash
helm registry logout public.ecr.aws
helm upgrade --install karpenter oci://public.ecr.aws/karpenter/karpenter \
  --version "1.5.2" \
  --namespace karpenter --create-namespace \
  --set "settings.clusterName=${CLUSTER_NAME}" \
  --set "settings.interruptionQueue=${CLUSTER_NAME}" \
  --set replicas=2 \
  --wait
```

### Step 3: Create Karpenter Resources

**Create EC2NodeClass:**

```yaml
apiVersion: karpenter.k8s.aws/v1
kind: EC2NodeClass
metadata:
  name: default
spec:
  role: KarpenterNodeRole-${CLUSTER_NAME}
  amiSelectorTerms:
    - alias: al2023@latest
  subnetSelectorTerms:
    - tags:
        karpenter.sh/discovery: ${CLUSTER_NAME}
  securityGroupSelectorTerms:
    - tags:
        karpenter.sh/discovery: ${CLUSTER_NAME}
  blockDeviceMappings:
    - deviceName: /dev/xvda
      ebs:
        volumeSize: 100Gi
        volumeType: gp3
        encrypted: true
  metadataOptions:
    httpTokens: required
```

**Create NodePool (mirror existing ASG capabilities):**

```yaml
apiVersion: karpenter.sh/v1
kind: NodePool
metadata:
  name: default
spec:
  template:
    spec:
      nodeClassRef:
        group: karpenter.k8s.aws
        kind: EC2NodeClass
        name: default
      requirements:
        # Match your existing node groups
        - key: kubernetes.io/arch
          operator: In
          values: ["amd64"]
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
  disruption:
    consolidationPolicy: WhenEmptyOrUnderutilized
    consolidateAfter: 5m
```

### Step 4: Test Karpenter (Non-Critical Workloads)

**Deploy a test workload:**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: karpenter-test
spec:
  replicas: 5
  selector:
    matchLabels:
      app: karpenter-test
  template:
    metadata:
      labels:
        app: karpenter-test
    spec:
      # Force scheduling on new nodes (not on CAS nodes)
      affinity:
        nodeAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
            nodeSelectorTerms:
              - matchExpressions:
                  - key: karpenter.sh/nodepool
                    operator: Exists
      containers:
        - name: pause
          image: registry.k8s.io/pause:3.9
          resources:
            requests:
              cpu: 100m
              memory: 100Mi
```

**Verify nodes are provisioned:**

```bash
kubectl get nodes -l karpenter.sh/nodepool
kubectl get nodeclaims
```

### Step 5: Migrate Workloads Gradually

**Option A: Cordon ASG nodes**

```bash
# Cordon all non-Karpenter nodes
kubectl get nodes --no-headers -l '!karpenter.sh/nodepool' | \
  awk '{print $1}' | \
  xargs -I {} kubectl cordon {}
```

**Option B: Use pod anti-affinity**

Add to deployments to prefer Karpenter nodes:

```yaml
affinity:
  nodeAffinity:
    preferredDuringSchedulingIgnoredDuringExecution:
      - weight: 100
        preference:
          matchExpressions:
            - key: karpenter.sh/nodepool
              operator: Exists
```

### Step 6: Drain ASG Nodes

```bash
# Drain nodes one by one
kubectl drain <node-name> --ignore-daemonsets --delete-emptydir-data

# Or scale down ASG
aws autoscaling update-auto-scaling-group \
  --auto-scaling-group-name <asg-name> \
  --desired-capacity 0 \
  --min-size 0
```

### Step 7: Disable Cluster Autoscaler

```bash
# Scale down CAS
kubectl scale deployment cluster-autoscaler -n kube-system --replicas=0

# Or uninstall
helm uninstall cluster-autoscaler -n kube-system
```

### Step 8: Clean Up

```bash
# Delete old ASGs (after validation period)
eksctl delete nodegroup --cluster=${CLUSTER_NAME} --name=<nodegroup-name>

# Remove CAS IAM resources
# Delete CAS deployment if not using Helm
kubectl delete deployment cluster-autoscaler -n kube-system
```

---

## Mapping CAS Configuration to Karpenter

### Node Group → NodePool

**CAS Node Group (eksctl):**

```yaml
nodeGroups:
  - name: general
    instanceType: m5.xlarge
    desiredCapacity: 3
    minSize: 1
    maxSize: 10
    labels:
      workload-type: general
```

**Karpenter NodePool:**

```yaml
apiVersion: karpenter.sh/v1
kind: NodePool
metadata:
  name: general
spec:
  template:
    metadata:
      labels:
        workload-type: general
    spec:
      nodeClassRef:
        group: karpenter.k8s.aws
        kind: EC2NodeClass
        name: default
      requirements:
        - key: node.kubernetes.io/instance-type
          operator: In
          values: ["m5.xlarge", "m5.2xlarge", "m5a.xlarge"] # Expand options
  limits:
    cpu: 100 # ~10 nodes worth
```

### Mixed Instance Types

**CAS:**

```yaml
instanceTypes: ["m5.large", "m5a.large", "m5.xlarge"]
```

**Karpenter:**

```yaml
requirements:
  - key: karpenter.k8s.aws/instance-category
    operator: In
    values: ["m"]
  - key: karpenter.k8s.aws/instance-size
    operator: In
    values: ["large", "xlarge"]
```

### Taints

**CAS:**

```yaml
taints:
  dedicated: gpu:NoSchedule
```

**Karpenter:**

```yaml
spec:
  template:
    spec:
      taints:
        - key: dedicated
          value: gpu
          effect: NoSchedule
```

---

## Rollback Plan

If issues occur:

1. **Cordon Karpenter nodes:**

   ```bash
   kubectl get nodes -l karpenter.sh/nodepool -o name | xargs kubectl cordon
   ```

2. **Scale up CAS:**

   ```bash
   kubectl scale deployment cluster-autoscaler -n kube-system --replicas=1
   ```

3. **Increase ASG capacity:**

   ```bash
   aws autoscaling update-auto-scaling-group \
     --auto-scaling-group-name <asg-name> \
     --desired-capacity 5
   ```

4. **Drain Karpenter nodes:**

   ```bash
   kubectl get nodes -l karpenter.sh/nodepool -o name | xargs kubectl drain --ignore-daemonsets
   ```

5. **Delete Karpenter nodes:**
   ```bash
   kubectl delete nodes -l karpenter.sh/nodepool
   ```

---

## Post-Migration Validation

```bash
# Verify all pods running
kubectl get pods --all-namespaces | grep -v Running

# Verify node distribution
kubectl get nodes -o wide

# Check Karpenter metrics
kubectl port-forward -n karpenter svc/karpenter 8080:8080
curl localhost:8080/metrics | grep karpenter_

# Monitor for 24-48 hours before cleanup
```

---

## Common Migration Issues

| Issue                                  | Cause                   | Solution                            |
| -------------------------------------- | ----------------------- | ----------------------------------- |
| Pods not scheduling to Karpenter nodes | Node selectors/affinity | Check for CAS-specific labels       |
| Spot interruptions                     | Normal behavior         | Verify SQS queue configured         |
| Higher instance variety                | Expected                | Karpenter optimizes for cost        |
| Nodes not consolidating                | PDBs or annotations     | Check `karpenter.sh/do-not-disrupt` |
