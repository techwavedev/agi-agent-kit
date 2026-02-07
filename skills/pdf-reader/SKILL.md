---
name: pdf-reader
description: Extract text from PDF files for manipulation, search, and reference. Use when needing to read PDF content, extract text from documents, search within PDFs, or convert PDF to text for further processing. Supports multiple extraction methods (pdfplumber, PyMuPDF, pdfminer) with automatic fallback.
---

# PDF Reader

Extract text from PDF files for text manipulation, search, and reference.

## Quick Start

Extract all text from a PDF:

```bash
python scripts/extract_text.py document.pdf
```

Save to file:

```bash
python scripts/extract_text.py document.pdf -o .tmp/output.txt
```

Extract specific pages:

```bash
python scripts/extract_text.py document.pdf -p 1-10 -o .tmp/pages.txt
```

## Workflow

1. **Extract text** → Run `scripts/extract_text.py`
2. **Process output** → Text is now searchable, editable, quotable
3. **Reference content** → Use extracted text for analysis or response

## Script Options

```
extract_text.py <pdf_path> [options]

Options:
  -o, --output FILE      Save to file (default: print to stdout)
  -m, --method METHOD    auto|pdfplumber|pymupdf|pdfminer (default: auto)
  -p, --pages RANGE      Page range: "1-5" or "1,3,5" (default: all)
  --preserve-layout      Keep spatial arrangement of text
  --json                 Output with metadata (page sizes, method used)
```

## Method Selection

| Scenario                 | Recommended Method  |
| ------------------------ | ------------------- |
| General use              | `auto` (default)    |
| Documents with tables    | `pdfplumber`        |
| Large PDFs, speed needed | `pymupdf`           |
| Maximum text accuracy    | `pdfminer`          |
| Scanned/image PDFs       | `pymupdf` (has OCR) |

## Examples

### Extract and search

```bash
python scripts/extract_text.py report.pdf | grep -i "revenue"
```

### Extract tables (use pdfplumber)

```bash
python scripts/extract_text.py data.pdf -m pdfplumber --json -o .tmp/data.json
```

### Specific pages with layout

```bash
python scripts/extract_text.py book.pdf -p 50-55 --preserve-layout -o .tmp/chapter.txt
```

## Dependencies

At least one library required:

```bash
pip install pdfplumber pymupdf pdfminer.six
```

For detailed library comparison, see [references/pdf_libraries.md](references/pdf_libraries.md).

## Troubleshooting

**Empty output?**

- PDF may be scanned/image-based → try `--method pymupdf` (has OCR)
- Check if PDF is password-protected

**Garbled text?**

- Try different method: `-m pdfminer`
- PDF may have non-standard font encoding

**Tables not formatted?**

- Use `-m pdfplumber --json` for structured output
- Consider `--preserve-layout` flag
