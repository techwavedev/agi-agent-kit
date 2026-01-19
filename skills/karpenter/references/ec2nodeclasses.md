# EC2NodeClass Configuration Reference

AWS-specific node configuration for Karpenter.

---

## EC2NodeClass Structure

```yaml
apiVersion: karpenter.k8s.aws/v1
kind: EC2NodeClass
metadata:
  name: <name>
spec:
  # Required
  role: <iam-role-name> # OR instanceProfile

  # AMI Selection
  amiSelectorTerms: []

  # Networking
  subnetSelectorTerms: []
  securityGroupSelectorTerms: []

  # Optional
  instanceProfile: <profile-name>
  amiFamily: AL2023 # AL2, AL2023, Bottlerocket, Ubuntu, Windows2019, Windows2022, Custom
  userData: ""
  blockDeviceMappings: []
  metadataOptions: {}
  associatePublicIPAddress: false
  tags: {}
  kubelet: {}
```

---

## AMI Selection

### Using Aliases (Recommended)

```yaml
amiSelectorTerms:
  - alias: al2023@latest # Amazon Linux 2023, latest version
```

Available aliases:
| Alias | Description |
|-------|-------------|
| `al2@latest` | Amazon Linux 2, latest |
| `al2023@latest` | Amazon Linux 2023, latest |
| `bottlerocket@latest` | Bottlerocket, latest |

### Using Tags

```yaml
amiSelectorTerms:
  - tags:
      karpenter.sh/discovery: my-cluster
      environment: production
```

### Using AMI ID

```yaml
amiSelectorTerms:
  - id: ami-0123456789abcdef0
```

### Using Name Pattern

```yaml
amiSelectorTerms:
  - name: "amazon-eks-node-1.29-*"
    owner: "602401143452" # AWS EKS AMI account
```

---

## Subnet Selection

### By Tags (Recommended)

```yaml
subnetSelectorTerms:
  - tags:
      karpenter.sh/discovery: my-cluster
```

### By ID

```yaml
subnetSelectorTerms:
  - id: subnet-0123456789abcdef0
  - id: subnet-abcdef0123456789a
```

### Multiple Criteria

```yaml
subnetSelectorTerms:
  - tags:
      karpenter.sh/discovery: my-cluster
      tier: private
```

---

## Security Group Selection

### By Tags

```yaml
securityGroupSelectorTerms:
  - tags:
      karpenter.sh/discovery: my-cluster
```

### By ID

```yaml
securityGroupSelectorTerms:
  - id: sg-0123456789abcdef0
```

### By Name

```yaml
securityGroupSelectorTerms:
  - name: "my-cluster-node-sg"
```

---

## Example EC2NodeClasses

### Default Linux (AL2023)

```yaml
apiVersion: karpenter.k8s.aws/v1
kind: EC2NodeClass
metadata:
  name: default
spec:
  role: KarpenterNodeRole-my-cluster
  amiSelectorTerms:
    - alias: al2023@latest
  subnetSelectorTerms:
    - tags:
        karpenter.sh/discovery: my-cluster
  securityGroupSelectorTerms:
    - tags:
        karpenter.sh/discovery: my-cluster
  blockDeviceMappings:
    - deviceName: /dev/xvda
      ebs:
        volumeSize: 100Gi
        volumeType: gp3
        iops: 3000
        throughput: 125
        encrypted: true
        deleteOnTermination: true
  metadataOptions:
    httpEndpoint: enabled
    httpProtocolIPv6: disabled
    httpPutResponseHopLimit: 1
    httpTokens: required # IMDSv2
  tags:
    Environment: production
    ManagedBy: karpenter
```

### Bottlerocket

```yaml
apiVersion: karpenter.k8s.aws/v1
kind: EC2NodeClass
metadata:
  name: bottlerocket
spec:
  role: KarpenterNodeRole-my-cluster
  amiSelectorTerms:
    - alias: bottlerocket@latest
  subnetSelectorTerms:
    - tags:
        karpenter.sh/discovery: my-cluster
  securityGroupSelectorTerms:
    - tags:
        karpenter.sh/discovery: my-cluster
  blockDeviceMappings:
    - deviceName: /dev/xvda
      ebs:
        volumeSize: 4Gi
        volumeType: gp3
    - deviceName: /dev/xvdb
      ebs:
        volumeSize: 100Gi
        volumeType: gp3
        encrypted: true
  metadataOptions:
    httpTokens: required
```

### GPU Nodes

```yaml
apiVersion: karpenter.k8s.aws/v1
kind: EC2NodeClass
metadata:
  name: gpu
spec:
  role: KarpenterNodeRole-my-cluster
  amiSelectorTerms:
    - alias: al2023@latest
  subnetSelectorTerms:
    - tags:
        karpenter.sh/discovery: my-cluster
  securityGroupSelectorTerms:
    - tags:
        karpenter.sh/discovery: my-cluster
  blockDeviceMappings:
    - deviceName: /dev/xvda
      ebs:
        volumeSize: 200Gi
        volumeType: gp3
        iops: 4000
        throughput: 250
        encrypted: true
  userData: |
    #!/bin/bash
    # Install NVIDIA drivers if not present
    nvidia-smi || yum install -y nvidia-driver-latest-dkms
  tags:
    workload: gpu
```

