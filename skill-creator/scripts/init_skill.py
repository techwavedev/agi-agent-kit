#!/usr/bin/env python3
"""
Skill Initializer - Creates a new skill from template

Usage:
    init_skill.py <skill-name> --path <path>

Examples:
    init_skill.py my-new-skill --path skills/public
    init_skill.py my-api-helper --path skills/private
    init_skill.py custom-skill --path /custom/location
"""

import subprocess
import sys
from pathlib import Path

# Path to the templates directory (sibling of scripts/)
_TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"


SKILL_TEMPLATE = """---
name: {skill_name}
description: [TODO: Complete and informative explanation of what the skill does and when to use it. Include WHEN to use this skill - specific scenarios, file types, or tasks that trigger it.]
---

# {skill_title}

## Overview

[TODO: 1-2 sentences explaining what this skill enables]

## Structuring This Skill

[TODO: Choose the structure that best fits this skill's purpose. Common patterns:

**1. Workflow-Based** (best for sequential processes)
- Works well when there are clear step-by-step procedures
- Example: DOCX skill with "Workflow Decision Tree" → "Reading" → "Creating" → "Editing"
- Structure: ## Overview → ## Workflow Decision Tree → ## Step 1 → ## Step 2...

**2. Task-Based** (best for tool collections)
- Works well when the skill offers different operations/capabilities
- Example: PDF skill with "Quick Start" → "Merge PDFs" → "Split PDFs" → "Extract Text"
- Structure: ## Overview → ## Quick Start → ## Task Category 1 → ## Task Category 2...

**3. Reference/Guidelines** (best for standards or specifications)
- Works well for brand guidelines, coding standards, or requirements
- Example: Brand styling with "Brand Guidelines" → "Colors" → "Typography" → "Features"
- Structure: ## Overview → ## Guidelines → ## Specifications → ## Usage...

**4. Capabilities-Based** (best for integrated systems)
- Works well when the skill provides multiple interrelated features
- Example: Product Management with "Core Capabilities" → numbered capability list
- Structure: ## Overview → ## Core Capabilities → ### 1. Feature → ### 2. Feature...

Patterns can be mixed and matched as needed. Most skills combine patterns (e.g., start with task-based, add workflow for complex operations).

Delete this entire "Structuring This Skill" section when done - it's just guidance.]

## [TODO: Replace with the first main section based on chosen structure]

[TODO: Add content here. See examples in existing skills:
- Code samples for technical skills
- Decision trees for complex workflows
- Concrete examples with realistic user requests
- References to scripts/templates/references as needed]

## Resources

This skill includes example resource directories that demonstrate how to organize different types of bundled resources:

### scripts/
Executable code (Python/Bash/etc.) that can be run directly to perform specific operations.

**Examples from other skills:**
- PDF skill: `fill_fillable_fields.py`, `extract_form_field_info.py` - utilities for PDF manipulation
- DOCX skill: `document.py`, `utilities.py` - Python modules for document processing

**Appropriate for:** Python scripts, shell scripts, or any executable code that performs automation, data processing, or specific operations.

**Note:** Scripts may be executed without loading into context, but can still be read by Claude for patching or environment adjustments.

### references/
Documentation and reference material intended to be loaded into context to inform Claude's process and thinking.

**Examples from other skills:**
- Product management: `communication.md`, `context_building.md` - detailed workflow guides
- BigQuery: API reference documentation and query examples
- Finance: Schema documentation, company policies

**Appropriate for:** In-depth documentation, API references, database schemas, comprehensive guides, or any detailed information that Claude should reference while working.

### assets/
Files not intended to be loaded into context, but rather used within the output Claude produces.

**Examples from other skills:**
- Brand styling: PowerPoint template files (.pptx), logo files
- Frontend builder: HTML/React boilerplate project directories
- Typography: Font files (.ttf, .woff2)

**Appropriate for:** Templates, boilerplate code, document templates, images, icons, fonts, or any files meant to be copied or used in the final output.

---

### eval/
Binary assertion tests for autonomous self-improvement (Karpathy Loop).

Contains an `evals.json` file with objective true/false test cases that validate the skill's SKILL.md structure and quality.

**When to use:** Run `python3 execution/run_skill_eval.py --evals eval/evals.json` to validate, or use `python3 execution/karpathy_loop.py --skill .` for autonomous improvement.

**Any unneeded directories can be deleted.** Not every skill requires all three types of resources.
"""

