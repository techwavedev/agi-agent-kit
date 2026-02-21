# Security Policy

## Supported Versions

Use the latest version of `@techwavedev/agi-agent-kit` to ensure you have the most secure and reliable agent framework.

| Version | Supported          |
| ------- | ------------------ |
| 1.5.x   | :white_check_mark: |
| 1.4.x   | :white_check_mark: |
| 1.3.x   | :white_check_mark: |
| < 1.3.0 | :x: (Stale)        |

## Reporting a Vulnerability

We take the security of our framework seriously. If you discover a security vulnerability, please follow these steps:

1. **Do NOT create a public GitHub issue** for sensitive security vulnerabilities.
2. Email your findings to `security@techwavedev.net` (or open a strictly private advisory if available).
3. Provide a detailed description of the vulnerability and steps to reproduce.

We will acknowledge your report within 48 hours and work with you to remediate the issue.

## Security Features

This framework includes built-in security mechanisms:

- **Pre-flight Sanitization:** `verify_public_release.py` and `scripts/verify_public_release.py` scan for private tokens, credentials, and forbidden terms before publishing.
- **Credential Exclusion:** `.gitignore` blocks `.env`, `credentials.json`, `token.json`, `*.pem`, and `*.key` from version control.
- **Deterministic Execution:** Limits the agent's ability to hallucinate dangerous commands by restricting it to pre-approved scripts.
- **Vulnerability Scanner Skill:** Built-in `vulnerability-scanner` skill with `security_scan.py` detects API keys, private keys, and hardcoded secrets in codebases.
- **Automated GitHub Scanning:** comprehensive CI/CD security pipeline including:
  - **Dependabot:** Automated dependency updates for NPM, Pip, and Actions.
  - **CodeQL:** Static application security testing (SAST) for Python and JavaScript.
  - **Trivy:** Container and filesystem vulnerability scanning for secrets and CVEs.
  - **VirusTotal:** Release artifact scanning for malware/viruses.
- **Provenance:** We use NPM provenance to verify build integrity.
