# Security Policy

## Supported Versions

Use the latest version of `@techwavedev/agi-agent-kit` to ensure you present the most secure and reliable agent framework.

| Version | Supported          |
| ------- | ------------------ |
| 1.1.x   | :white_check_mark: |
| 1.0.x   | :x:                |
| < 1.0   | :x:                |

## Reporting a Vulnerability

We take the security of our framework seriously. If you discover a security vulnerability, please follow these steps:

1.  **Do NOT create a public GitHub issue** for sensitive security vulnerabilities.
2.  Email your findings to `security@techwavedev.net` (or open a strictly private advisory if available).
3.  Provide a detailed description of the vulnerability and steps to reproduce.

We will acknowledge your report within 48 hours and work with you to remediate the issue.

## Security Features

This framework includes built-in security mechanisms:

- **Pre-flight Sanitization:** `verify_public_release.py` scans for private tokens and credentials before publishing.
- **Deterministic Execution:** Limits the agent's ability to hallucinate dangerous commands by restricting it to pre-approved scripts.
- **Provenance:** We use NPM provenance to verify build integrity.
