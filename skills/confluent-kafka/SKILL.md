---
name: confluent-kafka
description: Confluent Kafka specialist for tarball/Ansible custom installations. Expert in updating, maintaining, checking health, troubleshooting, documenting, analyzing metrics, and upgrading Confluent Kafka deployments from 7.x to 8.x versions. Covers KRaft mode (ZooKeeper-less), broker configuration, Schema Registry, Connect, ksqlDB, Control Center, and production-grade operations. Use when working with Confluent Platform installations, migrations to KRaft, performance tuning, health monitoring, and infrastructure-as-code with Ansible.
---

# Confluent Kafka Skill

Comprehensive skill for managing Confluent Platform Kafka clusters deployed via tarball distributions and automated with Ansible.

> **Last Updated:** 2026-01-20 from [Confluent Documentation](https://docs.confluent.io/)

---

## Quick Start

```bash
# SSH to a broker node and check Kafka status
ssh kafka-broker-01

# Verify broker is running
systemctl status confluent-server

# Check cluster health with broker ID
/opt/confluent/bin/kafka-broker-api-versions --bootstrap-server localhost:9092

# List active brokers in KRaft mode
/opt/confluent/bin/kafka-metadata --snapshot /var/kafka-logs/__cluster_metadata-0/00000000000000000000.log --command broker

# Check consumer group lag
/opt/confluent/bin/kafka-consumer-groups --bootstrap-server localhost:9092 --all-groups --describe
```

---

## Core Concepts

### Confluent Platform Components

| Component            | Description                              | Default Port |
| -------------------- | ---------------------------------------- | ------------ |
| **Kafka Broker**     | Core message broker (confluent-server)   | 9092         |
| **KRaft Controller** | Metadata management (replaces ZooKeeper) | 9093         |
| **Schema Registry**  | Avro/JSON/Protobuf schema management     | 8081         |
| **Kafka Connect**    | Data integration connectors              | 8083         |
| **ksqlDB**           | Stream processing with SQL               | 8088         |
| **Control Center**   | Web-based management UI                  | 9021         |
| **REST Proxy**       | HTTP interface to Kafka                  | 8082         |

### KRaft Architecture (8.x Native)

```
┌─────────────────────────────────────────────────────────────────┐
│  Confluent Kafka KRaft Cluster                                  │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Controller Quorum (Raft Consensus)                     │   │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐    │   │
│  │  │Controller-01 │ │Controller-02 │ │Controller-03 │    │   │
│  │  │  (voter)     │ │  (voter)     │ │  (voter)     │    │   │
│  │  └──────────────┘ └──────────────┘ └──────────────┘    │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                  │
│              Metadata updates via Raft                          │
│                              ▼                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Broker Nodes                                           │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐   │   │
│  │  │Broker-01 │ │Broker-02 │ │Broker-03 │ │Broker-N  │   │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘   │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Ecosystem Services                                     │   │
│  │  Schema Registry │ Connect │ ksqlDB │ Control Center   │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### Tarball Installation Layout

```
/opt/confluent/                      # Installation root
├── bin/                             # CLI tools (kafka-*, confluent-*)
├── etc/                             # Configuration templates
│   ├── kafka/
│   │   ├── server.properties        # Broker configuration
│   │   ├── kraft/                   # KRaft configs
│   │   └── log4j.properties
│   ├── schema-registry/
│   ├── kafka-connect/
│   └── control-center/
├── lib/                             # JARs and libraries
├── share/                           # Documentation
└── logs/                            # Application logs

/var/kafka-logs/                     # Data directory (broker logs)
├── __cluster_metadata-0/            # KRaft metadata log
├── __consumer_offsets-*/
└── <topic>-<partition>/

/var/log/confluent/                  # Service logs
├── kafka/
├── schema-registry/
└── control-center/
```

---

## Common Workflows

### 1. Check Cluster Health

```bash
# Broker status
systemctl status confluent-server

# Controller quorum status (KRaft)
/opt/confluent/bin/kafka-metadata \
  --snapshot /var/kafka-logs/__cluster_metadata-0/00000000000000000000.log \
  --command quorum

# Under-replicated partitions
/opt/confluent/bin/kafka-topics --bootstrap-server localhost:9092 \
  --describe --under-replicated-partitions

# Offline partitions (CRITICAL)
/opt/confluent/bin/kafka-topics --bootstrap-server localhost:9092 \
  --describe --unavailable-partitions

# Broker disk usage
df -h /var/kafka-logs

# JVM heap usage
jstat -gc $(pgrep -f kafka.Kafka) 1000 5
```

### 2. Monitor Consumer Lag

```bash
# All consumer groups
/opt/confluent/bin/kafka-consumer-groups --bootstrap-server localhost:9092 \
  --all-groups --describe

# Specific group
/opt/confluent/bin/kafka-consumer-groups --bootstrap-server localhost:9092 \
  --group my-consumer-group --describe

# Export lag metrics (for monitoring integration)
/opt/confluent/bin/kafka-consumer-groups --bootstrap-server localhost:9092 \
  --all-groups --describe | awk 'NR>1 {sum+=$6} END {print "Total Lag: " sum}'
```

### 3. Schema Registry Operations

```bash
# Check Schema Registry health
curl -s http://localhost:8081/ | jq

# List all subjects
curl -s http://localhost:8081/subjects | jq

# Get schema versions for a subject
curl -s http://localhost:8081/subjects/my-topic-value/versions | jq

# Get specific schema
curl -s http://localhost:8081/subjects/my-topic-value/versions/latest | jq

# Check compatibility
curl -X POST -H "Content-Type: application/vnd.schemaregistry.v1+json" \
  --data '{"schema": "{\"type\":\"record\",\"name\":\"Test\",\"fields\":[{\"name\":\"id\",\"type\":\"int\"}]}"}' \
  http://localhost:8081/compatibility/subjects/my-topic-value/versions/latest | jq
```

### 4. Connect Cluster Operations

```bash
# Connect worker status
curl -s http://localhost:8083/ | jq

# List connectors
curl -s http://localhost:8083/connectors | jq

# Connector status
curl -s http://localhost:8083/connectors/my-connector/status | jq

# Restart failed tasks
curl -X POST http://localhost:8083/connectors/my-connector/tasks/0/restart

# View connector config
curl -s http://localhost:8083/connectors/my-connector/config | jq
```

---

## Upgrade Guide: 7.x to 8.x

### Key Changes in 8.x

| Change                | Impact                                   |
| --------------------- | ---------------------------------------- |
| **KRaft GA**          | ZooKeeper deprecated, KRaft recommended  |
| **Java 17+**          | Minimum Java version requirement         |
| **Deprecated APIs**   | kafka-preferred-replica-election removed |
| **New Metrics**       | Enhanced KRaft controller metrics        |
| **Security Defaults** | Stricter TLS requirements                |

### Pre-Upgrade Checklist

```bash
# 1. Check current version
/opt/confluent/bin/kafka-broker-api-versions --version

# 2. Verify Java version (must be 17+)
java -version

# 3. Backup configurations
tar -czvf /backup/confluent-config-$(date +%Y%m%d).tar.gz /opt/confluent/etc/

# 4. Export topic configurations
/opt/confluent/bin/kafka-configs --bootstrap-server localhost:9092 \
  --entity-type topics --all --describe > /backup/topic-configs.txt

# 5. Check for deprecated configurations
grep -r "log.message.format.version\|inter.broker.protocol.version" /opt/confluent/etc/kafka/

# 6. Verify cluster health
/opt/confluent/bin/kafka-topics --bootstrap-server localhost:9092 \
  --describe --under-replicated-partitions
```

### Reference Files

- **[references/upgrade_7x_to_8x.md](references/upgrade_7x_to_8x.md)** — Complete 7.x to 8.x migration guide
- **[references/kraft_migration.md](references/kraft_migration.md)** — ZooKeeper to KRaft migration steps
- **[references/ansible_playbooks.md](references/ansible_playbooks.md)** — Ansible automation patterns

---

## Troubleshooting Guide

### Common Issues

| Issue                      | Diagnosis                                  | Solution                                      |
| -------------------------- | ------------------------------------------ | --------------------------------------------- |
| **Broker won't start**     | Check logs `/var/log/confluent/kafka/`     | Fix config, check disk space, verify ports    |
| **Controller quorum lost** | `kafka-metadata` shows <3 voters           | Restore failed controllers, check network     |
| **High consumer lag**      | Consumer processing slower than production | Scale consumers, optimize processing          |
| **ISR shrinking**          | Followers falling behind leader            | Check network, disk I/O, increase replica lag |
| **Schema Registry 409**    | Schema incompatibility                     | Check compatibility mode, use FULL_TRANSITIVE |
| **Connect task failed**    | Connector config or target system issue    | Check task status, review error in config     |
| **OOM on broker**          | Heap exhaustion                            | Tune JVM heap, check for memory leaks         |

### Debug Commands

```bash
# Kafka server logs (last 100 lines)
tail -100 /var/log/confluent/kafka/server.log

# Controller logs (KRaft)
tail -100 /var/log/confluent/kafka/controller.log

# Check open file descriptors
lsof -p $(pgrep -f kafka.Kafka) | wc -l

# Network connections to broker
netstat -an | grep 9092 | wc -l

# Thread dump for debugging hung brokers
jstack $(pgrep -f kafka.Kafka) > /tmp/kafka-thread-dump.txt

# GC logs analysis
grep "GC pause" /var/log/confluent/kafka/kafka-gc.log | tail -20

# KRaft metadata diagnostics
/opt/confluent/bin/kafka-metadata \
  --snapshot /var/kafka-logs/__cluster_metadata-0/00000000000000000000.log \
  --command topic --topics __consumer_offsets
```

---

## Ansible Automation

### Inventory Structure

```ini
# inventory/confluent.ini
[controllers]
kafka-controller-01 ansible_host=10.0.1.11 broker_id=1
kafka-controller-02 ansible_host=10.0.1.12 broker_id=2
kafka-controller-03 ansible_host=10.0.1.13 broker_id=3

[brokers]
kafka-broker-01 ansible_host=10.0.2.11 broker_id=101
kafka-broker-02 ansible_host=10.0.2.12 broker_id=102
kafka-broker-03 ansible_host=10.0.2.13 broker_id=103

[schema_registry]
kafka-sr-01 ansible_host=10.0.3.11

[connect]
kafka-connect-01 ansible_host=10.0.4.11

[control_center]
kafka-cc-01 ansible_host=10.0.5.11

[confluent:children]
controllers
brokers
schema_registry
connect
control_center

[confluent:vars]
confluent_version=8.0.0
kafka_kraft_enabled=true
kafka_listener_security_protocol=SASL_SSL
kafka_sasl_mechanism=PLAIN
```

### Common Playbook Tasks

```yaml
# roles/confluent-kafka/tasks/upgrade.yml
- name: Stop Kafka broker gracefully
  ansible.builtin.systemd:
    name: confluent-server
    state: stopped
  register: service_stop

- name: Wait for controlled shutdown
  ansible.builtin.wait_for:
    port: 9092
    state: stopped
    timeout: 300

- name: Backup current installation
  ansible.builtin.archive:
    path: /opt/confluent
    dest: "/backup/confluent-{{ ansible_date_time.date }}.tar.gz"
    format: gz

- name: Extract new Confluent version
  ansible.builtin.unarchive:
    src: "confluent-{{ confluent_version }}.tar.gz"
    dest: /opt/
    remote_src: no

- name: Update symlink
  ansible.builtin.file:
    src: "/opt/confluent-{{ confluent_version }}"
    dest: /opt/confluent
    state: link

- name: Start Kafka broker
  ansible.builtin.systemd:
    name: confluent-server
    state: started
    enabled: yes
```

### Reference Files

- **[references/ansible_playbooks.md](references/ansible_playbooks.md)** — Complete Ansible automation patterns

---

## Metrics and Monitoring

### Key JMX Metrics

```bash
# Using kafka JMX tool
export JMX_PORT=9999

# Under-replicated partitions (should be 0)
kafka.server:type=ReplicaManager,name=UnderReplicatedPartitions

# Active controller count (should be 1 in cluster)
kafka.controller:type=KafkaController,name=ActiveControllerCount

# Request handler idle ratio (should be > 0.3)
kafka.server:type=KafkaRequestHandlerPool,name=RequestHandlerAvgIdlePercent

# Network processor idle ratio
kafka.network:type=SocketServer,name=NetworkProcessorAvgIdlePercent

# Log flush latency
kafka.log:type=LogFlushStats,name=LogFlushRateAndTimeMs

# Bytes in/out per second
kafka.server:type=BrokerTopicMetrics,name=BytesInPerSec
kafka.server:type=BrokerTopicMetrics,name=BytesOutPerSec
```

### Prometheus Integration

```yaml
# prometheus-kafka-exporter config
# Add to server.properties
kafka_jmx_exporter:
  jmx_url: "service:jmx:rmi:///jndi/rmi://localhost:9999/jmxrmi"
  lowercaseOutputName: true
  lowercaseOutputLabelNames: true
  whitelistObjectNames:
    - "kafka.server:type=BrokerTopicMetrics,*"
    - "kafka.server:type=ReplicaManager,*"
    - "kafka.controller:type=KafkaController,*"
    - "kafka.server:type=KafkaRequestHandlerPool,*"
```

### Health Check Script

Run the health check script for comprehensive cluster analysis:

```bash
python skills/confluent-kafka/scripts/kafka_health_check.py \
  --bootstrap-servers kafka-01:9092,kafka-02:9092,kafka-03:9092 \
  --output reports/kafka/health/
```

---

## Configuration Best Practices

### Production Broker Settings

```properties
# /opt/confluent/etc/kafka/server.properties

# KRaft mode settings
process.roles=broker
node.id=101
controller.quorum.voters=1@kafka-controller-01:9093,2@kafka-controller-02:9093,3@kafka-controller-03:9093
controller.listener.names=CONTROLLER
inter.broker.listener.name=INTERNAL

# Listeners
listeners=INTERNAL://0.0.0.0:9092,EXTERNAL://0.0.0.0:9094
listener.security.protocol.map=INTERNAL:SASL_SSL,EXTERNAL:SASL_SSL,CONTROLLER:SASL_SSL
advertised.listeners=INTERNAL://kafka-01.internal:9092,EXTERNAL://kafka-01.external:9094

# Performance tuning
num.network.threads=8
num.io.threads=16
socket.send.buffer.bytes=102400
socket.receive.buffer.bytes=102400
socket.request.max.bytes=104857600

# Log settings
log.dirs=/var/kafka-logs
num.partitions=12
default.replication.factor=3
min.insync.replicas=2
log.retention.hours=168
log.segment.bytes=1073741824
log.retention.check.interval.ms=300000

# Replication
replica.lag.time.max.ms=30000
num.replica.fetchers=4
replica.fetch.max.bytes=1048576

# Compression
compression.type=producer

# Security
authorizer.class.name=kafka.security.authorizer.AclAuthorizer
super.users=User:admin
ssl.keystore.location=/var/ssl/kafka/kafka.keystore.jks
ssl.truststore.location=/var/ssl/kafka/kafka.truststore.jks
```

### JVM Tuning

```properties
# /opt/confluent/etc/kafka/jvm.config
# For 64GB RAM server with 32GB heap

-Xms24g
-Xmx24g
-XX:MetaspaceSize=256m
-XX:MaxMetaspaceSize=512m
-XX:+UseG1GC
-XX:MaxGCPauseMillis=20
-XX:InitiatingHeapOccupancyPercent=35
-XX:G1HeapRegionSize=16m
-XX:MinMetaspaceFreeRatio=50
-XX:MaxMetaspaceFreeRatio=80
-XX:+ExplicitGCInvokesConcurrent
-XX:+PrintFlagsFinal
-XX:+UnlockDiagnosticVMOptions
-XX:+UseCompressedOops
-Djava.awt.headless=true
```

---

## Scripts

### Cluster Health Report

```bash
# Generate comprehensive health report
python skills/confluent-kafka/scripts/kafka_health_check.py \
  --bootstrap-servers kafka-01:9092,kafka-02:9092,kafka-03:9092 \
  --output reports/kafka/health/ \
  --format both

# Quick status check only
python skills/confluent-kafka/scripts/kafka_health_check.py \
  --bootstrap-servers localhost:9092 \
  --quick
```

### Configuration Validator

```bash
# Validate server.properties before deployment
python skills/confluent-kafka/scripts/validate_config.py \
  --config /opt/confluent/etc/kafka/server.properties \
  --version 8.0

# Compare configurations across brokers
python skills/confluent-kafka/scripts/validate_config.py \
  --compare broker-01:/opt/confluent/etc/kafka/server.properties \
            broker-02:/opt/confluent/etc/kafka/server.properties
```

### Upgrade Pre-flight Check

```bash
# Run pre-upgrade validation
python skills/confluent-kafka/scripts/upgrade_preflight.py \
  --current-version 7.6 \
  --target-version 8.0 \
  --bootstrap-servers kafka-01:9092
```

---

## Best Practices

### Security

1. **Enable SASL/SSL** — Always use encryption and authentication in production
2. **ACLs** — Enable authorization with `authorizer.class.name`
3. **Rotate certificates** — Plan for SSL certificate rotation before expiry
4. **Secrets management** — Use Vault or AWS Secrets Manager for credentials

### Performance

1. **Partition count** — Start with 12 partitions per topic, scale as needed
2. **Replication factor** — Use 3 for durability (min.insync.replicas=2)
3. **Compression** — Use `lz4` or `zstd` for producer compression
4. **Batch size** — Tune producer `batch.size` and `linger.ms` for throughput

### Reliability

1. **min.insync.replicas=2** — Ensure durability with acks=all producers
2. **Unclean leader election** — Keep `unclean.leader.election.enable=false`
3. **Regular backups** — Back up controller metadata and configs
4. **Monitoring alerts** — Alert on under-replicated partitions, lag, disk

### Maintenance

1. **Rolling restarts** — Always use controlled shutdown for upgrades
2. **Documentation** — Keep runbooks for common operations
3. **Test upgrades** — Always test in non-prod first
4. **Capacity planning** — Monitor growth trends, plan disk expansion

---

## Related Skills

- **[aws](../aws/SKILL.md)** — AWS infrastructure for Kafka deployment
- **[victoriametrics](../victoriametrics/SKILL.md)** — Metrics collection for Kafka monitoring
- **[consul](../consul/SKILL.md)** — Service discovery integration

---

## External Resources

- [Confluent Documentation](https://docs.confluent.io/platform/current/overview.html)
- [Apache Kafka Documentation](https://kafka.apache.org/documentation/)
- [KRaft Migration Guide](https://docs.confluent.io/platform/current/installation/migrate-zk-kraft.html)
- [Confluent Platform Release Notes](https://docs.confluent.io/platform/current/release-notes/index.html)
- [Kafka Operations Best Practices](https://docs.confluent.io/platform/current/kafka/operations.html)
