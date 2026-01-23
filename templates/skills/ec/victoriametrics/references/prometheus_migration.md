# Prometheus Migration Reference

Complete guide for migrating from Prometheus to VictoriaMetrics.

## Migration Approaches

### 1. Dual-Write (Recommended)

Run Prometheus and VictoriaMetrics in parallel during migration.

```yaml
# prometheus.yml - Add remote_write
remote_write:
  - url: http://victoriametrics:8428/api/v1/write
    queue_config:
      max_samples_per_send: 10000
      capacity: 20000
      max_shards: 30
```

### 2. Replace Prometheus with vmagent

vmagent is a drop-in replacement for Prometheus scraping.

```bash
# vmagent uses same prometheus.yml format
vmagent \
  -promscrape.config=/etc/prometheus/prometheus.yml \
  -remoteWrite.url=http://victoriametrics:8428/api/v1/write
```

### 3. Historical Data Migration

Use vmctl to migrate existing data.

```bash
# From Prometheus snapshot
vmctl prometheus \
  --prom-snapshot=/var/lib/prometheus/data \
  --vm-addr=http://victoriametrics:8428 \
  --vm-concurrency=8 \
  --vm-batch-size=200000
```

---

## vmctl Migration Tool

### From Prometheus

```bash
# Step 1: Create Prometheus snapshot
curl -X POST http://prometheus:9090/api/v1/admin/tsdb/snapshot

# Step 2: Migrate snapshot
vmctl prometheus \
  --prom-snapshot=/var/lib/prometheus/snapshots/20240120T000000Z-xxx \
  --vm-addr=http://victoriametrics:8428 \
  --vm-concurrency=8

# With time filter
vmctl prometheus \
  --prom-snapshot=/path/to/snapshot \
  --vm-addr=http://victoriametrics:8428 \
  --prom-filter-time-start='2024-01-01T00:00:00Z' \
  --prom-filter-time-end='2024-01-31T23:59:59Z'
```

### From InfluxDB

```bash
vmctl influx \
  --influx-addr=http://influxdb:8086 \
  --influx-database=metrics \
  --influx-retention-policy=autogen \
  --vm-addr=http://victoriametrics:8428 \
  --vm-concurrency=8
```

### From Thanos

```bash
# Export from Thanos to Prometheus format, then use vmctl
thanos tools bucket replicate \
  --objstore.config-file=bucket.yml \
  --output-dir=/tmp/thanos-export

# Then migrate as Prometheus
vmctl prometheus \
  --prom-snapshot=/tmp/thanos-export \
  --vm-addr=http://victoriametrics:8428
```

### Between VictoriaMetrics Instances

```bash
# Native migration (fastest)
vmctl vm-native \
  --vm-native-src-addr=http://source-vm:8428 \
  --vm-native-dst-addr=http://dest-vm:8428 \
  --vm-native-filter-match='{__name__=~".*"}' \
  --vm-native-filter-time-start='2024-01-01T00:00:00Z' \
  --vm-concurrency=8
```

---

## Configuration Mapping

### Prometheus to VictoriaMetrics Flags

| Prometheus                           | VictoriaMetrics                 |
| ------------------------------------ | ------------------------------- |
| `--storage.tsdb.path`                | `-storageDataPath`              |
| `--storage.tsdb.retention.time`      | `-retentionPeriod`              |
| `--web.listen-address`               | `-httpListenAddr`               |
| `--query.timeout`                    | `-search.maxQueryDuration`      |
| `--query.max-concurrency`            | `-search.maxConcurrentRequests` |
| `--web.enable-remote-write-receiver` | (enabled by default)            |

### Prometheus to vmagent Flags

| Prometheus             | vmagent                    |
| ---------------------- | -------------------------- |
| `--config.file`        | `-promscrape.config`       |
| `--web.listen-address` | `-httpListenAddr`          |
| N/A                    | `-remoteWrite.url`         |
| N/A                    | `-remoteWrite.tmpDataPath` |

---

## Query Migration

### PromQL to MetricsQL

Most PromQL queries work unchanged. Key differences:

