# ZooKeeper to KRaft Migration Guide

Complete guide for migrating Confluent Kafka from ZooKeeper mode to KRaft mode.

---

## Table of Contents

1. [KRaft Overview](#kraft-overview)
2. [Migration Prerequisites](#migration-prerequisites)
3. [Migration Strategies](#migration-strategies)
4. [In-Place Migration Procedure](#in-place-migration-procedure)
5. [Post-Migration Tasks](#post-migration-tasks)
6. [Troubleshooting](#troubleshooting)

---

## KRaft Overview

### What is KRaft?

KRaft (Kafka Raft) replaces ZooKeeper as the metadata management system:

| Aspect         | ZooKeeper Mode              | KRaft Mode                   |
| -------------- | --------------------------- | ---------------------------- |
| Metadata store | External ZooKeeper ensemble | Internal Raft quorum         |
| Failover       | Depends on ZK availability  | Built-in Raft consensus      |
| Latency        | ZK round-trip overhead      | Direct controller access     |
| Operations     | Manage 2 clusters           | Single Kafka cluster         |
| Scaling        | ZK becomes bottleneck       | Controller scales with Kafka |

### KRaft Architecture

```
ZooKeeper Mode                    KRaft Mode

┌─────────┐                       ┌─────────────────────┐
│   ZK1   │◄──────┐              │  Controller-1       │
├─────────┤       │              │  (voter, node.id=1) │
│   ZK2   │◄──────┼── Metadata   └─────────────────────┘
├─────────┤       │                        │
│   ZK3   │◄──────┘              ┌─────────────────────┐
└─────────┘                       │  Controller-2       │
     ▲                            │  (voter, node.id=2) │
     │                            └─────────────────────┘
┌────┴────┐                                │
│Broker-1 │                       ┌─────────────────────┐
├─────────┤                       │  Controller-3       │
│Broker-2 │                       │  (voter, node.id=3) │
├─────────┤                       └─────────────────────┘
│Broker-3 │                                │
└─────────┘                       ┌────────┴────────┐
                                  │                 │
                          ┌───────┴───┐     ┌───────┴───┐
                          │ Broker-1  │     │ Broker-N  │
                          │(node.id   │     │(node.id   │
                          │  =101)    │     │  =10N)    │
                          └───────────┘     └───────────┘
```

### Node Roles in KRaft

| Role           | process.roles       | Description                          |
| -------------- | ------------------- | ------------------------------------ |
| **Controller** | `controller`        | Manages metadata, handles leadership |
| **Broker**     | `broker`            | Handles client requests, stores data |
| **Combined**   | `controller,broker` | Both roles (small clusters only)     |

---

## Migration Prerequisites

### Version Requirements

```bash
# Minimum supported versions
# Source: Confluent 7.4+ (Kafka 3.4+)
# Target: Confluent 8.0+ (recommended)

# Check current version
/opt/confluent/bin/kafka-broker-api-versions --bootstrap-server localhost:9092 --version
```

### Cluster Requirements

```bash
# 1. All brokers must be on same version
grep -h broker.id /opt/confluent/etc/kafka/server.properties
# (run on each broker, versions should match)

# 2. No offline partitions
/opt/confluent/bin/kafka-topics --bootstrap-server localhost:9092 \
  --describe --unavailable-partitions

# 3. All replicas in-sync
/opt/confluent/bin/kafka-topics --bootstrap-server localhost:9092 \
  --describe --under-replicated-partitions

# 4. ZooKeeper healthy
echo ruok | nc localhost 2181  # Should return "imok"
```

### Hardware Requirements for Controllers

| Cluster Size   | Controllers | CPU (cores) | Memory | Disk (SSD) |
| -------------- | ----------- | ----------- | ------ | ---------- |
| < 50 brokers   | 3           | 4           | 8GB    | 50GB       |
| 50-100 brokers | 3           | 8           | 16GB   | 100GB      |
| > 100 brokers  | 5           | 16          | 32GB   | 200GB      |

---

## Migration Strategies

### Strategy 1: In-Place Migration (Recommended)

Migrate existing brokers to KRaft mode without rebuilding:

```
Pros:
✅ No data movement required
✅ Minimal downtime
✅ Preserves topic configurations

Cons:
❌ Rollback is complex after finalization
❌ Requires careful coordination
```

### Strategy 2: Parallel Cluster Migration

Build new KRaft cluster and migrate topics:

```
Pros:
✅ Clean separation
✅ Easy rollback (keep old cluster)
✅ Test in isolation

Cons:
❌ Double infrastructure cost during migration
❌ Requires MirrorMaker or replication setup
❌ Client reconfiguration required
```

---

## In-Place Migration Procedure

### Phase 1: Prepare for Migration

#### Step 1.1: Enable Migration Mode on Brokers

```properties
# Add to ALL broker server.properties

# Keep existing ZK config
zookeeper.connect=zk1:2181,zk2:2181,zk3:2181

# Add controller quorum (future controllers)
controller.quorum.voters=1@controller-01:9093,2@controller-02:9093,3@controller-03:9093
controller.listener.names=CONTROLLER
listener.security.protocol.map=CONTROLLER:PLAINTEXT,...existing...

# Enable migration
zookeeper.metadata.migration.enable=true
```

#### Step 1.2: Deploy Controller Nodes

Create dedicated controller nodes (or use combined mode for small clusters):

```properties
# /opt/confluent/etc/kafka/kraft/controller.properties

# Controller ONLY
process.roles=controller
node.id=1  # Unique per controller (1, 2, 3...)

# Controller quorum
controller.quorum.voters=1@controller-01:9093,2@controller-02:9093,3@controller-03:9093
controller.listener.names=CONTROLLER
listener.security.protocol.map=CONTROLLER:PLAINTEXT

# Listeners
listeners=CONTROLLER://0.0.0.0:9093

# Data directory
log.dirs=/var/kafka-controller-data

# Migration settings - connect to ZK to read metadata
zookeeper.connect=zk1:2181,zk2:2181,zk3:2181
zookeeper.metadata.migration.enable=true
```

#### Step 1.3: Format Controller Storage

```bash
# Generate cluster ID (ONCE, use same ID for all controllers)
CLUSTER_ID=$(/opt/confluent/bin/kafka-storage random-uuid)
echo $CLUSTER_ID > /backup/cluster-id.txt

# Format storage on each controller
/opt/confluent/bin/kafka-storage format \
  -t $CLUSTER_ID \
  -c /opt/confluent/etc/kafka/kraft/controller.properties
```

### Phase 2: Start Migration

#### Step 2.1: Start Controllers in Migration Mode

```bash
# On each controller node
sudo systemctl start confluent-kafka-controller

# Verify controllers formed quorum
/opt/confluent/bin/kafka-metadata --snapshot /var/kafka-controller-data/__cluster_metadata-0/00000000000000000000.log \
  --command quorum

# Expected output: 3 voters, 1 leader
```

#### Step 2.2: Rolling Restart Brokers

```bash
# Restart each broker (one at a time) to pick up migration config
sudo systemctl restart confluent-server

# Verify broker joined KRaft quorum
# Look for log message:
grep "Registered broker" /var/log/confluent/kafka/server.log | tail -1

# Verify migration is in progress
/opt/confluent/bin/kafka-metadata --snapshot /var/kafka-controller-data/__cluster_metadata-0/00000000000000000000.log \
  --command broker
```

#### Step 2.3: Verify Dual-Write Mode

During migration, metadata is written to both ZooKeeper and KRaft:

```bash
# Check ZK still has metadata
/opt/confluent/bin/zookeeper-shell localhost:2181 <<< "ls /brokers/ids"

# Check KRaft has metadata
/opt/confluent/bin/kafka-metadata --snapshot /var/kafka-controller-data/__cluster_metadata-0/00000000000000000000.log \
  --command topic

# Both should show same brokers/topics
```

### Phase 3: Finalize Migration

**⚠️ WARNING: After finalization, rollback requires restoring from backup**

#### Step 3.1: Pre-Finalization Checks

```bash
# Ensure all brokers are in KRaft mode
/opt/confluent/bin/kafka-metadata --snapshot /var/kafka-controller-data/__cluster_metadata-0/00000000000000000000.log \
  --command broker | wc -l
# Should match expected broker count

# Verify no under-replicated partitions
/opt/confluent/bin/kafka-topics --bootstrap-server localhost:9092 \
  --describe --under-replicated-partitions

# Final backup before finalization
tar -czvf /backup/pre-finalization-$(date +%Y%m%d).tar.gz /opt/confluent/etc /var/kafka-logs
```

#### Step 3.2: Finalize Migration

```bash
# Run finalization (from any controller)
/opt/confluent/bin/kafka-metadata-migration \
  --snapshot /var/kafka-controller-data/__cluster_metadata-0/00000000000000000000.log \
  --finalize

# Verify finalization
grep "migration.state" /var/log/confluent/kafka/controller.log | tail -1
# Should show: FULLY_MIGRATED
```

#### Step 3.3: Remove ZooKeeper Configuration

```bash
# Remove ZK config from all brokers
# Edit /opt/confluent/etc/kafka/server.properties

# REMOVE:
# zookeeper.connect=...
# zookeeper.metadata.migration.enable=true

# Rolling restart brokers
for broker in kafka-01 kafka-02 kafka-03; do
  ssh $broker "sudo systemctl restart confluent-server"
  sleep 120  # Wait for ISR sync
  # Verify no under-replicated partitions
done
```

#### Step 3.4: Decommission ZooKeeper

```bash
# Stop ZooKeeper services (after successful finalization)
for zk in zk1 zk2 zk3; do
  ssh $zk "sudo systemctl stop confluent-zookeeper"
  ssh $zk "sudo systemctl disable confluent-zookeeper"
done

# Archive ZK data for safety
tar -czvf /backup/zookeeper-final-$(date +%Y%m%d).tar.gz /var/zookeeper
```

---

## Post-Migration Tasks

### Update Ecosystem Components

#### Schema Registry

```properties
# Update schema-registry.properties
# REMOVE:
# kafkastore.connection.url=zk1:2181

# KEEP/ADD:
kafkastore.bootstrap.servers=kafka-01:9092,kafka-02:9092,kafka-03:9092
```

#### Kafka Connect

```properties
# Connect already uses bootstrap.servers, no ZK dependency
# Just verify configuration
bootstrap.servers=kafka-01:9092,kafka-02:9092,kafka-03:9092
```

#### Control Center

```properties
# Update control-center.properties
# REMOVE:
# zookeeper.connect=...

# KEEP:
bootstrap.servers=kafka-01:9092,kafka-02:9092,kafka-03:9092

# Restart Control Center
sudo systemctl restart confluent-control-center
```

### Update Monitoring

```yaml
# Prometheus targets - remove ZK metrics, add controller metrics
- job_name: "kafka-controllers"
  static_configs:
    - targets:
        ["controller-01:9999", "controller-02:9999", "controller-03:9999"]

# Remove:
- job_name: "zookeeper"
  static_configs:
    - targets: ["zk1:7000", "zk2:7000", "zk3:7000"]
```

### Update Ansible Inventory

```ini
# REMOVE:
# [zookeeper]
# zk1 ansible_host=...

# ADD:
[controllers]
controller-01 ansible_host=10.0.1.1 node_id=1
controller-02 ansible_host=10.0.1.2 node_id=2
controller-03 ansible_host=10.0.1.3 node_id=3
```

---

## Troubleshooting

### Common Issues

| Issue                         | Diagnosis                  | Solution                                   |
| ----------------------------- | -------------------------- | ------------------------------------------ |
| Controllers won't form quorum | Network or config mismatch | Verify voter config matches on all nodes   |
| Brokers not registering       | Missing migration config   | Add `zookeeper.metadata.migration.enable`  |
| Metadata mismatch             | Dual-write failed          | Check controller logs, restart controllers |
| Finalization fails            | Not all brokers in KRaft   | Verify all brokers have restarted          |
| Client connection failures    | Listener config issues     | Verify `advertised.listeners` settings     |

### Debug Commands

```bash
# Controller logs
tail -100 /var/log/confluent/kafka/controller.log

# Check controller state
/opt/confluent/bin/kafka-metadata --snapshot /var/kafka-controller-data/__cluster_metadata-0/00000000000000000000.log \
  --command describe

# Verify quorum health
/opt/confluent/bin/kafka-metadata --snapshot /var/kafka-controller-data/__cluster_metadata-0/00000000000000000000.log \
  --command quorum

# Check migration state
grep -i "migration" /var/log/confluent/kafka/controller.log | tail -20

# Verify broker registration
/opt/confluent/bin/kafka-metadata --snapshot /var/kafka-controller-data/__cluster_metadata-0/00000000000000000000.log \
  --command broker

# Check metadata log size (should be reasonable, < 1GB typically)
du -sh /var/kafka-controller-data/__cluster_metadata-0/
```

### Rollback (Pre-Finalization Only)

If migration fails BEFORE finalization:

```bash
# 1. Stop controllers
sudo systemctl stop confluent-kafka-controller

# 2. Remove migration config from brokers
sed -i '/controller.quorum.voters/d' /opt/confluent/etc/kafka/server.properties
sed -i '/zookeeper.metadata.migration.enable/d' /opt/confluent/etc/kafka/server.properties

# 3. Rolling restart brokers
for broker in kafka-01 kafka-02 kafka-03; do
  ssh $broker "sudo systemctl restart confluent-server"
  sleep 60
done

# 4. Verify brokers reconnected to ZK
/opt/confluent/bin/zookeeper-shell localhost:2181 <<< "ls /brokers/ids"
```

### Post-Finalization Rollback

**⚠️ Requires full restore from backup - contact Confluent Support**

```bash
# 1. Stop all Kafka services
for host in kafka-01 kafka-02 kafka-03; do
  ssh $host "sudo systemctl stop confluent-server"
done

# 2. Restore ZooKeeper
tar -xzf /backup/zookeeper-pre-migration.tar.gz -C /

# 3. Restore Kafka configs and data
tar -xzf /backup/kafka-pre-migration.tar.gz -C /

# 4. Start ZooKeeper, then Kafka
# (Follow standard disaster recovery procedures)
```
