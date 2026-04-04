---
name: supply-chain-monitor
description: >
  Supply chain threat intelligence monitor. Scrapes TheHackerNews.com for
  supply chain security incidents and extracts compromised package names.
  Triggers on: 'check supply chain', 'supply chain threats', 'blocked packages',
  'scan for compromised packages', 'vet upstream skills', 'refresh blocklist',
  before accepting upstream skills, before releases.
---

# Supply Chain Monitor

Monitors security news for supply chain attacks targeting packages used in
CI/CD pipelines, AI/ML tooling, and developer dependencies. Extracts
compromised package names and updates the framework's blocklist.

## When to Use

- Before accepting upstream skills (`upstream-sync`)
- Before any release (refresh the blocklist first)
- User asks about supply chain security or package safety
- Periodically to keep `BLOCKED_PACKAGES` in `security_scan.py` current

## When NOT to Use

- General security auditing (use `security-scanning-security-hardening`)
- Dependency version updates (use Dependabot/Renovate)

## Quick Start

```bash
# 1. Scrape recent supply chain articles
python3 skills/supply-chain-monitor/scripts/scrape_thn.py \
  --output .tmp/supply-chain/articles.json --days 30

# 2. Extract compromised package names
python3 skills/supply-chain-monitor/scripts/extract_packages.py \
  --input .tmp/supply-chain/articles.json \
  --output .tmp/supply-chain/extracted_packages.json

# 3. Preview blocklist changes (dry-run by default)
python3 skills/supply-chain-monitor/scripts/update_blocklist.py \
  --input .tmp/supply-chain/extracted_packages.json

# 4. Apply changes (requires --confirm)
python3 skills/supply-chain-monitor/scripts/update_blocklist.py \
  --input .tmp/supply-chain/extracted_packages.json --confirm
```

## Core Workflow

### Step 1: Scrape

Fetches articles from TheHackerNews via RSS feed (primary) or HTML scraping
(fallback). Filters by supply chain keywords.

| Flag | Default | Purpose |
|------|---------|---------|
| `--output` | required | Output JSON path |
| `--days` | 30 | Look-back window |
| `--max-articles` | 20 | Cap results |
| `--source` | auto | `rss`, `html`, or `auto` |

### Step 2: Extract

Parses article text with regex patterns to find compromised package names.
Each match gets a confidence score (`high`, `medium`, `low`).

| Flag | Default | Purpose |
|------|---------|---------|
| `--input` | required | Articles JSON from Step 1 |
| `--output` | required | Extracted packages JSON |
| `--min-confidence` | medium | Filter threshold |

### Step 3: Update Blocklist

Patches `execution/security_scan.py` BLOCKED_PACKAGES and
`SECURITY_GUARDRAILS.md` blocked packages table. Idempotent — skips
packages already blocked.

| Flag | Default | Purpose |
|------|---------|---------|
| `--input` | required | Extracted packages JSON |
| `--dry-run` | true | Preview only (default) |
| `--confirm` | false | Actually write changes |

## Integration: Upstream Skill Acceptance

**Before accepting any upstream skill**, the agent MUST:

1. Run Steps 1-2 above (or use cached results < 24h old)
2. Grep each candidate skill directory against extracted package names
3. Also grep against the current `BLOCKED_PACKAGES` in `security_scan.py`
4. **Reject** any skill that references a blocked package
5. Report findings to the user with the source article URL

## Integration: Release Gate

The existing `security_scan.py blocked` mode (called by `release_gate.py`)
already enforces the blocklist. This skill keeps the list fresh — run it
before releases to catch newly-reported compromises.

## Integration: Memory

```bash
# Before scraping — check for recent cached results
python3 execution/memory_manager.py auto \
  --query "supply chain threat scan results"

# After updating blocklist — store the decision
python3 execution/memory_manager.py store \
  --content "Blocked package X due to supply chain compromise (source: THN article URL)" \
  --type decision --tags supply-chain security blocklist
```

## Scripts Reference

| Script | Purpose |
|--------|---------|
| `scripts/scrape_thn.py` | Fetch + filter THN articles |
| `scripts/extract_packages.py` | Extract package names from articles |
| `scripts/update_blocklist.py` | Patch security_scan.py + SECURITY_GUARDRAILS.md |

## Selectors & Parsing

For CSS selectors, RSS feed URLs, and parsing details, see
`references/thn_selectors.md`.
