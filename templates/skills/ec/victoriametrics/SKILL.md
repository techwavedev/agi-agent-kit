---
name: victoriametrics
description: VictoriaMetrics time-series database specialist covering deployment (bare metal, Docker, EKS/Kubernetes), cluster architecture (vminsert/vmselect/vmstorage), vmagent configuration, performance optimization, capacity planning, troubleshooting, monitoring, and Prometheus migration/compatibility. Use for any task involving: (1) Installing or upgrading VictoriaMetrics (single-node or cluster), (2) vmagent scraping and remote write configuration, (3) Capacity planning and resource optimization, (4) Prometheus to VictoriaMetrics migration with vmctl, (5) High availability and replication setup, (6) Kubernetes/EKS deployments with Helm or Operator, (7) MetricsQL queries and optimization, (8) Troubleshooting performance issues.
---

# VictoriaMetrics Skill

Expert-level guidance for VictoriaMetrics time-series database deployment, optimization, and operations.

## Quick Reference

| Component            | Purpose                                            |
| -------------------- | -------------------------------------------------- |
| `victoria-metrics`   | Single-node all-in-one TSDB                        |
| `vmagent`            | Metrics collection agent (scraping + remote write) |
| `vminsert`           | Cluster write path (accepts data)                  |
| `vmselect`           | Cluster read path (queries)                        |
| `vmstorage`          | Cluster storage nodes                              |
| `vmalert`            | Alerting and recording rules                       |
| `vmauth`             | Auth proxy and load balancer                       |
| `vmctl`              | Data migration tool                                |
| `vmbackup/vmrestore` | Backup and restore tools                           |

---

## Deployment Options

### Single-Node (Bare Metal/VM)

```bash
# Download latest release
wget https://github.com/VictoriaMetrics/VictoriaMetrics/releases/download/v1.102.0/victoria-metrics-linux-amd64-v1.102.0.tar.gz
tar -xzf victoria-metrics-linux-amd64-v1.102.0.tar.gz

# Start with common flags
./victoria-metrics-prod \
  -storageDataPath=/var/lib/victoriametrics \
  -retentionPeriod=90d \
  -httpListenAddr=:8428 \
  -selfScrapeInterval=10s
```

### Docker

```bash
docker run -d \
  --name victoriametrics \
  -p 8428:8428 \
  -v /data/victoriametrics:/victoria-metrics-data \
  victoriametrics/victoria-metrics:v1.102.0 \
  -storageDataPath=/victoria-metrics-data \
  -retentionPeriod=90d
```

### Docker Compose

```yaml
version: "3.8"
services:
  victoriametrics:
    image: victoriametrics/victoria-metrics:v1.102.0
    ports:
      - "8428:8428"
    volumes:
      - vmdata:/victoria-metrics-data
    command:
      - "-storageDataPath=/victoria-metrics-data"
      - "-retentionPeriod=90d"
      - "-selfScrapeInterval=10s"
    restart: unless-stopped

  vmagent:
    image: victoriametrics/vmagent:v1.102.0
    ports:
      - "8429:8429"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    command:
      - "-promscrape.config=/etc/prometheus/prometheus.yml"
      - "-remoteWrite.url=http://victoriametrics:8428/api/v1/write"
    restart: unless-stopped

volumes:
  vmdata:
```

### Systemd Service

```ini
# /etc/systemd/system/victoriametrics.service
[Unit]
Description=VictoriaMetrics
After=network.target

[Service]
Type=simple
User=victoriametrics
ExecStart=/usr/local/bin/victoria-metrics-prod \
  -storageDataPath=/var/lib/victoriametrics \
  -retentionPeriod=90d \
  -httpListenAddr=:8428
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

See `references/bare_metal.md` for complete installation guide.

---

## Kubernetes/EKS Deployment

### Helm Installation

```bash
# Add VictoriaMetrics Helm repo
helm repo add vm https://victoriametrics.github.io/helm-charts/
helm repo update

# Single-node deployment
helm install victoria-metrics vm/victoria-metrics-single \
  --namespace monitoring \
  --create-namespace \
  --set server.persistentVolume.size=100Gi \
  --set server.retentionPeriod=90d

