# PDF Library Reference

## Library Comparison

| Library      | Speed      | Tables   | OCR         | Layout  | Install                    |
| ------------ | ---------- | -------- | ----------- | ------- | -------------------------- |
| pdfplumber   | Medium     | ✅ Best  | ❌          | ✅ Good | `pip install pdfplumber`   |
| PyMuPDF      | ✅ Fastest | ⚠️ Basic | ✅ Built-in | ✅ Good | `pip install pymupdf`      |
| pdfminer.six | Slow       | ❌       | ❌          | ✅ Best | `pip install pdfminer.six` |

## When to Use Each

### pdfplumber (default)

Best for documents with tables, forms, or structured content.

```python
import pdfplumber
with pdfplumber.open("doc.pdf") as pdf:
    for page in pdf.pages:
        text = page.extract_text()
        tables = page.extract_tables()
```

### PyMuPDF (pymupdf)

Best for speed, large documents, or when OCR is needed.

```python
import fitz
doc = fitz.open("doc.pdf")
for page in doc:
    text = page.get_text()
    # OCR if needed (requires Tesseract)
    # text = page.get_text("text", flags=fitz.TEXT_PRESERVE_WHITESPACE)
```

### pdfminer.six

Best for maximum text accuracy and complex layouts.

```python
from pdfminer.high_level import extract_text
text = extract_text("doc.pdf")
```

## Common Issues

### Scanned PDFs (image-based)

Use PyMuPDF with OCR:

```bash
python scripts/extract_text.py scanned.pdf --method pymupdf
```

If text is empty, the PDF likely needs OCR processing.

### Tables Not Extracting

Use pdfplumber explicitly:

```bash
python scripts/extract_text.py table.pdf --method pdfplumber --json
```

### Encoding Issues

Try different methods or check if PDF has embedded fonts.

## Installation

Install all libraries for maximum compatibility:

```bash
pip install pdfplumber pymupdf pdfminer.six
```

Minimal (one library):

```bash
pip install pdfplumber  # Recommended default
```
