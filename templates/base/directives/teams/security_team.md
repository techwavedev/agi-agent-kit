# Team Directive: Security Team

## Team Identity

| Field       | Value               |
|-------------|---------------------|
| Team ID     | `security_team`     |
| Role        | Pre-release security gate: secrets → dependencies → code security |
| Trigger     | **MANDATORY** before every public release / npm publish |
| Mode        | Sequential |

---

## Goal

Block releases that contain security vulnerabilities. Three sequential gates:
1. **Secret scanning** — enhanced detection beyond regex (entropy analysis, file pattern matching)
2. **Dependency audit** — known CVEs in npm/pip dependencies
3. **Code security review** — OWASP Top 10 patterns, unsafe APIs, injection risks

**A single ❌ from any sub-agent blocks the release.**

---

## Sub-Agents (in order)

### 1. `secret-scanner`
- **Directive:** `directives/subagents/secret_scanner.md`
- **Role:** Deep secret detection — regex + high-entropy string analysis + dangerous file patterns
- **Checks:** API keys, tokens, private keys, .env leaks, high-entropy strings, certificates
- **Output:** `✅ clean` or `❌ secrets_found: [list]`
- **On failure:** HARD BLOCK — must remove secrets before proceeding

### 2. `dependency-auditor`
- **Directive:** `directives/subagents/dependency_auditor.md`
- **Role:** Audit npm and pip dependencies for known vulnerabilities
- **Checks:** `npm audit`, pip safety checks, license compliance (no GPL in MIT project)
- **Runs after:** `secret-scanner` gives `✅`
- **Output:** `✅ clean` or `❌ vulnerabilities: [list]` (critical/high block, moderate warn)
- **On failure:** Critical/High CVEs block release; Moderate issues are warnings only

### 3. `code-security-reviewer`
- **Directive:** `directives/subagents/code_security_reviewer.md`
- **Role:** Static analysis for OWASP Top 10 patterns in code
- **Runs after:** `dependency-auditor` gives `✅`
- **Output:** `✅ secure` or `❌ findings: [list]`
- **On failure:** Any critical finding blocks release

---

## Inputs

```json
{
  "changed_files": ["<list of changed file paths>"],
  "release_version": "<version being released>",
  "release_type": "npm|merge-to-public|tag"
}
```

---

## Execution Protocol

```
security_team
  │
  ├── [1] secret-scanner
  │     ├── ✅ → proceed to dependency-auditor
  │     └── ❌ → HARD BLOCK (no retry — fix secrets first)
  │
  ├── [2] dependency-auditor
  │     ├── ✅ → proceed to code-security-reviewer
  │     ├── ⚠️ moderate → proceed with warnings logged
  │     └── ❌ critical/high → HARD BLOCK
  │
  └── [3] code-security-reviewer
        ├── ✅ → release approved by security team
        └── ❌ → HARD BLOCK
```

---

## Outputs

```json
{
  "team": "security_team",
  "run_id": "<uuid>",
  "sub_agents": {
    "secret_scanner": { "status": "pass|fail", "findings": [] },
    "dependency_auditor": { "status": "pass|fail|warn", "cves": [], "license_issues": [] },
    "code_security_reviewer": { "status": "pass|fail", "findings": [] }
  },
  "overall_status": "pass|fail",
  "release_blocked": false
}
```

---

## Edge Cases

- **No package.json:** Skip npm audit, still run pip checks if requirements.txt exists
- **No dependencies at all:** `dependency-auditor` auto-passes
- **Offline / audit service down:** BLOCK release — do not skip security checks silently
- **Pre-existing CVEs:** If a CVE existed before this release, log it but don't block (flag with `pre_existing: true`)

---

## Memory Integration

```bash
python3 execution/memory_manager.py store \
  --content "security_team: release <version> security review. Result: <status>. Findings: <summary>" \
  --type decision \
  --tags security release-gate vulnerability-scan secret-scan
```