# Cluster deployment
helm install victoria-metrics-cluster vm/victoria-metrics-cluster \
  --namespace monitoring \
  --create-namespace \
  -f values-cluster.yaml
```

### Cluster Values (EKS)

```yaml
# values-cluster.yaml
vminsert:
  replicaCount: 2
  resources:
    requests:
      cpu: "500m"
      memory: "512Mi"
    limits:
      cpu: "2000m"
      memory: "2Gi"

vmselect:
  replicaCount: 2
  resources:
    requests:
      cpu: "500m"
      memory: "512Mi"
    limits:
      cpu: "2000m"
      memory: "4Gi"
  extraArgs:
    search.maxConcurrentRequests: "16"

vmstorage:
  replicaCount: 3
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
    retentionPeriod: "90d"
    dedup.minScrapeInterval: "15s"
```

### VictoriaMetrics Operator (Kubernetes)

```bash
# Install operator
helm install vm-operator vm/victoria-metrics-operator \
  --namespace monitoring \
  --create-namespace
```

```yaml
# VMCluster CRD
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
    storage:
      volumeClaimTemplate:
        spec:
          storageClassName: gp3
          resources:
            requests:
              storage: 200Gi
    resources:
      limits:
        cpu: "4"
        memory: "8Gi"
      requests:
        cpu: "1"
        memory: "4Gi"

  vmselect:
    replicaCount: 2
    resources:
      limits:
        cpu: "2"
        memory: "4Gi"
      requests:
        cpu: "500m"
        memory: "512Mi"

  vminsert:
    replicaCount: 2
    resources:
      limits:
        cpu: "2"
        memory: "2Gi"
      requests:
        cpu: "500m"
        memory: "512Mi"
```

See `references/kubernetes.md` for complete EKS patterns.

---

## vmagent Configuration

### Basic Scrape Config

```yaml
# prometheus.yml for vmagent
global:
  scrape_interval: 15s
  external_labels:
    cluster: production
    region: eu-west-1

scrape_configs:
  - job_name: "kubernetes-pods"
    kubernetes_sd_configs:
      - role: pod
    relabel_configs:
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
        action: keep
        regex: true
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_path]
        action: replace
        target_label: __metrics_path__
        regex: (.+)
      - source_labels:
          [__address__, __meta_kubernetes_pod_annotation_prometheus_io_port]
        action: replace
        regex: ([^:]+)(?::\d+)?;(\d+)
        replacement: $1:$2
        target_label: __address__

  - job_name: "node-exporter"
    static_configs:
      - targets: ["node-exporter:9100"]
```

### vmagent Flags

```bash
vmagent \
  -promscrape.config=/etc/prometheus/prometheus.yml \
  -remoteWrite.url=http://vminsert:8480/insert/0/prometheus/api/v1/write \
  -remoteWrite.tmpDataPath=/tmp/vmagent-remotewrite \
  -remoteWrite.maxDiskUsagePerURL=1GB \
  -remoteWrite.queues=8 \
  -promscrape.cluster.membersCount=2 \
  -promscrape.cluster.memberNum=0
```

### High Availability vmagent

```yaml
# Deploy multiple vmagents with cluster mode
apiVersion: operator.victoriametrics.com/v1beta1
kind: VMAgent
metadata:
  name: vmagent-ha
spec:
  replicaCount: 2
  extraArgs:
    promscrape.cluster.membersCount: "2"
  remoteWrite:
    - url: http://vminsert:8480/insert/0/prometheus/api/v1/write
```

---

## Prometheus Compatibility & Migration

### Prometheus Remote Write to VM

```yaml
# prometheus.yml
remote_write:
  - url: http://victoriametrics:8428/api/v1/write
    queue_config:
      max_samples_per_send: 10000
      capacity: 20000
      max_shards: 30
```

### Migrate Historical Data with vmctl

```bash
# From Prometheus to VictoriaMetrics
vmctl prometheus \
  --prom-snapshot=/path/to/prometheus/data \
  --vm-addr=http://victoriametrics:8428 \
  --vm-concurrency=8

