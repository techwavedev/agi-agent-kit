# VictoriaMetrics Troubleshooting Reference

Complete diagnostic and troubleshooting guide.

## Diagnostic Endpoints

### Health & Status

```bash
# Health check
curl http://localhost:8428/health

# Metrics (self-monitoring)
curl http://localhost:8428/metrics

# TSDB status
curl http://localhost:8428/api/v1/status/tsdb

# Active queries
curl http://localhost:8428/api/v1/status/active_queries

# Top queries by duration
curl http://localhost:8428/api/v1/status/top_queries

# Flags
curl http://localhost:8428/flags
```

### Cluster-Specific

```bash
# vmstorage status
curl http://vmstorage:8482/-/healthy

# vmselect status
curl http://vmselect:8481/health

# vminsert status
curl http://vminsert:8480/health

# Storage nodes from vmselect
curl http://vmselect:8481/api/v1/status/vmstorage
```

---

## Common Issues & Solutions

### Out of Memory (OOM)

**Symptoms:**

- Process killed by OOM killer
- Slow queries
- `vm_slow_row_inserts_total` increasing

**Diagnosis:**

```bash
# Check memory usage
curl -s http://localhost:8428/metrics | grep process_resident_memory
curl -s http://localhost:8428/metrics | grep vm_slow

# Check active series
curl http://localhost:8428/api/v1/status/tsdb
```

**Solutions:**

```bash
# 1. Reduce memory usage
-memory.allowedPercent=60  # Default is 80

# 2. Limit concurrent queries
-search.maxConcurrentRequests=8

# 3. Add RAM or scale out
```

---

### High Cardinality

**Symptoms:**

- Slow ingestion
- High memory usage
- `vm_hourly_series_limit_*` alerts

**Diagnosis:**

```bash
# Check cardinality
curl 'http://localhost:8428/api/v1/status/tsdb?topN=20'

# Metric with most series
curl 'http://localhost:8428/api/v1/status/tsdb?topN=10&focusLabel=__name__'

# High churn labels
curl 'http://localhost:8428/api/v1/status/tsdb?topN=10&focusLabel=pod'
```

**Solutions:**

```yaml
# 1. Drop high-cardinality labels in vmagent
relabel_configs:
  - action: labeldrop
    regex: (pod_template_hash|controller_revision_hash)

# 2. Set cardinality limits
-storage.maxHourlySeries=5000000
-storage.maxDailySeries=10000000

# 3. Use streaming aggregation to reduce cardinality
```

---

### Slow Queries

**Symptoms:**

- Query timeouts
- High latency in Grafana
- `vm_slow_*` metrics increasing

**Diagnosis:**

```bash
# Check current queries
curl http://localhost:8428/api/v1/status/active_queries

# Check top slow queries
curl http://localhost:8428/api/v1/status/top_queries

# Profile a query
curl 'http://localhost:8428/api/v1/query?query=your_query{}&trace=1'
```

**Solutions:**

```bash
# 1. Optimize query
# Use specific labels, limit time range

# 2. Increase workers for heavy queries
-search.maxWorkersPerQuery=16

# 3. Add caching
-search.cacheTimestampOffset=10m

# 4. Scale vmselect horizontally
```

---

### Disk Space Issues

**Symptoms:**

- Alerts on low disk space
- Insert failures
- Forced merge failures

**Diagnosis:**

```bash
# Check disk space
curl -s http://localhost:8428/metrics | grep vm_free_disk_space
curl -s http://localhost:8428/metrics | grep vm_data_size

# Check partition usage
df -h /var/lib/victoriametrics
```

**Solutions:**

```bash
# 1. Reduce retention
-retentionPeriod=30d

# 2. Enable downsampling
-downsampling.period=7d:1m,30d:5m,90d:1h

# 3. Delete old data
curl -X POST 'http://localhost:8428/api/v1/admin/tsdb/delete_series?match[]={__name__="unwanted_metric"}'

# 4. Force merge to reclaim space
curl http://localhost:8428/internal/forceMerge
```

---

### Replication Issues (Cluster)

**Symptoms:**

- Query returns incomplete data
- vmstorage nodes out of sync
- Alerts on replica lag

**Diagnosis:**

```bash
# Check storage node health
for i in 0 1 2; do
  curl http://vmstorage-$i:8482/-/healthy
done

# Check replication status from vmselect
curl http://vmselect:8481/api/v1/status/vmstorage
```

**Solutions:**

```bash
# 1. Ensure replicationFactor matches node count
-replicationFactor=2

# 2. Enable deduplication
-dedup.minScrapeInterval=15s

# 3. Check network connectivity between nodes
```