EXAMPLE_SCRIPT = '''#!/usr/bin/env python3
"""
Example helper script for {skill_name}

This is a placeholder script that can be executed directly.
Replace with actual implementation or delete if not needed.

Example real scripts from other skills:
- pdf/scripts/fill_fillable_fields.py - Fills PDF form fields
- pdf/scripts/convert_pdf_to_images.py - Converts PDF pages to images
"""

def main():
    print("This is an example script for {skill_name}")
    # TODO: Add actual script logic here
    # This could be data processing, file conversion, API calls, etc.

if __name__ == "__main__":
    main()
'''

EXAMPLE_REFERENCE = """# Reference Documentation for {skill_title}

This is a placeholder for detailed reference documentation.
Replace with actual reference content or delete if not needed.

Example real reference docs from other skills:
- product-management/references/communication.md - Comprehensive guide for status updates
- product-management/references/context_building.md - Deep-dive on gathering context
- bigquery/references/ - API references and query examples

## When Reference Docs Are Useful

Reference docs are ideal for:
- Comprehensive API documentation
- Detailed workflow guides
- Complex multi-step processes
- Information too lengthy for main SKILL.md
- Content that's only needed for specific use cases

## Structure Suggestions

### API Reference Example
- Overview
- Authentication
- Endpoints with examples
- Error codes
- Rate limits

### Workflow Guide Example
- Prerequisites
- Step-by-step instructions
- Common patterns
- Troubleshooting
- Best practices
"""

EXAMPLE_ASSET = """# Example Asset File

This placeholder represents where asset files would be stored.
Replace with actual asset files (templates, images, fonts, etc.) or delete if not needed.

Asset files are NOT intended to be loaded into context, but rather used within
the output Claude produces.

Example asset files from other skills:
- Brand guidelines: logo.png, slides_template.pptx
- Frontend builder: hello-world/ directory with HTML/React boilerplate
- Typography: custom-font.ttf, font-family.woff2
- Data: sample_data.csv, test_dataset.json

## Common Asset Types

- Templates: .pptx, .docx, boilerplate directories
- Images: .png, .jpg, .svg, .gif
- Fonts: .ttf, .otf, .woff, .woff2
- Boilerplate code: Project directories, starter files
- Icons: .ico, .svg
- Data files: .csv, .json, .xml, .yaml

Note: This is a text placeholder. Actual assets can be any file type.
"""

EVALS_TEMPLATE = """{
  "skill": "__SKILL_NAME__",
  "version": "1.0.0",
  "description": "Binary assertions for __SKILL_TITLE__ skill quality",
  "evaluations": [
    {
      "name": "frontmatter-valid",
      "description": "SKILL.md has proper YAML frontmatter with name and description",
      "input_file": "../SKILL.md",
      "assertions": [
        {"type": "has_yaml_frontmatter", "value": true},
        {"type": "contains", "value": "name:"},
        {"type": "contains", "value": "description:"}
      ]
    },
    {
      "name": "description-quality",
      "description": "Description is comprehensive (not a placeholder)",
      "input_file": "../SKILL.md",
      "assertions": [
        {"type": "not_contains", "value": "[TODO:"},
        {"type": "min_chars", "value": 200},
        {"type": "min_words", "value": 30}
      ]
    },
    {
      "name": "structure-complete",
      "description": "SKILL.md has overview and proper heading structure",
      "input_file": "../SKILL.md",
      "assertions": [
        {"type": "regex_match", "pattern": "^# "},
        {"type": "regex_match", "pattern": "^## "},
        {"type": "no_consecutive_blank_lines", "value": true}
      ]
    },
    {
      "name": "no-placeholder-content",
      "description": "No leftover placeholder text from template",
      "input_file": "../SKILL.md",
      "assertions": [
        {"type": "not_contains", "value": "[TODO:"},
        {"type": "not_contains", "value": "Replace with"},
        {"type": "not_contains", "value": "Delete this entire"}
      ]
    }
  ]
}"""


