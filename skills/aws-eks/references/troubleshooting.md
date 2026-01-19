# EKS Troubleshooting Guide

## Connection Issues

### Cannot connect to cluster

```bash
# Update kubeconfig
aws eks update-kubeconfig --name <cluster-name> --region <region>

# Verify AWS identity
aws sts get-caller-identity

# Check cluster endpoint access
aws eks describe-cluster --name <cluster-name> --query 'cluster.resourcesVpcConfig'
```

### "Unauthorized" errors

```bash
# Check aws-auth ConfigMap
kubectl get configmap aws-auth -n kube-system -o yaml

# Add IAM user/role to aws-auth
kubectl edit configmap aws-auth -n kube-system
```

Add under `mapUsers` or `mapRoles`:

```yaml
mapUsers: |
  - userarn: arn:aws:iam::<account>:user/<username>
    username: <username>
    groups:
      - system:masters
```

## Pod Issues

### Pod stuck in Pending

```bash
kubectl describe pod <pod-name> -n <namespace>
```

Common causes:

- **Insufficient resources**: Scale up node group or reduce requests
- **Node selector mismatch**: Check node labels
- **PVC not bound**: Check storage class and PVC status

### Pod CrashLoopBackOff

```bash
# Check logs
kubectl logs <pod-name> -n <namespace>
kubectl logs <pod-name> -n <namespace> --previous

# Check events
kubectl describe pod <pod-name> -n <namespace>
```

Common causes:

- Application error (check logs)
- Missing environment variables or secrets
- Liveness probe failing

### ImagePullBackOff

```bash
kubectl describe pod <pod-name> -n <namespace>
```

Fixes:

- Check image name and tag
- Verify ECR permissions (if using ECR)
- Check imagePullSecrets for private registries

## Node Issues

### Node NotReady

```bash
# Check node conditions
kubectl describe node <node-name>

# Check system pods on node
kubectl get pods -A --field-selector spec.nodeName=<node-name>

# SSH to node (if needed)
aws ssm start-session --target <instance-id>
```

Common causes:

- kubelet not running
- Network connectivity issues
- Disk pressure

### Node scaling issues

```bash
# Check cluster autoscaler logs
kubectl logs -n kube-system -l app=cluster-autoscaler

# Check ASG activity
aws autoscaling describe-scaling-activities \
  --auto-scaling-group-name <asg-name> \
  --max-items 10
```

## Networking Issues

### Pods cannot communicate

```bash
# Check VPC CNI
kubectl get pods -n kube-system -l k8s-app=aws-node

# Check CNI logs
kubectl logs -n kube-system -l k8s-app=aws-node

# Verify security groups
aws ec2 describe-security-groups --group-ids <sg-id>
```

### DNS resolution failing

```bash
# Check CoreDNS
kubectl get pods -n kube-system -l k8s-app=kube-dns
kubectl logs -n kube-system -l k8s-app=kube-dns

# Test DNS from pod
kubectl run test-dns --rm -it --image=busybox -- nslookup kubernetes
```

## Storage Issues

### PVC Pending

```bash
kubectl describe pvc <pvc-name> -n <namespace>

# Check storage class
kubectl get storageclass

# Check EBS CSI driver
kubectl get pods -n kube-system -l app=ebs-csi-controller
```

### Volume mount failures

```bash
kubectl describe pod <pod-name> -n <namespace>
# Look for "FailedMount" events
```

Common fixes:

- Check node IAM role has EBS permissions
- Verify AZ matches between node and volume
- Check EBS CSI driver is installed
