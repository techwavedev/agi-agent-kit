# TheHackerNews Parsing Reference

## RSS Feed (Primary Source)

- **URL**: `https://feeds.feedburner.com/TheHackersNews`
- **Format**: Atom/RSS with `<entry>` elements
- **Fields**: `<title>`, `<link>`, `<published>`, `<content>`
- **Advantages**: Structured, lightweight, no Cloudflare issues

## HTML Fallback

### Homepage / Label Pages

- **Supply chain label**: `https://thehackernews.com/search/label/Supply%20Chain`
- **Malware label**: `https://thehackernews.com/search/label/Malware`
- **Article containers**: `.body-post`
- **Title links**: `.home-title a`
- **Snippet**: `.home-desc`
- **Date**: `.item-label span`

### Article Pages

- **Headline**: `.story-title`
- **Body content**: `.articlebody`
- **Author**: `.author-name`
- **Date**: `.meta-date`

## Supply Chain Keywords

Used to filter articles for relevance:

```
supply chain, backdoor, compromised package, malicious package,
typosquatting, dependency confusion, trojanized, malware pypi,
malware npm, poisoned, credential harvesting, ci/cd compromise,
github action compromise, package hijack
```

## Rate Limiting

- TheHackerNews uses Cloudflare
- Use 1-2 second delay between requests
- Set `User-Agent` to a real browser string
- RSS feed has no rate limiting concerns

## Package Name Extraction Patterns

Common patterns in THN articles that indicate package names:

- Backtick-quoted: `` `package-name` ``
- Code blocks with install commands: `pip install X`, `npm install X`
- Import statements: `import X`, `from X import`
- GitHub action refs: `org/action-name@version`
- Quoted in threat context: "the malicious package 'X'"
- Version ranges: `X versions 1.2.3-1.2.5`
