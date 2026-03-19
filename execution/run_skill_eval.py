#!/usr/bin/env python3
"""
Script: run_skill_eval.py
Purpose: Binary assertion runner for skill self-improvement.
         Evaluates skill output against evals.json assertions and returns pass rates.

Usage:
    python3 execution/run_skill_eval.py --evals path/to/evals.json
    python3 execution/run_skill_eval.py --evals path/to/evals.json --verbose
    python3 execution/run_skill_eval.py --evals path/to/evals.json --test test-name

evals.json format:
    {
      "skill": "skill-name",
      "version": "1.0.0",
      "evaluations": [
        {
          "name": "test-name",
          "description": "What this test checks",
          "input": "Content or prompt to evaluate",
          "input_file": "path/to/file.md",  # Alternative: read input from file
          "assertions": [
            {"type": "contains", "value": "expected text"},
            {"type": "not_contains", "value": "forbidden text"},
            {"type": "max_words", "value": 300},
            {"type": "min_words", "value": 10},
            {"type": "max_lines", "value": 50},
            {"type": "min_lines", "value": 1},
            {"type": "regex_match", "pattern": "^## "},
            {"type": "regex_not_match", "pattern": "---$"},
            {"type": "starts_with", "value": "---"},
            {"type": "ends_with", "value": "\\n"},
            {"type": "has_yaml_frontmatter", "value": true},
            {"type": "no_consecutive_blank_lines", "value": true},
            {"type": "max_chars", "value": 5000},
            {"type": "min_chars", "value": 100},
            {"type": "contains_all", "value": ["word1", "word2"]},
            {"type": "contains_any", "value": ["option1", "option2"]},
            {"type": "line_count_equals", "value": 42},
            {"type": "no_trailing_whitespace", "value": true}
          ]
        }
      ]
    }

Exit Codes:
    0 - All assertions passed
    1 - Some assertions failed
    2 - Invalid arguments or evals.json not found
    3 - Parse error in evals.json
"""

import argparse
import json
import re
import sys
from pathlib import Path


