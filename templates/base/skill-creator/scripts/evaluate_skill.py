#!/usr/bin/env python3
"""
Script: evaluate_skill.py
Purpose: Automated structural evaluation of skills against binary criteria.
         Validates skill structure, YAML frontmatter, progressive disclosure,
         script executability, and stores results in Qdrant for cross-agent visibility.

Usage:
    python3 skill-creator/scripts/evaluate_skill.py \
      --skill-path skills/pdf-reader \
      --test-input "Read this PDF and extract key points" \
      --criteria '["Output contains summary", "Output has bullet points"]' \
      --runs 3 \
      --project agi-agent-kit

    python3 skill-creator/scripts/evaluate_skill.py \
      --skill-path skills/pdf-reader \
      --test-input "test" \
      --criteria '["SKILL.md exists", "Has frontmatter"]' \
      --json

Arguments:
    --skill-path  Path to skill directory (required)
    --test-input  The test prompt/input description (required)
    --criteria    JSON array of binary evaluation criteria (required)
    --runs        Number of evaluation runs (default: 3)
    --project     Project name for Qdrant storage (default: agi-agent-kit)
    --json        JSON-only output
    --no-store    Disable storing results in Qdrant

Exit Codes:
    0 - Evaluation complete, all criteria passed
    1 - Evaluation complete, some criteria failed
    2 - Invalid arguments or skill path not found
    3 - Qdrant connection error (evaluation still runs, storage skipped)
    4 - Unexpected error
"""

import argparse
import json
import os
import re
import stat
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

# Configuration
QDRANT_URL = os.environ.get("QDRANT_URL", "http://localhost:6333")
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "nomic-embed-text")
MEMORY_COLLECTION = os.environ.get("MEMORY_COLLECTION", "agent_memory")
MAX_SKILL_LINES = 200


# ---------------------------------------------------------------------------
# Qdrant helpers (self-contained, urllib only — mirrors memory_manager.py)
# ---------------------------------------------------------------------------

def _qdrant_request(method: str, path: str, body: dict = None, timeout: int = 10) -> dict:
    """Send a request to Qdrant and return parsed JSON."""
    url = f"{QDRANT_URL}{path}"
    data = json.dumps(body).encode() if body else None
    headers = {"Content-Type": "application/json"} if data else {}
    req = Request(url, data=data, headers=headers, method=method)
    with urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode())


def _get_embedding(text: str) -> list:
    """Get embedding vector from Ollama."""
    url = f"{OLLAMA_URL}/api/embeddings"
    payload = json.dumps({"model": EMBEDDING_MODEL, "prompt": text}).encode()
    req = Request(url, data=payload, headers={"Content-Type": "application/json"})
    with urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode())
    return data.get("embedding", [])


def _store_to_qdrant(content: str, metadata: dict) -> dict:
    """Store a point in the agent_memory collection."""
    try:
        embedding = _get_embedding(content)
    except Exception as e:
        return {"status": "error", "message": f"Embedding failed: {e}"}

    point_id = str(uuid.uuid4())
    payload = {
        "content": content,
        "type": "evaluation",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **metadata,
    }

    body = {"points": [{"id": point_id, "vector": embedding, "payload": payload}]}

    try:
        result = _qdrant_request("PUT", f"/collections/{MEMORY_COLLECTION}/points", body)
        return {"status": "stored", "id": point_id, "qdrant_status": result.get("status")}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def _search_qdrant(query: str, skill_name: str, top_k: int = 5) -> list:
    """Search Qdrant for prior evaluations of this skill."""
    try:
        embedding = _get_embedding(query)
    except Exception:
        return []

    body = {
        "vector": embedding,
        "limit": top_k,
        "with_payload": True,
        "filter": {
            "must": [
                {"key": "type", "match": {"value": "evaluation"}},
                {"key": "skill_name", "match": {"value": skill_name}},
            ]
        },
    }

    try:
        result = _qdrant_request("POST", f"/collections/{MEMORY_COLLECTION}/points/search", body)
        return result.get("result", [])
    except Exception:
        return []


# ---------------------------------------------------------------------------
# Structural evaluation checks
# ---------------------------------------------------------------------------

def check_skill_md_exists(skill_path: Path) -> bool:
    return (skill_path / "SKILL.md").is_file()


