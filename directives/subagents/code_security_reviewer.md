# Sub-Agent Directive: code-security-reviewer

## Identity

| Field      | Value                    |
|------------|--------------------------|
| Sub-agent  | `code-security-reviewer` |
| Team       | `security_team`          |
| Invoked by | Team orchestrator after `dependency-auditor` gives ✅ |

---

## Goal

Static analysis of code for OWASP Top 10 vulnerability patterns, unsafe API usage, and injection risks. Focus on code that ships to users (templates, execution scripts, skills).

---

## Inputs

| Name             | Type   | Required | Description |
|------------------|--------|----------|-------------|
| `changed_files`  | list   | ❌       | If provided, focus review on these files. Otherwise full scan |
| `release_version`| string | ✅       | Version being released |
| `handoff_state`  | object | ❌       | From dependency-auditor |

---

## Execution

1. **Run the deterministic scanner:**

```bash
python3 execution/security_scan.py code \
  --output .tmp/security/code_security.json
```

2. **Agent review** — Read findings and validate (reduce false positives)

3. **Verdict:**
   - `✅ secure` if no critical findings
   - `❌ findings` if any critical issue — **HARD BLOCK**

---

## What Gets Checked

| OWASP Category | Python Patterns | JS Patterns |
|----------------|-----------------|-------------|
| **Injection** | `os.system()`, `subprocess.call(shell=True)` with user input, `eval()`, `exec()` | `eval()`, `Function()`, `innerHTML` with user input |
| **Broken Auth** | Hardcoded passwords, default credentials | Same |
| **Sensitive Data** | Logging secrets, `print()` of tokens | `console.log()` of tokens |
| **XXE** | `xml.etree` without defusing | N/A |
| **Broken Access** | Missing permission checks on file ops | Missing input validation |
| **Misconfig** | `DEBUG=True` in production code, `verify=False` in requests | `NODE_ENV !== 'production'` checks missing |
| **XSS** | Template rendering without escaping | `dangerouslySetInnerHTML`, unescaped output |
| **Deserialization** | `pickle.loads()` on untrusted data, `yaml.load()` without SafeLoader | `JSON.parse()` on unvalidated input with prototype pollution |
| **Logging** | No error handling on external calls | Same |
| **SSRF** | `requests.get()` with user-controlled URLs without allowlist | `fetch()` with user-controlled URLs |

---

## Severity Classification

- 🔴 **Critical** — Exploitable vulnerability (injection, RCE, auth bypass) → **BLOCKS RELEASE**
- 🟡 **High** — Likely exploitable with effort (SSRF, unsafe deserialization) → **BLOCKS RELEASE**
- 🟠 **Moderate** — Defense-in-depth issue (missing validation, verbose errors) → Warning only
- 🔵 **Low** — Best practice deviation → Noted, non-blocking

---

## Outputs

```json
{
  "sub_agent": "code-security-reviewer",
  "status": "pass|fail",
  "verdict": "✅ secure|❌ findings",
  "findings": [
    {
      "file": "execution/scrape_single_site.py",
      "line": 23,
      "category": "injection",
      "severity": "critical",
      "description": "subprocess.call with shell=True using unsanitized URL input",
      "recommendation": "Use subprocess.run with shell=False and pass args as list",
      "cwe": "CWE-78"
    }
  ],
  "stats": {
    "files_scanned": 85,
    "patterns_checked": 30,
    "critical": 0,
    "high": 0,
    "moderate": 1,
    "low": 3
  }
}
```

---

## Edge Cases

- **Intentional use of eval/exec:** If in a REPL, sandbox, or test harness, flag as `moderate` not `critical`
- **shell=True in scripts:** Check if input is hardcoded string vs user-supplied. Hardcoded = `moderate`, user input = `critical`
- **Template code (templates/):** Extra scrutiny — this ships to users who may not audit it
- **False positives:** Agent should read surrounding context (±10 lines) before confirming a finding
