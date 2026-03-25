#!/usr/bin/env python3
"""
Script: scrape_thn.py
Purpose: Scrape TheHackerNews for supply chain security articles.

Usage:
    python3 skills/supply-chain-monitor/scripts/scrape_thn.py \
      --output .tmp/supply-chain/articles.json --days 30

Arguments:
    --output, -o       Output JSON file path (required)
    --days, -d         Look-back window in days (default: 30)
    --max-articles, -m Max articles to return (default: 20)
    --source, -s       Source: rss, html, or auto (default: auto)
    --verbose          Enable detailed logging

Exit Codes:
    0 - Success
    1 - Invalid arguments
    2 - Network error
    3 - No articles found
"""

import argparse
import json
import re
import sys
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from pathlib import Path

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError as e:
    print(json.dumps({
        "status": "error",
        "message": f"Missing dependency: {e}. Install with: pip install requests beautifulsoup4 lxml"
    }), file=sys.stderr)
    sys.exit(1)

RSS_URL = "https://feeds.feedburner.com/TheHackersNews"
LABEL_URLS = [
    "https://thehackernews.com/search/label/Supply%20Chain",
    "https://thehackernews.com/search/label/Malware",
]
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

SUPPLY_CHAIN_KEYWORDS = [
    "supply chain", "backdoor", "compromised package", "malicious package",
    "typosquatting", "dependency confusion", "trojanized", "malware pypi",
    "malware npm", "poisoned", "credential harvesting", "ci/cd compromise",
    "github action compromise", "package hijack", "malicious dependency",
    "npm malware", "pypi malware", "supply-chain attack",
]


def is_relevant(title: str, summary: str) -> bool:
    """Check if an article is relevant to supply chain security."""
    text = (title + " " + summary).lower()
    return any(kw in text for kw in SUPPLY_CHAIN_KEYWORDS)


def parse_rss_date(date_str: str) -> datetime:
    """Parse RSS date formats."""
    for fmt in [
        "%Y-%m-%dT%H:%M:%S.%f%z",
        "%Y-%m-%dT%H:%M:%S%z",
        "%a, %d %b %Y %H:%M:%S %z",
        "%a, %d %b %Y %H:%M:%S %Z",
    ]:
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except ValueError:
            continue
    return datetime.now(timezone.utc)


def scrape_rss(days: int, max_articles: int, verbose: bool) -> list:
    """Scrape articles from TheHackerNews RSS feed."""
    if verbose:
        print(f"  Fetching RSS feed: {RSS_URL}", file=sys.stderr)

    try:
        resp = requests.get(RSS_URL, headers=HEADERS, timeout=30)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(json.dumps({"status": "error", "message": f"RSS fetch failed: {e}"}), file=sys.stderr)
        return []

    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    articles = []

    try:
        root = ET.fromstring(resp.text)
    except ET.ParseError:
        if verbose:
            print("  RSS parse failed, returning empty", file=sys.stderr)
        return []

    # Handle Atom namespace
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    entries = root.findall(".//atom:entry", ns)
    if not entries:
        entries = root.findall(".//item")

    for entry in entries:
        # Atom format
        title_el = entry.find("atom:title", ns) or entry.find("title")
        link_el = entry.find("atom:link", ns) or entry.find("link")
        date_el = entry.find("atom:published", ns) or entry.find("pubDate")
        content_el = entry.find("atom:content", ns) or entry.find("description")

        title = title_el.text.strip() if title_el is not None and title_el.text else ""
        if link_el is not None:
            link = link_el.get("href", "") or (link_el.text or "").strip()
        else:
            link = ""
        date_str = date_el.text.strip() if date_el is not None and date_el.text else ""
        content_text = content_el.text.strip() if content_el is not None and content_el.text else ""

        # Strip HTML from content
        if content_text:
            soup = BeautifulSoup(content_text, "html.parser")
            summary = soup.get_text(separator=" ", strip=True)[:500]
        else:
            summary = ""

        pub_date = parse_rss_date(date_str)
        if pub_date.tzinfo is None:
            pub_date = pub_date.replace(tzinfo=timezone.utc)

        if pub_date < cutoff:
            continue

        if not is_relevant(title, summary):
            continue

        articles.append({
            "title": title,
            "url": link,
            "date": pub_date.isoformat(),
            "summary": summary,
            "body_text": summary,
            "source": "rss",
        })

        if len(articles) >= max_articles:
            break

    if verbose:
        print(f"  Found {len(articles)} relevant articles via RSS", file=sys.stderr)
    return articles