def check_yaml_frontmatter(skill_path: Path) -> tuple:
    """Return (has_frontmatter: bool, frontmatter: dict | None, error: str | None)."""
    skill_md = skill_path / "SKILL.md"
    if not skill_md.is_file():
        return False, None, "SKILL.md not found"

    content = skill_md.read_text(encoding="utf-8", errors="replace")
    if not content.startswith("---"):
        return False, None, "No YAML frontmatter delimiter"

    match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    if not match:
        return False, None, "Malformed frontmatter"

    try:
        # Use yaml if available, otherwise basic parsing
        try:
            import yaml
            fm = yaml.safe_load(match.group(1))
        except ImportError:
            fm = _parse_simple_yaml(match.group(1))

        if not isinstance(fm, dict):
            return False, None, "Frontmatter is not a mapping"
        return True, fm, None
    except Exception as e:
        return False, None, f"YAML parse error: {e}"


def _parse_simple_yaml(text: str) -> dict:
    """Minimal YAML parser for flat key-value frontmatter (fallback when PyYAML unavailable)."""
    result = {}
    for line in text.strip().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" in line:
            key, _, value = line.partition(":")
            result[key.strip()] = value.strip().strip('"').strip("'")
    return result


def check_required_fields(frontmatter: dict) -> tuple:
    """Check that name and description exist in frontmatter."""
    missing = []
    if not frontmatter:
        return False, ["name", "description"]
    if "name" not in frontmatter or not frontmatter["name"]:
        missing.append("name")
    if "description" not in frontmatter or not frontmatter["description"]:
        missing.append("description")
    return len(missing) == 0, missing


def check_line_count(skill_path: Path) -> tuple:
    """Return (under_limit: bool, line_count: int)."""
    skill_md = skill_path / "SKILL.md"
    if not skill_md.is_file():
        return False, 0
    lines = skill_md.read_text(encoding="utf-8", errors="replace").splitlines()
    return len(lines) <= MAX_SKILL_LINES, len(lines)


def check_scripts_dir(skill_path: Path) -> tuple:
    """Return (exists: bool, scripts: list)."""
    scripts_dir = skill_path / "scripts"
    if not scripts_dir.is_dir():
        return False, []
    scripts = [f.name for f in scripts_dir.iterdir() if f.is_file()]
    return True, scripts


def check_references_dir(skill_path: Path) -> bool:
    return (skill_path / "references").is_dir()


def check_script_executability(skill_path: Path) -> tuple:
    """Check if scripts have executable bit or shebang."""
    scripts_dir = skill_path / "scripts"
    if not scripts_dir.is_dir():
        return True, []  # No scripts dir = not applicable, pass

    issues = []
    for f in scripts_dir.iterdir():
        if not f.is_file():
            continue
        # Check for shebang
        try:
            first_line = f.read_text(encoding="utf-8", errors="replace").split("\n", 1)[0]
        except Exception:
            first_line = ""

        has_shebang = first_line.startswith("#!")
        has_exec = bool(f.stat().st_mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH))

        if f.suffix in (".py", ".sh", ".bash") and not has_shebang and not has_exec:
            issues.append(f"{f.name}: no shebang and not executable")

    return len(issues) == 0, issues


def check_name_convention(frontmatter: dict) -> tuple:
    """Validate name is hyphen-case."""
    name = frontmatter.get("name", "") if frontmatter else ""
    if not name:
        return False, "name is empty"
    if not isinstance(name, str):
        return False, f"name is {type(name).__name__}, expected str"
    if not re.match(r"^[a-z0-9][a-z0-9-]*[a-z0-9]$", name) and len(name) > 1:
        if not re.match(r"^[a-z0-9]$", name):
            return False, f"'{name}' is not valid hyphen-case"
    if "--" in name:
        return False, f"'{name}' contains consecutive hyphens"
    return True, None


# ---------------------------------------------------------------------------
# Evaluation runner
# ---------------------------------------------------------------------------

BUILTIN_CHECKS = {
    "SKILL.md exists": lambda p, _fm: (check_skill_md_exists(p), None),
    "Has YAML frontmatter": lambda p, _fm: (check_yaml_frontmatter(p)[0], check_yaml_frontmatter(p)[2]),
    "Has required fields (name, description)": lambda p, fm: (check_required_fields(fm)[0], check_required_fields(fm)[1] if not check_required_fields(fm)[0] else None),
    "Under 200 lines (progressive disclosure)": lambda p, _fm: (check_line_count(p)[0], f"{check_line_count(p)[1]} lines"),
    "Has scripts/ directory": lambda p, _fm: (check_scripts_dir(p)[0], None),
    "Has references/ directory": lambda p, _fm: (check_references_dir(p), None),
    "Scripts are executable": lambda p, _fm: (check_script_executability(p)[0], check_script_executability(p)[1] or None),
    "Name follows hyphen-case convention": lambda p, fm: (check_name_convention(fm)[0], check_name_convention(fm)[1]),
}


