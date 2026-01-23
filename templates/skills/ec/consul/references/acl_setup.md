# Consul ACL Setup and Token Management

## Table of Contents

- [Bootstrap ACLs](#bootstrap-acls)
- [Token Types](#token-types)
- [Creating Tokens](#creating-tokens)
- [Policy Examples](#policy-examples)
- [Troubleshooting ACLs](#troubleshooting-acls)

---

## Bootstrap ACLs

### Automatic Bootstrap (Recommended)

When using `manageSystemACLs: true` in Helm values, Consul automatically:

- Creates bootstrap token
- Stores it in Kubernetes secret
- Creates system tokens for components

```bash
# Retrieve bootstrap token
kubectl get secret consul-bootstrap-acl-token -n consul -o jsonpath='{.data.token}' | base64 -d
```

### Manual Bootstrap

```bash
# Bootstrap ACL system
kubectl exec -n consul consul-server-0 -- consul acl bootstrap

# Save the SecretID (bootstrap token) securely!
```

---

## Token Types

| Token Type       | Purpose                          | Scope                   |
| ---------------- | -------------------------------- | ----------------------- |
| **Bootstrap**    | Initial admin token              | Global, all permissions |
| **Agent**        | Node-level operations            | Per-node                |
| **Service**      | Service registration/intentions  | Per-service             |
| **Mesh Gateway** | Cross-datacenter traffic         | Federation              |
| **Connect CA**   | Certificate authority operations | Connect                 |

---

## Creating Tokens

### Create Policy First

```bash
# Create policy file
cat <<EOF > read-only-policy.hcl
service_prefix "" {
  policy = "read"
}
node_prefix "" {
  policy = "read"
}
EOF

# Apply policy
kubectl exec -n consul consul-server-0 -- consul acl policy create \
  -name "read-only" \
  -rules @/tmp/read-only-policy.hcl \
  -token=<bootstrap-token>
```

### Create Token with Policy

```bash
kubectl exec -n consul consul-server-0 -- consul acl token create \
  -description "Read-only monitoring token" \
  -policy-name "read-only" \
  -token=<bootstrap-token>
```

---

## Policy Examples

### Service Registration Policy

```hcl
service "api" {
  policy = "write"
}
service_prefix "" {
  policy = "read"
}
node_prefix "" {
  policy = "read"
}
```

### Mesh Gateway Policy

```hcl
service "mesh-gateway" {
  policy = "write"
}
service_prefix "" {
  policy = "read"
}
node_prefix "" {
  policy = "read"
}
agent_prefix "" {
  policy = "read"
}
```

### DNS Query Policy

```hcl
service_prefix "" {
  policy = "read"
}
node_prefix "" {
  policy = "read"
}
query_prefix "" {
  policy = "read"
}
```

---

## Troubleshooting ACLs

### Common Errors

| Error               | Cause                  | Solution                             |
| ------------------- | ---------------------- | ------------------------------------ |
| `ACL not found`     | Token doesn't exist    | Create token or use correct SecretID |
| `Permission denied` | Token lacks permission | Add required policy to token         |
| `ACL disabled`      | ACLs not enabled       | Enable ACLs in Helm values           |

### Debug Commands

```bash
# List all tokens
kubectl exec -n consul consul-server-0 -- consul acl token list -token=<bootstrap>

# Read specific token
kubectl exec -n consul consul-server-0 -- consul acl token read -id <accessor-id> -token=<bootstrap>

# List policies
kubectl exec -n consul consul-server-0 -- consul acl policy list -token=<bootstrap>

# Translate legacy tokens (if upgrading)
kubectl exec -n consul consul-server-0 -- consul acl token update -id <token-id> -upgrade-legacy -token=<bootstrap>
```

### Reset ACLs (Emergency)

```bash
# Delete ACL data and re-bootstrap (DATA LOSS!)
kubectl exec -n consul consul-server-0 -- consul acl bootstrap -reset

# Or recreate the bootstrap secret
kubectl delete secret consul-bootstrap-acl-token -n consul
helm upgrade consul hashicorp/consul -n consul -f values.yaml
```
