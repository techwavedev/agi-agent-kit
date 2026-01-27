#!/usr/bin/env python3
"""
Script: crawl_docs.py
Purpose: Recursively crawl documentation websites and extract content as markdown/JSON.

Usage:
    python crawl_docs.py --url <base-url> --subject <topic> [options]

Arguments:
    --url, -u       Starting URL (required)
    --subject, -s   Subject focus for filtering (required)
    --output, -o    Output directory (default: .tmp/crawled/)
    --depth, -d     Max crawl depth (default: 2)
    --filter, -f    URL path filter pattern (optional)
    --delay         Delay between requests in seconds (default: 0.5)
    --max-pages     Maximum pages to crawl (default: 100)
    --same-domain   Stay within same domain (default: true)
    --include-code  Preserve code blocks (default: true)
    --format        Output format: md, json, or both (default: both)
    --ignore-robots Ignore robots.txt (default: false)
    --verbose, -v   Verbose output

Exit Codes:
    0 - Success
    1 - Invalid arguments
    2 - Network error
    3 - No content found
    4 - Processing error
"""

import argparse
import json
import os
import re
import sys
import time
import hashlib
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin, urlparse, urlunparse
from urllib.robotparser import RobotFileParser

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


class DocumentationCrawler:
    """Intelligent documentation crawler with content extraction."""

    def __init__(self, base_url: str, subject: str, config: dict):
        self.base_url = base_url
        self.subject = subject
        self.config = config
        self.visited = set()
        self.pages = []
        self.domain = urlparse(base_url).netloc
        self.base_path = urlparse(base_url).path
        self.robot_parser = None
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'DocumentationHarvester/1.0 (+https://github.com/techwavedev/agi)',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        })
        
        # Initialize html2text converter
        self.converter = html2text.HTML2Text()
        self.converter.ignore_links = False
        self.converter.ignore_images = False
        self.converter.ignore_emphasis = False
        self.converter.body_width = 0  # No wrapping
        self.converter.unicode_snob = True
        self.converter.skip_internal_links = False
        
        # Load robots.txt if not ignored
        if not config.get('ignore_robots', False):
            self._load_robots_txt()

    def _load_robots_txt(self):
        """Load and parse robots.txt."""
        try:
            robots_url = f"{urlparse(self.base_url).scheme}://{self.domain}/robots.txt"
            self.robot_parser = RobotFileParser()
            self.robot_parser.set_url(robots_url)
            self.robot_parser.read()
        except Exception:
            self.robot_parser = None

    def _can_fetch(self, url: str) -> bool:
        """Check if URL can be fetched according to robots.txt."""
        if self.robot_parser is None:
            return True
        try:
            return self.robot_parser.can_fetch('*', url)
        except Exception:
            return True

    def _normalize_url(self, url: str) -> str:
        """Normalize URL to prevent duplicate crawling."""
        parsed = urlparse(url)
        # Remove fragment and normalize path
        normalized = urlunparse((
            parsed.scheme,
            parsed.netloc.lower(),
            parsed.path.rstrip('/') or '/',
            '',  # params
            parsed.query,
            ''   # fragment
        ))
        return normalized

    def _is_valid_url(self, url: str) -> bool:
        """Check if URL should be crawled."""
        parsed = urlparse(url)
        
        # Must be HTTP(S)
        if parsed.scheme not in ('http', 'https'):
            return False
        
        # Check domain restriction
        if self.config.get('same_domain', True):
            if parsed.netloc.lower() != self.domain.lower():
                return False
        
        # Check path filter
        path_filter = self.config.get('filter')
        if path_filter and path_filter not in parsed.path:
            return False
        
        # Skip non-documentation links
        skip_extensions = ('.pdf', '.zip', '.tar', '.gz', '.exe', '.dmg', 
                          '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico',
                          '.css', '.js', '.woff', '.woff2', '.ttf')
        if any(parsed.path.lower().endswith(ext) for ext in skip_extensions):
            return False
        
        return True

    def _extract_links(self, soup: BeautifulSoup, current_url: str) -> list:
        """Extract valid documentation links from a page."""
        links = []
        for anchor in soup.find_all('a', href=True):
            href = anchor['href']
            # Skip anchors
            if href.startswith('#'):
                continue
            # Resolve relative URLs
            absolute_url = urljoin(current_url, href)
            normalized = self._normalize_url(absolute_url)
            if self._is_valid_url(normalized) and normalized not in self.visited:
                links.append(normalized)
        return list(set(links))

    def _extract_main_content(self, soup: BeautifulSoup) -> BeautifulSoup:
        """Extract the main content area, removing navigation/sidebars."""
        # Try common content containers
        content_selectors = [
            'main',
            'article',
            '[role="main"]',
            '.main-content',
            '.content',
            '.documentation',
            '.docs-content',
            '.markdown-body',
            '#content',
            '#main-content',
            '.post-content',
        ]
        
        for selector in content_selectors:
            content = soup.select_one(selector)
            if content:
                return content
        
        # Fallback: return body after removing known non-content elements
        body = soup.find('body')
        if body:
            for selector in ['nav', 'header', 'footer', 'aside', '.sidebar', 
                           '.navigation', '.nav', '.toc', '.menu']:
                for element in body.select(selector):
                    element.decompose()
            return body
        
        return soup

    def _preserve_code_blocks(self, soup: BeautifulSoup) -> None:
        """Ensure code blocks are properly preserved."""
        # Mark code blocks to prevent conversion issues
        for pre in soup.find_all('pre'):
            code = pre.find('code')
            if code:
                # Try to get language from class
                classes = code.get('class', [])
                lang = ''
                for cls in classes:
                    if cls.startswith('language-') or cls.startswith('lang-'):
                        lang = cls.split('-', 1)[1]
                        break
                if lang:
                    code['data-language'] = lang

    def _html_to_markdown(self, soup: BeautifulSoup, url: str) -> str:
        """Convert HTML content to clean markdown."""
        # Preserve code blocks
        if self.config.get('include_code', True):
            self._preserve_code_blocks(soup)
        
        # Convert to markdown
        html_content = str(soup)
        markdown = self.converter.handle(html_content)
        
        # Clean up excessive whitespace
        markdown = re.sub(r'\n{3,}', '\n\n', markdown)
        
        # Add source URL as metadata
        header = f"---\nsource: {url}\nsubject: {self.subject}\ncrawled: {datetime.now().isoformat()}\n---\n\n"
        
        return header + markdown.strip()

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract page title."""
        # Try h1 first
        h1 = soup.find('h1')
        if h1:
            return h1.get_text(strip=True)
        # Fall back to title tag
        title = soup.find('title')
        if title:
            text = title.get_text(strip=True)
            # Remove common suffixes
            for sep in [' |', ' -', ' ::']:
                if sep in text:
                    text = text.split(sep)[0].strip()
            return text
        return 'Untitled'

    def _is_relevant(self, content: str, title: str) -> bool:
        """Check if content is relevant to the subject."""
        subject_lower = self.subject.lower()
        subject_words = subject_lower.split()
        
        text = (title + ' ' + content).lower()
        
        # Check if any subject word appears in content
        for word in subject_words:
            if len(word) > 2 and word in text:
                return True
        
        return False

    def _fetch_page(self, url: str) -> tuple:
        """Fetch a page and return (soup, status)."""
        try:
            if not self._can_fetch(url):
                if self.config.get('verbose'):
                    print(f"  ⛔ Blocked by robots.txt: {url}")
                return None, 'robots_blocked'
            
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            # Check content type
            content_type = response.headers.get('Content-Type', '')
            if 'text/html' not in content_type and 'application/xhtml' not in content_type:
                return None, 'not_html'
            
            soup = BeautifulSoup(response.content, 'lxml')
            return soup, 'ok'
            
        except requests.exceptions.RequestException as e:
            if self.config.get('verbose'):
                print(f"  ❌ Error fetching {url}: {e}")
            return None, 'error'

    def _url_to_filename(self, url: str) -> str:
        """Convert URL to a safe filename."""
        parsed = urlparse(url)
        path = parsed.path.strip('/').replace('/', '_') or 'index'
        # Sanitize
        path = re.sub(r'[^\w\-_.]', '_', path)
        # Limit length
        if len(path) > 100:
            path = path[:80] + '_' + hashlib.md5(path.encode()).hexdigest()[:8]
        return path + '.md'

    def crawl(self) -> dict:
        """Execute the crawl and return results."""
        max_depth = self.config.get('depth', 2)
        max_pages = self.config.get('max_pages', 100)
        delay = self.config.get('delay', 0.5)
        verbose = self.config.get('verbose', False)
        
        # Queue: (url, depth)
        queue = [(self._normalize_url(self.base_url), 0)]
        
        print(f"🕷️  Starting crawl: {self.base_url}")
        print(f"   Subject: {self.subject}")
        print(f"   Max depth: {max_depth}, Max pages: {max_pages}")
        print()
        
        while queue and len(self.pages) < max_pages:
            url, depth = queue.pop(0)
            
            if url in self.visited:
                continue
            
            self.visited.add(url)
            
            if verbose:
                print(f"  📄 [{depth}] {url}")
            
            # Fetch page
            soup, status = self._fetch_page(url)
            
            if soup is None:
                continue
            
            # Extract content
            title = self._extract_title(soup)
            main_content = self._extract_main_content(soup)
            markdown = self._html_to_markdown(main_content, url)
            
            # Check relevance
            if not self._is_relevant(markdown, title):
                if verbose:
                    print(f"       ↳ Skipped (not relevant)")
                continue
            
            # Store page
            page_data = {
                'url': url,
                'title': title,
                'depth': depth,
                'content': markdown,
                'filename': self._url_to_filename(url),
                'word_count': len(markdown.split()),
            }
            self.pages.append(page_data)
            
            if verbose:
                print(f"       ↳ ✅ {title} ({page_data['word_count']} words)")
            
            # Extract and queue links if not at max depth
            if depth < max_depth:
                links = self._extract_links(soup, url)
                for link in links:
                    if link not in self.visited:
                        queue.append((link, depth + 1))
            
            # Polite delay
            time.sleep(delay)
        
        print()
        print(f"✅ Crawl complete: {len(self.pages)} pages harvested")
        
        return {
            'base_url': self.base_url,
            'subject': self.subject,
            'pages_crawled': len(self.visited),
            'pages_harvested': len(self.pages),
            'pages': self.pages,
            'timestamp': datetime.now().isoformat(),
        }

    def save(self, output_dir: str, output_format: str = 'both') -> dict:
        """Save crawled content to disk."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        pages_path = output_path / 'pages'
        pages_path.mkdir(exist_ok=True)
        
        # Save individual markdown files
        if output_format in ('md', 'both'):
            for page in self.pages:
                filepath = pages_path / page['filename']
                filepath.write_text(page['content'], encoding='utf-8')
        
        # Generate index
        index_content = self._generate_index()
        (output_path / 'index.md').write_text(index_content, encoding='utf-8')
        
        # Save metadata
        metadata = {
            'base_url': self.base_url,
            'subject': self.subject,
            'pages_crawled': len(self.visited),
            'pages_harvested': len(self.pages),
            'timestamp': datetime.now().isoformat(),
            'config': self.config,
            'pages': [{k: v for k, v in p.items() if k != 'content'} for p in self.pages]
        }
        (output_path / 'metadata.json').write_text(
            json.dumps(metadata, indent=2), encoding='utf-8'
        )
        
        # Save JSON content
        if output_format in ('json', 'both'):
            content_data = {
                'subject': self.subject,
                'base_url': self.base_url,
                'timestamp': datetime.now().isoformat(),
                'pages': [{
                    'url': p['url'],
                    'title': p['title'],
                    'content': p['content'],
                    'word_count': p['word_count'],
                } for p in self.pages]
            }
            (output_path / 'content.json').write_text(
                json.dumps(content_data, indent=2, ensure_ascii=False), encoding='utf-8'
            )
        
        return {
            'output_dir': str(output_path),
            'files_created': {
                'index': str(output_path / 'index.md'),
                'metadata': str(output_path / 'metadata.json'),
                'pages_dir': str(pages_path),
                'page_count': len(self.pages),
            }
        }

    def _generate_index(self) -> str:
        """Generate a master index file."""
        lines = [
            f"# {self.subject} Documentation",
            "",
            f"> Crawled from: [{self.base_url}]({self.base_url})",
            f"> Pages: {len(self.pages)}",
            f"> Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## Table of Contents",
            "",
        ]
        
        # Group by depth for visual hierarchy
        for page in sorted(self.pages, key=lambda p: (p['depth'], p['title'])):
            indent = "  " * page['depth']
            lines.append(f"{indent}- [{page['title']}](pages/{page['filename']})")
        
        lines.extend([
            "",
            "---",
            "",
            "*Generated by Documentation Webcrawler*",
        ])
        
        return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(
        description='Crawl documentation websites and extract content.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument('--url', '-u', required=True, help='Starting URL')
    parser.add_argument('--subject', '-s', required=True, help='Subject focus for filtering')
    parser.add_argument('--output', '-o', default='.tmp/crawled/', help='Output directory')
    parser.add_argument('--depth', '-d', type=int, default=2, help='Max crawl depth')
    parser.add_argument('--filter', '-f', help='URL path filter pattern')
    parser.add_argument('--delay', type=float, default=0.5, help='Delay between requests')
    parser.add_argument('--max-pages', type=int, default=100, help='Maximum pages to crawl')
    parser.add_argument('--same-domain', action='store_true', default=True, help='Stay within same domain')
    parser.add_argument('--include-code', action='store_true', default=True, help='Preserve code blocks')
    parser.add_argument('--format', choices=['md', 'json', 'both'], default='both', help='Output format')
    parser.add_argument('--ignore-robots', action='store_true', help='Ignore robots.txt')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    config = {
        'depth': args.depth,
        'filter': args.filter,
        'delay': args.delay,
        'max_pages': args.max_pages,
        'same_domain': args.same_domain,
        'include_code': args.include_code,
        'ignore_robots': args.ignore_robots,
        'verbose': args.verbose,
    }
    
    try:
        crawler = DocumentationCrawler(args.url, args.subject, config)
        results = crawler.crawl()
        
        if not results['pages']:
            print(json.dumps({
                "status": "error",
                "message": "No relevant pages found"
            }), file=sys.stderr)
            sys.exit(3)
        
        save_result = crawler.save(args.output, args.format)
        
        print()
        print(json.dumps({
            "status": "success",
            "pages_harvested": results['pages_harvested'],
            "output": save_result
        }, indent=2))
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
        sys.exit(4)


if __name__ == '__main__':
    main()
