#!/usr/bin/env python3
"""
Script: extract_text.py
Purpose: Extract text from PDF files with multiple fallback methods

Usage:
    python extract_text.py <pdf_path> [--output <file>] [--method <method>] [--pages <range>]

Arguments:
    pdf_path          Path to PDF file (required)
    --output, -o      Output file path (default: stdout)
    --method, -m      Extraction method: auto|pdfplumber|pymupdf|pdfminer (default: auto)
    --pages, -p       Page range, e.g., "1-5" or "1,3,5" (default: all)
    --preserve-layout Keep spatial layout (default: false)
    --json            Output as JSON with metadata

Exit Codes: 0=success, 1=args, 2=file not found, 3=library error, 4=extraction error
"""

import argparse
import json
import sys
from pathlib import Path


def check_dependencies():
    """Check which PDF libraries are available."""
    available = {}
    
    try:
        import pdfplumber
        available['pdfplumber'] = pdfplumber
    except ImportError:
        pass
    
    try:
        import fitz  # PyMuPDF
        available['pymupdf'] = fitz
    except ImportError:
        pass
    
    try:
        from pdfminer.high_level import extract_text as pdfminer_extract
        available['pdfminer'] = pdfminer_extract
    except ImportError:
        pass
    
    return available


def parse_page_range(page_str: str, total_pages: int) -> list[int]:
    """Parse page range string into list of 0-indexed page numbers."""
    if not page_str:
        return list(range(total_pages))
    
    pages = set()
    for part in page_str.split(','):
        if '-' in part:
            start, end = part.split('-', 1)
            start = int(start) - 1 if start else 0
            end = int(end) if end else total_pages
            pages.update(range(start, min(end, total_pages)))
        else:
            page = int(part) - 1
            if 0 <= page < total_pages:
                pages.add(page)
    
    return sorted(pages)


def extract_with_pdfplumber(pdf_path: Path, pages: list[int] = None, preserve_layout: bool = False) -> dict:
    """Extract text using pdfplumber (best for tables and complex layouts)."""
    import pdfplumber
    
    result = {"pages": [], "metadata": {}}
    
    with pdfplumber.open(pdf_path) as pdf:
        result["metadata"] = {
            "total_pages": len(pdf.pages),
            "method": "pdfplumber"
        }
        
        if pdf.metadata:
            result["metadata"].update({k: v for k, v in pdf.metadata.items() if v})
        
        page_indices = pages if pages else range(len(pdf.pages))
        
        for i in page_indices:
            page = pdf.pages[i]
            if preserve_layout:
                text = page.extract_text(layout=True) or ""
            else:
                text = page.extract_text() or ""
            
            result["pages"].append({
                "page_num": i + 1,
                "text": text,
                "width": page.width,
                "height": page.height
            })
    
    return result


def extract_with_pymupdf(pdf_path: Path, pages: list[int] = None, preserve_layout: bool = False) -> dict:
    """Extract text using PyMuPDF/fitz (fastest, good OCR support)."""
    import fitz
    
    result = {"pages": [], "metadata": {}}
    
    doc = fitz.open(pdf_path)
    
    result["metadata"] = {
        "total_pages": len(doc),
        "method": "pymupdf"
    }
    
    if doc.metadata:
        result["metadata"].update({k: v for k, v in doc.metadata.items() if v})
    
    page_indices = pages if pages else range(len(doc))
    
    flags = fitz.TEXT_PRESERVE_WHITESPACE if preserve_layout else 0
    
    for i in page_indices:
        page = doc[i]
        text = page.get_text("text", flags=flags)
        
        result["pages"].append({
            "page_num": i + 1,
            "text": text,
            "width": page.rect.width,
            "height": page.rect.height
        })
    
    doc.close()
    return result


