# Blockchain-Authenticated Agent Memory

## Architecture

**Hyperledger Aries (ACA-Py)** provides W3C DID-based identity for agents.
This is an **optional add-on** (Pro mode only). Solo and Team modes work without it.

```
┌──────────────────────────────────────────────────┐
│  TRUST MODEL                                     │
│                                                  │
│  1. Register identity → DID created in wallet    │
│  2. Grant project access → stored in auth DB     │
│  3. Write: sign → store Qdrant → anchor hash     │
│  4. Read: check access → retrieve → verify hash  │
│                                                  │
│  Unregistered agent → rejected                   │
│  Tampered content → hash mismatch detected       │
│  No project grant → access denied                │
└──────────────────────────────────────────────────┘
```

## Quick Start (Pro Mode)

```bash
# 1. Set mode and credentials in .env
echo "MEMORY_MODE=pro" >> .env
echo "ARIES_ADMIN_KEY=your_secure_key" >> .env

# 2. Start Aries agent
docker compose -f docker-compose.aries.yml up -d

# 3. Initialize
python3 execution/blockchain_auth.py init

# 4. Register + grant
python3 execution/blockchain_auth.py register --entity-type developer --entity-id you@co.com
python3 execution/blockchain_auth.py grant --entity-id you@co.com --project myapp --permissions read,write

# 5. Store with auth
python3 execution/memory_manager.py store --content "Decision" --type decision --project myapp --auth
```

## Graceful Degradation

If Aries is not running, memory stores to Qdrant normally.
`--auth` flag reports `status: unavailable` but no crash, no data loss.

## Technology

| Component | Technology | Standard |
|---|---|---|
| Identity | Hyperledger Aries ACA-Py 1.5.0 | W3C DIDs |
| DID Method | `did:key` (ed25519) | W3C DID Core |
| Signing | HMAC-SHA256 (offline) / Ed25519 (via Aries) | — |
| Access Control | SQLite + Aries wallet | — |
| Audit Trail | SQLite append-only log | — |
| Docker Image | `ghcr.io/openwallet-foundation/acapy-agent:1.5.0` | OCI |
| License | Apache 2.0 | OSI |
| Governance | OpenWallet Foundation / Linux Foundation | — |
