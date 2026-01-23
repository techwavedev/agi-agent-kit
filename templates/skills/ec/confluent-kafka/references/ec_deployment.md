# EC Kafka Deployment Reference

This document provides the complete reference for Confluent Kafka KRaft deployments in European Commission (EC) controlled environments.

> **Note:** All hostnames, paths, and credentials shown use variable placeholders. Actual values must be provided via inventory files or environment-specific configuration outside of version control.

---

## Table of Contents

1. [Environment Overview](#environment-overview)
2. [Variable Definitions](#variable-definitions)
3. [Directory Structure](#directory-structure)
4. [Path Reference](#path-reference)
5. [Vault Integration](#vault-integration)
6. [Ansible Deployment](#ansible-deployment)
7. [EC Customizations](#ec-customizations)
8. [Service Management](#service-management)
9. [SSL/TLS Configuration](#ssltls-configuration)
10. [Troubleshooting](#troubleshooting)

---

## Environment Overview

### Design Principles

| Principle           | Implementation                        |
| ------------------- | ------------------------------------- |
| **KRaft-Only**      | No ZooKeeper; pure KRaft mode         |
| **SSL-Only**        | mTLS required; no SASL/RBAC           |
| **Non-Root**        | systemd user services; no sudo        |
| **Archive Install** | tar.gz deployment; no package manager |
| **Vault Secrets**   | HashiCorp Vault for credentials       |
| **No Drift**        | Explicit cleanup tasks                |

### Cluster Topology Template

```
CONTROLLERS (Quorum Voters)
├── {{ controller_host_1 }} (node_id: {{ controller_id_1 }}) :{{ controller_port }}
├── {{ controller_host_2 }} (node_id: {{ controller_id_2 }}) :{{ controller_port }}
└── {{ controller_host_3 }} (node_id: {{ controller_id_3 }}) :{{ controller_port }}

BROKERS
├── {{ broker_host_1 }} (node_id: {{ broker_id_1 }}) :{{ broker_port }}
├── {{ broker_host_2 }} (node_id: {{ broker_id_2 }}) :{{ broker_port }}
└── {{ broker_host_3 }} (node_id: {{ broker_id_3 }}) :{{ broker_port }}
```

---

## Variable Definitions

### Required Variables

Define these in your inventory or environment file (not in git):

```yaml
# Environment identifier
env_name: "poc" # poc, nonprod, prod

# User/Group
kafka_user: "{{ service_user }}" # e.g., b4-reuse
kafka_group: "{{ service_group }}" # e.g., apim

# Base paths
base_path: "/ec/local/reuse" # Main installation root
ansible_base: "/ec/local/kafka/ansible" # Ansible repository
java_version: "jdk-17.0.2" # Java version

# Confluent
confluent_version: "7.9.3" # Confluent Platform version

# Controller hosts
controller_hosts:
  - host: "{{ controller_host_1 }}"
    node_id: 0
  - host: "{{ controller_host_2 }}"
    node_id: 1
  - host: "{{ controller_host_3 }}"
    node_id: 2

# Broker hosts
broker_hosts:
  - host: "{{ broker_host_1 }}"
    node_id: 200
  - host: "{{ broker_host_2 }}"
    node_id: 201
  - host: "{{ broker_host_3 }}"
    node_id: 202

# Ports
controller_port: 9093
broker_port: 9443
jmx_port: 7071

# Vault
vault_address: "{{ vault_addr }}"
vault_namespace: "{{ vault_ns }}"
vault_mount: "{{ vault_kv_mount }}"
vault_path: "passwords/{{ env_name }}"

# SSL
keystore_filename: "{{ env_name }}-keystore.jks"
truststore_filename: "{{ env_name }}-truststore.jks"
```

### Example Environment File

Create `inventories/<env>/group_vars/all.yml`:

```yaml
# ansible_user and connection
ansible_user: "{{ service_user }}"
ansible_ssh_private_key_file: "{{ ssh_key_path }}"
ansible_python_interpreter: /usr/bin/python3.12

# User/Group for file ownership
user: "{{ service_user }}"
group: "{{ service_group }}"

# Paths
custom_java_path: "{{ base_path }}/opt/{{ java_version }}"
ssl_file_dir: "{{ base_path }}/opt/ssl"
secrets_dir: "{{ base_path }}/opt/ssl"
secprops_path: "{{ base_path }}/opt/ssl/security.properties"

# Vault
vault_bin: "{{ ansible_base }}/vault/vault"
vault_path: "passwords/{{ env_name }}"
```

---

## Directory Structure

### Installation Base

```
{{ base_path }}/                              # Main installation root
├── opt/
│   ├── confluent-{{ confluent_version }}/    # Confluent Platform installation
│   │   ├── bin/                              # CLI tools
│   │   ├── etc/                              # Default configs (unused)
│   │   └── share/                            # Java libraries
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
│   │
│   ├── config/kafka/                         # Custom configs
│   │   └── log4j.properties
│   │
│   └── monitoring/                           # JMX exporter
│
├── etc/
│   ├── kafka/
│   │   └── server.properties                 # Broker config
│   └── controller/
│       └── server.properties                 # Controller config
│
├── logs/                                     # Runtime logs + GC logs
├── tmp/                                      # Java temp directory
└── scripts/management/                       # Management scripts
    ├── kafka_node.sh
    └── kafka_tools.sh
```

### Ansible Repository Structure

```
{{ ansible_base }}/                            # Ansible base
├── ansible.cfg
├── README.md
├── inventories/
│   ├── {{ env_name }}/
│   │   ├── hosts.yml
│   │   └── group_vars/
│   │       ├── all.yml                       # Shared config
│   │       ├── kafka_controller.yml          # Controller-specific
│   │       └── kafka_broker.yml              # Broker-specific
│   └── ...
│
├── playbooks/
│   ├── 10-kafka-controllers.yml
│   ├── 20-kafka-brokers.yml
│   └── tasks/
│       ├── preflight.yml
│       ├── vault-bootstrap.yml
│       ├── vault-stage.yml
│       └── management.yml
│
├── resources/
│   ├── confluent-{{ confluent_version }}.tar.gz
│   ├── override.yml
│   ├── secrets.yml                           # NOT in git - contains vault config
│   └── ec-overrides.md
│
└── scripts/management/
```

---

## Path Reference

### Critical Paths Quick Reference

| Purpose               | Path Template                                                |
| --------------------- | ------------------------------------------------------------ |
| **Ansible Base**      | `{{ ansible_base }}/`                                        |
| **Installation**      | `{{ base_path }}/opt/confluent-{{ confluent_version }}/`     |
| **Binary Path**       | `{{ base_path }}/opt/confluent-{{ confluent_version }}/bin/` |
| **JAVA_HOME**         | `{{ base_path }}/opt/{{ java_version }}`                     |
| **Controller Config** | `{{ base_path }}/etc/controller/server.properties`           |
| **Broker Config**     | `{{ base_path }}/etc/kafka/server.properties`                |
| **Controller Data**   | `{{ base_path }}/opt/data/controller`                        |
| **Broker Data**       | `{{ base_path }}/opt/data`                                   |
| **SSL Directory**     | `{{ base_path }}/opt/ssl/`                                   |
| **Security Props**    | `{{ base_path }}/opt/ssl/security.properties`                |
| **Logs Directory**    | `{{ base_path }}/logs/`                                      |
| **Systemd (User)**    | `~/.config/systemd/user/`                                    |
| **Vault Binary**      | `{{ ansible_base }}/vault/vault`                             |

### Service Names

| Component      | Service Name            | Systemd File                                           |
| -------------- | ----------------------- | ------------------------------------------------------ |
| **Controller** | `confluent-kcontroller` | `~/.config/systemd/user/confluent-kcontroller.service` |
| **Broker**     | `confluent-server`      | `~/.config/systemd/user/confluent-server.service`      |

### Ports (Defaults)

| Service         | Port Variable              | Default |
| --------------- | -------------------------- | ------- |
| Controller      | `{{ controller_port }}`    | 9093    |
| Broker (Client) | `{{ broker_port }}`        | 9443    |
| JMX Prometheus  | `{{ jmx_port }}`           | 7071    |
| Node Exporter   | `{{ node_exporter_port }}` | 9100    |

---

## Vault Integration

### Configuration

```yaml
vault_address: "{{ vault_addr }}" # From environment
vault_namespace: "{{ vault_ns }}" # From environment
vault_mount: "{{ vault_kv_mount }}" # From environment
vault_path: "passwords/{{ env_name }}" # Environment-specific
vault_bin: "{{ ansible_base }}/vault/vault"
```

### Required Secrets

Vault must contain at path `passwords/{{ env_name }}`:

| Field                 | Purpose                                   |
| --------------------- | ----------------------------------------- |
| `masterkey`           | Secrets Protection master key             |
| `security_properties` | Pre-encrypted security.properties content |

### Bootstrap Workflow

```bash
# Export Vault token (obtain via PrivX or your auth method)
export VAULT_TOKEN="${VAULT_TOKEN}"

# Run bootstrap for environment
cd {{ ansible_base }}
ansible-playbook playbooks/tasks/vault-bootstrap.yml \
  -e vault_env={{ env_name }} \
  -e "@resources/secrets.yml"
```

### Secrets Protection

Passwords in config files use SecurePass provider:

```properties
config.providers=securepass
config.providers.securepass.class=io.confluent.kafka.security.config.provider.SecurePassConfigProvider

ssl.keystore.password=${securepass:{{ base_path }}/opt/ssl/security.properties:ssl.keystore.password}
ssl.key.password=${securepass:{{ base_path }}/opt/ssl/security.properties:ssl.key.password}
ssl.truststore.password=${securepass:{{ base_path }}/opt/ssl/security.properties:ssl.truststore.password}
```

---

## Ansible Deployment

### Environment Setup

```bash
# SSH to ansible control node
export VAULT_TOKEN="${VAULT_TOKEN}"
cd {{ ansible_base }}
```

### Deploy Controllers

```bash
ansible-playbook -i inventories/{{ env_name }}/hosts.yml \
  playbooks/10-kafka-controllers.yml \
  --limit {{ controller_host_1 }} \
  -vv \
  --skip-tags ec,package,sysctl,health_check \
  -e "@resources/override.yml"
```

### Deploy Brokers

```bash
ansible-playbook -i inventories/{{ env_name }}/hosts.yml \
  playbooks/20-kafka-brokers.yml \
  --limit {{ broker_host_1 }} \
  -vv \
  --skip-tags ec,package,sysctl,health_check \
  -e "@resources/override.yml"
```

### Skip Tags Reference

| Tag            | Purpose                   | When to Skip         |
| -------------- | ------------------------- | -------------------- |
| `ec`           | EC-specific modifications | Already applied      |
| `package`      | Package installation      | Re-runs              |
| `sysctl`       | Sysctl tuning             | No root access       |
| `health_check` | Post-deploy checks        | Manual verification  |
| `systemd`      | Service file updates      | No changes needed    |
| `filesystem`   | Directory permissions     | Already set          |
| `privileged`   | Root-requiring tasks      | Non-root environment |

### Dry Run

```bash
ansible-playbook -i inventories/{{ env_name }}/hosts.yml \
  playbooks/10-kafka-controllers.yml \
  --check \
  -e "@resources/override.yml"
```

---

## EC Customizations

### Summary of Modifications

All changes are documented in `{{ ansible_base }}/resources/ec-overrides.md` and tagged with `ec` in playbooks.

### Key Customizations

| Area                | Standard Confluent             | EC Override                          |
| ------------------- | ------------------------------ | ------------------------------------ |
| **Systemd Scope**   | System (`/etc/systemd/system`) | User (`~/.config/systemd/user`)      |
| **Systemd Target**  | `multi-user.target`            | `default.target`                     |
| **User/Group**      | Root ownership                 | `{{ kafka_user }}:{{ kafka_group }}` |
| **Java Install**    | Role-managed                   | Pre-installed at custom path         |
| **SSL Validation**  | Permissive assertions          | Debug messages (no fail)             |
| **Storage Format**  | Automatic                      | `--ignore-formatted` flag            |
| **SASL/RBAC**       | Configurable                   | Disabled (SSL-only)                  |
| **Support Metrics** | Enabled                        | Disabled                             |

---

## Service Management

### Using kafka_node.sh

```bash
# Start Kafka (auto-detects controller/broker)
{{ base_path }}/scripts/management/kafka_node.sh start

# Stop Kafka
{{ base_path }}/scripts/management/kafka_node.sh stop

# Check status
{{ base_path }}/scripts/management/kafka_node.sh status

# Restart
{{ base_path }}/scripts/management/kafka_node.sh restart
```

### Direct systemctl Commands

```bash
# Controller operations
systemctl --user start confluent-kcontroller
systemctl --user stop confluent-kcontroller
systemctl --user status confluent-kcontroller
systemctl --user restart confluent-kcontroller

# Broker operations
systemctl --user start confluent-server
systemctl --user stop confluent-server
systemctl --user status confluent-server
systemctl --user restart confluent-server

# Reload after config changes
systemctl --user daemon-reload
```

---

## SSL/TLS Configuration

### Certificate Files

| File                        | Purpose             | Location                   |
| --------------------------- | ------------------- | -------------------------- |
| `{{ keystore_filename }}`   | Node identity       | `{{ base_path }}/opt/ssl/` |
| `{{ truststore_filename }}` | CA certificates     | `{{ base_path }}/opt/ssl/` |
| `security.properties`       | Encrypted passwords | `{{ base_path }}/opt/ssl/` |

### Listener Configuration

**Controller:**

```properties
listeners=CONTROLLER://:{{ controller_port }}
listener.security.protocol.map=CONTROLLER:SSL
controller.listener.names=CONTROLLER
```

**Broker:**

```properties
listeners=SSL://:{{ broker_port }}
listener.security.protocol.map=SSL:SSL
advertised.listeners=SSL://{{ broker_host }}:{{ broker_port }}
security.inter.broker.protocol=SSL
```

### SSL Settings

```properties
ssl.enabled.protocols=TLSv1.3,TLSv1.2
ssl.client.auth=required
ssl.principal.mapping.rules=RULE:^CN=(.*?),.*$/\\$1/L,DEFAULT
```

---

## Troubleshooting

### Common Issues

| Problem                           | Likely Cause           | Solution                                            |
| --------------------------------- | ---------------------- | --------------------------------------------------- |
| **Vault bootstrap fails**         | Token expired/invalid  | Re-authenticate via PrivX                           |
| **Controllers won't form quorum** | Network/SSL issue      | Check listener reachability                         |
| **Brokers can't join**            | Controller unreachable | Verify `controller.quorum.voters`                   |
| **Service won't start**           | Missing master key     | Check systemd override                              |
| **Permission denied**             | Wrong owner            | `chown {{ kafka_user }}:{{ kafka_group }}` on paths |

### Validate Quorum

```bash
{{ base_path }}/opt/confluent-{{ confluent_version }}/bin/kafka-metadata \
  --snapshot {{ base_path }}/opt/data/controller/__cluster_metadata-0/00000000000000000000.log \
  --command quorum
```

### Check Logs

```bash
# Controller logs
tail -f {{ base_path }}/logs/controller.log

# Broker logs
tail -f {{ base_path }}/logs/server.log

# GC logs
tail -f {{ base_path }}/logs/gc.log

# Systemd journal
journalctl --user -u confluent-kcontroller -f
journalctl --user -u confluent-server -f
```

### Test SSL Connectivity

```bash
# Test controller SSL
openssl s_client -connect {{ controller_host }}:{{ controller_port }} \
  -cert {{ base_path }}/opt/ssl/client.crt \
  -key {{ base_path }}/opt/ssl/client.key \
  -CAfile {{ base_path }}/opt/ssl/ca.crt

# Test broker SSL
openssl s_client -connect {{ broker_host }}:{{ broker_port }} \
  -cert {{ base_path }}/opt/ssl/client.crt \
  -key {{ base_path }}/opt/ssl/client.key \
  -CAfile {{ base_path }}/opt/ssl/ca.crt
```

---

## Quick Reference Card

```
┌──────────────────────────────────────────────────────────────────────────┐
│                     EC KAFKA DEPLOYMENT QUICK REFERENCE                   │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  PATHS (configure via inventory)                                          │
│  ─────                                                                    │
│  Ansible:     {{ ansible_base }}/                                        │
│  Confluent:   {{ base_path }}/opt/confluent-{{ confluent_version }}/     │
│  Java:        {{ base_path }}/opt/{{ java_version }}/                    │
│  SSL:         {{ base_path }}/opt/ssl/                                   │
│  Data:        {{ base_path }}/opt/data/                                  │
│  Logs:        {{ base_path }}/logs/                                      │
│  Systemd:     ~/.config/systemd/user/                                    │
│                                                                           │
│  SERVICES                                                                 │
│  ────────                                                                 │
│  Controller:  systemctl --user {start|stop|status} confluent-kcontroller │
│  Broker:      systemctl --user {start|stop|status} confluent-server      │
│                                                                           │
│  PORTS (defaults)                                                         │
│  ─────                                                                    │
│  Controller:  {{ controller_port }} (SSL)                                │
│  Broker:      {{ broker_port }} (SSL)                                    │
│  JMX Export:  {{ jmx_port }}                                             │
│                                                                           │
│  DEPLOY                                                                   │
│  ──────                                                                   │
│  export VAULT_TOKEN="${VAULT_TOKEN}"                                     │
│  cd {{ ansible_base }}                                                   │
│  ansible-playbook playbooks/10-kafka-controllers.yml \                   │
│    -i inventories/{{ env_name }}/hosts.yml \                             │
│    --limit <host> -e "@resources/override.yml"                           │
│                                                                           │
│  USER/GROUP: {{ kafka_user }}:{{ kafka_group }}                          │
│                                                                           │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## Sample Inventory Template

Create `inventories/<env_name>/hosts.yml`:

```yaml
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

> **Important:** Replace all `{{ variable }}` placeholders with actual values in your environment-specific inventory files (which should NOT be committed to git).