| Feature            | PromQL          | MetricsQL                    |
| ------------------ | --------------- | ---------------------------- |
| Rate detection     | Manual interval | Auto detection               |
| Subqueries         | Limited         | Extended support             |
| Label manipulation | Limited         | `label_set()`, `label_del()` |
| Rollups            | Single function | Multi-function `rollup()`    |

### Query Examples

```promql
# PromQL
rate(http_requests_total[5m])

# MetricsQL (same, or use default auto-interval)
rate(http_requests_total)

# MetricsQL extras
rollup(http_requests_total)  # Returns min, max, avg
range_quantile(0.95, http_requests_total[1h])
```

---

## Grafana Migration

### Change Data Source

```yaml
# Grafana datasource config
apiVersion: 1
datasources:
  - name: VictoriaMetrics
    type: prometheus # Same type!
    url: http://victoriametrics:8428
    access: proxy
    isDefault: true
```

### Dashboard Compatibility

Most Prometheus dashboards work without changes. Adjust for:

1. **Rate intervals**: MetricsQL auto-detects, remove `[5m]` if needed
2. **Recording rules**: Migrate to vmalert format
3. **Alerting rules**: Migrate to vmalert format

---

## Recording Rules Migration

### Prometheus Format

```yaml
# prometheus-rules.yml
groups:
  - name: example
    rules:
      - record: job:http_requests:rate5m
        expr: rate(http_requests_total[5m])
```

### vmalert Format

```yaml
# Same format works!
groups:
  - name: example
    rules:
      - record: job:http_requests:rate5m
        expr: rate(http_requests_total[5m])
```

Deploy with vmalert:

```bash
vmalert \
  -rule=/etc/vmalert/rules/*.yml \
  -datasource.url=http://victoriametrics:8428 \
  -remoteWrite.url=http://victoriametrics:8428/api/v1/write
```

---

## Alerting Rules Migration

### Prometheus Format

```yaml
groups:
  - name: alerts
    rules:
      - alert: HighRequestLatency
        expr: http_request_duration_seconds{quantile="0.9"} > 1
        for: 10m
        labels:
          severity: critical
        annotations:
          summary: High request latency
```

### vmalert (Same Format)

```yaml
# vmalert uses identical format
groups:
  - name: alerts
    rules:
      - alert: HighRequestLatency
        expr: http_request_duration_seconds{quantile="0.9"} > 1
        for: 10m
        labels:
          severity: critical
        annotations:
          summary: High request latency
```

---

## Federation Migration

### Prometheus Federation

```yaml
# prometheus.yml
scrape_configs:
  - job_name: "federate"
    honor_labels: true
    metrics_path: "/federate"
    params:
      "match[]":
        - '{job="prometheus"}'
    static_configs:
      - targets: ["prometheus:9090"]
```

### VictoriaMetrics Alternative

Use vmagent with multiple remote_write targets:

```yaml
global:
  external_labels:
    cluster: source

scrape_configs:
  - job_name: "local"
    static_configs:
      - targets: ["localhost:9100"]

# vmagent sends to central VM
# No federation needed - direct remote_write
```

---

## Multi-Tenant Migration

### Prometheus + Thanos Multi-Tenancy

Thanos uses external labels for tenancy.

### VictoriaMetrics Cluster Multi-Tenancy

```bash
# Write to tenant 123
curl -X POST 'http://vminsert:8480/insert/123/prometheus/api/v1/write' \
  --data-binary @metrics.txt

# Query tenant 123
curl 'http://vmselect:8481/select/123/prometheus/api/v1/query?query=up'
```

---

## Validation Checklist

After migration, verify:

- [ ] All metrics visible in VictoriaMetrics
- [ ] Grafana dashboards loading correctly
- [ ] Alerting rules firing as expected
- [ ] Historical data queryable
- [ ] Recording rules generating data
- [ ] Scrape targets healthy
- [ ] No duplicate data sources in Grafana

---

## Rollback Plan

If issues occur:

1. Keep Prometheus running in parallel
2. Switch Grafana back to Prometheus datasource
3. Re-enable Prometheus alerting
4. Investigate VictoriaMetrics logs