# From InfluxDB
vmctl influx \
  --influx-addr=http://influxdb:8086 \
  --influx-database=metrics \
  --vm-addr=http://victoriametrics:8428

# Between VictoriaMetrics instances
vmctl vm-native \
  --vm-native-src-addr=http://old-vm:8428 \
  --vm-native-dst-addr=http://new-vm:8428 \
  --vm-native-filter-time-start='2024-01-01T00:00:00Z'
```

### MetricsQL vs PromQL

| PromQL                 | MetricsQL Enhancement                             |
| ---------------------- | ------------------------------------------------- |
| `rate()`               | `rate()` with auto-interval detection             |
| `irate()`              | `irate()` + `rollup_rate()`                       |
| `histogram_quantile()` | `histogram_quantile()` + `histogram_share()`      |
| N/A                    | `rollup()` - aggregates multiple functions        |
| N/A                    | `range_median()`, `range_first()`, `range_last()` |
| N/A                    | `label_set()`, `label_del()`, `label_keep()`      |
| N/A                    | `limit_offset()` for pagination                   |

### Query Compatibility

```bash
# Enable Prometheus-compatible mode
victoria-metrics \
  -search.latencyOffset=0s \
  -search.disableCache=false
```

See `references/prometheus_migration.md` for detailed migration guide.

---

## Capacity Planning

### Resource Guidelines

| Metric             | CPU (cores) | RAM     | Storage      |
| ------------------ | ----------- | ------- | ------------ |
| 100K active series | 0.5         | 1-2GB   | ~5GB/month   |
| 1M active series   | 2-4         | 8-16GB  | ~50GB/month  |
| 10M active series  | 8-16        | 32-64GB | ~500GB/month |
| 50M active series  | 32+         | 128GB+  | ~2.5TB/month |

### Recommended Spare Resources

- **CPU:** 50% spare for spikes
- **RAM:** 50% spare to prevent OOM
- **Disk:** 20% minimum free space

### Storage Calculation

```
Storage = (active_series × samples_per_day × bytes_per_sample × retention_days) / compression_ratio

Example:
1M series × 5760 samples/day × 2 bytes × 90 days / 10 (compression) = ~100GB
```

### Cluster Sizing

| Workload              | vminsert    | vmselect    | vmstorage    |
| --------------------- | ----------- | ----------- | ------------ |
| Small (<1M series)    | 2 replicas  | 2 replicas  | 3 replicas   |
| Medium (1-10M series) | 3 replicas  | 3 replicas  | 5 replicas   |
| Large (10M+ series)   | 5+ replicas | 5+ replicas | 10+ replicas |

---

## Performance Optimization

### Key Flags

```bash
# Deduplication (for HA setups)
-dedup.minScrapeInterval=15s

# Query optimization
-search.maxConcurrentRequests=16
-search.maxQueueDuration=30s
-search.maxQueryLen=16KB
-search.maxPointsPerTimeseries=30000

# Memory limits
-memory.allowedPercent=80

# Cache tuning
-search.cacheTimestampOffset=5m

# Cardinality limits
-storage.maxHourlySeries=5000000
-storage.maxDailySeries=10000000
```

### Filesystem Recommendations

```bash
# For >1TB storage, use these ext4 options
mkfs.ext4 -O 64bit,huge_file,extent -T huge /dev/sdb

# Mount options
/dev/sdb /var/lib/victoriametrics ext4 defaults,noatime,nodiratime 0 0
```

### OS Tuning

```bash
# Increase open files limit
echo "victoriametrics soft nofile 65535" >> /etc/security/limits.conf
echo "victoriametrics hard nofile 65535" >> /etc/security/limits.conf

# Disable THP (Transparent Huge Pages)
echo never > /sys/kernel/mm/transparent_hugepage/enabled
```

See `references/optimization.md` for detailed tuning guide.

---

## Monitoring & Alerting

### Self-Monitoring

```yaml
# Scrape VictoriaMetrics metrics
scrape_configs:
  - job_name: "victoriametrics"
    static_configs:
      - targets: ["localhost:8428"]