def run_single_evaluation(skill_path: Path, criteria: list, run_number: int) -> dict:
    """Run one evaluation pass against all criteria."""
    # Parse frontmatter once
    has_fm, frontmatter, fm_error = check_yaml_frontmatter(skill_path)

    results = []
    for criterion in criteria:
        criterion_lower = criterion.strip()
        matched_builtin = False

        # Try to match against built-in checks (case-insensitive partial match)
        for builtin_name, check_fn in BUILTIN_CHECKS.items():
            if criterion_lower.lower() in builtin_name.lower() or builtin_name.lower() in criterion_lower.lower():
                passed, detail = check_fn(skill_path, frontmatter)
                results.append({
                    "criterion": criterion,
                    "passed": bool(passed),
                    "detail": str(detail) if detail else None,
                    "check_type": "builtin",
                })
                matched_builtin = True
                break

        if not matched_builtin:
            # Structural heuristic: check if the criterion text appears in SKILL.md content
            skill_md = skill_path / "SKILL.md"
            if skill_md.is_file():
                content = skill_md.read_text(encoding="utf-8", errors="replace").lower()
                # Check for keywords from the criterion
                keywords = [w for w in re.findall(r"\w+", criterion_lower.lower()) if len(w) > 3]
                matches = sum(1 for kw in keywords if kw in content)
                relevance = matches / max(len(keywords), 1)
                passed = relevance >= 0.5
                results.append({
                    "criterion": criterion,
                    "passed": passed,
                    "detail": f"keyword relevance: {relevance:.0%} ({matches}/{len(keywords)} keywords found)",
                    "check_type": "heuristic",
                })
            else:
                results.append({
                    "criterion": criterion,
                    "passed": False,
                    "detail": "SKILL.md not found, cannot evaluate",
                    "check_type": "heuristic",
                })

    passed_count = sum(1 for r in results if r["passed"])
    return {
        "run": run_number,
        "total_criteria": len(results),
        "passed": passed_count,
        "failed": len(results) - passed_count,
        "pass_rate": round(passed_count / max(len(results), 1), 4),
        "criteria_results": results,
    }


