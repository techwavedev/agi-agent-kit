# Confluent Kafka Troubleshooting Guide

Comprehensive troubleshooting guide for common Confluent Kafka issues in tarball/Ansible deployments.

---

## Table of Contents

1. [Broker Issues](#broker-issues)
2. [KRaft Controller Issues](#kraft-controller-issues)
3. [Replication Problems](#replication-problems)
4. [Consumer Issues](#consumer-issues)
5. [Producer Issues](#producer-issues)
6. [Schema Registry Issues](#schema-registry-issues)
7. [Kafka Connect Issues](#kafka-connect-issues)
8. [Performance Issues](#performance-issues)
9. [Security Issues](#security-issues)

---

## Broker Issues

### Broker Won't Start

**Symptoms:**

- `systemctl status confluent-server` shows failed
- Broker process exits immediately after startup

**Diagnosis:**

```bash
# Check service status
systemctl status confluent-server

# View recent logs
journalctl -u confluent-server -n 100

# Check Kafka server logs
tail -500 /var/log/confluent/kafka/server.log | grep -i "error\|exception\|fatal"

# Check for port conflicts
netstat -tlnp | grep -E "9092|9093"

# Verify disk space
df -h /var/kafka-logs
```

**Common Causes & Solutions:**

| Cause                   | Solution                                |
| ----------------------- | --------------------------------------- |
| Port already in use     | Kill conflicting process or change port |
| Corrupted log files     | Remove corrupted segment (last resort)  |
| Insufficient disk space | Free disk space or expand volume        |
| Invalid configuration   | Fix syntax errors in server.properties  |
| Missing directories     | Create log.dirs with proper permissions |
| Java not found          | Set JAVA_HOME in systemd unit           |

**Fix: Permission Issues**

```bash
# Fix ownership
chown -R kafka:kafka /var/kafka-logs
chown -R kafka:kafka /opt/confluent

# Fix permissions
chmod 750 /var/kafka-logs
chmod 640 /opt/confluent/etc/kafka/server.properties
```

**Fix: Corrupted Segment Recovery**

```bash
# CAUTION: Data loss possible - only as last resort
# Identify corrupted segment from logs
cat /var/log/confluent/kafka/server.log | grep "Corrupted"

# Move corrupted partition (will be re-replicated)
mv /var/kafka-logs/<topic>-<partition> /backup/corrupted/

# Restart broker - partition will sync from replicas
systemctl restart confluent-server
```

---

### Broker Crash Loop

**Symptoms:**

- Broker starts then crashes within seconds
- Repeated restart attempts

**Diagnosis:**

```bash
# Check for OOM killer
dmesg | grep -i "killed process" | tail -10

# Check heap dump
ls -la /opt/confluent/*.hprof

# Review GC logs
grep "GC pause" /var/log/confluent/kafka/kafka-gc.log | tail -20
```

**Solutions:**

```bash
# Increase heap size (edit systemd unit)
# /etc/systemd/system/confluent-server.service
Environment="KAFKA_HEAP_OPTS=-Xms8g -Xmx8g"

# Reduce replica fetch size if OOM during catchup
# In server.properties:
replica.fetch.max.bytes=524288

# Reload and restart
systemctl daemon-reload
systemctl restart confluent-server
```

---

## KRaft Controller Issues

### Controller Quorum Not Forming

**Symptoms:**

- Controllers can't elect a leader
- `kafka-metadata` command hangs

**Diagnosis:**

```bash
# Check controller logs
tail -200 /var/log/confluent/kafka/controller.log | grep -i "voter\|quorum\|elect"

# Verify network connectivity between controllers
for port in 9093; do
  nc -zv controller-01 $port
  nc -zv controller-02 $port
  nc -zv controller-03 $port
done

# Check controller.quorum.voters consistency
grep controller.quorum.voters /opt/confluent/etc/kafka/kraft/controller.properties
```

**Common Causes:**

| Cause                   | Solution                                                 |
| ----------------------- | -------------------------------------------------------- |
| Mismatched voter config | Ensure identical `controller.quorum.voters` on all nodes |
| Network/firewall issues | Open port 9093 between controllers                       |
| Different cluster IDs   | Re-format storage with same cluster ID                   |
| Time skew               | Sync NTP across all nodes                                |

**Fix: Rebuild Controller Quorum**

```bash
# CAUTION: Only if all controllers failed
# 1. Stop all controllers
for host in controller-01 controller-02 controller-03; do
  ssh $host "systemctl stop confluent-server"
done

# 2. Backup existing data
tar -czvf /backup/controller-data-$(date +%Y%m%d).tar.gz /var/kafka-controller/

# 3. Clear and re-format with same cluster ID
CLUSTER_ID=$(cat /backup/cluster-id.txt)
/opt/confluent/bin/kafka-storage format -t $CLUSTER_ID -c /opt/confluent/etc/kafka/kraft/controller.properties --force

# 4. Start controllers one at a time
ssh controller-01 "systemctl start confluent-server"
sleep 30
ssh controller-02 "systemctl start confluent-server"
sleep 30
ssh controller-03 "systemctl start confluent-server"

# 5. Verify quorum
/opt/confluent/bin/kafka-metadata --snapshot /var/kafka-controller/__cluster_metadata-0/00000000000000000000.log --command quorum
```

---

### Broker Not Registering with KRaft

**Symptoms:**

- Broker starts but doesn't appear in `kafka-metadata broker` output
- "Cannot connect to controller" errors

**Diagnosis:**

```bash
# Check broker logs for controller connection
grep -i "controller" /var/log/confluent/kafka/server.log | tail -50

# Verify broker config matches controller quorum
grep controller.quorum.voters /opt/confluent/etc/kafka/server.properties

# Test connectivity to controller port
nc -zv controller-01 9093
```

**Fix:**

```bash
# Ensure these match between broker and controllers:
# - controller.quorum.voters
# - controller.listener.names
# - Security settings (SASL/SSL)

# Verify listener security map includes CONTROLLER
grep listener.security.protocol.map /opt/confluent/etc/kafka/server.properties
# Should include: CONTROLLER:PLAINTEXT (or SASL_SSL, etc.)

# Restart broker
systemctl restart confluent-server
```

---

## Replication Problems

### Under-Replicated Partitions (URP)

**Symptoms:**

- `kafka-topics --describe --under-replicated-partitions` shows results
- Alerts from monitoring

**Diagnosis:**

```bash
# List URPs
/opt/confluent/bin/kafka-topics --bootstrap-server localhost:9092 \
  --describe --under-replicated-partitions

# Check which brokers are affected
/opt/confluent/bin/kafka-topics --bootstrap-server localhost:9092 \
  --describe --under-replicated-partitions | awk '{print $4}' | sort | uniq -c

# Check replica lag on affected broker
grep "Replica lag" /var/log/confluent/kafka/server.log | tail -20

# Check network between replicas
iperf3 -c broker-02 -p 5201
```

**Common Causes & Solutions:**

| Cause              | Solution                                 |
| ------------------ | ---------------------------------------- |
| Slow disk I/O      | Check disk latency, use SSDs             |
| Network congestion | Check bandwidth, increase socket buffers |
| Follower too slow  | Increase `replica.lag.time.max.ms`       |
| Broker overloaded  | Redistribute partitions, add brokers     |
| GC pauses          | Tune JVM, increase heap                  |

**Fix: Increase Replica Lag Tolerance**

```properties
# In server.properties
replica.lag.time.max.ms=45000  # Default 30000
num.replica.fetchers=8         # Default 1
replica.fetch.max.bytes=10485760  # 10MB
```

---

### ISR Shrinking Repeatedly

**Symptoms:**

- ISR changes frequently in logs
- Followers constantly falling out and rejoining

**Diagnosis:**

```bash
# Count ISR changes
grep "ISR" /var/log/confluent/kafka/server.log | tail -100

# Check broker request latency
grep "RequestHandlerAvgIdlePercent" /var/log/confluent/kafka/server.log

# Monitor network latency
ping -c 100 broker-02 | tail -5
```

**Fix: Tune Replication**

```properties
# In server.properties - increase tolerance
replica.lag.time.max.ms=60000
replica.socket.receive.buffer.bytes=1048576
replica.socket.timeout.ms=60000

# Increase replica fetcher threads
num.replica.fetchers=4
```

---

## Consumer Issues

### High Consumer Lag

**Symptoms:**

- Consumer group shows large lag
- Messages processing delayed

**Diagnosis:**

```bash
# Check consumer group lag
/opt/confluent/bin/kafka-consumer-groups --bootstrap-server localhost:9092 \
  --group my-group --describe

# Check if consumers are connected
/opt/confluent/bin/kafka-consumer-groups --bootstrap-server localhost:9092 \
  --group my-group --describe --members

# Check consumer assignment
/opt/confluent/bin/kafka-consumer-groups --bootstrap-server localhost:9092 \
  --group my-group --describe --members --verbose
```

**Solutions:**

| Cause                            | Solution                                                |
| -------------------------------- | ------------------------------------------------------- |
| Too few consumers                | Scale consumer instances                                |
| Slow processing                  | Optimize consumer logic, async processing               |
| Too many partitions per consumer | Increase consumers or reduce partitions                 |
| Large messages                   | Increase `fetch.max.bytes`, `max.partition.fetch.bytes` |
| Network bottleneck               | Increase fetch size, check bandwidth                    |

---

### Consumer Group Rebalancing Constantly

**Symptoms:**

- Frequent "JoinGroup" requests in logs
- Processing stops during rebalances

**Diagnosis:**

```bash
# Check for rebalance triggers
grep -i "rebalance\|join" /var/log/myapp/consumer.log | tail -50

# Check session timeout settings
# Consumer config should have reasonable timeouts
```

**Fix: Tune Consumer Config**

```properties
# In consumer configuration
session.timeout.ms=45000      # Default 10000
heartbeat.interval.ms=15000   # Should be < session.timeout/3
max.poll.interval.ms=600000   # Increase if processing is slow
max.poll.records=100          # Reduce if processing is slow
```

---

## Producer Issues

### Producer Timeout Errors

**Symptoms:**

- `TimeoutException` in producer logs
- Messages not delivered

**Diagnosis:**

```bash
# Check broker availability
/opt/confluent/bin/kafka-broker-api-versions --bootstrap-server localhost:9092

# Check producer metrics if using JMX
# record-send-rate, request-latency-avg

# Verify topic exists
/opt/confluent/bin/kafka-topics --bootstrap-server localhost:9092 \
  --topic my-topic --describe
```

**Fix: Tune Producer Config**

```properties
# In producer configuration
request.timeout.ms=60000      # Default 30000
delivery.timeout.ms=180000    # Default 120000
retries=10                    # Default MAX_INT in newer versions
retry.backoff.ms=500          # Delay between retries
```

---

### Producer Not Acknowledging (acks=all Slow)

**Symptoms:**

- Slow produce latency with `acks=all`
- Works fine with `acks=1`

**Diagnosis:**

```bash
# Check min.insync.replicas
/opt/confluent/bin/kafka-topics --bootstrap-server localhost:9092 \
  --topic my-topic --describe

# Check for URPs on the topic
/opt/confluent/bin/kafka-topics --bootstrap-server localhost:9092 \
  --topic my-topic --describe --under-replicated-partitions
```

**Solutions:**

- Ensure all replicas are in ISR
- Check network latency between brokers
- Reduce `min.insync.replicas` (trades durability for performance)
- Use compression to reduce replication traffic

---

## Schema Registry Issues

### Schema Registry 409 Conflict

**Symptoms:**

- `io.confluent.kafka.schemaregistry.client.rest.exceptions.RestClientException: Schema being registered is incompatible with an earlier schema`

**Diagnosis:**

```bash
# Check current compatibility mode
curl http://localhost:8081/config | jq

# Check specific subject compatibility
curl http://localhost:8081/config/my-topic-value | jq

# Get existing schema
curl http://localhost:8081/subjects/my-topic-value/versions/latest | jq
```

**Solutions:**

```bash
# Option 1: Change compatibility mode (if acceptable)
curl -X PUT -H "Content-Type: application/vnd.schemaregistry.v1+json" \
  --data '{"compatibility": "NONE"}' \
  http://localhost:8081/config/my-topic-value

# Option 2: Register as new subject
# Use a different subject name

# Option 3: Delete old versions (CAUTION - impacts consumers)
curl -X DELETE http://localhost:8081/subjects/my-topic-value/versions/1
```

---

### Schema Registry Leader Election Failure

**Symptoms:**

- Schema Registry returns 500 errors
- "Not the leader" errors

**Diagnosis:**

```bash
# Check SR logs
tail -100 /var/log/confluent/schema-registry/schema-registry.log

# Check _schemas topic
/opt/confluent/bin/kafka-topics --bootstrap-server localhost:9092 \
  --topic _schemas --describe

# Check consumer group
/opt/confluent/bin/kafka-consumer-groups --bootstrap-server localhost:9092 \
  --group schema-registry --describe
```

**Fix:**

```bash
# Restart SR instances to trigger re-election
systemctl restart confluent-schema-registry

# If _schemas topic is corrupt, may need to recreate (DESTROYS ALL SCHEMAS)
```

---

## Kafka Connect Issues

### Connector Task Failed

**Symptoms:**

- Connector status shows FAILED
- Connector tasks not processing

**Diagnosis:**

```bash
# Check connector status
curl -s http://localhost:8083/connectors/my-connector/status | jq

# Get task details
curl -s http://localhost:8083/connectors/my-connector/tasks/0/status | jq

# View Connect worker logs
tail -200 /var/log/confluent/kafka-connect/connect.log | grep -i "error\|exception"
```

**Fix: Restart Failed Task**

```bash
# Restart specific task
curl -X POST http://localhost:8083/connectors/my-connector/tasks/0/restart

# Or restart entire connector
curl -X POST http://localhost:8083/connectors/my-connector/restart

# Update connector config if needed
curl -X PUT -H "Content-Type: application/json" \
  --data @updated-config.json \
  http://localhost:8083/connectors/my-connector/config
```

---

### Connector Not Starting

**Symptoms:**

- POST to create connector returns 201 but connector never starts
- Connector shows UNASSIGNED

**Diagnosis:**

```bash
# Check if worker has capacity
curl -s http://localhost:8083/ | jq

# Check for classpath issues
curl -s http://localhost:8083/connector-plugins | jq | grep -i "class"

# Verify connector JAR is in plugin path
ls -la /opt/confluent/share/java/kafka-connect-jdbc/
```

---

## Performance Issues

### High Disk I/O

**Diagnosis:**

```bash
# Check disk I/O
iostat -x 5

# Check Kafka log flush
grep "LogFlushRateAndTimeMs" /var/log/confluent/kafka/server.log

# Check log compaction
grep "cleaner" /var/log/confluent/kafka/server.log
```

**Tuning:**

```properties
# In server.properties
log.flush.interval.messages=50000    # Reduce sync frequency
log.flush.interval.ms=10000
log.cleaner.io.buffer.load.factor=0.9
log.cleaner.threads=2
```

---

### High Network Utilization

**Diagnosis:**

```bash
# Check network stats
sar -n DEV 5

# Check broker network threads
grep "NetworkProcessorAvgIdlePercent" /var/log/confluent/kafka/server.log

# Monitor with JMX
# kafka.network:type=SocketServer,name=NetworkProcessorAvgIdlePercent
```

**Tuning:**

```properties
# In server.properties
num.network.threads=8
socket.send.buffer.bytes=1048576
socket.receive.buffer.bytes=1048576

# Enable compression
compression.type=lz4
```

---

## Security Issues

### ACL Permission Denied

**Symptoms:**

- `ClusterAuthorizationException` or `TopicAuthorizationException`
- Clients can't produce or consume

**Diagnosis:**

```bash
# List all ACLs
/opt/confluent/bin/kafka-acls --bootstrap-server localhost:9092 --list

# Check ACLs for specific topic
/opt/confluent/bin/kafka-acls --bootstrap-server localhost:9092 \
  --topic my-topic --list

# Check ACLs for specific principal
/opt/confluent/bin/kafka-acls --bootstrap-server localhost:9092 \
  --principal User:myuser --list
```

**Fix: Add Required ACLs**

```bash
# Allow producer
/opt/confluent/bin/kafka-acls --bootstrap-server localhost:9092 \
  --add --allow-principal User:myuser \
  --operation Write --topic my-topic

# Allow consumer
/opt/confluent/bin/kafka-acls --bootstrap-server localhost:9092 \
  --add --allow-principal User:myuser \
  --operation Read --topic my-topic \
  --group my-consumer-group
```

---

### SSL Handshake Failure

**Symptoms:**

- `SslAuthenticationException: SSL handshake failed`
- Clients can't connect over SSL

**Diagnosis:**

```bash
# Test SSL connection
openssl s_client -connect localhost:9093 -tls1_2

# Verify keystore
keytool -list -keystore /var/ssl/kafka/kafka.keystore.jks

# Check certificate expiry
keytool -list -keystore /var/ssl/kafka/kafka.keystore.jks -v | grep "Valid"

# Verify truststore
keytool -list -keystore /var/ssl/kafka/kafka.truststore.jks
```

**Common Causes:**

| Cause                  | Solution                                         |
| ---------------------- | ------------------------------------------------ |
| Certificate expired    | Generate new certificates                        |
| Wrong CA in truststore | Import correct CA certificate                    |
| Hostname mismatch      | Use correct SAN or disable hostname verification |
| TLS version mismatch   | Align TLS versions between client and server     |

---

## General Debugging Tools

### Useful Log Locations

```
/var/log/confluent/kafka/server.log          # Broker logs
/var/log/confluent/kafka/controller.log      # KRaft controller logs
/var/log/confluent/kafka/kafka-gc.log        # GC logs
/var/log/confluent/schema-registry/          # Schema Registry logs
/var/log/confluent/kafka-connect/            # Connect worker logs
/var/log/confluent/control-center/           # Control Center logs
```

### JMX Monitoring

```bash
# Enable JMX (add to KAFKA_OPTS)
export KAFKA_OPTS="-Dcom.sun.management.jmxremote \
  -Dcom.sun.management.jmxremote.port=9999 \
  -Dcom.sun.management.jmxremote.authenticate=false \
  -Dcom.sun.management.jmxremote.ssl=false"

# Query JMX metrics
java -jar jmxterm.jar -l localhost:9999
> beans kafka.*:*
> get -b kafka.server:type=ReplicaManager,name=UnderReplicatedPartitions Value
```

### Thread Dump

```bash
# Get Kafka broker thread dump
jstack $(pgrep -f kafka.Kafka) > /tmp/kafka-threads-$(date +%Y%m%d-%H%M%S).txt

# Analyze for deadlocks
jstack $(pgrep -f kafka.Kafka) | grep -A 50 "deadlock"
```

### Heap Dump

```bash
# Trigger heap dump
jmap -dump:format=b,file=/tmp/kafka-heap.hprof $(pgrep -f kafka.Kafka)

# Analyze with Eclipse MAT or jhat
```