```

### Key Metrics

| Metric                            | Alert Threshold |
| --------------------------------- | --------------- |
| `vm_free_disk_space_bytes`        | < 20% of total  |
| `process_resident_memory_bytes`   | > 80% of limit  |
| `vm_slow_row_inserts_total`       | Rate > 0        |
| `vm_slow_metric_name_loads_total` | Rate > 0        |
| `vm_rows_inserted_total`          | Sudden drops    |
| `vm_http_request_errors_total`    | Rate > 0        |

### vmalert Rules

```yaml
# alerting_rules.yml
groups:
  - name: victoriametrics
    rules:
      - alert: VMDiskSpaceLow
        expr: vm_free_disk_space_bytes / vm_available_disk_space_bytes < 0.2
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "VictoriaMetrics disk space low"

      - alert: VMSlowInserts
        expr: rate(vm_slow_row_inserts_total[5m]) > 0
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "VictoriaMetrics experiencing slow inserts - low RAM"

      - alert: VMHighCardinality
        expr: vm_new_timeseries_created_total > 1000000
        for: 1h
        labels:
          severity: warning
        annotations:
          summary: "High cardinality detected"
```

---

## Troubleshooting

### Common Issues

| Issue            | Diagnosis                        | Solution                                 |
| ---------------- | -------------------------------- | ---------------------------------------- |
| Slow queries     | Check `vm_slow_*` metrics        | Increase RAM, add vmselect replicas      |
| OOM crashes      | Check memory usage trends        | Reduce `-memory.allowedPercent`, add RAM |
| Disk full        | Check `vm_free_disk_space_bytes` | Reduce retention, add storage            |
| High cardinality | Use cardinality explorer         | Add relabeling rules to drop labels      |
| Insert delays    | Check `vm_rows_pending`          | Increase vminsert replicas               |

### Diagnostic Commands

```bash
# Check active queries
curl http://localhost:8428/api/v1/status/active_queries

# Check top queries
curl http://localhost:8428/api/v1/status/top_queries

# Check TSDB stats
curl http://localhost:8428/api/v1/status/tsdb

# Force flush in-memory data
curl http://localhost:8428/internal/force_flush

# Create snapshot
curl http://localhost:8428/snapshot/create

# Check cardinality
curl 'http://localhost:8428/api/v1/status/tsdb?topN=10'
```

### Logs Analysis

```bash
# Look for warnings
grep -i "warn\|error\|slow" /var/log/victoriametrics.log

# Common issues to look for:
# - "too many open files" → increase ulimits
# - "cannot allocate memory" → OOM, increase RAM
# - "slow" → RAM too low for cardinality
```

See `references/troubleshooting.md` for complete diagnostic guide.

---

## Backup & Restore

### Create Snapshot

```bash
# Create snapshot
curl http://localhost:8428/snapshot/create
# Returns: {"status":"ok","snapshot":"20240120_123456"}

# Backup with vmbackup
vmbackup \
  -storageDataPath=/var/lib/victoriametrics \
  -snapshot.createURL=http://localhost:8428/snapshot/create \
  -dst=s3://bucket/backups/$(date +%Y%m%d)
```

### Restore

```bash
vmrestore \
  -src=s3://bucket/backups/20240120 \
  -storageDataPath=/var/lib/victoriametrics
```

---

## References

- [VictoriaMetrics Docs](https://docs.victoriametrics.com/victoriametrics/)
- [Cluster Docs](https://docs.victoriametrics.com/victoriametrics/cluster-victoriametrics/)
- [vmagent Docs](https://docs.victoriametrics.com/victoriametrics/vmagent/)
- [vmctl Migration](https://docs.victoriametrics.com/victoriametrics/vmctl/)
- [MetricsQL](https://docs.victoriametrics.com/victoriametrics/metricsql/)
- [Helm Charts](https://github.com/VictoriaMetrics/helm-charts)
- [Operator](https://github.com/VictoriaMetrics/operator)
- See `references/` for detailed guides
