# Memory System Modes

## Choose Your Mode

Set `MEMORY_MODE` in your `.env` file or environment:

```bash
export MEMORY_MODE=solo   # or team, or pro
```

## Mode Comparison

| Feature | Solo | Team | Pro |
|---|:---:|:---:|:---:|
| **Infrastructure** | Ollama + Qdrant | Ollama + Qdrant | Ollama + Qdrant + MultiChain |
| Vector memory (store/retrieve) | ✅ | ✅ | ✅ |
| Hybrid search (vector + BM25) | ✅ | ✅ | ✅ |
| Semantic cache | ✅ | ✅ | ✅ |
| Developer identity tagging | — | ✅ | ✅ |
| Agent identity tagging | — | ✅ | ✅ |
| Shared team memory (`--shared`) | — | ✅ | ✅ |
| Developer isolation | — | ✅ | ✅ |
| `--developer` / `--agent` filters | — | ✅ | ✅ |
| Signed writes (HMAC-SHA256) | — | — | ✅ |
| On-chain hash anchoring | — | — | ✅ |
| Project access control | — | — | ✅ |
| Tamper detection | — | — | ✅ |
| Audit trail | — | — | ✅ |
| Poisoning prevention | — | — | ✅ |

## When to Use Each

### 🟢 Solo — Single Developer, Local Work

You're one developer, one machine, no collaboration needed.

```bash
# .env
MEMORY_MODE=solo
```

**Setup:** Just Ollama + Qdrant.

```bash
ollama serve &
docker run -d -p 6333:6333 qdrant/qdrant
python3 execution/session_boot.py --auto-fix
```

### 🔵 Team — Multiple Developers or Agents (Default)

Multiple developers or agents share context. Each write is tagged with who wrote it.
Private memories stay private; `--shared` makes them team-visible.

```bash
# .env
MEMORY_MODE=team
AGI_DEVELOPER_ID=your@email.com   # optional, auto-detected from git
```

**Setup:** Same as Solo (Ollama + Qdrant). No extra infrastructure.

```bash
python3 execution/session_boot.py --auto-fix
```

**New capabilities:**
```bash
# Store team-visible context
python3 execution/memory_manager.py store \
  --content "Use PostgreSQL for all services" --type decision --shared

# Retrieve only shared team context
python3 execution/memory_manager.py auto --query "database choice" --shared-only

# Filter by specific developer
python3 execution/memory_manager.py retrieve --query "API design" --developer alice@co.com
```

### 🟣 Pro — Blockchain-Authenticated Memory

Full trust model. Agents authenticate on-chain, writes are signed and hash-anchored,
project access is token-gated.

```bash
# .env
MEMORY_MODE=pro
MULTICHAIN_RPC_URL=http://localhost:4730
MULTICHAIN_RPC_USER=agiadmin
MULTICHAIN_RPC_PASS=agipass123
```

**Setup:** Ollama + Qdrant + MultiChain.

```bash
# Start MultiChain
cd templates/base
docker compose -f docker-compose.multichain.yml up -d

# Initialize blockchain streams
python3 execution/blockchain_auth.py init

# Register your identity
python3 execution/blockchain_auth.py register \
  --entity-type developer --entity-id "your@email.com"

# Grant project access
python3 execution/blockchain_auth.py grant \
  --entity-id "your@email.com" --project myapp --permissions read,write

# Boot check (shows blockchain status)
python3 execution/session_boot.py --auto-fix
```

**New capabilities:**
```bash
# Store with blockchain signing + hash anchoring
python3 execution/memory_manager.py store \
  --content "Critical decision" --type decision --project myapp --auth

# Retrieve with access control
python3 execution/memory_manager.py retrieve \
  --query "critical decision" --project myapp --auth

# Verify content integrity
python3 execution/blockchain_auth.py verify --content "Critical decision"

# View full audit trail
python3 execution/blockchain_auth.py audit --project myapp
```

## Upgrading Between Modes

Modes are backward-compatible. You can upgrade at any time:

| Upgrade | Data migration? | Extra infra? |
|---|---|---|
| Solo → Team | None needed (tags added to new writes) | None |
| Team → Pro | None (existing memories work unsigned) | MultiChain Docker |
| Pro → Team | None (blockchain just ignored) | Remove MultiChain |
| Team → Solo | None (identity tags just ignored) | None |
