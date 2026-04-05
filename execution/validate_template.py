#!/usr/bin/env python3
"""
Script: validate_template.py
Purpose: Validate templates/base/ integrity — ensures the public NPM scaffold
         is complete, consistent, and ready for publishing.

Usage:
    python3 execution/validate_template.py                 # Full validation
    python3 execution/validate_template.py --check-scripts # Scripts only
    python3 execution/validate_template.py --check-skills  # Core skills only
    python3 execution/validate_template.py --json          # JSON output

Exit Codes:
    0 - All validations pass
    1 - Validation failures found
    2 - Template directory not found
"""

import argparse
import ast
import json
import os
import sys
from pathlib import Path

PROJECT_DIR = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TEMPLATE_DIR = PROJECT_DIR / "templates" / "base"
SKILLS_DIR = PROJECT_DIR / "templates" / "skills"

# ──────────────────────────────────────────────
# Required structure
# ──────────────────────────────────────────────

REQUIRED_FILES = [
    "AGENTS.md",
    "README.md",
    "CHANGELOG.md",
    "requirements.txt",
    ".env.example",
    ".gitignore",
    "data/workflows.json",
    "knowledge/core.md",
]

REQUIRED_DIRS = [
    "execution",
    "directives",
    "directives/subagents",
    "directives/teams",
    ".agent/rules",
    ".agent/workflows",
    "skill-creator",
    "skill-creator/scripts",
    "data",
    "docs",
    "knowledge",
]

REQUIRED_SCRIPTS = [
    "execution/session_boot.py",
    "execution/session_init.py",
    "execution/memory_manager.py",
    "execution/memory_usage_proof.py",
    "execution/dispatch_agent_team.py",
    "execution/agent_team_result.py",
    "execution/cross_agent_context.py",
    "execution/run_test_scenario.py",
    "execution/benchmark_modes.py",
]

REQUIRED_DIRECTIVES = [
    "directives/memory_integration.md",
    "directives/release_process.md",
    "directives/subagents/doc_writer.md",
    "directives/subagents/doc_reviewer.md",
    "directives/subagents/changelog_updater.md",
    "directives/subagents/spec_reviewer.md",
    "directives/subagents/quality_reviewer.md",
    "directives/subagents/test_generator.md",
    "directives/subagents/test_verifier.md",
    "directives/teams/documentation_team.md",
    "directives/teams/code_review_team.md",
    "directives/teams/qa_team.md",
    "directives/teams/build_deploy_team.md",
]

CORE_SKILLS = ["qdrant-memory", "documentation", "pdf-reader", "webcrawler"]

# Files that should NEVER exist in the template
FORBIDDEN_FILES = [
    "execution/sync_to_template.py",
    "execution/validate_template.py",
    "directives/framework_development.md",
    "directives/template_sync.md",
    "directives/skill_development.md",
    ".agent/rules/framework_dev_rules.md",
    ".agent/rules/versioning_rules.md",
    ".agent/scripts/release_gate.py",
    ".env",
    "token.json",
    "credentials.json",
]


def validate_structure() -> list:
    """Validate template directory structure."""
    issues = []

    if not TEMPLATE_DIR.exists():
        return [{"severity": "critical", "check": "structure", "message": "templates/base/ directory not found"}]

    for f in REQUIRED_FILES:
        path = TEMPLATE_DIR / f
        if not path.exists():
            issues.append({"severity": "error", "check": "structure", "file": f, "message": f"Missing required file: {f}"})
        elif path.stat().st_size == 0:
            issues.append({"severity": "warning", "check": "structure", "file": f, "message": f"File is empty: {f}"})

    for d in REQUIRED_DIRS:
        path = TEMPLATE_DIR / d
        if not path.exists():
            issues.append({"severity": "error", "check": "structure", "dir": d, "message": f"Missing required directory: {d}"})

    return issues


def validate_scripts() -> list:
    """Validate all required execution scripts exist and have valid Python syntax."""
    issues = []

    for script in REQUIRED_SCRIPTS:
        path = TEMPLATE_DIR / script
        if not path.exists():
            issues.append({"severity": "error", "check": "scripts", "file": script, "message": f"Missing: {script}"})
            continue

        # Check syntax
        try:
            source = path.read_text(encoding="utf-8")
            ast.parse(source, filename=script)
        except SyntaxError as e:
            issues.append({
                "severity": "error",
                "check": "scripts",
                "file": script,
                "message": f"Syntax error at line {e.lineno}: {e.msg}"
            })

        # Check has docstring
        if not source.strip().startswith('#!/usr/bin/env python3'):
            issues.append({"severity": "warning", "check": "scripts", "file": script, "message": "Missing shebang line"})

    return issues


def validate_directives() -> list:
    """Validate all required directives exist and are non-empty."""
    issues = []

    for directive in REQUIRED_DIRECTIVES:
        path = TEMPLATE_DIR / directive
        if not path.exists():
            issues.append({"severity": "error", "check": "directives", "file": directive, "message": f"Missing: {directive}"})
        elif path.stat().st_size < 50:
            issues.append({"severity": "warning", "check": "directives", "file": directive, "message": f"Suspiciously small (<50 bytes): {directive}"})

    return issues


