# 🛡️ Security Guardrails & Policy

AGI Agent Kit (Antigravity) is a powerful framework. With great power comes great responsibility. This document defines the **Rules of Engagement** for all security and offensive capabilities within the agent framework.

## 🔴 Offensive Skills Policy (The "Red Line")

**What is an Offensive Skill?**
Any skill designed to penetrate, exploit, disrupt, or simulate attacks against systems.
_Examples: Pentesting, SQL Injection, Phishing Simulation, Red Teaming._

### 1. The "Authorized Use Only" Disclaimer

Every offensive skill **MUST** begin with this exact disclaimer in its `SKILL.md`:

> **⚠️ AUTHORIZED USE ONLY**
> This skill is for educational purposes or authorized security assessments only.
> You must have explicit, written permission from the system owner before using this tool.
> Misuse of this tool is illegal and strictly prohibited.

### 2. Mandatory User Confirmation

Offensive skills must **NEVER** run fully autonomously.

- **Requirement**: The skill description/instructions must explicitly tell the agent to _ask for user confirmation_ before executing any exploit or attack command.
- **Agent Instruction**: "Ask the user to verify the target URL/IP before running."

### 3. Safe by Design

- **No Weaponized Payloads**: Skills should not include active malware, ransomware, or non-educational exploits.
- **Sandbox Recommended**: Instructions should recommend running in a contained environment (Docker/VM).

---

## 🔵 Defensive Skills Policy

**What is a Defensive Skill?**
Tools for hardening, auditing, monitoring, or protecting systems.
_Examples: Linting, Log Analysis, Configuration Auditing._

- **Data Privacy**: Defensive skills must not upload data to 3rd party servers without explicit user consent.
- **Non-Destructive**: Audits should be read-only by default.

---

## 🚫 Blocked Packages & Tools

The following packages and tools are **banned from this codebase** due to confirmed supply chain compromises or critical security vulnerabilities. No skill, directive, execution script, or CI workflow may reference, recommend, or depend on them.

| Package / Tool | Reason | Date Blocked | Alternative |
|----------------|--------|--------------|-------------|
| `litellm` | TeamPCP supply chain backdoor (versions 1.82.7–1.82.8) — credential harvesting, K8s lateral movement, persistent backdoor | 2026-03-25 | Direct SDK wrappers (OpenAI SDK, Langfuse SDK) |
| `trivy` / `aquasecurity/trivy-action` | 75/76 version tags force-pushed to credential stealer by TeamPCP | 2026-03-25 | Snyk, Checkov, CodeQL, Semgrep |
| `aquasecurity/setup-trivy` | Tags v0.2.0-v0.2.6 force-pushed — exfiltrates CI/CD secrets | 2026-03-25 | Snyk, Checkov, CodeQL, Semgrep |

### Enforcement

1. **Pre-publish scan**: `execution/security_scan.py` checks for blocked package references before release.
2. **CI gate**: Any PR introducing a blocked package name in code or docs will be flagged.
3. **To add a new entry**: Append to the table above and add the pattern to `execution/security_scan.py` `BLOCKED_PACKAGES` list.

### Requesting an Unblock

If a blocked package has been remediated and you want to re-allow it:
1. Verify the fix with an independent security audit or CVE resolution.
2. Open a PR with evidence and update this table with the unblock rationale.
3. Requires explicit maintainer approval.

---

## ⚖️ Legal Disclaimer

By using this framework, you agree that:

1. You are responsible for your own actions.
2. The authors and contributors are not liable for any damage caused by these tools.
3. You will comply with all local, state, and federal laws regarding cybersecurity.
