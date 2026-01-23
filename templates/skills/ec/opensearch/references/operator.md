# OpenSearch Kubernetes Operator Reference

Deploy and manage OpenSearch clusters on Kubernetes using the official OpenSearch Operator.

## Official Resources

- **GitHub:** https://github.com/opensearch-project/opensearch-k8s-operator
- **Documentation:** https://docs.opensearch.org/latest/install-and-configure/install-opensearch/operator/

---

## Installation

### Prerequisites

- Kubernetes 1.23+
- Helm 3.x
- kubectl with cluster admin access
- StorageClass with dynamic provisioning (recommended)

### Install via Helm

```bash
# Add the OpenSearch Operator Helm repository
helm repo add opensearch-operator https://opensearch-project.github.io/opensearch-k8s-operator/
helm repo update

# Install the operator
helm install opensearch-operator opensearch-operator/opensearch-operator \
  --namespace opensearch-operator-system \
  --create-namespace \
  --version 2.6.0
```

### Verify Installation

```bash
kubectl get pods -n opensearch-operator-system
kubectl get crd | grep opensearch
```

---

## Cluster Deployment

### Minimal Cluster

```yaml
apiVersion: opensearch.opster.io/v1
kind: OpenSearchCluster
metadata:
  name: my-cluster
  namespace: opensearch
spec:
  general:
    serviceName: my-cluster
    version: 2.17.0
    httpPort: 9200
    vendor: opensearch
    setVMMaxMapCount: true
  nodePools:
    - component: nodes
      replicas: 3
      diskSize: "30Gi"
      roles:
        - cluster_manager
        - data
        - ingest
      resources:
        requests:
          memory: "2Gi"
          cpu: "500m"
        limits:
          memory: "4Gi"
          cpu: "2000m"
```

### Production Cluster (Dedicated Roles)

```yaml
apiVersion: opensearch.opster.io/v1
kind: OpenSearchCluster
metadata:
  name: production-cluster
  namespace: opensearch
spec:
  general:
    serviceName: production-cluster
    version: 2.17.0
    httpPort: 9200
    vendor: opensearch
    setVMMaxMapCount: true
    pluginsList:
      - "repository-s3"
    additionalConfig:
      indices.query.bool.max_clause_count: "4096"
      search.max_buckets: "20000"

  dashboards:
    enable: true
    version: 2.17.0
    replicas: 2
    resources:
      requests:
        memory: "512Mi"
        cpu: "200m"
      limits:
        memory: "1Gi"
        cpu: "500m"

  nodePools:
    # Dedicated cluster managers (odd number for quorum)
    - component: cluster-manager
      replicas: 3
      diskSize: "10Gi"
      roles:
        - cluster_manager
      resources:
        requests:
          memory: "2Gi"
          cpu: "500m"
        limits:
          memory: "2Gi"
          cpu: "1000m"
      persistence:
        storageClass: gp3
        accessModes:
          - ReadWriteOnce
      jvm: "-Xms1g -Xmx1g"

    # Hot data nodes (recent data, SSDs)
    - component: data-hot
      replicas: 3
      diskSize: "500Gi"
      roles:
        - data
        - ingest
      nodeSelector:
        node-type: hot
      resources:
        requests:
          memory: "16Gi"
          cpu: "4000m"
        limits:
          memory: "16Gi"
          cpu: "8000m"
      persistence:
        storageClass: gp3-fast
        accessModes:
          - ReadWriteOnce
      jvm: "-Xms8g -Xmx8g"
      additionalConfig:
        node.attr.temp: "hot"

    # Warm data nodes (older data, HDDs)
    - component: data-warm
      replicas: 2
      diskSize: "2Ti"
      roles:
        - data
      nodeSelector:
        node-type: warm
      resources:
        requests:
          memory: "8Gi"
          cpu: "2000m"
        limits:
          memory: "8Gi"
          cpu: "4000m"
      persistence:
        storageClass: gp3-standard
        accessModes:
          - ReadWriteOnce
      jvm: "-Xms4g -Xmx4g"
      additionalConfig:
        node.attr.temp: "warm"

    # Coordinating nodes (query routing)
    - component: coordinating
      replicas: 2
      diskSize: "10Gi"
      roles: [] # No roles = coordinating only
      resources:
        requests:
          memory: "4Gi"
          cpu: "1000m"
        limits:
          memory: "4Gi"
          cpu: "2000m"
      jvm: "-Xms2g -Xmx2g"
```

---

## Security Configuration

### TLS Certificates

```yaml
spec:
  security:
    tls:
      transport:
        generate: true
        perNode: true
      http:
        generate: true
```

### Custom Certificates

```yaml
spec:
  security:
    tls:
      transport:
        secret:
          name: opensearch-transport-certs
        generate: false
      http:
        secret:
          name: opensearch-http-certs
        generate: false
```

### Admin Credentials

```bash
# Create admin credentials secret
kubectl create secret generic admin-credentials \
  --from-literal=username=admin \
  --from-literal=password='StrongP@ssw0rd!' \
  -n opensearch
```

```yaml
spec:
  security:
    config:
      adminCredentialsSecret:
        name: admin-credentials
```

### Security Config Secret