### Graviton (ARM64)

```yaml
apiVersion: karpenter.k8s.aws/v1
kind: EC2NodeClass
metadata:
  name: graviton
spec:
  role: KarpenterNodeRole-my-cluster
  amiSelectorTerms:
    - alias: al2023@latest
  subnetSelectorTerms:
    - tags:
        karpenter.sh/discovery: my-cluster
        tier: private
  securityGroupSelectorTerms:
    - tags:
        karpenter.sh/discovery: my-cluster
  blockDeviceMappings:
    - deviceName: /dev/xvda
      ebs:
        volumeSize: 100Gi
        volumeType: gp3
        encrypted: true
  tags:
    architecture: arm64
```

### Windows Nodes

```yaml
apiVersion: karpenter.k8s.aws/v1
kind: EC2NodeClass
metadata:
  name: windows
spec:
  role: KarpenterNodeRole-my-cluster
  amiFamily: Windows2022
  amiSelectorTerms:
    - name: "Windows_Server-2022-English-Core-EKS_Optimized-1.29-*"
      owner: "801119661308" # Amazon
  subnetSelectorTerms:
    - tags:
        karpenter.sh/discovery: my-cluster
  securityGroupSelectorTerms:
    - tags:
        karpenter.sh/discovery: my-cluster
  blockDeviceMappings:
    - deviceName: /dev/sda1
      ebs:
        volumeSize: 100Gi
        volumeType: gp3
        encrypted: true
```

### High I/O with Local NVMe

```yaml
apiVersion: karpenter.k8s.aws/v1
kind: EC2NodeClass
metadata:
  name: high-io
spec:
  role: KarpenterNodeRole-my-cluster
  amiSelectorTerms:
    - alias: al2023@latest
  subnetSelectorTerms:
    - tags:
        karpenter.sh/discovery: my-cluster
  securityGroupSelectorTerms:
    - tags:
        karpenter.sh/discovery: my-cluster
  # Root volume only; local NVMe is ephemeral
  blockDeviceMappings:
    - deviceName: /dev/xvda
      ebs:
        volumeSize: 50Gi
        volumeType: gp3
  userData: |
    #!/bin/bash
    # Mount local NVMe at /data
    NVME_DEVICES=$(lsblk -d -n -o NAME | grep nvme | grep -v nvme0)
    if [ -n "$NVME_DEVICES" ]; then
      mdadm --create /dev/md0 --level=0 --raid-devices=$(echo "$NVME_DEVICES" | wc -w) $(echo "$NVME_DEVICES" | sed 's/^/\/dev\//g')
      mkfs.xfs /dev/md0
      mkdir -p /data
      mount /dev/md0 /data
    fi
```

---

## Kubelet Configuration

Override kubelet settings:

```yaml
spec:
  kubelet:
    maxPods: 110
    podsPerCore: 20
    systemReserved:
      cpu: 100m
      memory: 100Mi
    kubeReserved:
      cpu: 200m
      memory: 200Mi
    evictionHard:
      memory.available: 5%
      nodefs.available: 10%
    evictionSoft:
      memory.available: 10%
      nodefs.available: 15%
    evictionSoftGracePeriod:
      memory.available: 1m
      nodefs.available: 1m
    clusterDNS:
      - 172.20.0.10
```

---

## UserData Examples

### Mount EFS

```yaml
userData: |
  #!/bin/bash
  yum install -y amazon-efs-utils
  mkdir -p /mnt/efs
  mount -t efs fs-12345678:/ /mnt/efs
```

### Install Monitoring Agent

```yaml
userData: |
  #!/bin/bash
  curl -o /tmp/cwagent.rpm https://s3.amazonaws.com/amazoncloudwatch-agent/amazon_linux/amd64/latest/amazon-cloudwatch-agent.rpm
  rpm -i /tmp/cwagent.rpm
  /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl -a fetch-config -m ec2 -s
```

### Custom DNS

```yaml
userData: |
  #!/bin/bash
  cat <<EOF >> /etc/resolv.conf
  nameserver 10.0.0.2
  search corp.example.com
  EOF
```

---

## Metadata Options (IMDS)

Secure IMDS configuration:

```yaml
metadataOptions:
  httpEndpoint: enabled # Enable IMDS
  httpProtocolIPv6: disabled # IPv4 only
  httpPutResponseHopLimit: 1 # Restrict to instance only
  httpTokens: required # Require IMDSv2 (IMPORTANT)
```

---

## Tags

Tags applied to EC2 instances and volumes:

```yaml
tags:
  Environment: production
  Team: platform
  CostCenter: "12345"
  Application: kubernetes
  ManagedBy: karpenter
  # Required for EKS
  kubernetes.io/cluster/my-cluster: owned
```
