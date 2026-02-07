# Confluent Kafka Upgrade Guide: 7.x to 8.x

Complete guide for upgrading Confluent Platform from 7.x versions to 8.x with tarball installations.

---

## ⚠️ EC Environment Path Mappings

> **This guide uses standard Confluent paths in examples.** For EC deployments, substitute paths as follows:

| Standard Path         | EC Path                                                  |
| --------------------- | -------------------------------------------------------- |
| `/opt/confluent/`     | `{{ base_path }}/opt/confluent-{{ confluent_version }}/` |
| `/var/kafka-logs/`    | `{{ base_path }}/opt/data`                               |
| `/var/log/confluent/` | `{{ base_path }}/logs/`                                  |
| `/var/ssl/kafka/`     | `{{ base_path }}/opt/ssl/`                               |
| `localhost:9092`      | `$BOOTSTRAP` (use SSL port 9443)                         |
| `sudo systemctl`      | `systemctl --user`                                       |

**EC Quick Setup:**

```bash
export KAFKA_HOME={{ base_path }}/opt/confluent-{{ confluent_version }}
export BOOTSTRAP={{ broker_host_1 }}:{{ broker_port }}
```

See **[ec_deployment.md](ec_deployment.md)** for complete EC paths and configuration.

---

## Table of Contents