def validate_skills() -> list:
    """Validate core skills are present and properly structured."""
    issues = []

    for skill_name in CORE_SKILLS:
        skill_dir = SKILLS_DIR / "core" / skill_name
        if not skill_dir.exists():
            issues.append({"severity": "error", "check": "skills", "skill": skill_name, "message": f"Missing core skill: {skill_name}"})
            continue

        # Check SKILL.md exists
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.exists():
            issues.append({"severity": "error", "check": "skills", "skill": skill_name, "message": f"Missing SKILL.md in {skill_name}"})
        else:
            content = skill_md.read_text(encoding="utf-8")
            if "---" not in content:
                issues.append({"severity": "warning", "check": "skills", "skill": skill_name, "message": f"SKILL.md missing frontmatter in {skill_name}"})

        # Check scripts dir exists
        scripts_dir = skill_dir / "scripts"
        if not scripts_dir.exists():
            issues.append({"severity": "warning", "check": "skills", "skill": skill_name, "message": f"Missing scripts/ in {skill_name}"})
        elif not list(scripts_dir.glob("*.py")):
            issues.append({"severity": "warning", "check": "skills", "skill": skill_name, "message": f"No Python scripts in {skill_name}/scripts/"})

    return issues


def validate_forbidden() -> list:
    """Ensure private files haven't leaked into template."""
    issues = []

    for f in FORBIDDEN_FILES:
        path = TEMPLATE_DIR / f
        if path.exists():
            issues.append({
                "severity": "critical",
                "check": "forbidden",
                "file": f,
                "message": f"PRIVATE FILE LEAKED to template: {f}"
            })

    return issues


def validate_agents_md() -> list:
    """Validate AGENTS.md consistency between root and template."""
    issues = []
    root_agents = PROJECT_DIR / "AGENTS.md"
    tmpl_agents = TEMPLATE_DIR / "AGENTS.md"

    if not root_agents.exists() or not tmpl_agents.exists():
        issues.append({"severity": "error", "check": "agents_md", "message": "AGENTS.md missing from root or template"})
        return issues

    root_content = root_agents.read_text(encoding="utf-8")
    tmpl_content = tmpl_agents.read_text(encoding="utf-8")

    if root_content != tmpl_content:
        # Count differing lines
        root_lines = root_content.splitlines()
        tmpl_lines = tmpl_content.splitlines()
        diff_count = sum(1 for a, b in zip(root_lines, tmpl_lines) if a != b)
        diff_count += abs(len(root_lines) - len(tmpl_lines))
        issues.append({
            "severity": "error",
            "check": "agents_md",
            "message": f"AGENTS.md drift: {diff_count} lines differ between root and template"
        })

    return issues


def main():
    parser = argparse.ArgumentParser(description="Validate template integrity")
    parser.add_argument("--check-scripts", action="store_true", help="Only validate scripts")
    parser.add_argument("--check-skills", action="store_true", help="Only validate core skills")
    parser.add_argument("--json", action="store_true", help="JSON-only output")
    args = parser.parse_args()

    if not TEMPLATE_DIR.exists():
        print(json.dumps({"status": "error", "message": "templates/base/ not found"}))
        sys.exit(2)

    # Run selected or all checks
    all_issues = []

    if args.check_scripts:
        all_issues.extend(validate_scripts())
    elif args.check_skills:
        all_issues.extend(validate_skills())
    else:
        all_issues.extend(validate_structure())
        all_issues.extend(validate_scripts())
        all_issues.extend(validate_directives())
        all_issues.extend(validate_skills())
        all_issues.extend(validate_forbidden())
        all_issues.extend(validate_agents_md())

    # Summarize
    critical = [i for i in all_issues if i["severity"] == "critical"]
    errors = [i for i in all_issues if i["severity"] == "error"]
    warnings = [i for i in all_issues if i["severity"] == "warning"]

    report = {
        "status": "fail" if critical or errors else "pass",
        "critical": len(critical),
        "errors": len(errors),
        "warnings": len(warnings),
        "issues": all_issues,
    }

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(f"\n🔍 Template Validation Report")
        print(f"   Status:   {'❌ FAIL' if report['status'] == 'fail' else '✅ PASS'}")
        print(f"   Critical: {len(critical)}")
        print(f"   Errors:   {len(errors)}")
        print(f"   Warnings: {len(warnings)}")

        if all_issues:
            print()
            for issue in all_issues:
                icon = {"critical": "🔴", "error": "🟠", "warning": "🟡"}[issue["severity"]]
                print(f"   {icon} [{issue['check']}] {issue['message']}")

        if report["status"] == "pass":
            print(f"\n✅ Template is valid and ready for publishing.")
        else:
            print(f"\n❌ Fix the above issues before publishing.")

    sys.exit(0 if report["status"] == "pass" else 1)


if __name__ == "__main__":
    main()
