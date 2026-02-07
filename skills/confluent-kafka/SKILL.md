---
name: confluent-kafka
description: Confluent Kafka specialist for tarball/Ansible custom installations. Expert in updating, maintaining, checking health, troubleshooting, documenting, analyzing metrics, and upgrading Confluent Kafka deployments from 7.x to 8.x versions. Covers KRaft mode (ZooKeeper-less), broker configuration, Schema Registry, Connect, ksqlDB, Control Center, and production-grade operations. Use when working with Confluent Platform installations, migrations to KRaft, performance tuning, health monitoring, and infrastructure-as-code with Ansible.
---

# Confluent Kafka Skill

Comprehensive skill for managing Confluent Platform Kafka clusters deployed via tarball distributions and automated with Ansible. **Primary deployment context is EC (European Commission) controlled environments using KRaft-only, SSL-only, non-root systemd user services.**

> **Last Updated:** 2026-02-07 from [Confluent Documentation](https://docs.confluent.io/)

---

## EC Environment Quick Reference

> **Note:** Values below use variable placeholders. Define actual values in inventory files outside git.

| Item                  | Variable / Default                             |
| --------------------- | ---------------------------------------------- |
| **Confluent Version** | `{{ confluent_version }}` (e.g., 7.9.3)        |
| **Ansible Base**      | `{{ ansible_base }}`                           |
| **Confluent Install** | `{{ base_path }}/opt/confluent-{{ version }}/` |
| **JAVA_HOME**         | `{{ base_path }}/opt/{{ java_version }}`       |
| **SSL Directory**     | `{{ base_path }}/opt/ssl/`                     |
| **Data: Controller**  | `{{ base_path }}/opt/data/controller`          |
| **Data: Broker**      | `{{ base_path }}/opt/data`                     |
| **Logs**              | `{{ base_path }}/logs/`                        |
| **Systemd (User)**    | `~/.config/systemd/user/`                      |
| **User/Group**        | `{{ kafka_user }}:{{ kafka_group }}`           |
| **Controller Port**   | `{{ controller_port }}` (default: 9093)        |
| **Broker Port**       | `{{ broker_port }}` (default: 9443)            |

> **Full EC deployment reference:** [references/ec_deployment.md](references/ec_deployment.md)

---

## Quick Start (EC Environment)

```bash
# Set environment variables (or source from environment file)
export KAFKA_HOME={{ base_path }}/opt/confluent-{{ confluent_version }}
export BOOTSTRAP={{ broker_host_1 }}:{{ broker_port }},{{ broker_host_2 }}:{{ broker_port }}
export CLIENT_PROPS={{ base_path }}/etc/kafka/client.properties

# SSH to a broker node
ssh {{ kafka_user }}@{{ broker_host_1 }}

# Verify broker is running (user systemd scope)
systemctl --user status confluent-server

# Check cluster health
$KAFKA_HOME/bin/kafka-broker-api-versions \
  --bootstrap-server $BOOTSTRAP \
  --command-config $CLIENT_PROPS

# Check controller quorum (KRaft)
$KAFKA_HOME/bin/kafka-metadata \
  --snapshot {{ base_path }}/opt/data/controller/__cluster_metadata-0/00000000000000000000.log \
  --command quorum

# Use management script
{{ base_path }}/scripts/management/kafka_node.sh status
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

### EC Installation Layout

```
{{ base_path }}/                              # Main installation root
├── opt/
│   ├── confluent-{{ confluent_version }}/    # Confluent Platform
│   │   ├── bin/                              # CLI tools
│   │   ├── etc/                              # Default configs (unused)
│   │   └── share/                            # Libraries
│   │
│   ├── {{ java_version }}/                   # Java installation
│   │
│   ├── ssl/                                  # SSL certificates
│   │   ├── {{ keystore_filename }}
│   │   ├── {{ truststore_filename }}
│   │   └── security.properties               # Encrypted passwords
│   │
│   ├── data/                                 # Kafka data
│   │   ├── controller/                       # Controller logs
│   │   └── (broker data at root)
│   │
│   ├── logs/                                 # Application logs
│   └── monitoring/                           # JMX exporter
│
├── etc/
│   ├── kafka/server.properties               # Broker config
│   └── controller/server.properties          # Controller config
│
├── logs/                                     # Runtime + GC logs
├── tmp/                                      # Java temp directory
└── scripts/management/                       # Management scripts
    ├── kafka_node.sh                         # Start/stop wrapper
    └── kafka_tools.sh                        # Aux tools

~/.config/systemd/user/                       # User-scope systemd
├── confluent-kcontroller.service             # Controller service
└── confluent-server.service                  # Broker service
```

> **Standard paths** (non-EC): `/opt/confluent/`, `/var/kafka-logs/`, `/etc/systemd/system/`

---

## Common Workflows

### 1. Check Cluster Health (EC)

```bash
# Set environment (source from your environment file)
export KAFKA_HOME={{ base_path }}/opt/confluent-{{ confluent_version }}
export BOOTSTRAP={{ broker_host_1 }}:{{ broker_port }},{{ broker_host_2 }}:{{ broker_port }},{{ broker_host_3 }}:{{ broker_port }}
export CLIENT_PROPS={{ base_path }}/etc/kafka/client.properties

# Broker status (user systemd)
systemctl --user status confluent-server

# Controller quorum status (KRaft)
$KAFKA_HOME/bin/kafka-metadata \
  --snapshot {{ base_path }}/opt/data/controller/__cluster_metadata-0/00000000000000000000.log \
  --command quorum

# Under-replicated partitions
$KAFKA_HOME/bin/kafka-topics --bootstrap-server $BOOTSTRAP \
  --command-config $CLIENT_PROPS \
  --describe --under-replicated-partitions

# Offline partitions (CRITICAL)
$KAFKA_HOME/bin/kafka-topics --bootstrap-server $BOOTSTRAP \
  --command-config $CLIENT_PROPS \
  --describe --unavailable-partitions

# Broker disk usage
df -h /ec/local/reuse/opt/data

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

- **[references/ec_deployment.md](references/ec_deployment.md)** — **EC deployment paths, Vault, and setup**
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

### Debug Commands (EC)

```bash
# Set paths (source from your environment file)
export KAFKA_HOME={{ base_path }}/opt/confluent-{{ confluent_version }}
export LOG_DIR={{ base_path }}/logs
export DATA_DIR={{ base_path }}/opt/data

# Kafka server logs (last 100 lines)
tail -100 $LOG_DIR/server.log

# Controller logs (KRaft)
tail -100 $LOG_DIR/controller.log

# Systemd journal logs
journalctl --user -u confluent-server -f
journalctl --user -u confluent-kcontroller -f

# Check open file descriptors
lsof -p $(pgrep -f kafka.Kafka) | wc -l

# Network connections to broker
netstat -an | grep {{ broker_port }} | wc -l

# Thread dump for debugging hung brokers
jstack $(pgrep -f kafka.Kafka) > /tmp/kafka-thread-dump.txt

# GC logs analysis
grep "GC pause" $LOG_DIR/gc.log | tail -20

# KRaft metadata diagnostics
$KAFKA_HOME/bin/kafka-metadata \
  --snapshot $DATA_DIR/controller/__cluster_metadata-0/00000000000000000000.log \
  --command topic --topics __consumer_offsets
```

### Detailed Troubleshooting

For in-depth troubleshooting scenarios, see **[references/troubleshooting.md](references/troubleshooting.md)**.

---

## Ansible Automation (EC Environment)

### EC Inventory Structure

```yaml
# {{ ansible_base }}/inventories/{{ env_name }}/hosts.yml
# Replace {{ variable }} placeholders with actual values in your inventory (not in git)
all:
  children:
    kafka_controller:
      hosts:
        { { controller_host_1 } }:
          node_id: { { controller_id_1 } }
        { { controller_host_2 } }:
          node_id: { { controller_id_2 } }
        { { controller_host_3 } }:
          node_id: { { controller_id_3 } }

    kafka_broker:
      hosts:
        { { broker_host_1 } }:
          node_id: { { broker_id_1 } }
        { { broker_host_2 } }:
          node_id: { { broker_id_2 } }
        { { broker_host_3 } }:
          node_id: { { broker_id_3 } }
```

### EC Deployment Commands

```bash
# Export Vault token (obtain via PrivX or your auth method)
export VAULT_TOKEN="${VAULT_TOKEN}"
cd {{ ansible_base }}

# Vault bootstrap (one-time per environment)
ansible-playbook playbooks/tasks/vault-bootstrap.yml \
  -e vault_env={{ env_name }} \
  -e "@resources/secrets.yml"

# Deploy controllers
ansible-playbook -i inventories/{{ env_name }}/hosts.yml \
  playbooks/10-kafka-controllers.yml \
  --limit {{ controller_host_1 }} \
  -vv \
  --skip-tags ec,package,sysctl,health_check \
  -e "@resources/override.yml"

# Deploy brokers
ansible-playbook -i inventories/{{ env_name }}/hosts.yml \
  playbooks/20-kafka-brokers.yml \
  --limit {{ broker_host_1 }} \
  -vv \
  --skip-tags ec,package,sysctl,health_check \
  -e "@resources/override.yml"
```

### EC Systemd User Service Pattern

```yaml
# User-scope systemd (no root)
- name: Kafka Started
  ansible.builtin.systemd:
    name: "{{ kafka_broker_service_name }}"
    enabled: true
    scope: user # EC constraint: user-mode systemd
    state: started
  tags: systemd
```

### Skip Tags Reference

| Tag            | Purpose              | When to Skip    |
| -------------- | -------------------- | --------------- |
| `ec`           | EC-specific mods     | Already applied |
| `package`      | Package installation | Re-runs         |
| `sysctl`       | Sysctl tuning        | No root         |
| `health_check` | Post-checks          | Manual          |
| `privileged`   | Root-required        | Non-root env    |

### Reference Files

- **[references/ec_deployment.md](references/ec_deployment.md)** — **Complete EC paths, Vault, Ansible setup**
- **[references/ansible_playbooks.md](references/ansible_playbooks.md)** — Generic Ansible automation patterns

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
