#!/usr/bin/env python3
"""
Script: extract_packages.py
Purpose: Extract compromised package names from scraped security articles.

Usage:
    python3 skills/supply-chain-monitor/scripts/extract_packages.py \
      --input .tmp/supply-chain/articles.json \
      --output .tmp/supply-chain/extracted_packages.json

Arguments:
    --input, -i           Articles JSON from scrape_thn.py (required)
    --output, -o          Output JSON file path (required)
    --min-confidence, -c  Minimum confidence: high, medium, low (default: medium)
    --verbose             Enable detailed logging

Exit Codes:
    0 - Success (packages found)
    1 - Invalid arguments
    2 - Input file not found
    3 - No packages extracted
"""

import argparse
import json
import re
import sys
from pathlib import Path

# Threat context keywords — package names near these are likely compromised
THREAT_KEYWORDS = [
    "malicious", "backdoor", "compromised", "trojanized", "supply chain",
    "credential harvesting", "exfiltrate", "c2", "command and control",
    "malware", "poisoned", "hijack", "typosquat", "dependency confusion",
    "reverse shell", "cryptominer", "data theft", "persistent backdoor",
]

# Patterns for extracting package names from article text
EXTRACTION_PATTERNS = [
    # pip/npm install commands
    (r"(?:pip|pip3)\s+install\s+([a-zA-Z0-9_-]{2,50})", "pypi", "high"),
    (r"npm\s+install\s+([a-zA-Z0-9@/_-]{2,80})", "npm", "high"),
    # Python imports
    (r"(?:from|import)\s+([a-zA-Z_][a-zA-Z0-9_]{2,40})", "pypi", "medium"),
    # GitHub Actions
    (r"uses:\s*([a-zA-Z0-9_-]+/[a-zA-Z0-9_-]+)@", "github_actions", "high"),
    # Docker images
    (r"(?:image|FROM):\s*([a-zA-Z0-9_/-]+:[a-zA-Z0-9._-]+)", "docker", "medium"),
    # Backtick-quoted package names in threat context
    (r"[`\u201c\u201d\"']([a-zA-Z0-9_-]{2,50})[`\u201c\u201d\"']", "unknown", "low"),
    # "the malicious package X" pattern
    (r"(?:malicious|compromised|backdoored|trojanized)\s+(?:package|library|module|dependency)\s+[`\"']?([a-zA-Z0-9_-]{2,50})", "unknown", "high"),
    # "versions X.Y.Z" pattern for version-specific compromises
    (r"([a-zA-Z0-9_-]{2,50})\s+versions?\s+\d+\.\d+", "unknown", "high"),
]

# Common false positives to filter out
FALSE_POSITIVES = {
    "python", "python3", "node", "npm", "pip", "git", "docker", "bash",
    "linux", "windows", "macos", "ubuntu", "the", "this", "that", "with",
    "from", "import", "install", "package", "version", "latest", "main",
    "master", "true", "false", "none", "null", "test", "example",
    "security", "vulnerability", "attack", "malware", "backdoor",
    "researchers", "discovered", "found", "reported", "according",
}

CONFIDENCE_ORDER = {"high": 3, "medium": 2, "low": 1}


def extract_from_article(article: dict, verbose: bool) -> list:
    """Extract package names from a single article."""
    text = article.get("body_text", "") or article.get("summary", "")
    title = article.get("title", "")
    full_text = title + " " + text
    found = []

    for pattern, ecosystem, base_confidence in EXTRACTION_PATTERNS:
        for match in re.finditer(pattern, full_text, re.IGNORECASE):
            pkg_name = match.group(1).strip().lower()

            # Filter false positives
            if pkg_name in FALSE_POSITIVES:
                continue
            if len(pkg_name) < 3:
                continue

            # Check threat context — is the match near threat keywords?
            start = max(0, match.start() - 200)
            end = min(len(full_text), match.end() + 200)
            context_window = full_text[start:end].lower()

            has_threat_context = any(kw in context_window for kw in THREAT_KEYWORDS)

            # Adjust confidence based on context
            if has_threat_context and base_confidence == "low":
                confidence = "medium"
            elif has_threat_context and base_confidence in ("medium", "high"):
                confidence = "high"
            elif not has_threat_context and base_confidence == "high":
                confidence = "medium"
            elif not has_threat_context:
                confidence = "low"
            else:
                confidence = base_confidence

            # Build reason from surrounding context
            reason_start = max(0, match.start() - 100)
            reason_end = min(len(full_text), match.end() + 100)
            reason_context = full_text[reason_start:reason_end].strip()
            reason_context = re.sub(r"\s+", " ", reason_context)[:200]

            found.append({
                "name": pkg_name,
                "ecosystem": ecosystem,
                "pattern": rf"\b{re.escape(pkg_name)}\b",
                "reason": reason_context,
                "source_url": article.get("url", ""),
                "source_date": article.get("date", ""),
                "confidence": confidence,
                "alternative": "",
            })

    return found


def deduplicate(packages: list) -> list:
    """Deduplicate packages, keeping highest confidence for each name."""
    best = {}
    for pkg in packages:
        key = pkg["name"]
        if key not in best or CONFIDENCE_ORDER.get(pkg["confidence"], 0) > CONFIDENCE_ORDER.get(best[key]["confidence"], 0):
            best[key] = pkg
    return list(best.values())


def main():
    parser = argparse.ArgumentParser(description="Extract compromised package names from articles")
    parser.add_argument("--input", "-i", required=True, help="Articles JSON from scrape_thn.py")
    parser.add_argument("--output", "-o", required=True, help="Output JSON file path")
    parser.add_argument("--min-confidence", "-c", choices=["high", "medium", "low"], default="medium")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(json.dumps({"status": "error", "message": f"Input file not found: {args.input}"}), file=sys.stderr)
        sys.exit(2)

    articles = json.loads(input_path.read_text())
    if not isinstance(articles, list):
        print(json.dumps({"status": "error", "message": "Input must be a JSON array"}), file=sys.stderr)
        sys.exit(1)

    all_packages = []
    for article in articles:
        extracted = extract_from_article(article, args.verbose)
        all_packages.extend(extracted)
        if args.verbose and extracted:
            print(f"  {article.get('title', '')[:60]}: {len(extracted)} packages", file=sys.stderr)

    # Deduplicate
    packages = deduplicate(all_packages)

    # Filter by confidence
    min_level = CONFIDENCE_ORDER[args.min_confidence]
    packages = [p for p in packages if CONFIDENCE_ORDER.get(p["confidence"], 0) >= min_level]

    # Sort by confidence (high first)
    packages.sort(key=lambda p: -CONFIDENCE_ORDER.get(p["confidence"], 0))

    # Write output
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(packages, indent=2))

    result = {
        "status": "success" if packages else "no_packages",
        "packages_extracted": len(packages),
        "by_confidence": {
            "high": sum(1 for p in packages if p["confidence"] == "high"),
            "medium": sum(1 for p in packages if p["confidence"] == "medium"),
            "low": sum(1 for p in packages if p["confidence"] == "low"),
        },
        "output": args.output,
    }
    print(json.dumps(result, indent=2))

    if not packages:
        sys.exit(3)
    sys.exit(0)


if __name__ == "__main__":
    main()
