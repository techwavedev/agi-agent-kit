# VictoriaMetrics Kubernetes/EKS Reference

Complete guide for deploying VictoriaMetrics on Kubernetes and Amazon EKS.

## Helm Charts

### Repository Setup

```bash
helm repo add vm https://victoriametrics.github.io/helm-charts/
helm repo update
```

### Available Charts

| Chart                        | Use Case                                |
| ---------------------------- | --------------------------------------- |
| `victoria-metrics-single`    | Single-node deployment                  |
| `victoria-metrics-cluster`   | Cluster deployment                      |
| `victoria-metrics-agent`     | vmagent only                            |
| `victoria-metrics-alert`     | vmalert only                            |
| `victoria-metrics-auth`      | vmauth proxy                            |
| `victoria-metrics-operator`  | Kubernetes Operator                     |
| `victoria-metrics-k8s-stack` | Full stack (like kube-prometheus-stack) |

---

## Single-Node on EKS

### Basic Installation

```bash
helm install vmsingle vm/victoria-metrics-single \
  --namespace monitoring \
  --create-namespace \
  --set server.persistentVolume.enabled=true \
  --set server.persistentVolume.size=100Gi \
  --set server.persistentVolume.storageClass=gp3 \
  --set server.retentionPeriod=90d
```

### Production Values

```yaml
# values-single-eks.yaml
server:
  persistentVolume:
    enabled: true
    size: 200Gi
    storageClass: gp3

  resources:
    requests:
      cpu: "1000m"
      memory: "4Gi"
    limits:
      cpu: "4000m"
      memory: "8Gi"

  extraArgs:
    retentionPeriod: 90d
    dedup.minScrapeInterval: 15s
    search.maxConcurrentRequests: "16"
    memory.allowedPercent: "80"

  nodeSelector:
    node-type: monitoring

  tolerations:
    - key: "monitoring"
      operator: "Equal"
      value: "true"
      effect: "NoSchedule"

  affinity:
    podAntiAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
        - labelSelector:
            matchLabels:
              app: victoriametrics
          topologyKey: "kubernetes.io/hostname"
```

---

## Cluster on EKS

### Installation

```bash
helm install vmcluster vm/victoria-metrics-cluster \
  --namespace monitoring \
  --create-namespace \
  -f values-cluster-eks.yaml
```

### Production Values

```yaml
# values-cluster-eks.yaml
vminsert:
  replicaCount: 3

  resources:
    requests:
      cpu: "500m"
      memory: "512Mi"
    limits:
      cpu: "2000m"
      memory: "2Gi"

  extraArgs:
    maxLabelsPerTimeseries: "50"

  podAntiAffinity:
    requiredDuringSchedulingIgnoredDuringExecution:
      - labelSelector:
          matchLabels:
            app: vminsert
        topologyKey: "topology.kubernetes.io/zone"

vmselect:
  replicaCount: 3

  resources:
    requests:
      cpu: "500m"
      memory: "1Gi"
    limits:
      cpu: "4000m"
      memory: "8Gi"

  extraArgs:
    search.maxConcurrentRequests: "32"
    search.maxQueueDuration: "30s"
    search.maxQueryDuration: "60s"
    dedup.minScrapeInterval: "15s"

  podAntiAffinity:
    requiredDuringSchedulingIgnoredDuringExecution:
      - labelSelector:
          matchLabels:
            app: vmselect
        topologyKey: "topology.kubernetes.io/zone"

vmstorage:
  replicaCount: 3

  persistentVolume:
    enabled: true
    size: 500Gi
    storageClass: gp3

  resources:
    requests:
      cpu: "1000m"
      memory: "4Gi"
    limits:
      cpu: "4000m"
      memory: "16Gi"

  extraArgs:
    retentionPeriod: "90d"
    dedup.minScrapeInterval: "15s"
    storage.minFreeDiskSpaceBytes: "10GB"

  podAntiAffinity:
    requiredDuringSchedulingIgnoredDuringExecution:
      - labelSelector:
          matchLabels:
            app: vmstorage
        topologyKey: "topology.kubernetes.io/zone"

  nodeSelector:
    node-type: storage
```

---

## VictoriaMetrics Operator

### Installation

```bash
helm install vm-operator vm/victoria-metrics-operator \
  --namespace monitoring \
  --create-namespace \
  --set operator.disable_prometheus_converter=false
```

### VMCluster CRD

```yaml
apiVersion: operator.victoriametrics.com/v1beta1
kind: VMCluster
metadata:
  name: production
  namespace: monitoring
spec:
  retentionPeriod: "90d"
  replicationFactor: 2

  vmstorage:
    replicaCount: 3
    storageDataPath: /vm-data
    storage:
      volumeClaimTemplate:
        spec:
          storageClassName: gp3
          resources:
            requests:
              storage: 500Gi
    resources:
      limits:
        cpu: "4"
        memory: "16Gi"
      requests:
        cpu: "1"
        memory: "4Gi"
    affinity:
      podAntiAffinity:
        requiredDuringSchedulingIgnoredDuringExecution:
          - labelSelector:
              matchLabels:
                app.kubernetes.io/name: vmstorage
            topologyKey: topology.kubernetes.io/zone

  vmselect:
    replicaCount: 3
    cacheMountPath: /cache
    extraArgs:
      search.maxConcurrentRequests: "32"
    resources:
      limits:
        cpu: "4"
        memory: "8Gi"
      requests:
        cpu: "500m"
        memory: "1Gi"

  vminsert:
    replicaCount: 3
    resources:
      limits:
        cpu: "2"
        memory: "2Gi"
      requests:
        cpu: "500m"
        memory: "512Mi"
```

