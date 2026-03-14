# Memory System Modes

Set `MEMORY_MODE` in `.env`:

```bash
export MEMORY_MODE=solo   # or team, or pro
```

## Feature Comparison

| Feature | Solo | Team | Pro |
|---|:---:|:---:|:---:|
| **Infrastructure** | Ollama + Qdrant | Same | + Aries (Docker) |
| Vector + hybrid search | ✅ | ✅ | ✅ |
| Semantic cache | ✅ | ✅ | ✅ |
| Developer identity tagging | — | ✅ | ✅ |
| Agent identity tagging | — | ✅ | ✅ |
| Shared team memory | — | ✅ | ✅ |
| Developer isolation | — | ✅ | ✅ |
| W3C DID identity | — | — | ✅ |
| Signed writes (HMAC / Ed25519) | — | — | ✅ |
| Hash anchoring (tamper detection) | — | — | ✅ |
| Project access control | — | — | ✅ |
| Audit trail | — | — | ✅ |

## Setup Per Mode

### 🟢 Solo — Single Developer

```bash
MEMORY_MODE=solo
# Just Ollama + Qdrant. Nothing else needed.
python3 execution/session_boot.py --auto-fix
```

### 🔵 Team — Multiple Agents/Developers (Default)

```bash
MEMORY_MODE=team
# Same infra as Solo. Identity auto-detected from git config.
python3 execution/memory_manager.py store --content "Decision" --type decision --shared
```

### 🟣 Pro — Blockchain Auth (Optional Add-On)

```bash
MEMORY_MODE=pro
# Requires: docker compose -f docker-compose.aries.yml up -d
# See docs/blockchain-auth.md for full setup
python3 execution/blockchain_auth.py init
python3 execution/memory_manager.py store --content "Decision" --type decision --auth
```

## Upgrading

All modes are backward-compatible. No data migration needed.

| Upgrade | Extra Infra? |
|---|---|
| Solo → Team | None |
| Team → Pro | Aries Docker container |
| Pro → Team | Remove Aries container |
| Team → Solo | None |
