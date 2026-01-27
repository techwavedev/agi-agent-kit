#!/usr/bin/env python3
"""
Script: system_checkup.py
Purpose: Diagnostic tool to verify system health (skills, workflows, scripts, directives).

Usage:
    python3 execution/system_checkup.py [--verbose] [--output <file>]

Arguments:
    --output  Optional path to save JSON report
    --verbose Enable detailed logging

Exit Codes:
    0 - All Checks Passed
    1 - Warnings Found (but functional)
    4 - Critical Errors (Broken system)
"""

import argparse
import json
import sys
import os
import ast
import yaml
from pathlib import Path
from typing import List, Dict, Any

class SystemChecker:
    def __init__(self, root_dir: Path, verbose: bool = False):
        self.root = root_dir
        self.verbose = verbose
        self.report = {
            "status": "pending",
            "summary": {"total": 0, "passed": 0, "warnings": 0, "errors": 0},
            "details": []
        }
        self.has_errors = False

    def log(self, message: str, status: str = "INFO"):
        if self.verbose or status != "INFO":
            print(f"[{status}] {message}", file=sys.stderr)

    def add_result(self, category: str, item: str, status: str, message: str):
        result = {"category": category, "item": str(item), "status": status, "message": message}
        self.report["details"].append(result)
        self.report["summary"]["total"] += 1
        if status == "PASS":
            self.report["summary"]["passed"] += 1
        elif status == "WARNING":
            self.report["summary"]["warnings"] += 1
        elif status == "ERROR":
            self.report["summary"]["errors"] += 1
            self.has_errors = True
        
        icon = "✅" if status == "PASS" else ("⚠️ " if status == "WARNING" else "❌")
        self.log(f"{icon} {category}: {item} - {message}", status)

    def check_python_syntax(self, file_path: Path) -> bool:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                ast.parse(f.read(), filename=str(file_path))
            return True
        except Exception as e:
            return str(e)

    def check_skills(self):
        skills_dir = self.root / "skills"
        if not skills_dir.exists():
             self.add_result("Structure", "skills/", "WARNING", "Skills directory not found")
             return

        for skill_path in skills_dir.iterdir():
            if not skill_path.is_dir():
                continue
            
            skill_name = skill_path.name
            
            # Check SKILL.md
            md_file = skill_path / "SKILL.md"
            if not md_file.exists():
                self.add_result("Skills", skill_name, "ERROR", "Missing SKILL.md")
            else:
                self.add_result("Skills", skill_name, "PASS", "SKILL.md exists")

            # Check scripts
            scripts_dir = skill_path / "scripts"
            if scripts_dir.exists():
                for script in scripts_dir.glob("*.py"):
                    rel_path = script.relative_to(self.root)
                    syntax_check = self.check_python_syntax(script)
                    if syntax_check is True:
                         self.add_result("Scripts", rel_path, "PASS", "Syntax valid")
                    else:
                         self.add_result("Scripts", rel_path, "ERROR", f"Syntax error: {syntax_check}")

    def check_workflows(self):
        workflows_dir = self.root / ".agent" / "workflows"
        if not workflows_dir.exists():
            self.add_result("Structure", ".agent/workflows", "WARNING", "Workflows directory not found")
            return

        for workflow in workflows_dir.glob("*.md"):
             self.add_result("Workflows", workflow.name, "PASS", "Workflow file exists")
             # Could add frontmatter parsing here generally

    def check_execution_scripts(self):
        exec_dir = self.root / "execution"
        if not exec_dir.exists():
            return
        
        for script in exec_dir.glob("*.py"):
            rel_path = script.relative_to(self.root)
            syntax_check = self.check_python_syntax(script)
            if syntax_check is True:
                self.add_result("Execution", rel_path, "PASS", "Syntax valid")
            else:
                self.add_result("Execution", rel_path, "ERROR", f"Syntax error: {syntax_check}")

    def check_directives(self):
        directives_dir = self.root / "directives"
        if directives_dir.exists():
            for directive in directives_dir.glob("*.md"):
                self.add_result("Directives", directive.name, "PASS", "Directive exists")

    def check_core_files(self):
        core_files = ["AGENTS.md", "GEMINI.md", "README.md", "package.json"]
        for filename in core_files:
            file_path = self.root / filename
            if file_path.exists():
                self.add_result("Core Files", filename, "PASS", "File exists")
            else:
                self.add_result("Core Files", filename, "ERROR", "Missing essential file")

    def check_scripts_dir(self):
        scripts_dir = self.root / "scripts"
        if scripts_dir.exists():
            for script in scripts_dir.glob("*.py"):
                rel_path = script.relative_to(self.root)
                syntax_check = self.check_python_syntax(script)
                if syntax_check is True:
                    self.add_result("Scripts (Root)", rel_path, "PASS", "Syntax valid")
                else:
                    self.add_result("Scripts (Root)", rel_path, "ERROR", f"Syntax error: {syntax_check}")

    def run(self):
        self.check_core_files()
        self.check_skills()
        self.check_workflows()
        self.check_execution_scripts()
        self.check_scripts_dir()
        self.check_directives()
        
        if self.has_errors:
            self.report["status"] = "failed"
            return 4
        elif self.report["summary"]["warnings"] > 0:
            self.report["status"] = "warning"
            return 1
        else:
            self.report["status"] = "success"
            return 0

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', help='Output JSON file path')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')
    args = parser.parse_args()

    # Determine root directory (parent of execution dir)
    root_dir = Path(__file__).resolve().parent.parent
    
    checker = SystemChecker(root_dir, args.verbose)
    exit_code = checker.run()

    # Create output if requested
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(checker.report, indent=2))
        print(f"Report saved to {args.output}")

    # Print summary to stdout
    summary = checker.report["summary"]
    print(f"\nSystem Checkup Complete: {checker.report['status'].upper()}")
    print(f"Total: {summary['total']} | Passed: {summary['passed']} | Warnings: {summary['warnings']} | Errors: {summary['errors']}")
    
    sys.exit(exit_code)

if __name__ == '__main__':
    main()
