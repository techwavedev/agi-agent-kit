# EKS Cluster Operations

## Create Cluster

### Using eksctl (recommended)

```bash
eksctl create cluster \
  --name <cluster-name> \
  --region <region> \
  --version 1.29 \
  --nodegroup-name standard-nodes \
  --node-type t3.medium \
  --nodes 3 \
  --nodes-min 1 \
  --nodes-max 5 \
  --managed
```

### Using AWS CLI

```bash
# 1. Create cluster (control plane only)
aws eks create-cluster \
  --name <cluster-name> \
  --region <region> \
  --kubernetes-version 1.29 \
  --role-arn <cluster-role-arn> \
  --resources-vpc-config subnetIds=<subnet-1>,<subnet-2>,securityGroupIds=<sg-id>

# 2. Wait for cluster to be active
aws eks wait cluster-active --name <cluster-name> --region <region>

# 3. Create node group
aws eks create-nodegroup \
  --cluster-name <cluster-name> \
  --nodegroup-name <nodegroup-name> \
  --node-role <node-role-arn> \
  --subnets <subnet-1> <subnet-2> \
  --instance-types t3.medium \
  --scaling-config minSize=1,maxSize=5,desiredSize=3 \
  --region <region>
```

## Update Cluster

### Update Kubernetes version

```bash
aws eks update-cluster-version \
  --name <cluster-name> \
  --kubernetes-version 1.30 \
  --region <region>
```

### Update node group

```bash
# Update AMI/version
aws eks update-nodegroup-version \
  --cluster-name <cluster-name> \
  --nodegroup-name <nodegroup-name> \
  --region <region>

# Update scaling
aws eks update-nodegroup-config \
  --cluster-name <cluster-name> \
  --nodegroup-name <nodegroup-name> \
  --scaling-config minSize=2,maxSize=10,desiredSize=5 \
  --region <region>
```

## Delete Cluster

### Using eksctl

```bash
eksctl delete cluster --name <cluster-name> --region <region>
```

### Using AWS CLI

```bash
# 1. Delete node groups first
aws eks delete-nodegroup \
  --cluster-name <cluster-name> \
  --nodegroup-name <nodegroup-name> \
  --region <region>

# 2. Wait for node group deletion
aws eks wait nodegroup-deleted \
  --cluster-name <cluster-name> \
  --nodegroup-name <nodegroup-name> \
  --region <region>

# 3. Delete cluster
aws eks delete-cluster --name <cluster-name> --region <region>
```

## Add-ons Management

### List available add-ons

```bash
aws eks describe-addon-versions --region <region>
```

### Install add-on

```bash
aws eks create-addon \
  --cluster-name <cluster-name> \
  --addon-name <addon-name> \
  --region <region>
```

Common add-ons:

- `vpc-cni` - VPC networking
- `coredns` - DNS
- `kube-proxy` - Network proxy
- `aws-ebs-csi-driver` - EBS storage
- `aws-efs-csi-driver` - EFS storage
