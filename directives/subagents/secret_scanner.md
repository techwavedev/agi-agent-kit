# Sub-Agent Directive: secret-scanner

## Identity

| Field      | Value              |
|------------|--------------------|
| Sub-agent  | `secret-scanner`   |
| Team       | `security_team`    |
| Invoked by | Team orchestrator (first in sequence) |

---

## Goal

Detect hardcoded secrets, credentials, and sensitive data that must never be published. Goes beyond simple regex — uses entropy analysis and dangerous file pattern matching.

---

## Inputs

| Name             | Type   | Required | Description |
|------------------|--------|----------|-------------|
| `changed_files`  | list   | ❌       | If provided, scan only these files. Otherwise, full repo scan |
| `release_version`| string | ✅       | Version being released (for logging) |

---

## Execution

1. **Run the deterministic scanner:**

```bash
python3 execution/security_scan.py secrets \
  --output .tmp/security/secret_scan.json
```

2. **Review results** from the JSON output

3. **Verdict:**
   - `✅ clean` if zero findings
   - `❌ secrets_found` if any findings — **HARD BLOCK, no exceptions**

---

## What Gets Scanned

| Category | Patterns |
|----------|----------|
| **API Keys** | AWS (`AKIA...`), GCP, Azure, OpenAI (`sk-`), Anthropic, Stripe, Twilio |
| **Tokens** | JWT, OAuth, Bearer, GitHub (`ghp_`, `gho_`, `ghs_`), GitLab (`glpat-`) |
| **Private Keys** | RSA, DSA, EC, PGP (`-----BEGIN ... PRIVATE KEY-----`) |
| **Certificates** | `.pem`, `.p12`, `.pfx` files in tracked directories |
| **Connection Strings** | Database URIs with passwords, Redis URLs |
| **Environment Files** | `.env`, `.env.*` files that shouldn't be committed |
| **High Entropy** | Strings >20 chars with Shannon entropy >4.5 in assignments |

---

## Outputs

```json
{
  "sub_agent": "secret-scanner",
  "status": "pass|fail",
  "verdict": "✅ clean|❌ secrets_found",
  "findings": [
    {
      "file": "path/to/file.py",
      "line": 42,
      "type": "api_key",
      "pattern": "OpenAI API key (sk-...)",
      "severity": "critical",
      "recommendation": "Move to .env and add to .gitignore"
    }
  ],
  "stats": {
    "files_scanned": 150,
    "patterns_checked": 12,
    "entropy_checks": true
  }
}
```

---

## Edge Cases

- **Binary files:** Skip (not text-searchable)
- **Test fixtures with fake keys:** If a key starts with `test_`, `fake_`, `mock_`, or `example_`, flag as `info` not `critical`
- **Git history:** Only scan current working tree (historical secrets need `git filter-branch`, out of scope)
- **Minified JS:** Skip files >500KB single-line (likely vendor bundles)
