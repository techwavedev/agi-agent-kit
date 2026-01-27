# Infrastructure Report Generation

## Goal

Generate comprehensive infrastructure reports with separate documentation and diagrams for technical and billing audiences.

## Output Structure

```
reports/<resource-name>/
├── README.md                           # Quick overview and links
├── cluster_technical_documentation.md  # Full technical details
├── billing_summary.md                  # Cost breakdown for finance
├── diagrams/
│   ├── technical.puml                  # PlantUML for architects/engineers
│   └── billing.puml                    # PlantUML for billing/management
```

## Execution

### 1. Gather Information

For EKS clusters:

```bash
aws eks describe-cluster --name <name> --region eu-west-1
aws eks list-nodegroups --cluster-name <name> --region eu-west-1
aws eks describe-nodegroup --cluster-name <name> --nodegroup-name <ng> --region eu-west-1
aws eks list-addons --cluster-name <name> --region eu-west-1
```

For Kubernetes resources:

```bash
kubectl get all -n <namespace> -o wide
kubectl get pvc -n <namespace> -o wide
kubectl get ingress,service -n <namespace>
```

### 2. Create Technical Documentation

Include:

- Cluster configuration (version, endpoint, authentication)
- VPC and networking (subnets, security groups)
- Node groups (instance types, scaling, AMI)
- Add-ons and their versions
- Security (KMS, logging, IAM roles)
- Tags and cost center

### 3. Create Billing Summary

Include:

- Monthly cost breakdown by category
- Cost per component
- Resource allocation summary
- Cost optimization recommendations
- Contact information

### 4. Create PlantUML Diagrams

**Use v20.0 of AWS icons:**

```plantuml
!define AWSPuml https://raw.githubusercontent.com/awslabs/aws-icons-for-plantuml/v20.0/dist
!include AWSPuml/AWSCommon.puml
```

**Technical diagram (`diagrams/technical.puml`):**

- All infrastructure components
- IAM roles, KMS keys
- VPCs, subnets, security groups
- Node details, add-ons
- Relationships and data flow

**Billing diagram (`diagrams/billing.puml`):**

- Simplified view with costs
- Cost distribution chart
- Plain language explanations
- Optimization opportunities
- No technical jargon

## Key Principles

1. **Separate audiences**: Technical team needs details; billing team needs costs
2. **PlantUML v20.0**: Always use current stable version of AWS icons
3. **Consistent structure**: Same folder layout for all reports
4. **Actionable insights**: Include recommendations and issues found
5. **Cost allocation**: Always include cost center and tags
