# Sub-Agent Directive: dependency-auditor

## Identity

| Field      | Value                 |
|------------|-----------------------|
| Sub-agent  | `dependency-auditor`  |
| Team       | `security_team`       |
| Invoked by | Team orchestrator after `secret-scanner` gives ✅ |

---

## Goal

Audit all project dependencies for known CVEs and license compliance issues. Critical/High vulnerabilities block the release.

---

## Inputs

| Name              | Type   | Required | Description |
|-------------------|--------|----------|-------------|
| `release_version` | string | ✅       | Version being released |
| `handoff_state`   | object | ❌       | From secret-scanner (confirms secrets are clean) |

---

## Execution

1. **Run the deterministic scanner:**

```bash
python3 execution/security_scan.py dependencies \
  --output .tmp/security/dependency_audit.json
```

2. **Review results** from the JSON output

3. **Verdict:**
   - `✅ clean` if no critical/high CVEs and no license violations
   - `⚠️ warnings` if moderate CVEs only — proceed with warnings logged
   - `❌ vulnerabilities` if critical/high CVEs or license violations — **HARD BLOCK**

---

## What Gets Checked

| Check | Tool | Blocking |
|-------|------|----------|
| **npm audit** | `npm audit --json` | Critical/High = block, Moderate = warn |
| **pip safety** | `pip-audit` or `safety check` (if available) | Critical/High = block |
| **License compliance** | Package license field scan | GPL/AGPL in MIT project = block |
| **Outdated with known CVEs** | Cross-ref with advisory databases | If CVE exists = block |

---

## Outputs

```json
{
  "sub_agent": "dependency-auditor",
  "status": "pass|fail|warn",
  "verdict": "✅ clean|⚠️ warnings|❌ vulnerabilities",
  "npm_audit": {
    "critical": 0,
    "high": 0,
    "moderate": 2,
    "low": 5,
    "info": 1,
    "advisories": []
  },
  "license_issues": [],
  "pre_existing": [],
  "recommendations": []
}
```

---

## Edge Cases

- **No package.json:** Skip npm audit, check for `requirements.txt` or `pyproject.toml`
- **No lock file:** Run `npm install --package-lock-only` first to generate one
- **npm audit unavailable (offline):** BLOCK — never skip dependency audit silently
- **Pre-existing CVEs:** If a CVE was present in the previous release tag too, flag as `pre_existing: true` and warn (don't block)
- **Dev dependencies only:** CVEs in devDependencies are warnings, not blocks (they don't ship to users)