def extract_with_pdfminer(pdf_path: Path, pages: list[int] = None, preserve_layout: bool = False) -> dict:
    """Extract text using pdfminer (best text accuracy, slower)."""
    from pdfminer.high_level import extract_text, extract_pages
    from pdfminer.layout import LAParams
    
    result = {"pages": [], "metadata": {"method": "pdfminer"}}
    
    laparams = LAParams(
        detect_vertical=preserve_layout,
        all_texts=True
    )
    
    # Get total pages
    all_pages = list(extract_pages(pdf_path, laparams=laparams))
    result["metadata"]["total_pages"] = len(all_pages)
    
    page_indices = pages if pages else range(len(all_pages))
    
    for i in page_indices:
        if i < len(all_pages):
            page = all_pages[i]
            text_content = []
            for element in page:
                if hasattr(element, 'get_text'):
                    text_content.append(element.get_text())
            
            result["pages"].append({
                "page_num": i + 1,
                "text": "".join(text_content),
                "width": page.width,
                "height": page.height
            })
    
    return result


def extract_text(pdf_path: Path, method: str = "auto", pages: list[int] = None, 
                 preserve_layout: bool = False) -> dict:
    """Extract text from PDF using specified or best available method."""
    available = check_dependencies()
    
    if not available:
        print(json.dumps({
            "status": "error",
            "message": "No PDF library available. Install: pip install pdfplumber pymupdf pdfminer.six"
        }), file=sys.stderr)
        sys.exit(3)
    
    # Method selection
    if method == "auto":
        # Preference order: pdfplumber (best tables), pymupdf (fastest), pdfminer (most accurate)
        if 'pdfplumber' in available:
            method = 'pdfplumber'
        elif 'pymupdf' in available:
            method = 'pymupdf'
        else:
            method = 'pdfminer'
    
    if method not in available:
        print(json.dumps({
            "status": "error",
            "message": f"Method '{method}' not available. Install the corresponding library.",
            "available": list(available.keys())
        }), file=sys.stderr)
        sys.exit(3)
    
    # Extract based on method
    extractors = {
        'pdfplumber': extract_with_pdfplumber,
        'pymupdf': extract_with_pymupdf,
        'pdfminer': extract_with_pdfminer
    }
    
    return extractors[method](pdf_path, pages, preserve_layout)


def main():
    parser = argparse.ArgumentParser(
        description="Extract text from PDF files",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('pdf_path', help='Path to PDF file')
    parser.add_argument('-o', '--output', help='Output file path')
    parser.add_argument('-m', '--method', default='auto', 
                        choices=['auto', 'pdfplumber', 'pymupdf', 'pdfminer'],
                        help='Extraction method')
    parser.add_argument('-p', '--pages', help='Page range (e.g., "1-5" or "1,3,5")')
    parser.add_argument('--preserve-layout', action='store_true',
                        help='Preserve spatial layout')
    parser.add_argument('--json', action='store_true', dest='output_json',
                        help='Output as JSON with metadata')
    
    args = parser.parse_args()
    
    pdf_path = Path(args.pdf_path)
    if not pdf_path.exists():
        print(json.dumps({"status": "error", "message": f"File not found: {pdf_path}"}), 
              file=sys.stderr)
        sys.exit(2)
    
    try:
        # Get total pages first for page range parsing
        available = check_dependencies()
        if not available:
            sys.exit(3)
        
        # Quick page count
        if 'pymupdf' in available:
            import fitz
            doc = fitz.open(pdf_path)
            total_pages = len(doc)
            doc.close()
        elif 'pdfplumber' in available:
            import pdfplumber
            with pdfplumber.open(pdf_path) as pdf:
                total_pages = len(pdf.pages)
        else:
            total_pages = 9999  # Will be limited during extraction
        
        pages = parse_page_range(args.pages, total_pages) if args.pages else None
        
        result = extract_text(
            pdf_path, 
            method=args.method,
            pages=pages,
            preserve_layout=args.preserve_layout
        )
        
        # Format output
        if args.output_json:
            output = json.dumps({"status": "success", **result}, indent=2)
        else:
            # Plain text output
            output = "\n\n".join(
                f"--- Page {p['page_num']} ---\n{p['text']}" 
                for p in result['pages']
            )
        
        if args.output:
            Path(args.output).parent.mkdir(parents=True, exist_ok=True)
            Path(args.output).write_text(output)
            print(json.dumps({"status": "success", "output": args.output, 
                            "pages_extracted": len(result['pages'])}))
        else:
            print(output)
        
        sys.exit(0)
        
    except Exception as e:
        print(json.dumps({"status": "error", "message": str(e), "type": type(e).__name__}),
              file=sys.stderr)
        sys.exit(4)


if __name__ == '__main__':
    main()