1. [Version Compatibility Matrix](#version-compatibility-matrix)
2. [Breaking Changes](#breaking-changes)
3. [Pre-Upgrade Requirements](#pre-upgrade-requirements)
4. [Upgrade Order](#upgrade-order)
5. [Rolling Upgrade Procedure](#rolling-upgrade-procedure)
6. [Post-Upgrade Validation](#post-upgrade-validation)
7. [Rollback Procedure](#rollback-procedure)

---

## Version Compatibility Matrix

| Source Version | Target Version | Java Minimum | KRaft Support       | Notes                   |
| -------------- | -------------- | ------------ | ------------------- | ----------------------- |
| 7.3.x          | 8.0.x          | Java 17      | Migration supported | Upgrade to 7.6 first    |
| 7.4.x          | 8.0.x          | Java 17      | Migration supported | Recommended path        |
| 7.5.x          | 8.0.x          | Java 17      | Migration supported | Direct upgrade possible |
| 7.6.x          | 8.0.x          | Java 17      | Migration supported | Seamless upgrade        |
| 7.x (any)      | 8.1.x          | Java 17      | KRaft GA            | Via 8.0.x if from <7.5  |

### Java Version Requirements

```bash
# Check current Java version
java -version

# 8.x requires Java 17+
# Install Amazon Corretto 17 (recommended)
curl -LO https://corretto.aws/downloads/latest/amazon-corretto-17-x64-linux-jdk.tar.gz
tar -xzf amazon-corretto-17-x64-linux-jdk.tar.gz -C /opt/
export JAVA_HOME=/opt/amazon-corretto-17.0.9.8.1-linux-x64
export PATH=$JAVA_HOME/bin:$PATH

# Update KAFKA_HEAP_OPTS if needed in systemd unit
```

---

## Breaking Changes

### Removed Features

| Feature                                    | Replacement                           |
| ------------------------------------------ | ------------------------------------- |
| `kafka-preferred-replica-election.sh`      | Use `kafka-leader-election.sh`        |
| `log.message.format.version`               | Removed (always uses latest format)   |
| ZooKeeper mode (new installs)              | Use KRaft mode                        |
| `kafka-acls.sh --authorizer-properties`    | Use `--bootstrap-server`              |
| Legacy consumer (`kafka-console-consumer`) | Use `--bootstrap-server` (not `--zk`) |

### Deprecated Configurations to Remove

```properties
# ❌ REMOVE these from server.properties before upgrade
log.message.format.version=X.X
inter.broker.protocol.version=X.X (will be auto-managed)
zookeeper.connect=... (if migrating to KRaft)

# ✅ Add these for 8.x
# (controller-related settings if using KRaft)
```

### Configuration Changes

```properties
# 7.x configuration
log.message.format.version=3.6
inter.broker.protocol.version=3.6
zookeeper.connect=zk1:2181,zk2:2181,zk3:2181

# 8.x configuration (KRaft)
# REMOVE log.message.format.version
# REMOVE inter.broker.protocol.version
# REMOVE zookeeper.connect

# ADD KRaft settings
process.roles=broker
node.id=101
controller.quorum.voters=1@controller1:9093,2@controller2:9093,3@controller3:9093
controller.listener.names=CONTROLLER
```

---

## Pre-Upgrade Requirements

### 1. Environment Assessment

```bash
# Run pre-flight check script
python skills/confluent-kafka/scripts/upgrade_preflight.py \
  --current-version 7.6 \
  --target-version 8.0 \
  --bootstrap-servers kafka-01:9092,kafka-02:9092,kafka-03:9092

# Manual checks
# Check current version
/opt/confluent/bin/kafka-broker-api-versions --bootstrap-server localhost:9092 --version

# Check inter.broker.protocol.version (must match across cluster)
grep inter.broker.protocol.version /opt/confluent/etc/kafka/server.properties

# Check for deprecated configs
grep -E "(log.message.format|zookeeper)" /opt/confluent/etc/kafka/server.properties
```

### 2. Cluster Health Verification

```bash
# No under-replicated partitions
/opt/confluent/bin/kafka-topics --bootstrap-server localhost:9092 \
  --describe --under-replicated-partitions

# No offline partitions
/opt/confluent/bin/kafka-topics --bootstrap-server localhost:9092 \
  --describe --unavailable-partitions

# All brokers in ISR
/opt/confluent/bin/kafka-metadata --snapshot /var/kafka-logs/__cluster_metadata-0/00000000000000000000.log \
  --command broker

# Controller status
# For ZK mode:
/opt/confluent/bin/zookeeper-shell localhost:2181 <<< "get /controller"
# For KRaft mode:
/opt/confluent/bin/kafka-metadata --snapshot /var/kafka-logs/__cluster_metadata-0/00000000000000000000.log \
  --command quorum
```

### 3. Backup Everything

```bash
# Create timestamped backup directory
BACKUP_DIR="/backup/confluent-upgrade-$(date +%Y%m%d-%H%M%S)"
mkdir -p $BACKUP_DIR

# Backup configurations
cp -r /opt/confluent/etc $BACKUP_DIR/etc

# Backup systemd units
cp /etc/systemd/system/confluent-* $BACKUP_DIR/

# Backup topic configurations
/opt/confluent/bin/kafka-configs --bootstrap-server localhost:9092 \
  --entity-type topics --all --describe > $BACKUP_DIR/topic-configs.txt

# Backup ACLs
/opt/confluent/bin/kafka-acls --bootstrap-server localhost:9092 \
  --list > $BACKUP_DIR/acls.txt

# If using ZK, backup ZooKeeper data
# (Only needed if not migrating to KRaft)
tar -czvf $BACKUP_DIR/zk-data.tar.gz /var/zookeeper/data

# Backup Schema Registry subjects
for subject in $(curl -s http://localhost:8081/subjects | jq -r '.[]'); do
  curl -s http://localhost:8081/subjects/$subject/versions/latest > $BACKUP_DIR/schemas/$subject.json
done

# Create tarball of entire backup
tar -czvf $BACKUP_DIR.tar.gz $BACKUP_DIR
```

### 4. Download New Version

```bash
# Download Confluent Platform 8.x tarball
CONFLUENT_VERSION=8.0.0
curl -LO https://packages.confluent.io/archive/8.0/confluent-$CONFLUENT_VERSION.tar.gz

# Verify checksum
sha256sum confluent-$CONFLUENT_VERSION.tar.gz

# Extract (don't overwrite yet)
tar -xzf confluent-$CONFLUENT_VERSION.tar.gz -C /opt/
# Creates /opt/confluent-$CONFLUENT_VERSION

# Distribute to all nodes
for host in kafka-01 kafka-02 kafka-03; do
  scp confluent-$CONFLUENT_VERSION.tar.gz $host:/tmp/
done
```

---

## Upgrade Order

**Critical**: Follow this upgrade order to maintain cluster availability:

```
1. Schema Registry (all nodes)
         ↓
2. REST Proxy (all nodes)
         ↓
3. Kafka Connect (all workers)
         ↓
4. ksqlDB Server (all nodes)
         ↓
5. Control Center
         ↓
6. Kafka Brokers (rolling, one at a time)
         ↓
7. Controllers (rolling, if separate from brokers)
         ↓
8. ZooKeeper → KRaft Migration (if applicable)
```

---

## Rolling Upgrade Procedure

### Step 1: Upgrade Schema Registry

```bash
# On each Schema Registry node (one at a time)

# 1. Stop service
sudo systemctl stop confluent-schema-registry

# 2. Backup current config
cp /opt/confluent/etc/schema-registry/schema-registry.properties /backup/

# 3. Update symlink to new version
sudo rm /opt/confluent
sudo ln -s /opt/confluent-8.0.0 /opt/confluent

# 4. Copy configuration to new version
cp /backup/schema-registry.properties /opt/confluent/etc/schema-registry/

# 5. Start service
sudo systemctl start confluent-schema-registry

# 6. Verify health
curl http://localhost:8081/ | jq

# Wait for healthy status before proceeding to next node
```

### Step 2: Upgrade Kafka Connect

```bash
# On each Connect worker (one at a time)

# 1. Pause all connectors (from any worker)
for connector in $(curl -s localhost:8083/connectors | jq -r '.[]'); do
  curl -X PUT localhost:8083/connectors/$connector/pause
done

# 2. Stop Connect worker
sudo systemctl stop confluent-kafka-connect

# 3. Update symlink
sudo rm /opt/confluent
sudo ln -s /opt/confluent-8.0.0 /opt/confluent

# 4. Copy configuration
cp /backup/connect-distributed.properties /opt/confluent/etc/kafka/

# 5. Copy custom connectors
cp -r /backup/connectors /opt/confluent/share/java/

# 6. Start Connect worker
sudo systemctl start confluent-kafka-connect

# 7. Verify worker joined cluster
curl http://localhost:8083/ | jq

# After all workers upgraded, resume connectors
for connector in $(curl -s localhost:8083/connectors | jq -r '.[]'); do
  curl -X PUT localhost:8083/connectors/$connector/resume
done
```

### Step 3: Upgrade Kafka Brokers (Rolling)

**CRITICAL**: Upgrade ONE broker at a time. Wait for ISR sync before proceeding.

```bash
# Pre-upgrade per broker
BROKER_ID=101
BROKER_HOST=kafka-01

# 1. Verify broker is not controller (for ZK mode)
/opt/confluent/bin/zookeeper-shell localhost:2181 <<< "get /controller" | grep -v $BROKER_ID

# 2. Controlled shutdown (gracefully migrate leadership)
sudo systemctl stop confluent-server

# 3. Wait for partitions to be reassigned
sleep 60
/opt/confluent/bin/kafka-topics --bootstrap-server kafka-02:9092 \
  --describe --under-replicated-partitions

# 4. Update symlink
sudo rm /opt/confluent
sudo ln -s /opt/confluent-8.0.0 /opt/confluent

# 5. Merge configurations
# Copy old config
cp /backup/server.properties /opt/confluent/etc/kafka/

# Remove deprecated settings
sed -i '/log.message.format.version/d' /opt/confluent/etc/kafka/server.properties
sed -i '/inter.broker.protocol.version/d' /opt/confluent/etc/kafka/server.properties

# 6. Start broker
sudo systemctl start confluent-server

# 7. Verify broker joined cluster
/opt/confluent/bin/kafka-broker-api-versions --bootstrap-server localhost:9092

# 8. Wait for full ISR sync
watch "/opt/confluent/bin/kafka-topics --bootstrap-server localhost:9092 \
  --describe --under-replicated-partitions | wc -l"

# Only proceed to next broker when under-replicated = 0
```

### Step 4: Upgrade Control Center

```bash
# Control Center can be upgraded last (non-critical)

sudo systemctl stop confluent-control-center

sudo rm /opt/confluent
sudo ln -s /opt/confluent-8.0.0 /opt/confluent

cp /backup/control-center.properties /opt/confluent/etc/confluent-control-center/

# Update any version-specific settings
# control.center.connect.cluster=... (verify endpoints)

sudo systemctl start confluent-control-center

# Verify UI is accessible
curl -I http://localhost:9021
```

---

## Post-Upgrade Validation

### 1. Verify All Components

```bash
# Check all service versions
for service in confluent-server confluent-schema-registry confluent-kafka-connect; do
  echo "=== $service ==="
  systemctl status $service | head -5
done

# Broker version
/opt/confluent/bin/kafka-broker-api-versions --bootstrap-server localhost:9092 --version

# Schema Registry version
curl -s http://localhost:8081/ | jq

# Connect version
curl -s http://localhost:8083/ | jq

# Control Center (check UI)
curl -I http://localhost:9021
```

### 2. Cluster Health Check

```bash
# Run comprehensive health check
python skills/confluent-kafka/scripts/kafka_health_check.py \
  --bootstrap-servers kafka-01:9092,kafka-02:9092,kafka-03:9092 \
  --output reports/kafka/post-upgrade/

# Verify no under-replicated partitions
/opt/confluent/bin/kafka-topics --bootstrap-server localhost:9092 \
  --describe --under-replicated-partitions

# Verify all consumer groups are healthy
/opt/confluent/bin/kafka-consumer-groups --bootstrap-server localhost:9092 \
  --all-groups --describe

# Verify connectors are running
curl -s http://localhost:8083/connectors | jq -r '.[]' | while read c; do
  echo "$c: $(curl -s http://localhost:8083/connectors/$c/status | jq -r '.connector.state')"
done
```

### 3. Functional Testing

```bash
# Produce test message
echo "upgrade-test-$(date +%s)" | /opt/confluent/bin/kafka-console-producer \
  --bootstrap-server localhost:9092 \
  --topic upgrade-test

# Consume test message
/opt/confluent/bin/kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic upgrade-test \
  --from-beginning \
  --max-messages 1

# Test Schema Registry
curl -X POST -H "Content-Type: application/vnd.schemaregistry.v1+json" \
  --data '{"schema": "{\"type\": \"string\"}"}' \
  http://localhost:8081/subjects/upgrade-test-value/versions
```

---

## Rollback Procedure

If upgrade fails, rollback to previous version:

```bash
# 1. Stop the failed service
sudo systemctl stop confluent-server

# 2. Restore previous symlink
sudo rm /opt/confluent
sudo ln -s /opt/confluent-7.6.0 /opt/confluent

# 3. Restore configuration from backup
cp $BACKUP_DIR/etc/kafka/server.properties /opt/confluent/etc/kafka/

# 4. Start service
sudo systemctl start confluent-server

# 5. Verify cluster health
/opt/confluent/bin/kafka-broker-api-versions --bootstrap-server localhost:9092
/opt/confluent/bin/kafka-topics --bootstrap-server localhost:9092 \
  --describe --under-replicated-partitions
```

### Rollback Considerations

- **Inter-broker protocol**: Brokers can communicate across one minor version difference
- **Log format**: 8.x log format is backward compatible with 7.x readers
- **Metadata**: KRaft metadata is NOT backward compatible if migration was started
- **Schema Registry**: Subject compatibility is maintained, no rollback needed

---

## Ansible Upgrade Playbook

For automated rolling upgrades, see [ansible_playbooks.md](ansible_playbooks.md) for the complete playbook.

Quick example:

```bash
# Run rolling upgrade
ansible-playbook -i inventory/confluent.ini playbooks/upgrade.yml \
  -e confluent_target_version=8.0.0 \
  -e rolling_restart=true \
  --limit brokers
```
