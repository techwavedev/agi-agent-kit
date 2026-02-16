---
name: azure-keyvault-keys-rust
description: |
  Azure Key Vault Keys SDK for Rust. Use for creating, managing, and using cryptographic keys.
  Triggers: "keyvault keys rust", "KeyClient rust", "create key rust", "encrypt rust", "sign rust".
package: azure_security_keyvault_keys
---

# Azure Key Vault Keys SDK for Rust

Client library for Azure Key Vault Keys — secure storage and management of cryptographic keys.

## Installation

```sh
cargo add azure_security_keyvault_keys azure_identity
```

## Environment Variables

```bash
AZURE_KEYVAULT_URL=https://<vault-name>.vault.azure.net/
```

## Authentication

```rust
use azure_identity::DeveloperToolsCredential;
use azure_security_keyvault_keys::KeyClient;

let credential = DeveloperToolsCredential::new(None)?;
let client = KeyClient::new(
    "https://<vault-name>.vault.azure.net/",
    credential.clone(),
    None,
)?;
```

## Key Types

| Type | Description |
|------|-------------|
| RSA | RSA keys (2048, 3072, 4096 bits) |
| EC | Elliptic curve keys (P-256, P-384, P-521) |
| RSA-HSM | HSM-protected RSA keys |
| EC-HSM | HSM-protected EC keys |

## Core Operations

### Get Key

```rust
let key = client
    .get_key("key-name", None)
    .await?
    .into_model()?;

println!("Key ID: {:?}", key.key.as_ref().map(|k| &k.kid));
```

### Create Key

```rust
use azure_security_keyvault_keys::models::{CreateKeyParameters, KeyType};

let params = CreateKeyParameters {
    kty: KeyType::Rsa,
    key_size: Some(2048),
    ..Default::default()
};

let key = client
    .create_key("key-name", params.try_into()?, None)
    .await?
    .into_model()?;
```

### Create EC Key

```rust
use azure_security_keyvault_keys::models::{CreateKeyParameters, KeyType, CurveName};

let params = CreateKeyParameters {
    kty: KeyType::Ec,
    curve: Some(CurveName::P256),
    ..Default::default()
};

let key = client
    .create_key("ec-key", params.try_into()?, None)
    .await?
    .into_model()?;
```

### Delete Key

```rust
client.delete_key("key-name", None).await?;
```

### List Keys

```rust
use azure_security_keyvault_keys::ResourceExt;
use futures::TryStreamExt;

let mut pager = client.list_key_properties(None)?.into_stream();
while let Some(key) = pager.try_next().await? {
    let name = key.resource_id()?.name;
    println!("Key: {}", name);
}
```

### Backup Key

```rust
let backup = client.backup_key("key-name", None).await?;
// Store backup.value safely
```

### Restore Key

```rust
use azure_security_keyvault_keys::models::RestoreKeyParameters;

let params = RestoreKeyParameters {
    key_bundle_backup: backup_bytes,
};

client.restore_key(params.try_into()?, None).await?;
```

## Cryptographic Operations

Key Vault can perform crypto operations without exposing the private key:

```rust
// For cryptographic operations, use the key's operations
// Available operations depend on key type and permissions:
// - encrypt/decrypt (RSA)
// - sign/verify (RSA, EC)
// - wrapKey/unwrapKey (RSA)
```

## Best Practices

1. **Use Entra ID auth** — `DeveloperToolsCredential` for dev, `ManagedIdentityCredential` for production
2. **Use HSM keys for sensitive workloads** — hardware-protected keys
3. **Use EC for signing** — more efficient than RSA
4. **Use RSA for encryption** — when encrypting data
5. **Backup keys** — for disaster recovery
6. **Enable soft delete** — required for production vaults
7. **Use key rotation** — create new versions periodically

## RBAC Permissions

Assign these Key Vault roles:
- `Key Vault Crypto User` — use keys for crypto operations
- `Key Vault Crypto Officer` — full CRUD on keys

## Reference Links

| Resource | Link |
|----------|------|
| API Reference | https://docs.rs/azure_security_keyvault_keys |
| Source Code | https://github.com/Azure/azure-sdk-for-rust/tree/main/sdk/keyvault/azure_security_keyvault_keys |
| crates.io | https://crates.io/crates/azure_security_keyvault_keys |


---

## 🧠 AGI Framework Integration

> **Adapted for [@techwavedev/agi-agent-kit](https://www.npmjs.com/package/@techwavedev/agi-agent-kit)**
> Original source: [antigravity-awesome-skills](https://github.com/sickn33/antigravity-awesome-skills)

### Hybrid Memory Integration (Qdrant + BM25)

Before executing complex tasks with this skill:
```bash
python3 execution/memory_manager.py auto --query "<task summary>"
```

**Decision Tree:**
- **Cache hit?** Use cached response directly — no need to re-process.
- **Memory match?** Inject `context_chunks` into your reasoning.
- **No match?** Proceed normally, then store results:

```bash
python3 execution/memory_manager.py store \
  --content "Description of what was decided/solved" \
  --type decision \
  --tags azure-keyvault-keys-rust <relevant-tags>
```

> **Note:** Storing automatically updates both Vector (Qdrant) and Keyword (BM25) indices.

### Agent Team Collaboration

- **Strategy**: This skill communicates via the shared memory system.
- **Orchestration**: Invoked by `orchestrator` via intelligent routing.
- **Context Sharing**: Always read previous agent outputs from memory before starting.

### Local LLM Support

When available, use local Ollama models for embedding and lightweight inference:
- Embeddings: `nomic-embed-text` via Qdrant memory system
- Lightweight analysis: Local models reduce API costs for repetitive patterns