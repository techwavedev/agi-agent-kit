# Karpenter Troubleshooting Reference

Detailed troubleshooting guide for common Karpenter issues.

---

## Controller Issues

### Karpenter Not Running

**Symptoms:** No pods in karpenter namespace

```bash
kubectl get pods -n karpenter
# No resources found
```

**Diagnosis:**

```bash
# Check Helm release
helm list -n karpenter

# Check events
kubectl get events -n karpenter --sort-by='.lastTimestamp'
```

**Solutions:**

1. Verify Helm installation completed
2. Check IRSA configuration (ServiceAccount annotation)
3. Verify node exists for controller to run on

### Controller CrashLoopBackOff

**Symptoms:**

```bash
kubectl get pods -n karpenter
# NAME                         READY   STATUS             RESTARTS
# karpenter-xyz                0/1     CrashLoopBackOff   5
```

**Diagnosis:**

```bash
kubectl logs -n karpenter -l app.kubernetes.io/name=karpenter -c controller --previous
```

**Common Causes:**

| Error                                            | Cause                   | Fix                               |
| ------------------------------------------------ | ----------------------- | --------------------------------- |
| `WebIdentityErr: failed to retrieve credentials` | IRSA not configured     | Verify OIDC provider and IAM role |
| `sts.amazonaws.com: i/o timeout`                 | DNS not resolving       | Set `dnsPolicy: Default` in Helm  |
| `unauthorized`                                   | IAM permissions missing | Check IAM role policies           |

### Enable Debug Logging

```bash
# Via Helm
helm upgrade karpenter oci://public.ecr.aws/karpenter/karpenter \
  --namespace karpenter \
  --reuse-values \
  --set logLevel=debug

# Via env var
kubectl set env deployment/karpenter -n karpenter LOG_LEVEL=debug

# View debug logs
kubectl logs -n karpenter -l app.kubernetes.io/name=karpenter -c controller -f
```

---

## Provisioning Issues

### Pods Stuck Pending

**Symptoms:** Pods remain in `Pending` state despite unschedulability

**Diagnosis:**

```bash
# Check pod events
kubectl describe pod <pod-name> -n <namespace>

# Look for Karpenter logs
kubectl logs -n karpenter -l app.kubernetes.io/name=karpenter -c controller | grep <pod-name>
```

**Common Causes:**

1. **No matching NodePool:**

   ```bash
   # Verify NodePools exist
   kubectl get nodepools

   # Check requirements match pod spec
   kubectl get nodepool <name> -o yaml
   ```

2. **NodePool limits exceeded:**

   ```bash
   kubectl describe nodepool <name>
   # Look for: Status.Resources showing at or near limits
   ```

3. **No valid instance types:**
   - Requirements too restrictive
   - Instance types unavailable in region/AZ
   - Check: `kubectl logs -n karpenter ... | grep "no instance type"`

### Node Launched But Not Ready

**Symptoms:** Node appears in cluster but shows `NotReady`

**Diagnosis:**

```bash
kubectl describe node <node-name>
# Check Conditions section

kubectl get events --field-selector involvedObject.name=<node-name>
```

**Common Causes:**

| Issue                 | Diagnosis            | Solution                               |
| --------------------- | -------------------- | -------------------------------------- |
| CNI not running       | Check aws-node pods  | Verify VPC CNI DaemonSet               |
| kubelet failing       | Check kubelet logs   | SSH to node, check `/var/log/messages` |
| ENI attachment failed | EC2 console          | Check subnet capacity, security groups |
| IP exhaustion         | Check pod-eni errors | Expand CIDR or use prefix delegation   |

### Insufficient Capacity

**Log Message:**

```
could not schedule pod, incompatible with nodepool "<name>", no instance type satisfied resources
```

**Solutions:**

1. Expand allowed instance types in NodePool
2. Add more instance categories/generations
3. Check pod resource requests aren't too large
4. Verify instances available in all target AZs

---

## Disruption Issues

### Nodes Not Consolidating

**Symptoms:** Underutilized nodes persist

**Diagnosis:**

```bash
# Check consolidation policy
kubectl get nodepool <name> -o jsonpath='{.spec.disruption}'

# Check node conditions
kubectl get nodeclaim <name> -o jsonpath='{.status.conditions}'
```