def scrape_html(days: int, max_articles: int, verbose: bool) -> list:
    """Scrape articles from TheHackerNews HTML label pages."""
    articles = []
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    for url in LABEL_URLS:
        if len(articles) >= max_articles:
            break

        if verbose:
            print(f"  Fetching HTML: {url}", file=sys.stderr)

        try:
            resp = requests.get(url, headers=HEADERS, timeout=30)
            resp.raise_for_status()
        except requests.RequestException as e:
            if verbose:
                print(f"  Failed: {e}", file=sys.stderr)
            continue

        soup = BeautifulSoup(resp.text, "lxml")
        posts = soup.select(".body-post")

        for post in posts:
            if len(articles) >= max_articles:
                break

            title_el = post.select_one(".home-title a")
            desc_el = post.select_one(".home-desc")

            title = title_el.get_text(strip=True) if title_el else ""
            link = title_el.get("href", "") if title_el else ""
            summary = desc_el.get_text(strip=True) if desc_el else ""

            if not is_relevant(title, summary):
                continue

            # Avoid duplicates
            if any(a["url"] == link for a in articles):
                continue

            articles.append({
                "title": title,
                "url": link,
                "date": datetime.now(timezone.utc).isoformat(),
                "summary": summary[:500],
                "body_text": summary,
                "source": "html",
            })

        time.sleep(1.5)  # Rate limiting

    if verbose:
        print(f"  Found {len(articles)} relevant articles via HTML", file=sys.stderr)
    return articles


def fetch_article_body(url: str, verbose: bool) -> str:
    """Fetch full article body for deeper package extraction."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")
        body = soup.select_one(".articlebody")
        if body:
            return body.get_text(separator=" ", strip=True)
    except Exception as e:
        if verbose:
            print(f"  Failed to fetch article body: {e}", file=sys.stderr)
    return ""


def main():
    parser = argparse.ArgumentParser(description="Scrape TheHackerNews for supply chain articles")
    parser.add_argument("--output", "-o", required=True, help="Output JSON file path")
    parser.add_argument("--days", "-d", type=int, default=30, help="Look-back window in days")
    parser.add_argument("--max-articles", "-m", type=int, default=20, help="Max articles")
    parser.add_argument("--source", "-s", choices=["rss", "html", "auto"], default="auto", help="Source")
    parser.add_argument("--fetch-bodies", action="store_true", help="Fetch full article bodies (slower)")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    args = parser.parse_args()

    articles = []

    if args.source in ("rss", "auto"):
        articles = scrape_rss(args.days, args.max_articles, args.verbose)

    if args.source == "html" or (args.source == "auto" and len(articles) < 3):
        html_articles = scrape_html(args.days, args.max_articles - len(articles), args.verbose)
        # Merge without duplicates
        seen_urls = {a["url"] for a in articles}
        for a in html_articles:
            if a["url"] not in seen_urls:
                articles.append(a)
                seen_urls.add(a["url"])

    # Optionally fetch full bodies for better extraction
    if args.fetch_bodies:
        for i, article in enumerate(articles):
            if args.verbose:
                print(f"  Fetching body {i+1}/{len(articles)}: {article['title'][:60]}", file=sys.stderr)
            body = fetch_article_body(article["url"], args.verbose)
            if body:
                article["body_text"] = body
            time.sleep(1.5)

    if not articles:
        print(json.dumps({"status": "no_articles", "message": "No relevant supply chain articles found"}))
        sys.exit(3)

    # Write output
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(articles, indent=2))

    result = {
        "status": "success",
        "articles_found": len(articles),
        "output": args.output,
        "date_range": f"last {args.days} days",
    }
    print(json.dumps(result, indent=2))
    sys.exit(0)


if __name__ == "__main__":
    main()
