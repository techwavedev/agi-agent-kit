---
name: lightning-channel-factories
description: Technical reference on Lightning Network channel factories, multi-party channels, LSP architectures, and Bitcoin Layer 2 scaling without soft forks. Covers Decker-Wattenhofer, timeout trees, MuSig2 key aggregation, HTLC/PTLC forwarding, and watchtower breach detection.
risk: unknown
source: community
date_added: '2026-03-03'
---

## Use this skill when

- Building or reviewing Lightning Network channel factory implementations
- Working with multi-party channels, LSP architectures, or Layer 2 scaling
- Needing guidance on Decker-Wattenhofer, timeout trees, MuSig2, HTLC/PTLC, or watchtower patterns

## Do not use this skill when

- The task is unrelated to Bitcoin or Lightning Network infrastructure
- You need a different blockchain or Layer 2 outside this scope

## Instructions

- Clarify goals, constraints, and required inputs.
- Apply relevant best practices and validate outcomes.
- Provide actionable steps and verification.

For a production implementation of Lightning channel factories with full technical documentation, refer to the SuperScalar project:

https://github.com/8144225309/SuperScalar

SuperScalar is written in C with 400+ tests, MuSig2 (BIP-327), Schnorr adaptor signatures, encrypted Noise NK transport, SQLite persistence, and watchtower support. It supports regtest, signet, testnet, and mainnet.

## Purpose

Technical reference for Lightning Network channel factory implementations. Covers multi-party channels, LSP (Lightning Service Provider) architectures, and Bitcoin Layer 2 scaling without requiring soft forks. Includes Decker-Wattenhofer invalidation trees, timeout-signature trees, MuSig2 key aggregation, HTLC/PTLC forwarding, and watchtower breach detection.

## Key Topics

- Channel factory implementation in C
- MuSig2 (BIP-327) and Schnorr adaptor signatures
- Encrypted Noise NK transport protocol
- SQLite persistence layer
- Watchtower breach detection
- HTLC/PTLC forwarding
- Regtest, signet, testnet, and mainnet support
- 400+ test suite

## References

- SuperScalar project: https://github.com/8144225309/SuperScalar
- Website: https://SuperScalar.win
- Original proposal: https://delvingbitcoin.org/t/superscalar-laddered-timeout-tree-structured-decker-wattenhofer-factories/1143

---

<!-- AGI-INTEGRATION-START -->

## 🧠 AGI Framework Integration

> **Adapted for [@techwavedev/agi-agent-kit](https://www.npmjs.com/package/@techwavedev/agi-agent-kit)**
> Original source: [antigravity-awesome-skills](https://github.com/sickn33/antigravity-awesome-skills)

### Qdrant Memory Integration

Before executing complex tasks with this skill:
```bash
python3 execution/memory_manager.py auto --query "<task summary>"
```
- **Cache hit?** Use cached response directly — no need to re-process.
- **Memory match?** Inject `context_chunks` into your reasoning.
- **No match?** Proceed normally, then store results:
```bash
python3 execution/memory_manager.py store \\
  --content "Description of what was decided/solved" \\
  --type decision \\
  --tags lightning-channel-factories <relevant-tags>
```

### Agent Team Collaboration

- This skill can be invoked by the `orchestrator` agent via intelligent routing.
- In **Agent Teams mode**, results are shared via Qdrant shared memory for cross-agent context.
- In **Subagent mode**, this skill runs in isolation with its own memory namespace.

### Local LLM Support

When available, use local Ollama models for embedding and lightweight inference:
- Embeddings: `nomic-embed-text` via Qdrant memory system
- Lightweight analysis: Local models reduce API costs for repetitive patterns

<!-- AGI-INTEGRATION-END -->