### VMAgent CRD

```yaml
apiVersion: operator.victoriametrics.com/v1beta1
kind: VMAgent
metadata:
  name: vmagent
  namespace: monitoring
spec:
  replicaCount: 2

  selectAllByDefault: true

  remoteWrite:
    - url: http://vminsert-production.monitoring:8480/insert/0/prometheus/api/v1/write

  extraArgs:
    promscrape.cluster.membersCount: "2"

  resources:
    requests:
      cpu: "250m"
      memory: "256Mi"
    limits:
      cpu: "1000m"
      memory: "1Gi"

  scrapeInterval: 30s
```

### VMAlert CRD

```yaml
apiVersion: operator.victoriametrics.com/v1beta1
kind: VMAlert
metadata:
  name: vmalert
  namespace: monitoring
spec:
  replicaCount: 2

  datasource:
    url: http://vmselect-production.monitoring:8481/select/0/prometheus

  remoteWrite:
    url: http://vminsert-production.monitoring:8480/insert/0/prometheus

  remoteRead:
    url: http://vmselect-production.monitoring:8481/select/0/prometheus

  notifiers:
    - url: http://alertmanager.monitoring:9093

  selectAllByDefault: true

  resources:
    requests:
      cpu: "100m"
      memory: "128Mi"
    limits:
      cpu: "500m"
      memory: "512Mi"
```

---

## vmagent DaemonSet (EKS)

For node-level scraping:

```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: vmagent-node
  namespace: monitoring
spec:
  selector:
    matchLabels:
      app: vmagent-node
  template:
    metadata:
      labels:
        app: vmagent-node
    spec:
      serviceAccountName: vmagent
      containers:
        - name: vmagent
          image: victoriametrics/vmagent:v1.102.0
          args:
            - -promscrape.config=/config/prometheus.yml
            - -remoteWrite.url=http://vminsert:8480/insert/0/prometheus/api/v1/write
            - -remoteWrite.tmpDataPath=/tmp/vmagent
          ports:
            - containerPort: 8429
          volumeMounts:
            - name: config
              mountPath: /config
            - name: tmpdata
              mountPath: /tmp/vmagent
          resources:
            requests:
              cpu: "100m"
              memory: "128Mi"
            limits:
              cpu: "500m"
              memory: "512Mi"
      volumes:
        - name: config
          configMap:
            name: vmagent-config
        - name: tmpdata
          emptyDir: {}
```

---

## Storage Classes (EKS)

### GP3 StorageClass

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: gp3
provisioner: ebs.csi.aws.com
parameters:
  type: gp3
  iops: "3000"
  throughput: "125"
  fsType: ext4
reclaimPolicy: Retain
allowVolumeExpansion: true
volumeBindingMode: WaitForFirstConsumer
```

### IO2 for High Performance

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: io2-high-iops
provisioner: ebs.csi.aws.com
parameters:
  type: io2
  iops: "10000"
  fsType: ext4
reclaimPolicy: Retain
allowVolumeExpansion: true
volumeBindingMode: WaitForFirstConsumer
```

---

## Service Mesh Integration

### Istio

```yaml
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: victoriametrics
  namespace: monitoring
spec:
  hosts:
    - victoriametrics.example.com
  gateways:
    - monitoring-gateway
  http:
    - match:
        - uri:
            prefix: /
      route:
        - destination:
            host: vmselect
            port:
              number: 8481
```

---

## Ingress (ALB)

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: victoriametrics
  namespace: monitoring
  annotations:
    kubernetes.io/ingress.class: alb
    alb.ingress.kubernetes.io/scheme: internal
    alb.ingress.kubernetes.io/target-type: ip
    alb.ingress.kubernetes.io/healthcheck-path: /health
spec:
  rules:
    - host: vm.internal.example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: vmselect
                port:
                  number: 8481
```

---

## Monitoring the Stack

### ServiceMonitor for Prometheus Operator Compatibility

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: victoriametrics
  namespace: monitoring
spec:
  selector:
    matchLabels:
      app: victoriametrics
  endpoints:
    - port: http
      interval: 30s
      path: /metrics
```

---

## Backup to S3 (EKS)

### IRSA Setup

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: vmbackup
  namespace: monitoring
  annotations:
    eks.amazonaws.com/role-arn: arn:aws:iam::ACCOUNT_ID:role/vmbackup-role
```

### CronJob for Backup

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: vmbackup
  namespace: monitoring
spec:
  schedule: "0 2 * * *" # Daily at 2 AM
  jobTemplate:
    spec:
      template:
        spec:
          serviceAccountName: vmbackup
          containers:
            - name: vmbackup
              image: victoriametrics/vmbackup:v1.102.0
              args:
                - -storageDataPath=/vm-data
                - -snapshot.createURL=http://vmstorage:8482/snapshot/create
                - -dst=s3://my-bucket/vmbackups/$(date +%Y%m%d)
              volumeMounts:
                - name: vm-data
                  mountPath: /vm-data
          volumes:
            - name: vm-data
              persistentVolumeClaim:
                claimName: vmstorage-data
          restartPolicy: OnFailure
```
