# EKS IAM Roles and Service Accounts

## Required IAM Roles

### Cluster Role

The EKS cluster needs a role with these policies:

- `AmazonEKSClusterPolicy`

```bash
# Create cluster role
aws iam create-role \
  --role-name EKSClusterRole \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": {"Service": "eks.amazonaws.com"},
      "Action": "sts:AssumeRole"
    }]
  }'

aws iam attach-role-policy \
  --role-name EKSClusterRole \
  --policy-arn arn:aws:iam::aws:policy/AmazonEKSClusterPolicy
```

### Node Role

Node groups need a role with these policies:

- `AmazonEKSWorkerNodePolicy`
- `AmazonEKS_CNI_Policy`
- `AmazonEC2ContainerRegistryReadOnly`

```bash
# Create node role
aws iam create-role \
  --role-name EKSNodeRole \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": {"Service": "ec2.amazonaws.com"},
      "Action": "sts:AssumeRole"
    }]
  }'

aws iam attach-role-policy --role-name EKSNodeRole \
  --policy-arn arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy

aws iam attach-role-policy --role-name EKSNodeRole \
  --policy-arn arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy

aws iam attach-role-policy --role-name EKSNodeRole \
  --policy-arn arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly
```

## IAM Roles for Service Accounts (IRSA)

IRSA allows Kubernetes pods to assume IAM roles.

### 1. Enable OIDC Provider

```bash
eksctl utils associate-iam-oidc-provider \
  --cluster <cluster-name> \
  --region <region> \
  --approve
```

### 2. Create IAM Role for Service Account

```bash
eksctl create iamserviceaccount \
  --cluster <cluster-name> \
  --namespace <namespace> \
  --name <service-account-name> \
  --attach-policy-arn <policy-arn> \
  --approve \
  --region <region>
```

### 3. Use in Pod

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: my-app-sa
  namespace: my-namespace
  annotations:
    eks.amazonaws.com/role-arn: arn:aws:iam::<account>:role/<role-name>
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
spec:
  template:
    spec:
      serviceAccountName: my-app-sa
      containers:
        - name: app
          # AWS SDK will auto-discover credentials
```

## Common IRSA Use Cases

### S3 Access

```bash
eksctl create iamserviceaccount \
  --cluster <cluster> \
  --namespace <ns> \
  --name s3-reader \
  --attach-policy-arn arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess \
  --approve
```

### Secrets Manager

```bash
eksctl create iamserviceaccount \
  --cluster <cluster> \
  --namespace <ns> \
  --name secrets-reader \
  --attach-policy-arn arn:aws:iam::aws:policy/SecretsManagerReadWrite \
  --approve
```

### EBS CSI Driver

```bash
eksctl create iamserviceaccount \
  --cluster <cluster> \
  --namespace kube-system \
  --name ebs-csi-controller-sa \
  --attach-policy-arn arn:aws:iam::aws:policy/service-role/AmazonEBSCSIDriverPolicy \
  --approve
```

## Debugging IRSA

```bash
# Verify service account annotation
kubectl get sa <sa-name> -n <namespace> -o yaml

# Check pod has AWS credentials
kubectl exec -it <pod> -- env | grep AWS

# Test STS assume role
kubectl exec -it <pod> -- aws sts get-caller-identity
```
