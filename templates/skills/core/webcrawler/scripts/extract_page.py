#!/usr/bin/env python3
"""
Script: extract_page.py
Purpose: Extract content from a single documentation page.

Usage:
    python extract_page.py --url <page-url> [options]

Arguments:
    --url, -u        Page URL to extract (required)
    --output, -o     Output file (default: stdout)
    --format, -f     Output format: md or json (default: md)
    --include-links  Include internal links (default: true)

Exit Codes:
    0 - Success
    1 - Invalid arguments
    2 - Network error
    3 - No content found
"""

import argparse
import json
import re
import sys
from datetime import datetime
from urllib.parse import urljoin, urlparse

try:
    import requests
    from bs4 import BeautifulSoup
    import html2text
except ImportError as e:
    print(json.dumps({
        "status": "error",
        "message": f"Missing dependency: {e}. Install with: pip install requests beautifulsoup4 html2text lxml"
    }), file=sys.stderr)
    sys.exit(1)


def extract_main_content(soup: BeautifulSoup) -> BeautifulSoup:
    """Extract the main content area, removing navigation/sidebars."""
    content_selectors = [
        'main', 'article', '[role="main"]', '.main-content', '.content',
        '.documentation', '.docs-content', '.markdown-body', '#content',
        '#main-content', '.post-content',
    ]
    
    for selector in content_selectors:
        content = soup.select_one(selector)
        if content:
            return content
    
    body = soup.find('body')
    if body:
        for selector in ['nav', 'header', 'footer', 'aside', '.sidebar', 
                       '.navigation', '.nav', '.toc', '.menu']:
            for element in body.select(selector):
                element.decompose()
        return body
    
    return soup


def extract_title(soup: BeautifulSoup) -> str:
    """Extract page title."""
    h1 = soup.find('h1')
    if h1:
        return h1.get_text(strip=True)
    title = soup.find('title')
    if title:
        text = title.get_text(strip=True)
        for sep in [' |', ' -', ' ::']:
            if sep in text:
                text = text.split(sep)[0].strip()
        return text
    return 'Untitled'


def html_to_markdown(soup: BeautifulSoup, url: str) -> str:
    """Convert HTML content to clean markdown."""
    converter = html2text.HTML2Text()
    converter.ignore_links = False
    converter.ignore_images = False
    converter.body_width = 0
    converter.unicode_snob = True
    
    html_content = str(soup)
    markdown = converter.handle(html_content)
    
    # Clean up excessive whitespace
    markdown = re.sub(r'\n{3,}', '\n\n', markdown)
    
    # Add source metadata
    header = f"---\nsource: {url}\ncrawled: {datetime.now().isoformat()}\n---\n\n"
    
    return header + markdown.strip()


def fetch_and_extract(url: str, include_links: bool = True) -> dict:
    """Fetch a page and extract its content."""
    headers = {
        'User-Agent': 'DocumentationHarvester/1.0',
        'Accept': 'text/html,application/xhtml+xml',
    }
    
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.content, 'lxml')
    title = extract_title(soup)
    main_content = extract_main_content(soup)
    markdown = html_to_markdown(main_content, url)
    
    # Extract links if requested
    links = []
    if include_links:
        domain = urlparse(url).netloc
        for anchor in main_content.find_all('a', href=True):
            href = anchor['href']
            if href.startswith('#'):
                continue
            absolute_url = urljoin(url, href)
            if urlparse(absolute_url).netloc == domain:
                links.append({
                    'url': absolute_url,
                    'text': anchor.get_text(strip=True),
                })
    
    return {
        'url': url,
        'title': title,
        'content': markdown,
        'word_count': len(markdown.split()),
        'links': links,
        'timestamp': datetime.now().isoformat(),
    }


def main():
    parser = argparse.ArgumentParser(description='Extract content from a documentation page.')
    parser.add_argument('--url', '-u', required=True, help='Page URL to extract')
    parser.add_argument('--output', '-o', help='Output file (default: stdout)')
    parser.add_argument('--format', '-f', choices=['md', 'json'], default='md', help='Output format')
    parser.add_argument('--include-links', action='store_true', default=True, help='Include internal links')
    
    args = parser.parse_args()
    
    try:
        result = fetch_and_extract(args.url, args.include_links)
        
        if args.format == 'md':
            output = result['content']
        else:
            output = json.dumps(result, indent=2, ensure_ascii=False)
        
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(output)
            print(json.dumps({
                "status": "success",
                "title": result['title'],
                "word_count": result['word_count'],
                "output": args.output
            }))
        else:
            print(output)
        
        sys.exit(0)
        
    except requests.exceptions.RequestException as e:
        print(json.dumps({
            "status": "error",
            "type": "network_error",
            "message": str(e)
        }), file=sys.stderr)
        sys.exit(2)
        
    except Exception as e:
        print(json.dumps({
            "status": "error",
            "type": type(e).__name__,
            "message": str(e)
        }), file=sys.stderr)
        sys.exit(3)


if __name__ == '__main__':
    main()