def title_case_skill_name(skill_name):
    """Convert hyphenated skill name to Title Case for display."""
    return ' '.join(word.capitalize() for word in skill_name.split('-'))


def init_skill(skill_name, path):
    """
    Initialize a new skill directory with template SKILL.md.

    Args:
        skill_name: Name of the skill
        path: Path where the skill directory should be created

    Returns:
        Path to created skill directory, or None if error
    """
    # Determine skill directory path
    skill_dir = Path(path).resolve() / skill_name

    # Check if directory already exists
    if skill_dir.exists():
        print(f"❌ Error: Skill directory already exists: {skill_dir}")
        return None

    # Create skill directory
    try:
        skill_dir.mkdir(parents=True, exist_ok=False)
        print(f"✅ Created skill directory: {skill_dir}")
    except Exception as e:
        print(f"❌ Error creating directory: {e}")
        return None

    # Create SKILL.md from template
    skill_title = title_case_skill_name(skill_name)
    skill_content = SKILL_TEMPLATE.format(
        skill_name=skill_name,
        skill_title=skill_title
    )

    skill_md_path = skill_dir / 'SKILL.md'
    try:
        skill_md_path.write_text(skill_content)
        print("✅ Created SKILL.md")
    except Exception as e:
        print(f"❌ Error creating SKILL.md: {e}")
        return None

    # Create resource directories with example files
    try:
        # Create scripts/ directory with example script
        scripts_dir = skill_dir / 'scripts'
        scripts_dir.mkdir(exist_ok=True)
        example_script = scripts_dir / 'example.py'
        example_script.write_text(EXAMPLE_SCRIPT.format(skill_name=skill_name))
        example_script.chmod(0o755)
        print("✅ Created scripts/example.py")

        # Create references/ directory with example reference doc
        references_dir = skill_dir / 'references'
        references_dir.mkdir(exist_ok=True)
        example_reference = references_dir / 'api_reference.md'
        example_reference.write_text(EXAMPLE_REFERENCE.format(skill_title=skill_title))
        print("✅ Created references/api_reference.md")

        # Create assets/ directory with example asset placeholder
        assets_dir = skill_dir / 'assets'
        assets_dir.mkdir(exist_ok=True)
        example_asset = assets_dir / 'example_asset.txt'
        example_asset.write_text(EXAMPLE_ASSET)
        print("✅ Created assets/example_asset.txt")

        # Create eval/ directory with evals.json template
        eval_dir = skill_dir / 'eval'
        eval_dir.mkdir(exist_ok=True)
        evals_json = eval_dir / 'evals.json'
        evals_content = (EVALS_TEMPLATE
                         .replace("__SKILL_NAME__", skill_name)
                         .replace("__SKILL_TITLE__", title_case_skill_name(skill_name)))
        evals_json.write_text(evals_content)
        print("✅ Created eval/evals.json")
    except Exception as e:
        print(f"❌ Error creating resource directories: {e}")
        return None

    # Create optional MCP server files (additive — skipped if templates missing)
    mcp_template = _TEMPLATES_DIR / "mcp_server_template.py"
    mcp_tools_template = _TEMPLATES_DIR / "mcp_tools_template.json"

    if mcp_template.exists():
        try:
            mcp_server_content = mcp_template.read_text().replace("__SKILL_NAME__", skill_name)
            mcp_server_path = skill_dir / "mcp_server.py"
            mcp_server_path.write_text(mcp_server_content)
            mcp_server_path.chmod(0o755)
            print("✅ Created mcp_server.py")
        except Exception as e:
            print(f"  ⚠️  Could not create mcp_server.py: {e}")

    if mcp_tools_template.exists():
        try:
            mcp_tools_path = skill_dir / "mcp_tools.json"
            mcp_tools_path.write_text(mcp_tools_template.read_text())
            print("✅ Created mcp_tools.json")
        except Exception as e:
            print(f"  ⚠️  Could not create mcp_tools.json: {e}")

    # Print next steps
    print(f"\n✅ Skill '{skill_name}' initialized successfully at {skill_dir}")
    print("\nNext steps:")
    print("1. Edit SKILL.md to complete the TODO items and update the description")
    print("2. Customize or delete the example files in scripts/, references/, and assets/")
    print("3. Fill in mcp_server.py + mcp_tools.json to expose tools via MCP (optional)")
    print("4. Run the validator when ready to check the skill structure")

    return skill_dir


