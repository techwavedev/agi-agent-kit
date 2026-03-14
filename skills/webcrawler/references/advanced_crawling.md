# Advanced Crawling Reference

## JavaScript-Rendered Pages

Some documentation sites render content with JavaScript. For these, use Playwright:

```bash
# Install Playwright
pip install playwright
playwright install chromium

# Use in crawl_docs.py with --render-js flag (future feature)
```

### Manual Extraction with Playwright

```python
from playwright.sync_api import sync_playwright

def extract_js_rendered(url: str) -> str:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(url, wait_until='networkidle')
        content = page.content()
        browser.close()
        return content
```

---

## Rate Limiting Strategies

### Exponential Backoff

```python
import time
import random

def fetch_with_backoff(url, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = requests.get(url)
            if response.status_code == 429:  # Too Many Requests
                wait = (2 ** attempt) + random.uniform(0, 1)
                time.sleep(wait)
                continue
            return response
        except requests.exceptions.RequestException:
            if attempt == max_retries - 1:
                raise
            time.sleep(2 ** attempt)
```

### Respecting Crawl-Delay

```python
from urllib.robotparser import RobotFileParser

rp = RobotFileParser()
rp.set_url("https://example.com/robots.txt")
rp.read()

crawl_delay = rp.crawl_delay("*")
if crawl_delay:
    time.sleep(crawl_delay)
```

---

## Content Extraction Patterns

### Documentation Site Patterns

| Site Type       | Content Selector       | Notes                     |
| --------------- | ---------------------- | ------------------------- |
| **ReadTheDocs** | `.document`, `.body`   | Standard Sphinx output    |
| **GitBook**     | `.page-inner`          | Modern docs platform      |
| **Docusaurus**  | `.markdown`, `article` | React-based docs          |
| **MkDocs**      | `.md-content`          | Python-based docs         |
| **Notion**      | `.notion-page-content` | Requires special handling |
| **Confluence**  | `#main-content`        | Enterprise wiki           |

### Handling Dynamic Navigation

Some sites use JavaScript for navigation. Strategy:

1. Extract sitemap from `sitemap.xml` if available
2. Parse navigation elements for all page links
3. Follow `next`/`prev` pagination links

```python
def get_sitemap_urls(base_url: str) -> list:
    sitemap_url = f"{base_url}/sitemap.xml"
    response = requests.get(sitemap_url)
    soup = BeautifulSoup(response.content, 'lxml-xml')
    return [loc.text for loc in soup.find_all('loc')]
```

---

## Large Documentation Sets

For documentation with 500+ pages:

1. **Use depth limits** — Start with `--depth 1` to get main sections
2. **Section by section** — Crawl each major section separately
3. **Resume capability** — Check `metadata.json` for already-crawled pages
4. **Parallel crawling** — Use async requests (not implemented in base script)

### Memory-Efficient Streaming

```python
# For very large crawls, write pages immediately instead of buffering
def crawl_streaming(url, output_dir):
    for page in discover_pages(url):
        content = extract_page(page)
        save_immediately(content, output_dir)
        # Page content is not kept in memory
```

---

## Integration with RAG Pipelines

### Chunking Strategy

After crawling, chunk documents for embedding:

```python
def chunk_document(content: str, chunk_size: int = 500) -> list:
    """Split document into overlapping chunks."""
    words = content.split()
    chunks = []
    overlap = chunk_size // 4

    for i in range(0, len(words), chunk_size - overlap):
        chunk = ' '.join(words[i:i + chunk_size])
        if chunk:
            chunks.append(chunk)

    return chunks
```

### Metadata Preservation

Keep source URLs with chunks for citation:

```python
{
    "text": "chunk content...",
    "metadata": {
        "source_url": "https://docs.example.com/page",
        "title": "Page Title",
        "section": "Getting Started"
    }
}
```

---

## Troubleshooting

### Common Issues

| Problem                 | Solution                                           |
| ----------------------- | -------------------------------------------------- |
| **403 Forbidden**       | Add realistic User-Agent, increase delay           |
| **Cloudflare blocking** | Use Playwright with stealth plugin                 |
| **CAPTCHA**             | Cannot bypass; manual intervention required        |
| **Session-based auth**  | Export cookies, use `--cookies` option             |
| **Infinite scroll**     | Use Playwright to scroll and wait for content      |
| **Rate limiting (429)** | Implement exponential backoff, respect Retry-After |

### Debugging

Enable verbose mode to trace crawl behavior:

```bash
python crawl_docs.py --url "..." --subject "..." -v 2>&1 | tee crawl.log
```