```yaml
spec:
  security:
    config:
      securityConfigSecret:
        name: security-config
```

Create the security config:

```bash
kubectl create secret generic security-config \
  --from-file=internal_users.yml \
  --from-file=roles.yml \
  --from-file=roles_mapping.yml \
  --from-file=config.yml \
  -n opensearch
```

---

## Scaling

### Horizontal Scaling

```bash
# Scale data nodes
kubectl patch opensearchcluster my-cluster -n opensearch \
  --type='json' \
  -p='[{"op": "replace", "path": "/spec/nodePools/0/replicas", "value": 5}]'
```

### Vertical Scaling

```yaml
nodePools:
  - component: data
    resources:
      requests:
        memory: "8Gi" # Increased from 4Gi
        cpu: "2000m"
      limits:
        memory: "8Gi"
        cpu: "4000m"
    jvm: "-Xms4g -Xmx4g" # 50% of memory
```

### Disk Expansion

```yaml
nodePools:
  - component: data
    diskSize: "200Gi" # Increased from 100Gi
    persistence:
      storageClass: gp3 # Must support volume expansion
```

---

## Upgrades

### Rolling Upgrade

```yaml
spec:
  general:
    version: 2.18.0 # New version
```

The operator performs rolling upgrades automatically.

### Upgrade Strategy

```yaml
spec:
  general:
    version: 2.18.0
  nodePools:
    - component: data
      pdb:
        enable: true
        minAvailable: 2 # Ensure availability during upgrade
```

---

## Plugins

### Install Plugins

```yaml
spec:
  general:
    pluginsList:
      - "repository-s3"
      - "analysis-icu"
      - "ingest-attachment"
```

### Custom Plugin from URL

```yaml
spec:
  general:
    pluginsList:
      - "https://example.com/plugins/my-plugin-1.0.0.zip"
```

---

## Snapshots & Backups

### S3 Repository

```yaml
spec:
  general:
    pluginsList:
      - "repository-s3"
    keystore:
      - secret:
          name: s3-credentials
        keyMappings:
          access_key: s3.client.default.access_key
          secret_key: s3.client.default.secret_key
```

```bash
# Create S3 credentials secret
kubectl create secret generic s3-credentials \
  --from-literal=access_key=AKIAXXXXXXXX \
  --from-literal=secret_key=xxxxxxxxxxxx \
  -n opensearch
```

### Register Repository

```json
PUT /_snapshot/s3-backup
{
  "type": "s3",
  "settings": {
    "bucket": "opensearch-backups",
    "base_path": "snapshots",
    "region": "eu-west-1"
  }
}
```

---

## Monitoring

### Prometheus Integration

```yaml
spec:
  general:
    monitoring:
      enable: true
      scrapeInterval: "30s"
      pluginUrl: "https://github.com/aiven/prometheus-exporter-plugin-for-opensearch/releases/download/2.17.0.0/prometheus-exporter-2.17.0.0.zip"
```

### ServiceMonitor (Prometheus Operator)

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: opensearch
  namespace: opensearch
spec:
  selector:
    matchLabels:
      opster.io/opensearch-cluster: my-cluster
  endpoints:
    - port: http
      path: /_prometheus/metrics
      interval: 30s
```

---

## Ingress

### NGINX Ingress

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: opensearch-ingress
  namespace: opensearch
  annotations:
    nginx.ingress.kubernetes.io/backend-protocol: "HTTPS"
    nginx.ingress.kubernetes.io/ssl-passthrough: "true"
spec:
  ingressClassName: nginx
  rules:
    - host: opensearch.example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: my-cluster
                port:
                  number: 9200
```

### Dashboards Ingress

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: opensearch-dashboards
  namespace: opensearch
spec:
  ingressClassName: nginx
  rules:
    - host: dashboards.example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: my-cluster-dashboards
                port:
                  number: 5601
```

---

## Troubleshooting

### Check Operator Logs

```bash
kubectl logs -n opensearch-operator-system \
  -l control-plane=controller-manager -f
```

### Check Cluster Status

```bash
kubectl get opensearchclusters -n opensearch
kubectl describe opensearchcluster my-cluster -n opensearch
```

### Check Pod Status

```bash
kubectl get pods -n opensearch -l opster.io/opensearch-cluster=my-cluster
kubectl logs -n opensearch my-cluster-nodes-0
```

### Common Issues

| Issue                | Solution                                 |
| -------------------- | ---------------------------------------- |
| Pods in Pending      | Check PVC status, StorageClass           |
| Cluster Yellow       | Check replica allocation, node resources |
| Init container fails | Verify sysctl settings, vm.max_map_count |
| TLS errors           | Regenerate certificates, check secrets   |
| Memory issues        | Adjust JVM heap, check limits            |

### Force Pod Restart

```bash
kubectl delete pod my-cluster-nodes-0 -n opensearch
```

---

## Best Practices

1. **Always use dedicated cluster managers** (3 or 5 for quorum)
2. **Set JVM heap to 50% of memory** (max 32GB)
3. **Use PodDisruptionBudgets** for availability
4. **Enable TLS** for transport and HTTP
5. **Regular snapshots** to S3 or other repository
6. **Monitor cluster health** with Prometheus
7. **Use node selectors** for hot/warm architecture