def get_historical_evaluations(skill_name: str) -> list:
    """Retrieve past evaluations from Qdrant."""
    hits = _search_qdrant(f"skill evaluation {skill_name}", skill_name, top_k=10)
    history = []
    for hit in hits:
        payload = hit.get("payload", {})
        history.append({
            "timestamp": payload.get("timestamp"),
            "pass_rate": payload.get("pass_rate"),
            "total_criteria": payload.get("total_criteria"),
            "passed": payload.get("passed"),
            "score": hit.get("score"),
        })
    # Sort by timestamp descending
    history.sort(key=lambda h: h.get("timestamp") or "", reverse=True)
    return history


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Evaluate a skill against binary criteria with Qdrant memory integration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Full evaluation with Qdrant storage
  python3 skill-creator/scripts/evaluate_skill.py \\
    --skill-path skills/pdf-reader \\
    --test-input "Read a PDF" \\
    --criteria '["SKILL.md exists", "Has YAML frontmatter", "Under 200 lines"]'

  # JSON output, skip Qdrant storage
  python3 skill-creator/scripts/evaluate_skill.py \\
    --skill-path skills/my-skill \\
    --test-input "test" \\
    --criteria '["Has required fields"]' \\
    --json --no-store
        """,
    )
    parser.add_argument("--skill-path", required=True, help="Path to skill directory")
    parser.add_argument("--test-input", required=True, help="Test prompt / input description")
    parser.add_argument("--criteria", required=True, help="JSON array of binary criteria strings")
    parser.add_argument("--runs", type=int, default=3, help="Number of evaluation runs (default: 3)")
    parser.add_argument("--project", default="agi-agent-kit", help="Project name for Qdrant storage")
    parser.add_argument("--json", action="store_true", dest="json_output", help="JSON-only output")
    parser.add_argument("--no-store", action="store_true", help="Skip storing results in Qdrant")

    args = parser.parse_args()

    # Validate skill path
    skill_path = Path(args.skill_path).resolve()
    if not skill_path.is_dir():
        msg = {"status": "error", "message": f"Skill path not found: {skill_path}"}
        print(json.dumps(msg), file=sys.stderr)
        sys.exit(2)

    # Parse criteria
    try:
        criteria = json.loads(args.criteria)
        if not isinstance(criteria, list) or not all(isinstance(c, str) for c in criteria):
            raise ValueError("criteria must be a JSON array of strings")
    except (json.JSONDecodeError, ValueError) as e:
        msg = {"status": "error", "message": f"Invalid --criteria: {e}"}
        print(json.dumps(msg), file=sys.stderr)
        sys.exit(2)

    # Derive skill name from directory or frontmatter
    skill_name = skill_path.name
    has_fm, fm, _ = check_yaml_frontmatter(skill_path)
    if has_fm and fm and fm.get("name"):
        skill_name = fm["name"]

    # Check for historical evaluations (best-effort)
    historical = []
    qdrant_available = True
    try:
        historical = get_historical_evaluations(skill_name)
    except Exception:
        qdrant_available = False

    # Run evaluations
    runs = []
    for i in range(1, args.runs + 1):
        run_result = run_single_evaluation(skill_path, criteria, i)
        runs.append(run_result)

    # Aggregate results
    avg_pass_rate = round(sum(r["pass_rate"] for r in runs) / len(runs), 4)
    total_passed = sum(r["passed"] for r in runs)
    total_criteria = sum(r["total_criteria"] for r in runs)

    # Build historical comparison
    historical_comparison = None
    if historical:
        prev_rate = historical[0].get("pass_rate")
        if prev_rate is not None:
            delta = round(avg_pass_rate - prev_rate, 4)
            historical_comparison = {
                "previous_pass_rate": prev_rate,
                "current_pass_rate": avg_pass_rate,
                "delta": delta,
                "trend": "improved" if delta > 0 else ("declined" if delta < 0 else "stable"),
                "evaluations_found": len(historical),
            }

    timestamp = datetime.now(timezone.utc).isoformat()

    report = {
        "status": "success",
        "skill_name": skill_name,
        "skill_path": str(skill_path),
        "test_input": args.test_input,
        "runs": runs,
        "summary": {
            "total_runs": len(runs),
            "average_pass_rate": avg_pass_rate,
            "total_passed": total_passed,
            "total_criteria_checked": total_criteria,
        },
        "historical_comparison": historical_comparison,
        "timestamp": timestamp,
    }

    # Store in Qdrant
    store_result = None
    if not args.no_store:
        store_content = (
            f"Skill evaluation: {skill_name} | "
            f"pass_rate={avg_pass_rate} | "
            f"criteria={len(criteria)} | "
            f"test_input={args.test_input}"
        )
        store_metadata = {
            "skill_name": skill_name,
            "skill_path": str(skill_path),
            "project": args.project,
            "pass_rate": avg_pass_rate,
            "total_criteria": len(criteria),
            "passed": total_passed // len(runs) if runs else 0,
            "criteria_list": criteria,
            "tags": ["evaluation", "skill", skill_name],
        }
        try:
            store_result = _store_to_qdrant(store_content, store_metadata)
        except Exception as e:
            store_result = {"status": "error", "message": str(e)}
            qdrant_available = False

        report["qdrant_store"] = store_result

    # Output
    if args.json_output:
        print(json.dumps(report, indent=2))
    else:
        # Human-readable output
        all_passed = avg_pass_rate == 1.0
        status_icon = "PASS" if all_passed else "FAIL"
        print(f"\n{'='*60}")
        print(f"  Skill Evaluation: {skill_name}  [{status_icon}]")
        print(f"{'='*60}")
        print(f"  Path:       {skill_path}")
        print(f"  Test Input: {args.test_input}")
        print(f"  Runs:       {len(runs)}")
        print(f"  Pass Rate:  {avg_pass_rate:.0%}")
        print()

        # Show criteria from the first run (deterministic, so all runs match)
        if runs:
            print("  Criteria Results:")
            for cr in runs[0]["criteria_results"]:
                icon = "+" if cr["passed"] else "-"
                detail = f" ({cr['detail']})" if cr.get("detail") else ""
                print(f"    [{icon}] {cr['criterion']}{detail}")
            print()

        # Historical comparison
        if historical_comparison:
            trend = historical_comparison["trend"]
            delta = historical_comparison["delta"]
            sign = "+" if delta > 0 else ""
            print(f"  Historical: {trend} ({sign}{delta:.0%} vs previous)")
            print(f"  Prior evaluations found: {historical_comparison['evaluations_found']}")
            print()

        # Qdrant status
        if not args.no_store:
            if store_result and store_result.get("status") == "stored":
                print(f"  Stored to Qdrant: {store_result['id']}")
            elif not qdrant_available:
                print("  Qdrant: unavailable (results not stored)")
            else:
                print(f"  Qdrant store: {store_result}")

        print(f"{'='*60}\n")

    # Exit code: 0 if all passed, 1 if some failed
    sys.exit(0 if avg_pass_rate == 1.0 else 1)


if __name__ == "__main__":
    main()
