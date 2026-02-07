#!/usr/bin/env python3
"""
research_report.py — Research Report Formatter for NotebookLM RAG

Takes raw research findings (from NotebookLM queries) and formats them
into a structured report with confidence levels, source attribution,
and actionable recommendations.

Usage:
    python3 research_report.py --input .tmp/research_findings.json --output .tmp/research_report.md
    echo '{"findings": [...]}' | python3 research_report.py --output .tmp/report.md

Arguments:
    --input    Path to JSON file with research findings (or stdin)
    --output   Path for the Markdown report (required)
    --format   Output format: markdown | json (default: markdown)

Input JSON Schema:
    {
        "topic": "string",
        "notebooks_consulted": ["string"],
        "findings": [
            {
                "question": "string",
                "answer": "string",
                "notebook": "string",
                "confidence": "HIGH | MEDIUM | LOW",
                "session_id": "string (optional)"
            }
        ]
    }

Exit Codes:
    0 - Success
    1 - Invalid arguments
    2 - Input file not found
    4 - Processing error
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path


def classify_confidence(answer: str) -> str:
    """Heuristic to classify confidence if not provided."""
    low_signals = [
        "not mentioned",
        "no information",
        "not found",
        "unclear",
        "doesn't cover",
        "not documented",
        "i cannot find",
        "no relevant",
    ]
    medium_signals = [
        "might",
        "possibly",
        "could be",
        "seems to",
        "appears",
        "suggests",
        "inferred",
        "based on context",
    ]

    answer_lower = answer.lower()

    for signal in low_signals:
        if signal in answer_lower:
            return "LOW"
    for signal in medium_signals:
        if signal in answer_lower:
            return "MEDIUM"
    return "HIGH"


def generate_markdown_report(data: dict) -> str:
    """Generate a structured Markdown research report."""
    topic = data.get("topic", "Research Topic")
    notebooks = data.get("notebooks_consulted", [])
    findings = data.get("findings", [])

    high_findings = []
    medium_findings = []
    low_findings = []
    gaps = []

    for f in findings:
        confidence = f.get("confidence") or classify_confidence(f.get("answer", ""))
        f["confidence"] = confidence  # Ensure it's set

        if confidence == "HIGH":
            high_findings.append(f)
        elif confidence == "MEDIUM":
            medium_findings.append(f)
        else:
            low_findings.append(f)
            gaps.append(f)

    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    report = []
    report.append(f"## 📓 Research Report: {topic}\n")
    report.append(f"**Generated:** {now}")
    report.append(f"**Notebooks Consulted:** {', '.join(notebooks) if notebooks else 'N/A'}")
    report.append(f"**Questions Asked:** {len(findings)}")
    report.append(f"**Confidence Breakdown:** {len(high_findings)} HIGH | {len(medium_findings)} MEDIUM | {len(low_findings)} LOW")
    report.append("")

    # Confirmed findings (HIGH)
    if high_findings:
        report.append("### ✅ Confirmed Findings (HIGH Confidence)")
        report.append("")
        for i, f in enumerate(high_findings, 1):
            report.append(f"**{i}. Q:** {f['question']}")
            report.append(f"")
            report.append(f"> {f['answer']}")
            report.append(f"")
            if f.get("notebook"):
                report.append(f"*Source: {f['notebook']}*")
            report.append("")

    # Inferred insights (MEDIUM)
    if medium_findings:
        report.append("### 🔶 Inferred Insights (MEDIUM Confidence)")
        report.append("")
        for i, f in enumerate(medium_findings, 1):
            report.append(f"**{i}. Q:** {f['question']}")
            report.append(f"")
            report.append(f"> {f['answer']}")
            report.append(f"")
            if f.get("notebook"):
                report.append(f"*Source: {f['notebook']}*")
            report.append("")

    # Knowledge gaps (LOW)
    if gaps:
        report.append("### ❌ Knowledge Gaps (Not Found in Documentation)")
        report.append("")
        for i, f in enumerate(gaps, 1):
            report.append(f"{i}. **{f['question']}** — {f.get('answer', 'No information found')}")
        report.append("")

    # Recommendations
    report.append("### 📋 Recommended Actions")
    report.append("")
    if high_findings:
        report.append("1. **Proceed with confidence** on findings backed by documentation")
    if gaps:
        report.append(f"2. **Fill knowledge gaps** — {len(gaps)} question(s) had no documentation coverage")
        report.append("3. **Update notebooks** — Consider adding missing documentation for future queries")
    if medium_findings:
        report.append(f"4. **Verify inferences** — {len(medium_findings)} finding(s) were inferred, not directly stated")
    report.append("")
    report.append("---")
    report.append("*Report generated by NotebookLM RAG skill*")

    return "\n".join(report)


def generate_json_report(data: dict) -> str:
    """Generate a structured JSON report."""
    findings = data.get("findings", [])
    for f in findings:
        if not f.get("confidence"):
            f["confidence"] = classify_confidence(f.get("answer", ""))

    report = {
        "topic": data.get("topic", "Research Topic"),
        "generated_at": datetime.now().isoformat(),
        "notebooks_consulted": data.get("notebooks_consulted", []),
        "total_questions": len(findings),
        "confidence_summary": {
            "high": len([f for f in findings if f["confidence"] == "HIGH"]),
            "medium": len([f for f in findings if f["confidence"] == "MEDIUM"]),
            "low": len([f for f in findings if f["confidence"] == "LOW"]),
        },
        "findings": findings,
    }
    return json.dumps(report, indent=2)


def main():
    parser = argparse.ArgumentParser(
        description="Format NotebookLM research findings into structured reports",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--input", help="Path to JSON findings file (or use stdin)")
    parser.add_argument("--output", required=True, help="Path for the output report")
    parser.add_argument(
        "--format",
        choices=["markdown", "json"],
        default="markdown",
        help="Output format (default: markdown)",
    )
    args = parser.parse_args()

    # Read input
    if args.input:
        input_path = Path(args.input)
        if not input_path.exists():
            print(f"Error: Input file not found: {input_path}", file=sys.stderr)
            sys.exit(2)
        content = input_path.read_text("utf-8")
    elif not sys.stdin.isatty():
        content = sys.stdin.read()
    else:
        print("Error: Provide --input file or pipe JSON to stdin", file=sys.stderr)
        sys.exit(1)

    try:
        data = json.loads(content)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON input: {e}", file=sys.stderr)
        sys.exit(4)

    # Generate report
    if args.format == "markdown":
        report = generate_markdown_report(data)
    else:
        report = generate_json_report(data)

    # Write output
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report, encoding="utf-8")

    print(json.dumps({
        "status": "success",
        "output": str(output_path),
        "format": args.format,
        "findings_count": len(data.get("findings", [])),
    }))
    sys.exit(0)


if __name__ == "__main__":
    main()
