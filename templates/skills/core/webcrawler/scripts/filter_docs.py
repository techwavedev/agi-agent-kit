#!/usr/bin/env python3
"""
Script: filter_docs.py
Purpose: Filter already-crawled documentation by subject or pattern.

Usage:
    python filter_docs.py --input <crawl-dir> --subject <topic> --output <output-dir>

Arguments:
    --input, -i      Crawled docs directory (required)
    --subject, -s    Subject to filter for (required)
    --output, -o     Filtered output directory (required)
    --threshold, -t  Relevance threshold 0.0-1.0 (default: 0.3)

Exit Codes:
    0 - Success
    1 - Invalid arguments
    2 - Input not found
    3 - No matching content
"""

import argparse
import json
import re
import sys
from pathlib import Path
from datetime import datetime


def calculate_relevance(content: str, title: str, subject: str) -> float:
    """Calculate relevance score based on subject keywords."""
    subject_lower = subject.lower()
    subject_words = [w for w in subject_lower.split() if len(w) > 2]
    
    if not subject_words:
        return 0.0
    
    text = (title + ' ' + content).lower()
    total_words = len(text.split())
    
    if total_words == 0:
        return 0.0
    
    # Count keyword occurrences
    keyword_count = 0
    for word in subject_words:
        keyword_count += len(re.findall(r'\b' + re.escape(word) + r'\b', text))
    
    # Calculate density-based score
    density = keyword_count / total_words
    
    # Bonus for title matches
    title_lower = title.lower()
    title_bonus = 0.3 if any(w in title_lower for w in subject_words) else 0.0
    
    # Normalize to 0-1 range
    score = min(1.0, (density * 100) + title_bonus)
    
    return score


def filter_crawled_docs(input_dir: Path, subject: str, threshold: float) -> list:
    """Filter documents based on relevance to subject."""
    pages_dir = input_dir / 'pages'
    
    if not pages_dir.exists():
        raise FileNotFoundError(f"Pages directory not found: {pages_dir}")
    
    filtered = []
    
    for md_file in pages_dir.glob('*.md'):
        content = md_file.read_text(encoding='utf-8')
        
        # Extract title from frontmatter or first heading
        title = 'Untitled'
        if content.startswith('---'):
            # Has frontmatter
            end = content.find('---', 3)
            if end > 0:
                body = content[end + 3:].strip()
                # Try to get first heading
                match = re.search(r'^#\s+(.+)$', body, re.MULTILINE)
                if match:
                    title = match.group(1)
        else:
            match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
            if match:
                title = match.group(1)
        
        score = calculate_relevance(content, title, subject)
        
        if score >= threshold:
            filtered.append({
                'file': md_file.name,
                'title': title,
                'score': score,
                'content': content,
                'word_count': len(content.split()),
            })
    
    # Sort by relevance
    filtered.sort(key=lambda x: x['score'], reverse=True)
    
    return filtered


def save_filtered(filtered: list, output_dir: Path, subject: str, input_dir: Path):
    """Save filtered documents to output directory."""
    output_dir.mkdir(parents=True, exist_ok=True)
    pages_dir = output_dir / 'pages'
    pages_dir.mkdir(exist_ok=True)
    
    # Copy filtered pages
    for page in filtered:
        (pages_dir / page['file']).write_text(page['content'], encoding='utf-8')
    
    # Generate new index
    index_lines = [
        f"# {subject} (Filtered Documentation)",
        "",
        f"> Filtered from: {input_dir}",
        f"> Pages: {len(filtered)}",
        f"> Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## Table of Contents",
        "",
    ]
    
    for page in filtered:
        index_lines.append(f"- [{page['title']}](pages/{page['file']}) (relevance: {page['score']:.2f})")
    
    (output_dir / 'index.md').write_text('\n'.join(index_lines), encoding='utf-8')
    
    # Save metadata
    metadata = {
        'subject': subject,
        'source': str(input_dir),
        'pages_filtered': len(filtered),
        'timestamp': datetime.now().isoformat(),
        'pages': [{k: v for k, v in p.items() if k != 'content'} for p in filtered]
    }
    (output_dir / 'metadata.json').write_text(json.dumps(metadata, indent=2), encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description='Filter crawled documentation by subject.')
    parser.add_argument('--input', '-i', required=True, help='Crawled docs directory')
    parser.add_argument('--subject', '-s', required=True, help='Subject to filter for')
    parser.add_argument('--output', '-o', required=True, help='Filtered output directory')
    parser.add_argument('--threshold', '-t', type=float, default=0.3, help='Relevance threshold')
    
    args = parser.parse_args()
    
    input_dir = Path(args.input)
    output_dir = Path(args.output)
    
    if not input_dir.exists():
        print(json.dumps({
            "status": "error",
            "message": f"Input directory not found: {input_dir}"
        }), file=sys.stderr)
        sys.exit(2)
    
    try:
        print(f"🔍 Filtering docs for: {args.subject}")
        print(f"   Source: {input_dir}")
        print(f"   Threshold: {args.threshold}")
        print()
        
        filtered = filter_crawled_docs(input_dir, args.subject, args.threshold)
        
        if not filtered:
            print(json.dumps({
                "status": "error",
                "message": "No pages matched the filter criteria"
            }), file=sys.stderr)
            sys.exit(3)
        
        save_filtered(filtered, output_dir, args.subject, input_dir)
        
        print(f"✅ Filtered {len(filtered)} pages")
        print()
        print(json.dumps({
            "status": "success",
            "pages_filtered": len(filtered),
            "output": str(output_dir)
        }, indent=2))
        sys.exit(0)
        
    except Exception as e:
        print(json.dumps({
            "status": "error",
            "type": type(e).__name__,
            "message": str(e)
        }), file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