**Common Blockers:**

1. **PodDisruptionBudgets:**

   ```bash
   kubectl get pdb --all-namespaces
   # PDBs blocking eviction prevent consolidation
   ```

2. **Pod annotations:**

   ```yaml
   # Pods with this annotation block node deletion
   karpenter.sh/do-not-disrupt: "true"
   ```

3. **NodePool annotation:**

   ```yaml
   # NodePool-level disruption blocking
   karpenter.sh/do-not-disrupt: "true"
   ```

4. **System pods:**
   - kube-system pods without PDBs
   - Check DaemonSets tolerating Karpenter nodes

### Drift Not Detected

**Symptoms:** AMI updated but nodes not replaced

**Diagnosis:**

```bash
# Check drift conditions
kubectl get nodeclaim -o custom-columns=NAME:.metadata.name,DRIFTED:.status.conditions[?(@.type=="Drifted")].status

# Verify EC2NodeClass AMI
kubectl get ec2nodeclass <name> -o jsonpath='{.status.amis}'
```

**Force Drift:**

```bash
kubectl annotate ec2nodeclass <name> karpenter.k8s.aws/forced-drift=$(date +%s) --overwrite
```

### Nodes Expiring Unexpectedly

**Symptoms:** Nodes terminated before expected lifetime

**Diagnosis:**

```bash
kubectl get nodeclaim <name> -o jsonpath='{.status.conditions[?(@.type=="Expired")]}'
```

**Configuration:**

```yaml
spec:
  disruption:
    expireAfter: 720h # 30 days
```

---

## Installation Issues

### Missing Service Linked Role

**Error:**

```
ServiceLinkedRoleCreationNotPermitted: The provided credentials do not have permission to create the service-linked role for EC2 Spot Instances
```

**Solution:**

```bash
aws iam create-service-linked-role --aws-service-name spot.amazonaws.com
```

### STS Timeout

**Error:**

```
Post "https://sts.eu-west-1.amazonaws.com/": dial tcp: lookup sts.eu-west-1.amazonaws.com: i/o timeout
```

**Solutions:**

1. Set `dnsPolicy: Default` in Karpenter deployment
2. Ensure CoreDNS is running before Karpenter
3. Use Fargate profile or MNG for system pods

### Role Name Too Long

**Error:** IAM role name exceeds 64 characters

**Solution:** Use shorter role name:

```bash
# Instead of
KarpenterNodeRole-my-very-long-cluster-name-with-many-characters

# Use
KarpenterNodeRole-prod-cluster
```

---

## Spot Instance Issues

### Spot Interruption Handling

Karpenter automatically:

1. Receives interruption notice (2 min warning)
2. Cordons the node
3. Drains pods gracefully
4. Terminates the instance

**Verify SQS queue configured:**

```bash
kubectl get deployment -n karpenter karpenter -o yaml | grep -A5 interruptionQueue
```

### Spot Capacity Unavailable

**Log Message:**

```
no offering matched the requirements, none of the instance types appear to be available
```

**Solutions:**

1. Add more instance types to requirements
2. Enable multiple availability zones
3. Mix Spot with On-Demand via capacity-type weights

---

## Useful Commands

### View All Karpenter Resources

```bash
# All Karpenter CRDs
kubectl api-resources | grep karpenter

# NodePools with status
kubectl get nodepools -o wide

# EC2NodeClasses with status
kubectl get ec2nodeclasses -o wide

# NodeClaims (current nodes)
kubectl get nodeclaims -o wide

# Karpenter-managed nodes
kubectl get nodes -l karpenter.sh/nodepool -o wide
```

### Export Current Configuration

```bash
# Export all NodePools
kubectl get nodepools -o yaml > nodepools-backup.yaml

# Export all EC2NodeClasses
kubectl get ec2nodeclasses -o yaml > ec2nodeclasses-backup.yaml
```

### Monitor Karpenter Events

```bash
# Watch Karpenter controller logs
kubectl logs -n karpenter -l app.kubernetes.io/name=karpenter -c controller -f

# Watch node creation/deletion
kubectl get nodes -l karpenter.sh/nodepool -w

# Watch NodeClaims
kubectl get nodeclaims -w
```