def run_assertion(assertion: dict, content: str) -> dict:
    """
    Run a single binary assertion against content.
    Returns {"passed": bool, "assertion": str, "detail": str}
    """
    atype = assertion.get("type", "")
    value = assertion.get("value")
    pattern = assertion.get("pattern")

    try:
        if atype == "contains":
            passed = value in content
            return {"passed": passed, "assertion": f"contains '{value}'",
                    "detail": "" if passed else f"'{value}' not found in content"}

        elif atype == "not_contains":
            passed = value not in content
            return {"passed": passed, "assertion": f"not_contains '{value}'",
                    "detail": "" if passed else f"'{value}' was found in content"}

        elif atype == "max_words":
            word_count = len(content.split())
            passed = word_count <= value
            return {"passed": passed, "assertion": f"max_words <= {value}",
                    "detail": f"word_count={word_count}"}

        elif atype == "min_words":
            word_count = len(content.split())
            passed = word_count >= value
            return {"passed": passed, "assertion": f"min_words >= {value}",
                    "detail": f"word_count={word_count}"}

        elif atype == "max_lines":
            line_count = len(content.splitlines())
            passed = line_count <= value
            return {"passed": passed, "assertion": f"max_lines <= {value}",
                    "detail": f"line_count={line_count}"}

        elif atype == "min_lines":
            line_count = len(content.splitlines())
            passed = line_count >= value
            return {"passed": passed, "assertion": f"min_lines >= {value}",
                    "detail": f"line_count={line_count}"}

        elif atype == "max_chars":
            char_count = len(content)
            passed = char_count <= value
            return {"passed": passed, "assertion": f"max_chars <= {value}",
                    "detail": f"char_count={char_count}"}

        elif atype == "min_chars":
            char_count = len(content)
            passed = char_count >= value
            return {"passed": passed, "assertion": f"min_chars >= {value}",
                    "detail": f"char_count={char_count}"}

        elif atype == "regex_match":
            passed = bool(re.search(pattern, content, re.MULTILINE))
            return {"passed": passed, "assertion": f"regex_match '{pattern}'",
                    "detail": "" if passed else "pattern not found"}

        elif atype == "regex_not_match":
            passed = not bool(re.search(pattern, content, re.MULTILINE))
            return {"passed": passed, "assertion": f"regex_not_match '{pattern}'",
                    "detail": "" if passed else "pattern was found (should not be)"}

        elif atype == "starts_with":
            passed = content.startswith(value)
            return {"passed": passed, "assertion": f"starts_with '{value}'",
                    "detail": "" if passed else f"starts with '{content[:50]}...'"}

        elif atype == "ends_with":
            passed = content.endswith(value)
            return {"passed": passed, "assertion": f"ends_with '{value}'",
                    "detail": "" if passed else f"ends with '...{content[-50:]}'"}

        elif atype == "has_yaml_frontmatter":
            passed = content.startswith("---") and "\n---" in content[3:]
            return {"passed": passed, "assertion": "has_yaml_frontmatter",
                    "detail": "" if passed else "no valid YAML frontmatter found"}

        elif atype == "no_consecutive_blank_lines":
            passed = "\n\n\n" not in content
            return {"passed": passed, "assertion": "no_consecutive_blank_lines",
                    "detail": "" if passed else "found consecutive blank lines"}

        elif atype == "contains_all":
            missing = [v for v in value if v not in content]
            passed = len(missing) == 0
            return {"passed": passed, "assertion": f"contains_all {value}",
                    "detail": "" if passed else f"missing: {missing}"}

        elif atype == "contains_any":
            found = [v for v in value if v in content]
            passed = len(found) > 0
            return {"passed": passed, "assertion": f"contains_any {value}",
                    "detail": f"found: {found}" if passed else "none found"}

        elif atype == "line_count_equals":
            line_count = len(content.splitlines())
            passed = line_count == value
            return {"passed": passed, "assertion": f"line_count_equals {value}",
                    "detail": f"line_count={line_count}"}

        elif atype == "no_trailing_whitespace":
            lines_with_trailing = [
                i + 1 for i, line in enumerate(content.splitlines())
                if line != line.rstrip()
            ]
            passed = len(lines_with_trailing) == 0
            return {"passed": passed, "assertion": "no_trailing_whitespace",
                    "detail": "" if passed else f"trailing whitespace on lines: {lines_with_trailing[:10]}"}

        else:
            return {"passed": False, "assertion": f"unknown type '{atype}'",
                    "detail": "assertion type not recognized"}

    except Exception as e:
        return {"passed": False, "assertion": f"{atype}", "detail": f"error: {e}"}


def run_evaluation(eval_entry: dict, base_dir: Path = None) -> dict:
    """Run all assertions for a single evaluation entry."""
    name = eval_entry.get("name", "unnamed")
    description = eval_entry.get("description", "")
    assertions = eval_entry.get("assertions", [])

    # Get input content
    content = eval_entry.get("input", "")
    input_file = eval_entry.get("input_file")

    if input_file and not content:
        file_path = Path(input_file)
        if base_dir and not file_path.is_absolute():
            file_path = base_dir / file_path
        try:
            content = file_path.read_text()
        except Exception as e:
            return {
                "name": name,
                "description": description,
                "passed": 0,
                "failed": len(assertions),
                "total": len(assertions),
                "pass_rate": 0.0,
                "error": f"Cannot read input_file: {e}",
                "results": []
            }

    # Run each assertion
    results = []
    passed_count = 0
    for assertion in assertions:
        result = run_assertion(assertion, content)
        results.append(result)
        if result["passed"]:
            passed_count += 1

    total = len(assertions)
    pass_rate = (passed_count / total * 100) if total > 0 else 100.0

    return {
        "name": name,
        "description": description,
        "passed": passed_count,
        "failed": total - passed_count,
        "total": total,
        "pass_rate": round(pass_rate, 1),
        "results": results
    }


