---
name: azure-identity-rust
description: |
  Azure Identity SDK for Rust authentication. Use for DeveloperToolsCredential, ManagedIdentityCredential, ClientSecretCredential, and token-based authentication.
  Triggers: "azure-identity", "DeveloperToolsCredential", "authentication rust", "managed identity rust", "credential rust".
package: azure_identity
---

# Azure Identity SDK for Rust

Authentication library for Azure SDK clients using Microsoft Entra ID (formerly Azure AD).

## Installation

```sh
cargo add azure_identity
```

## Environment Variables

```bash
# Service Principal (for production/CI)
AZURE_TENANT_ID=<your-tenant-id>
AZURE_CLIENT_ID=<your-client-id>
AZURE_CLIENT_SECRET=<your-client-secret>

# User-assigned Managed Identity (optional)
AZURE_CLIENT_ID=<managed-identity-client-id>
```

## DeveloperToolsCredential

The recommended credential for local development. Tries developer tools in order (Azure CLI, Azure Developer CLI):

```rust
use azure_identity::DeveloperToolsCredential;
use azure_security_keyvault_secrets::SecretClient;

let credential = DeveloperToolsCredential::new(None)?;
let client = SecretClient::new(
    "https://my-vault.vault.azure.net/",
    credential.clone(),
    None,
)?;
```

### Credential Chain Order

| Order | Credential | Environment |
|-------|-----------|-------------|
| 1 | AzureCliCredential | `az login` |
| 2 | AzureDeveloperCliCredential | `azd auth login` |

## Credential Types

| Credential | Usage |
|------------|-------|
| `DeveloperToolsCredential` | Local development - tries CLI tools |
| `ManagedIdentityCredential` | Azure VMs, App Service, Functions, AKS |
| `WorkloadIdentityCredential` | Kubernetes workload identity |
| `ClientSecretCredential` | Service principal with secret |
| `ClientCertificateCredential` | Service principal with certificate |
| `AzureCliCredential` | Direct Azure CLI auth |
| `AzureDeveloperCliCredential` | Direct azd CLI auth |
| `AzurePipelinesCredential` | Azure Pipelines service connection |
| `ClientAssertionCredential` | Custom assertions (federated identity) |

## ManagedIdentityCredential

For Azure-hosted resources:

```rust
use azure_identity::ManagedIdentityCredential;

// System-assigned managed identity
let credential = ManagedIdentityCredential::new(None)?;

// User-assigned managed identity
let options = ManagedIdentityCredentialOptions {
    client_id: Some("<user-assigned-mi-client-id>".into()),
    ..Default::default()
};
let credential = ManagedIdentityCredential::new(Some(options))?;
```

## ClientSecretCredential

For service principal with secret:

```rust
use azure_identity::ClientSecretCredential;

let credential = ClientSecretCredential::new(
    "<tenant-id>".into(),
    "<client-id>".into(),
    "<client-secret>".into(),
    None,
)?;
```

## Best Practices

1. **Use `DeveloperToolsCredential` for local dev** — automatically picks up Azure CLI
2. **Use `ManagedIdentityCredential` in production** — no secrets to manage
3. **Clone credentials** — credentials are `Arc`-wrapped and cheap to clone
4. **Reuse credential instances** — same credential can be used with multiple clients
5. **Use `tokio` feature** — `cargo add azure_identity --features tokio`

## Reference Links

| Resource | Link |
|----------|------|
| API Reference | https://docs.rs/azure_identity |
| Source Code | https://github.com/Azure/azure-sdk-for-rust/tree/main/sdk/identity/azure_identity |
| crates.io | https://crates.io/crates/azure_identity |


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
  --tags azure-identity-rust <relevant-tags>
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