---

### Ingestion Delays

**Symptoms:**

- Data not appearing immediately
- Lag in dashboards

**Diagnosis:**

```bash
# Check pending rows
curl -s http://localhost:8428/metrics | grep vm_rows_pending

# Check insert rate
curl -s http://localhost:8428/metrics | grep vm_rows_inserted_total
```

**Solutions:**

```bash
# 1. Force flush (for testing)
curl http://localhost:8428/internal/force_flush

# 2. Reduce flush interval
-inmemoryDataFlushInterval=5s

# 3. Scale vminsert for cluster
```

---

### Connection Issues

**Symptoms:**

- "connection refused" errors
- Timeouts from vmagent

**Diagnosis:**

```bash
# Test connectivity
curl -v http://victoriametrics:8428/health

# Check listening ports
netstat -tlnp | grep victoria

# Check firewall/security groups
```

**Solutions:**

```bash
# 1. Check bind address
-httpListenAddr=0.0.0.0:8428

# 2. Check Kubernetes service
kubectl get svc -n monitoring

# 3. Check network policies
kubectl get networkpolicy -n monitoring
```

---

### Data Loss Concerns

**Symptoms:**

- Missing data points
- Gaps in graphs

**Diagnosis:**

```bash
# Check for unclean shutdowns
grep -i "unclean\|crash\|oom" /var/log/victoriametrics.log

# Check insert success
curl -s http://localhost:8428/metrics | grep vm_http_request_errors_total
```

**Solutions:**

```bash
# 1. Ensure graceful shutdown
kill -INT $(pidof victoria-metrics)

# 2. Configure proper liveness probes in K8s
# 3. Regular backups with vmbackup
```

---

## Log Analysis

### Key Log Patterns

```bash
# Errors
grep -i "error\|warn\|fatal" /var/log/victoriametrics.log

# Slow operations
grep -i "slow" /var/log/victoriametrics.log

# OOM warnings
grep -i "memory\|oom\|cannot allocate" /var/log/victoriametrics.log

# Disk issues
grep -i "disk\|storage\|no space" /var/log/victoriametrics.log
```

### Log Level

```bash
# Increase log verbosity temporarily
-loggerLevel=INFO  # Options: INFO, WARN, ERROR
```

---

## Profiling

### CPU Profile

```bash
curl http://localhost:8428/debug/pprof/profile?seconds=30 > cpu.prof
go tool pprof cpu.prof
```

### Memory Profile

```bash
curl http://localhost:8428/debug/pprof/heap > heap.prof
go tool pprof heap.prof
```

### Goroutine Dump

```bash
curl http://localhost:8428/debug/pprof/goroutine?debug=1
```

---

## Recovery Procedures

### Restore from Backup

```bash
# Stop VictoriaMetrics
systemctl stop victoriametrics

# Clear data directory
rm -rf /var/lib/victoriametrics/*

# Restore
vmrestore \
  -src=s3://bucket/backups/20240120 \
  -storageDataPath=/var/lib/victoriametrics

# Start VictoriaMetrics
systemctl start victoriametrics
```

### Repair Corrupted Data

```bash
# Stop VictoriaMetrics
systemctl stop victoriametrics

# Remove cache (safe)
rm -rf /var/lib/victoriametrics/cache

# If index is corrupted, rebuild from data
# (may take time for large datasets)
rm -rf /var/lib/victoriametrics/indexdb

# Start - index will rebuild
systemctl start victoriametrics
```

---

## Metrics to Monitor

### Critical Metrics

| Metric                                   | Alert Threshold | Action                                  |
| ---------------------------------------- | --------------- | --------------------------------------- |
| `vm_free_disk_space_bytes`               | < 20GB          | Expand disk or reduce retention         |
| `process_resident_memory_bytes`          | > 85% limit     | Add RAM or reduce memory.allowedPercent |
| `rate(vm_slow_row_inserts_total[5m])`    | > 0             | RAM too low for cardinality             |
| `rate(vm_http_request_errors_total[5m])` | > 0             | Check logs for errors                   |
| `vm_active_merges`                       | High sustained  | Disk I/O bottleneck                     |

### Key Dashboard Queries

```promql
# Ingestion rate
rate(vm_rows_inserted_total[5m])

# Query rate
rate(vm_http_requests_total{path=~"/api/v1/query.*"}[5m])

# Memory usage
process_resident_memory_bytes / 1024 / 1024 / 1024

# Disk usage
vm_data_size_bytes / 1024 / 1024 / 1024

# Active time series
vm_cache_entries{type="storage/hour_metric_ids"}
```
