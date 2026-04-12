# Copilot Code Review & Bug Hunting Instructions

This file serves as the definitive reference for the **Copilot Code review automations** you conduct on the `main` branch and in pull requests.

## Primary Objective: Bug Hunting & Issue Reporting
When scanning or reviewing the default `main` branch, your objective is to:
1. Conduct deep logic and syntactical analysis for known edge cases.
2. If ANY bugs, vulnerabilities, or deviations from the architecture rules exist, you MUST immediately document the finding and clearly formulate it so an Issue can be automatically opened or manually raised.

## Core Rules to Enforce:
1. **Security & Walled Garden Protocols**: 
   - Ensure absolutely no leakage of private repository URLs (e.g. `techwavedev/agi`) into public facing outputs.
   - Forbid the use of insecure shell calls (e.g., must use `execFile` over `exec`).
   - Validate that no hardcoded tokens, credentials, or private files are accidentally pushed.
2. **Architecture Compliance**:
   - The framework prioritizes "Determinism Over Probability". Ensure all LLM/probabilistic steps are only making routing decisions and relying on `execution/` scripts for heavy data transformations.
3. **Memory Protocol Usage**:
   - Ensure workflows adhere strictly to the hybrid memory system (Qdrant + BM25), properly calling `session_boot.py` and `memory_manager.py`.
4. **Versioning Adherence**:
   - Strictly adhere to the "Patch Until Limit (.99)" protocol.

If your code review automation detects violations of any of the above, flag them as critical failures and suggest or open tracked issues natively.
