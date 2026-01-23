---
name: karpenter
description: Karpenter Kubernetes autoscaler specialist for EKS clusters. Use for troubleshooting, documenting, managing, creating, updating, upgrading Karpenter deployments, and obtaining live cluster information. Covers NodePool/EC2NodeClass configuration, cost optimization, node consolidation, drift detection, Spot interruption handling, and migration from Cluster Autoscaler. Requires kubectl access to target EKS cluster.
---

# Karpenter Skill

Comprehensive skill for managing Karpenter—the high-performance Kubernetes autoscaler for AWS EKS.

> **Last Updated:** 2026-01-23 from [karpenter.sh](https://karpenter.sh/)

---

## Quick Start

```bash
# Set cluster context
export CLUSTER_NAME=eks-nonprod
aws eks update-kubeconfig --name $CLUSTER_NAME --region eu-west-1

# Verify Karpenter is running
kubectl get pods -n karpenter

# List NodePools
kubectl get nodepools

# List EC2NodeClasses
kubectl get ec2nodeclasses
```

---

## Core Concepts

### Key Resources

| Resource         | Description                                                                  |
| ---------------- | ---------------------------------------------------------------------------- |
| **NodePool**     | Defines constraints, limits, and disruption policies for provisioned nodes   |
| **EC2NodeClass** | AWS-specific configuration (AMI, security groups, subnets, instance profile) |
| **NodeClaim**    | Individual node request created by Karpenter                                 |

### How Karpenter Works

1. **Watches** for unschedulable pods (`Unschedulable=True`)
2. **Evaluates** pod requirements (resources, affinity, tolerations, node selectors)
3. **Provisions** right-sized nodes matching constraints and cost optimization
4. **Disrupts** nodes via consolidation, drift, expiration, or interruption handling

---

## Common Workflows

### 1. Check Karpenter Status

```bash
# Controller pods
kubectl get pods -n karpenter

# Controller logs
kubectl logs -n karpenter -l app.kubernetes.io/name=karpenter -c controller --tail=100

# NodePools and their status
kubectl get nodepools -o wide

# EC2NodeClasses
kubectl get ec2nodeclasses -o wide

# NodeClaims (requested nodes)
kubectl get nodeclaims -o wide

# Karpenter-managed nodes
kubectl get nodes -l karpenter.sh/nodepool
```

### 2. Create a NodePool

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
    memory: 1000Gi
  disruption:
    consolidationPolicy: WhenEmptyOrUnderutilized
    consolidateAfter: 1m
```

### 3. Create an EC2NodeClass

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
  instanceProfile: KarpenterNodeInstanceProfile-${CLUSTER_NAME}
```

### 4. Troubleshoot Pending Pods

```bash
# Find unschedulable pods
kubectl get pods --all-namespaces -o wide | grep Pending

# Check why a pod is pending
kubectl describe pod <pod-name> -n <namespace>

# Check Karpenter logs for provisioning issues
kubectl logs -n karpenter -l app.kubernetes.io/name=karpenter -c controller | grep -i "could not"

# Verify NodePool requirements can be met
kubectl describe nodepool <nodepool-name>
```

### 5. Force Node Refresh (Drift)

```bash
# Annotate EC2NodeClass to trigger drift
kubectl annotate ec2nodeclass default karpenter.k8s.aws/forced-drift=$(date +%s) --overwrite

# Watch drift propagation
kubectl get nodeclaims -w
```

### 6. Manual Node Cordoning/Draining

```bash
# Cordon a node (prevent scheduling)
kubectl cordon <node-name>

# Drain a node (evict pods gracefully)
kubectl drain <node-name> --ignore-daemonsets --delete-emptydir-data

# Delete node (Karpenter handles cleanup via finalizer)
kubectl delete node <node-name>
```

---

## Troubleshooting Guide

### Enable Debug Logging

```bash
# Helm upgrade with debug
helm upgrade karpenter oci://public.ecr.aws/karpenter/karpenter \
  --set logLevel=debug \
  -n karpenter

# Or patch deployment
kubectl set env deployment/karpenter -n karpenter LOG_LEVEL=debug
```

### Common Issues

| Issue                         | Diagnosis                        | Solution                               |
| ----------------------------- | -------------------------------- | -------------------------------------- |
| **No nodes provisioned**      | Check controller logs for errors | Verify IAM permissions, subnet/SG tags |
| **Node not ready**            | `kubectl describe node`          | Check CNI, kubelet, VPC DNS            |
| **Spot interruption**         | Events in node description       | Karpenter auto-drains and replaces     |
| **Drift not detected**        | Check `drifted` condition        | Verify AMI changes, annotate to force  |
| **Consolidation not working** | Check `consolidatable` condition | Verify pods can be evicted (PDB, etc.) |

### Reference Files

- **[references/troubleshooting.md](references/troubleshooting.md)** — Detailed troubleshooting scenarios
- **[references/nodepools.md](references/nodepools.md)** — NodePool configuration patterns
- **[references/ec2nodeclasses.md](references/ec2nodeclasses.md)** — EC2NodeClass examples
- **[references/migration.md](references/migration.md)** — Migration from Cluster Autoscaler

---

## Scripts

### Get Cluster Status

```bash
# Run from skill directory
python scripts/karpenter_status.py --cluster eks-nonprod
```

### Generate NodePool YAML

```bash
python scripts/generate_nodepool.py \
  --name gpu-workloads \
  --instance-types "p3.2xlarge,p3.8xlarge" \
  --capacity-type spot \
  --cpu-limit 500
```

---

## Best Practices

### Cost Optimization

1. **Use Spot Instances** — Include `spot` in capacity-type requirements
2. **Enable Consolidation** — Use `WhenEmptyOrUnderutilized` policy
3. **Set Limits** — Define CPU/memory limits per NodePool
4. **Right-size Selection** — Use instance categories and generations

### Reliability

1. **Multi-AZ** — Don't restrict to single availability zone
2. **Instance Diversity** — Allow multiple instance types for flexibility
3. **PodDisruptionBudgets** — Protect critical workloads during consolidation
4. **Expiration** — Set `expireAfter` for node recycling (security)

### Security

1. **IMDSv2** — Enforce in EC2NodeClass with `metadataOptions`
2. **node IAM Role** — Scope permissions to minimum required
3. **Private subnets** — Use private subnets for nodes

---

## Installation & Upgrade

### Install Karpenter

```bash
export KARPENTER_VERSION="1.5.2"
export CLUSTER_NAME="eks-nonprod"
export AWS_PARTITION="aws"
export AWS_REGION="eu-west-1"
export AWS_ACCOUNT_ID="$(aws sts get-caller-identity --query Account --output text)"

helm registry logout public.ecr.aws
helm upgrade --install karpenter oci://public.ecr.aws/karpenter/karpenter \
  --version "${KARPENTER_VERSION}" \
  --namespace karpenter --create-namespace \
  --set "settings.clusterName=${CLUSTER_NAME}" \
  --set "settings.interruptionQueue=${CLUSTER_NAME}" \
  --set controller.resources.requests.cpu=1 \
  --set controller.resources.requests.memory=1Gi \
  --set controller.resources.limits.cpu=1 \
  --set controller.resources.limits.memory=1Gi \
  --wait
```

### Upgrade Karpenter

```bash
# Check current version
kubectl get deployment -n karpenter karpenter -o jsonpath='{.spec.template.spec.containers[0].image}'

# Upgrade
helm upgrade karpenter oci://public.ecr.aws/karpenter/karpenter \
  --version "${NEW_VERSION}" \
  --namespace karpenter \
  --reuse-values
```

---

## Related Skills

- **[aws](../aws/SKILL.md)** — Parent AWS skill for broader AWS operations
- **[aws-terraform](../aws-terraform/SKILL.md)** — Infrastructure as Code for Karpenter deployment

---

## External Resources

- [Karpenter Documentation](https://karpenter.sh/docs/)
- [Karpenter EKS Best Practices](https://aws.github.io/aws-eks-best-practices/karpenter/)
- [Karpenter Blueprints](https://github.com/aws-samples/karpenter-blueprints)
- [EKS Karpenter Workshop](https://www.eksworkshop.com/docs/autoscaling/compute/karpenter/)
