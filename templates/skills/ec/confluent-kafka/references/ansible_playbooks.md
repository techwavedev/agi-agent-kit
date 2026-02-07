# Confluent Kafka Ansible Playbooks

Ansible automation patterns for Confluent Kafka tarball installations.

---

## ⚠️ EC Environment Notes

> **This guide shows generic Ansible patterns.** For EC-specific deployments:

| Standard Pattern                      | EC Pattern                                               |
| ------------------------------------- | -------------------------------------------------------- |
| Root systemd (`/etc/systemd/system/`) | User systemd (`~/.config/systemd/user/`)                 |
| `ansible_become: yes`                 | `ansible_become: false`                                  |
| `systemctl start`                     | `systemctl --user start`                                 |
| `/opt/confluent/`                     | `{{ base_path }}/opt/confluent-{{ confluent_version }}/` |
| `/var/kafka-logs/`                    | `{{ base_path }}/opt/data`                               |
| `/var/ssl/kafka/`                     | `{{ base_path }}/opt/ssl/`                               |

**EC Ansible Base:** `{{ ansible_base }}/` (e.g., `/ec/local/kafka/ansible/`)

**Key EC Constraints:**

- No root access (`ansible_become: false`)
- User-scope systemd services (`scope: user`)
- HashiCorp Vault for secrets
- SSL-only (no SASL/RBAC)

See **[ec_deployment.md](ec_deployment.md)** for complete EC Ansible setup and deployment commands.

---

## Table of Contents