def auto_update_catalog(skills_dir: Path) -> bool:
    """
    Auto-run update_catalog.py after skill creation.
    
    Args:
        skills_dir: Path to the skills directory
    
    Returns:
        True if successful, False otherwise
    """
    # Locate update_catalog.py relative to this script
    script_dir = Path(__file__).resolve().parent
    catalog_script = script_dir / "update_catalog.py"
    
    if not catalog_script.exists():
        print(f"  ⚠️  Could not find update_catalog.py at {catalog_script}")
        return False
    
    print(f"\n📚 Auto-updating skills catalog...")
    try:
        result = subprocess.run(
            [sys.executable, str(catalog_script), "--skills-dir", str(skills_dir)],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            print("✅ Skills catalog updated automatically")
            return True
        else:
            print(f"  ⚠️  Catalog update returned non-zero: {result.stderr.strip()}")
            return False
    except subprocess.TimeoutExpired:
        print("  ⚠️  Catalog update timed out (30s)")
        return False
    except Exception as e:
        print(f"  ⚠️  Catalog update failed: {e}")
        return False


def auto_update_docs(skills_dir: Path, skill_name: str) -> bool:
    """
    Auto-run documentation sync after skill creation.
    
    Args:
        skills_dir: Path to the skills directory
        skill_name: Name of the skill to update docs for
    
    Returns:
        True if successful, False otherwise
    """
    # Locate sync_docs.py in the documentation skill
    sync_script = skills_dir / "documentation" / "scripts" / "sync_docs.py"
    
    if not sync_script.exists():
        # Documentation skill not installed — silently skip
        return False
    
    print(f"\n📝 Auto-updating documentation...")
    try:
        result = subprocess.run(
            [
                sys.executable, str(sync_script),
                "--skills-dir", str(skills_dir),
                "--update-catalog", "true",
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode == 0:
            print("✅ Documentation updated automatically")
            return True
        else:
            # sync_docs may not exist or have issues — non-fatal
            print(f"  ⚠️  Documentation sync skipped: {result.stderr.strip()[:200]}")
            return False
    except subprocess.TimeoutExpired:
        print("  ⚠️  Documentation sync timed out (60s)")
        return False
    except Exception as e:
        print(f"  ⚠️  Documentation sync skipped: {e}")
        return False


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Initialize a new skill from template with auto-update of catalog and docs.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  init_skill.py my-new-skill --path skills/
  init_skill.py my-api-helper --path skills/ --no-auto-update
  init_skill.py custom-skill --path /custom/location --skills-dir skills/

Skill name requirements:
  - Hyphen-case identifier (e.g., 'data-analyzer')
  - Lowercase letters, digits, and hyphens only
  - Max 40 characters
  - Must match directory name exactly
""",
    )
    parser.add_argument("skill_name", help="Name of the skill to create")
    parser.add_argument("--path", required=True, help="Directory where skill folder will be created")
    parser.add_argument(
        "--no-auto-update",
        action="store_true",
        default=False,
        help="Skip automatic catalog and documentation updates (default: auto-update ON)",
    )
    parser.add_argument(
        "--skills-dir",
        default=None,
        help="Skills directory for catalog/docs update (default: same as --path)",
    )

    # Support legacy positional format: init_skill.py <name> --path <path>
    args = parser.parse_args()

    skill_name = args.skill_name
    path = args.path
    skills_dir = Path(args.skills_dir or path).resolve()

    print(f"🚀 Initializing skill: {skill_name}")
    print(f"   Location: {path}")
    print()

    result = init_skill(skill_name, path)

    if not result:
        sys.exit(1)

    # Auto-update catalog and documentation (unless explicitly disabled)
    if not args.no_auto_update:
        auto_update_catalog(skills_dir)
        auto_update_docs(skills_dir, skill_name)
    else:
        print("\n⏭️  Auto-update skipped (--no-auto-update)")
        print(f"   Manual update: python skill-creator/scripts/update_catalog.py --skills-dir {skills_dir}")

    print(f"\n🎉 Done! Skill '{skill_name}' is ready for development.")
    sys.exit(0)


if __name__ == "__main__":
    main()