def main():
    parser = argparse.ArgumentParser(
        description="Binary assertion runner for skill self-improvement (Karpathy Loop)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run all evals
  python3 execution/run_skill_eval.py --evals skills/my-skill/eval/evals.json

  # Run a specific test
  python3 execution/run_skill_eval.py --evals skills/my-skill/eval/evals.json --test frontmatter-check

  # Verbose output with details
  python3 execution/run_skill_eval.py --evals skills/my-skill/eval/evals.json --verbose
        """,
    )
    parser.add_argument("--evals", required=True, help="Path to evals.json file")
    parser.add_argument("--test", help="Run only a specific test by name")
    parser.add_argument("--verbose", action="store_true", help="Show detailed assertion results")
    parser.add_argument("--json-only", action="store_true", help="Output raw JSON only (no human-readable text)")

    args = parser.parse_args()

    # Load evals.json
    evals_path = Path(args.evals)
    if not evals_path.exists():
        print(json.dumps({"status": "error", "message": f"evals.json not found: {evals_path}"}), file=sys.stderr)
        sys.exit(2)

    try:
        evals_data = json.loads(evals_path.read_text())
    except json.JSONDecodeError as e:
        print(json.dumps({"status": "error", "message": f"Invalid JSON in evals.json: {e}"}), file=sys.stderr)
        sys.exit(3)

    skill_name = evals_data.get("skill", "unknown")
    version = evals_data.get("version", "0.0.0")
    evaluations = evals_data.get("evaluations", [])
    base_dir = evals_path.parent

    # Filter to specific test if requested
    if args.test:
        evaluations = [e for e in evaluations if e.get("name") == args.test]
        if not evaluations:
            print(json.dumps({"status": "error", "message": f"Test '{args.test}' not found"}), file=sys.stderr)
            sys.exit(2)

    # Run all evaluations
    all_results = []
    total_passed = 0
    total_assertions = 0

    for eval_entry in evaluations:
        result = run_evaluation(eval_entry, base_dir)
        all_results.append(result)
        total_passed += result["passed"]
        total_assertions += result["total"]

    overall_pass_rate = (total_passed / total_assertions * 100) if total_assertions > 0 else 100.0

    summary = {
        "status": "pass" if overall_pass_rate == 100.0 else "fail",
        "skill": skill_name,
        "version": version,
        "total_tests": len(all_results),
        "total_assertions": total_assertions,
        "total_passed": total_passed,
        "total_failed": total_assertions - total_passed,
        "pass_rate": round(overall_pass_rate, 1),
        "evaluations": all_results
    }

    if args.json_only:
        print(json.dumps(summary, indent=2))
    else:
        # Human-readable output
        print(f"\n{'='*60}")
        print(f"  Skill Eval: {skill_name} v{version}")
        print(f"{'='*60}\n")

        for result in all_results:
            status = "✅" if result["pass_rate"] == 100.0 else "❌"
            print(f"  {status} {result['name']} — {result['pass_rate']}% ({result['passed']}/{result['total']})")

            if args.verbose or result["pass_rate"] < 100.0:
                for r in result["results"]:
                    icon = "  ✓" if r["passed"] else "  ✗"
                    detail = f" ({r['detail']})" if r["detail"] else ""
                    print(f"    {icon} {r['assertion']}{detail}")

            if result.get("error"):
                print(f"    ⚠ {result['error']}")

        print(f"\n{'─'*60}")
        print(f"  Overall: {summary['pass_rate']}% ({total_passed}/{total_assertions} assertions)")
        print(f"{'─'*60}\n")

        # Also output JSON for piping
        print(json.dumps({"pass_rate": summary["pass_rate"], "status": summary["status"]}, indent=2))

    sys.exit(0 if summary["status"] == "pass" else 1)


if __name__ == "__main__":
    main()