1. [Directory Structure](#directory-structure)
2. [Inventory Configuration](#inventory-configuration)
3. [Common Variables](#common-variables)
4. [Playbooks](#playbooks)
5. [Roles](#roles)
6. [Usage Examples](#usage-examples)

---

## Directory Structure

```
ansible/
├── inventory/
│   ├── production/
│   │   ├── hosts.ini
│   │   └── group_vars/
│   │       ├── all.yml
│   │       ├── controllers.yml
│   │       ├── brokers.yml
│   │       └── schema_registry.yml
│   └── staging/
│       └── ...
├── playbooks/
│   ├── install.yml
│   ├── upgrade.yml
│   ├── rolling_restart.yml
│   ├── health_check.yml
│   ├── backup.yml
│   └── kraft_migration.yml
├── roles/
│   ├── confluent-common/
│   ├── confluent-controller/
│   ├── confluent-broker/
│   ├── confluent-schema-registry/
│   ├── confluent-connect/
│   └── confluent-control-center/
└── files/
    ├── confluent-8.0.0.tar.gz
    └── ssl/
```

---

## Inventory Configuration

### Production Inventory

```ini
# inventory/production/hosts.ini

[controllers]
kafka-controller-01 ansible_host=10.0.1.11 node_id=1
kafka-controller-02 ansible_host=10.0.1.12 node_id=2
kafka-controller-03 ansible_host=10.0.1.13 node_id=3

[brokers]
kafka-broker-01 ansible_host=10.0.2.11 node_id=101
kafka-broker-02 ansible_host=10.0.2.12 node_id=102
kafka-broker-03 ansible_host=10.0.2.13 node_id=103
kafka-broker-04 ansible_host=10.0.2.14 node_id=104
kafka-broker-05 ansible_host=10.0.2.15 node_id=105

[schema_registry]
kafka-sr-01 ansible_host=10.0.3.11
kafka-sr-02 ansible_host=10.0.3.12

[connect]
kafka-connect-01 ansible_host=10.0.4.11
kafka-connect-02 ansible_host=10.0.4.12
kafka-connect-03 ansible_host=10.0.4.13

[control_center]
kafka-cc-01 ansible_host=10.0.5.11

[confluent:children]
controllers
brokers
schema_registry
connect
control_center

[confluent:vars]
ansible_user=kafka
ansible_become=yes
ansible_python_interpreter=/usr/bin/python3
```

### Group Variables

```yaml
# inventory/production/group_vars/all.yml

# Confluent Platform version
confluent_version: "8.0.0"
confluent_install_base: "/opt"
confluent_install_path: "{{ confluent_install_base }}/confluent-{{ confluent_version }}"
confluent_symlink: "{{ confluent_install_base }}/confluent"

# Java configuration
java_home: "/opt/amazon-corretto-17"
kafka_heap_opts: "-Xms6g -Xmx6g"

# Cluster configuration
cluster_id: "MkU3OThlYzExNjdmNGIyMG" # Generated once: kafka-storage random-uuid
kafka_kraft_enabled: true

# Controller quorum
controller_quorum_voters: >-
  1@kafka-controller-01:9093,2@kafka-controller-02:9093,3@kafka-controller-03:9093

# Listeners
kafka_listener_internal_port: 9092
kafka_listener_external_port: 9094
kafka_controller_port: 9093

# Security
kafka_security_protocol: "SASL_SSL"
kafka_sasl_mechanism: "PLAIN"
ssl_keystore_path: "/var/ssl/kafka/kafka.keystore.jks"
ssl_truststore_path: "/var/ssl/kafka/kafka.truststore.jks"

# Data directories
kafka_log_dirs: "/var/kafka-logs"
controller_data_dir: "/var/kafka-controller"

# Logging
kafka_log_path: "/var/log/confluent/kafka"
```

```yaml
# inventory/production/group_vars/brokers.yml

# Broker-specific settings
kafka_broker_heap_opts: "-Xms8g -Xmx8g"
kafka_num_partitions: 12
kafka_default_replication_factor: 3
kafka_min_insync_replicas: 2

# Performance tuning
kafka_num_network_threads: 8
kafka_num_io_threads: 16
kafka_socket_send_buffer_bytes: 102400
kafka_socket_receive_buffer_bytes: 102400

# Retention
kafka_log_retention_hours: 168
kafka_log_segment_bytes: 1073741824
```

---

## Common Variables

```yaml
# inventory/production/group_vars/controllers.yml

# Controller-specific settings
controller_heap_opts: "-Xms4g -Xmx4g"
controller_log_dirs: "{{ controller_data_dir }}"
```

---

## Playbooks

### Installation Playbook

```yaml
# playbooks/install.yml
---
- name: Install Confluent Platform
  hosts: confluent
  become: yes
  vars:
    tarball_path: "files/confluent-{{ confluent_version }}.tar.gz"

  tasks:
    - name: Create kafka user
      ansible.builtin.user:
        name: kafka
        shell: /bin/bash
        system: yes
        create_home: yes

    - name: Create directories
      ansible.builtin.file:
        path: "{{ item }}"
        state: directory
        owner: kafka
        group: kafka
        mode: "0755"
      loop:
        - "{{ confluent_install_base }}"
        - "{{ kafka_log_dirs }}"
        - "{{ kafka_log_path }}"
        - /var/ssl/kafka

    - name: Extract Confluent Platform
      ansible.builtin.unarchive:
        src: "{{ tarball_path }}"
        dest: "{{ confluent_install_base }}"
        owner: kafka
        group: kafka
        creates: "{{ confluent_install_path }}"

    - name: Create symlink
      ansible.builtin.file:
        src: "{{ confluent_install_path }}"
        dest: "{{ confluent_symlink }}"
        state: link
        owner: kafka
        group: kafka

    - name: Install Java
      ansible.builtin.include_role:
        name: confluent-common
        tasks_from: install_java

- name: Configure Controllers
  hosts: controllers
  become: yes
  roles:
    - confluent-controller

- name: Configure Brokers
  hosts: brokers
  become: yes
  roles:
    - confluent-broker

- name: Configure Schema Registry
  hosts: schema_registry
  become: yes
  roles:
    - confluent-schema-registry

- name: Configure Connect
  hosts: connect
  become: yes
  roles:
    - confluent-connect

- name: Configure Control Center
  hosts: control_center
  become: yes
  roles:
    - confluent-control-center
```

### Rolling Upgrade Playbook

```yaml
# playbooks/upgrade.yml
---
- name: Pre-upgrade validation
  hosts: brokers[0]
  become: yes
  tasks:
    - name: Check for under-replicated partitions
      ansible.builtin.command: >
        {{ confluent_symlink }}/bin/kafka-topics 
        --bootstrap-server localhost:{{ kafka_listener_internal_port }}
        --describe --under-replicated-partitions
      register: urp_check
      changed_when: false

    - name: Fail if partitions are under-replicated
      ansible.builtin.fail:
        msg: "Under-replicated partitions detected. Aborting upgrade."
      when: urp_check.stdout | length > 0

- name: Upgrade Schema Registry (rolling)
  hosts: schema_registry
  become: yes
  serial: 1
  tasks:
    - name: Stop Schema Registry
      ansible.builtin.systemd:
        name: confluent-schema-registry
        state: stopped

    - name: Update symlink
      ansible.builtin.file:
        src: "{{ confluent_install_path }}"
        dest: "{{ confluent_symlink }}"
        state: link
        force: yes

    - name: Start Schema Registry
      ansible.builtin.systemd:
        name: confluent-schema-registry
        state: started

    - name: Wait for Schema Registry health
      ansible.builtin.uri:
        url: "http://localhost:8081/"
        status_code: 200
      register: sr_health
      until: sr_health.status == 200
      retries: 30
      delay: 10

- name: Upgrade Kafka Brokers (rolling)
  hosts: brokers
  become: yes
  serial: 1
  max_fail_percentage: 0
  tasks:
    - name: Get broker ID
      ansible.builtin.command: >
        grep broker.id {{ confluent_symlink }}/etc/kafka/server.properties
      register: broker_id_line
      changed_when: false

    - name: Extract broker ID
      ansible.builtin.set_fact:
        broker_id: "{{ broker_id_line.stdout.split('=')[1] }}"

    - name: Initiate controlled shutdown
      ansible.builtin.systemd:
        name: confluent-server
        state: stopped

    - name: Wait for partition leadership migration
      ansible.builtin.pause:
        seconds: 60

    - name: Verify broker is stopped
      ansible.builtin.wait_for:
        port: "{{ kafka_listener_internal_port }}"
        state: stopped
        timeout: 120

    - name: Backup current configuration
      ansible.builtin.archive:
        path: "{{ confluent_symlink }}/etc/kafka"
        dest: "/backup/kafka-config-{{ ansible_date_time.epoch }}.tar.gz"

    - name: Update symlink to new version
      ansible.builtin.file:
        src: "{{ confluent_install_path }}"
        dest: "{{ confluent_symlink }}"
        state: link
        force: yes

    - name: Restore configuration
      ansible.builtin.copy:
        src: "/backup/server.properties"
        dest: "{{ confluent_symlink }}/etc/kafka/server.properties"
        remote_src: yes

    - name: Remove deprecated configs
      ansible.builtin.lineinfile:
        path: "{{ confluent_symlink }}/etc/kafka/server.properties"
        regexp: "{{ item }}"
        state: absent
      loop:
        - "^log.message.format.version"
        - "^inter.broker.protocol.version"

    - name: Start Kafka broker
      ansible.builtin.systemd:
        name: confluent-server
        state: started

    - name: Wait for broker to join cluster
      ansible.builtin.command: >
        {{ confluent_symlink }}/bin/kafka-broker-api-versions
        --bootstrap-server localhost:{{ kafka_listener_internal_port }}
      register: broker_check
      until: broker_check.rc == 0
      retries: 30
      delay: 10

    - name: Wait for ISR sync
      ansible.builtin.command: >
        {{ confluent_symlink }}/bin/kafka-topics
        --bootstrap-server localhost:{{ kafka_listener_internal_port }}
        --describe --under-replicated-partitions
      register: isr_check
      until: isr_check.stdout | length == 0
      retries: 60
      delay: 10
      changed_when: false
```

### Rolling Restart Playbook

```yaml
# playbooks/rolling_restart.yml
---
- name: Rolling restart Kafka brokers
  hosts: brokers
  become: yes
  serial: 1
  max_fail_percentage: 0

  tasks:
    - name: Check cluster health before restart
      ansible.builtin.command: >
        {{ confluent_symlink }}/bin/kafka-topics
        --bootstrap-server localhost:{{ kafka_listener_internal_port }}
        --describe --under-replicated-partitions
      register: pre_check
      changed_when: false
      delegate_to: "{{ groups['brokers'][0] }}"
      run_once: true

    - name: Stop broker
      ansible.builtin.systemd:
        name: confluent-server
        state: stopped

    - name: Wait for controlled shutdown
      ansible.builtin.wait_for:
        port: "{{ kafka_listener_internal_port }}"
        state: stopped
        timeout: 300

    - name: Start broker
      ansible.builtin.systemd:
        name: confluent-server
        state: started

    - name: Wait for broker health
      ansible.builtin.wait_for:
        port: "{{ kafka_listener_internal_port }}"
        state: started
        timeout: 120

    - name: Wait for ISR sync
      ansible.builtin.command: >
        {{ confluent_symlink }}/bin/kafka-topics
        --bootstrap-server localhost:{{ kafka_listener_internal_port }}
        --describe --under-replicated-partitions
      register: isr_check
      until: isr_check.stdout | length == 0
      retries: 60
      delay: 10
      changed_when: false
```

### Health Check Playbook

```yaml
# playbooks/health_check.yml
---
- name: Kafka Cluster Health Check
  hosts: brokers[0]
  become: yes
  gather_facts: no

  tasks:
    - name: Check broker count
      ansible.builtin.command: >
        {{ confluent_symlink }}/bin/kafka-metadata
        --snapshot {{ kafka_log_dirs }}/__cluster_metadata-0/00000000000000000000.log
        --command broker
      register: broker_count
      changed_when: false

    - name: Display broker count
      ansible.builtin.debug:
        msg: "Active brokers: {{ broker_count.stdout_lines | length }}"

    - name: Check controller quorum
      ansible.builtin.command: >
        {{ confluent_symlink }}/bin/kafka-metadata
        --snapshot {{ kafka_log_dirs }}/__cluster_metadata-0/00000000000000000000.log
        --command quorum
      register: quorum_status
      changed_when: false

    - name: Display quorum status
      ansible.builtin.debug:
        var: quorum_status.stdout_lines

    - name: Check under-replicated partitions
      ansible.builtin.command: >
        {{ confluent_symlink }}/bin/kafka-topics
        --bootstrap-server localhost:{{ kafka_listener_internal_port }}
        --describe --under-replicated-partitions
      register: urp
      changed_when: false

    - name: Display URP status
      ansible.builtin.debug:
        msg: "{{ 'No under-replicated partitions' if urp.stdout | length == 0 else urp.stdout }}"

    - name: Check offline partitions
      ansible.builtin.command: >
        {{ confluent_symlink }}/bin/kafka-topics
        --bootstrap-server localhost:{{ kafka_listener_internal_port }}
        --describe --unavailable-partitions
      register: offline
      changed_when: false

    - name: Alert on offline partitions
      ansible.builtin.fail:
        msg: "CRITICAL: Offline partitions detected: {{ offline.stdout }}"
      when: offline.stdout | length > 0

- name: Check Schema Registry
  hosts: schema_registry[0]
  become: yes
  gather_facts: no

  tasks:
    - name: Schema Registry health
      ansible.builtin.uri:
        url: http://localhost:8081/
        return_content: yes
      register: sr_health

    - name: Display SR status
      ansible.builtin.debug:
        msg: "Schema Registry: {{ sr_health.json }}"

- name: Check Connect cluster
  hosts: connect[0]
  become: yes
  gather_facts: no

  tasks:
    - name: Connect cluster health
      ansible.builtin.uri:
        url: http://localhost:8083/
        return_content: yes
      register: connect_health

    - name: List connectors
      ansible.builtin.uri:
        url: http://localhost:8083/connectors
        return_content: yes
      register: connectors

    - name: Display Connect status
      ansible.builtin.debug:
        msg: "Connect workers: {{ connect_health.json.kafka_cluster_id }}, Connectors: {{ connectors.json | length }}"
```

### Backup Playbook

```yaml
# playbooks/backup.yml
---
- name: Backup Confluent Kafka Configuration
  hosts: confluent
  become: yes
  vars:
    backup_base: "/backup"
    backup_dir: "{{ backup_base }}/confluent-{{ ansible_date_time.date }}"

  tasks:
    - name: Create backup directory
      ansible.builtin.file:
        path: "{{ backup_dir }}"
        state: directory
        mode: "0755"

    - name: Backup configurations
      ansible.builtin.archive:
        path: "{{ confluent_symlink }}/etc"
        dest: "{{ backup_dir }}/{{ inventory_hostname }}-config.tar.gz"

    - name: Backup SSL certificates
      ansible.builtin.archive:
        path: /var/ssl/kafka
        dest: "{{ backup_dir }}/{{ inventory_hostname }}-ssl.tar.gz"
      ignore_errors: yes

- name: Backup Kafka metadata
  hosts: brokers[0]
  become: yes
  vars:
    backup_dir: "/backup/confluent-{{ ansible_date_time.date }}"

  tasks:
    - name: Export topic configurations
      ansible.builtin.shell: >
        {{ confluent_symlink }}/bin/kafka-configs
        --bootstrap-server localhost:{{ kafka_listener_internal_port }}
        --entity-type topics --all --describe > {{ backup_dir }}/topic-configs.txt
      changed_when: false

    - name: Export ACLs
      ansible.builtin.shell: >
        {{ confluent_symlink }}/bin/kafka-acls
        --bootstrap-server localhost:{{ kafka_listener_internal_port }}
        --list > {{ backup_dir }}/acls.txt
      changed_when: false

    - name: Create controller snapshot
      ansible.builtin.command: >
        {{ confluent_symlink }}/bin/kafka-metadata
        --snapshot {{ kafka_log_dirs }}/__cluster_metadata-0/00000000000000000000.log
        --command snapshot > {{ backup_dir }}/metadata-snapshot.json
      changed_when: false
```

---

## Roles

### Broker Role Example

```yaml
# roles/confluent-broker/tasks/main.yml
---
- name: Template broker configuration
  ansible.builtin.template:
    src: server.properties.j2
    dest: "{{ confluent_symlink }}/etc/kafka/server.properties"
    owner: kafka
    group: kafka
    mode: "0644"
  notify: Restart Kafka broker

- name: Template JVM options
  ansible.builtin.template:
    src: jvm.config.j2
    dest: "{{ confluent_symlink }}/etc/kafka/jvm.config"
    owner: kafka
    group: kafka
    mode: "0644"
  notify: Restart Kafka broker

- name: Create systemd unit
  ansible.builtin.template:
    src: confluent-server.service.j2
    dest: /etc/systemd/system/confluent-server.service
    mode: "0644"
  notify:
    - Reload systemd
    - Restart Kafka broker

- name: Enable and start Kafka broker
  ansible.builtin.systemd:
    name: confluent-server
    state: started
    enabled: yes
    daemon_reload: yes
```

```jinja2
{# roles/confluent-broker/templates/server.properties.j2 #}

# Broker Configuration
# Generated by Ansible - Do not edit manually

# KRaft mode settings
process.roles=broker
node.id={{ node_id }}
controller.quorum.voters={{ controller_quorum_voters }}
controller.listener.names=CONTROLLER
inter.broker.listener.name=INTERNAL

# Listeners
listeners=INTERNAL://0.0.0.0:{{ kafka_listener_internal_port }},EXTERNAL://0.0.0.0:{{ kafka_listener_external_port }}
advertised.listeners=INTERNAL://{{ ansible_fqdn }}:{{ kafka_listener_internal_port }},EXTERNAL://{{ ansible_fqdn }}:{{ kafka_listener_external_port }}
listener.security.protocol.map=INTERNAL:{{ kafka_security_protocol }},EXTERNAL:{{ kafka_security_protocol }},CONTROLLER:{{ kafka_security_protocol }}

# SASL Configuration
sasl.mechanism.inter.broker.protocol=PLAIN
sasl.enabled.mechanisms=PLAIN

# SSL Configuration
ssl.keystore.location={{ ssl_keystore_path }}
ssl.keystore.password={{ ssl_keystore_password }}
ssl.truststore.location={{ ssl_truststore_path }}
ssl.truststore.password={{ ssl_truststore_password }}

# Data directories
log.dirs={{ kafka_log_dirs }}

# Performance tuning
num.network.threads={{ kafka_num_network_threads }}
num.io.threads={{ kafka_num_io_threads }}
socket.send.buffer.bytes={{ kafka_socket_send_buffer_bytes }}
socket.receive.buffer.bytes={{ kafka_socket_receive_buffer_bytes }}
socket.request.max.bytes=104857600

# Topic defaults
num.partitions={{ kafka_num_partitions }}
default.replication.factor={{ kafka_default_replication_factor }}
min.insync.replicas={{ kafka_min_insync_replicas }}

# Log retention
log.retention.hours={{ kafka_log_retention_hours }}
log.segment.bytes={{ kafka_log_segment_bytes }}
log.retention.check.interval.ms=300000

# Replication
replica.lag.time.max.ms=30000
num.replica.fetchers=4
replica.fetch.max.bytes=1048576

# Security
authorizer.class.name=kafka.security.authorizer.AclAuthorizer
super.users=User:admin
```

---

## Usage Examples

### Full Cluster Installation

```bash
# Deploy new cluster
ansible-playbook -i inventory/production/hosts.ini playbooks/install.yml

# Verify installation
ansible-playbook -i inventory/production/hosts.ini playbooks/health_check.yml
```

### Rolling Upgrade

```bash
# Pre-upgrade backup
ansible-playbook -i inventory/production/hosts.ini playbooks/backup.yml

# Upgrade from 7.6 to 8.0
ansible-playbook -i inventory/production/hosts.ini playbooks/upgrade.yml \
  -e confluent_version=8.0.0 \
  -e confluent_install_path=/opt/confluent-8.0.0

# Post-upgrade validation
ansible-playbook -i inventory/production/hosts.ini playbooks/health_check.yml
```

### Rolling Restart

```bash
# Restart all brokers (one at a time)
ansible-playbook -i inventory/production/hosts.ini playbooks/rolling_restart.yml

# Restart specific broker
ansible-playbook -i inventory/production/hosts.ini playbooks/rolling_restart.yml \
  --limit kafka-broker-03
```

### Ad-hoc Commands

```bash
# Check all broker versions
ansible brokers -i inventory/production/hosts.ini -m shell \
  -a "{{ confluent_symlink }}/bin/kafka-broker-api-versions --bootstrap-server localhost:9092 --version"

# Check disk usage on all brokers
ansible brokers -i inventory/production/hosts.ini -m shell \
  -a "df -h /var/kafka-logs"

# Restart Schema Registry cluster
ansible schema_registry -i inventory/production/hosts.ini -m systemd \
  -a "name=confluent-schema-registry state=restarted" --become
```
