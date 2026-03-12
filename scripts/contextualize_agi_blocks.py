#!/usr/bin/env python3
"""
Script: contextualize_agi_blocks.py
Purpose: Replace generic copy-paste AGI integration blocks with contextual,
         domain-specific blocks that demonstrate real framework integration.

Each block is tailored to the skill's name, description, and category —
showing concrete examples of how that specific skill benefits from:
  - Semantic Cache (avoid re-doing expensive work)
  - Hybrid Memory (Qdrant vectors + BM25 keywords)
  - Agent Teams (documentation, code review, QA)
  - Cross-Agent Collaboration (multi-LLM context sharing)
  - Control Tower (task tracking across agents)
  - Blockchain Identity (signed audit trails)
  - Playbook Engine (multi-skill sequences)
  - Self-Annealing (error → fix → learn cycle)

Usage:
    python3 scripts/contextualize_agi_blocks.py --skills-dir templates/skills/extended/
    python3 scripts/contextualize_agi_blocks.py --skills-dir templates/skills/extended/ --dry-run
    python3 scripts/contextualize_agi_blocks.py --file templates/skills/extended/security/aws-compliance-checker/SKILL.md

Exit Codes:
    0 - Success
    1 - Invalid arguments
    2 - Processing error
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

AGI_START = "<!-- AGI-INTEGRATION-START -->"
AGI_END = "<!-- AGI-INTEGRATION-END -->"

# Category-to-domain mapping for contextual examples
CATEGORY_CONTEXTS = {
    "security": {
        "domain": "security",
        "cache_query": "prior security audit results for {name}",
        "store_type": "technical",
        "store_example": "Audit findings: 3 critical IAM misconfigurations found and remediated",
        "team_action": "Completed security audit — 3 critical findings fixed, compliance score 94%",
        "memory_benefit": "Cache compliance check results to avoid re-running expensive AWS API calls. Retrieve prior audit findings to track remediation progress across sessions.",
        "cross_agent": "Share security findings with other agents so they avoid introducing vulnerabilities in their code changes.",
        "extra_features": [
            ("Signed Audit Trail", "All security findings are cryptographically signed with the agent's Ed25519 identity, providing tamper-proof audit logs for compliance reporting."),
            ("Semantic Cache for Compliance", "Cache compliance check results (`semantic_cache.py`) to avoid redundant AWS API calls. Cache hit at similarity >0.92 returns prior results instantly."),
        ],
    },
    "devops": {
        "domain": "infrastructure",
        "cache_query": "deployment configuration and patterns for {name}",
        "store_type": "technical",
        "store_example": "Deployment pipeline: configured blue-green deployment with health checks on port 8080",
        "team_action": "Deployed infrastructure changes — updated CI/CD pipeline with new health check endpoints",
        "memory_benefit": "Retrieve prior deployment configurations, rollback procedures, and incident post-mortems. Avoid re-discovering infrastructure patterns.",
        "cross_agent": "Broadcast deployment changes so frontend and backend agents update their configurations accordingly.",
        "extra_features": [
            ("Playbook Integration", "Use the `ship-saas-mvp` or `full-stack-deploy` playbook to sequence this skill with testing, documentation, and deployment verification."),
        ],
    },
    "frontend": {
        "domain": "frontend/design",
        "cache_query": "design system decisions and component patterns for {name}",
        "store_type": "decision",
        "store_example": "Design system: adopted 8px grid, Inter font family, HSL color tokens with dark mode support",
        "team_action": "Implemented UI components — new design system with accessibility compliance (WCAG 2.1 AA)",
        "memory_benefit": "Retrieve prior design decisions (color palettes, typography, spacing scales) to maintain visual consistency across sessions. Cache generated design tokens.",
        "cross_agent": "Share design decisions with backend agents (API contract changes) and QA agents (visual regression baselines).",
        "extra_features": [
            ("Design Memory Persistence", "Store design system tokens and component decisions in Qdrant so any agent on any platform (Claude, Gemini, Cursor) can retrieve and apply consistent styling."),
        ],
    },
    "backend": {
        "domain": "backend/API",
        "cache_query": "API design patterns and architecture decisions for {name}",
        "store_type": "decision",
        "store_example": "API architecture: REST with HATEOAS, JWT auth, rate limiting at 100 req/min per tenant",
        "team_action": "Implemented API endpoints — 5 new routes with OpenAPI spec and integration tests",
        "memory_benefit": "Retrieve prior API design decisions, database schema choices, and error handling patterns. Cache API response templates for consistent error formatting.",
        "cross_agent": "Share API contract changes with frontend agents so they update their client code, and with QA agents for test coverage.",
        "extra_features": [
            ("Agent Team: Code Review", "After implementation, dispatch `code_review_team` for two-stage review (spec compliance + code quality) before merging."),
        ],
    },
    "testing": {
        "domain": "testing/QA",
        "cache_query": "test patterns and coverage strategies for {name}",
        "store_type": "technical",
        "store_example": "Testing strategy: integration tests hit real DB (no mocks), 85% line coverage, mutation testing on critical paths",
        "team_action": "QA complete — test suite expanded with 12 new integration tests, all passing",
        "memory_benefit": "Retrieve prior test strategies, known flaky tests, and coverage gaps. Cache test infrastructure setup to avoid re-configuring test environments.",
        "cross_agent": "Share test results and coverage reports with code review agents so they can verify adequate coverage on changed code.",
        "extra_features": [
            ("TDD Enforcement", "This skill integrates with the framework's iron-law RED-GREEN-REFACTOR cycle. No production code without a failing test first."),
            ("Agent Team: QA", "Dispatch `qa_team` to generate tests and verify they pass before marking implementation complete."),
        ],
    },
    "debugging": {
        "domain": "debugging/diagnostics",
        "cache_query": "error patterns and debugging solutions for {name}",
        "store_type": "error",
        "store_example": "Root cause: memory leak from unclosed DB connections in pool — fixed with context manager",
        "team_action": "Debugged and resolved critical issue — root cause documented for future reference",
        "memory_benefit": "Retrieve prior error resolutions and debugging strategies. The hybrid search excels here — BM25 finds exact error codes/stack traces while vectors find semantically similar past issues.",
        "cross_agent": "Store error resolutions so any agent encountering the same issue retrieves the fix instantly instead of re-debugging.",
        "extra_features": [
            ("Self-Annealing Loop", "When this skill resolves an error, store the fix in memory AND update the relevant directive. The system gets stronger with each resolved issue."),
            ("BM25 Exact Match", "Error codes, stack traces, and log messages are best found via BM25 keyword search. The hybrid system automatically uses exact matching for these patterns."),
        ],
    },
    "architecture": {
        "domain": "architecture/design",
        "cache_query": "architecture decisions and trade-off analysis for {name}",
        "store_type": "decision",
        "store_example": "Architecture: event-driven microservices with CQRS, Pulsar for messaging, Qdrant for semantic search",
        "team_action": "Completed architecture review — ADR documented, trade-offs analyzed, team aligned",
        "memory_benefit": "Retrieve prior Architecture Decision Records (ADRs), trade-off analyses, and system design rationale. Critical for maintaining consistency across long-running projects.",
        "cross_agent": "Broadcast architecture decisions to ALL agents so implementation stays aligned with the chosen patterns.",
        "extra_features": [
            ("Control Tower Coordination", "Register architecture tasks in the Control Tower so all agents across machines know the current system design and constraints."),
        ],
    },
    "documentation": {
        "domain": "documentation",
        "cache_query": "documentation patterns and prior content for {name}",
        "store_type": "technical",
        "store_example": "Documentation: API reference generated from OpenAPI spec, deployment guide updated with new env vars",
        "team_action": "Documentation updated — API reference, deployment guide, and CHANGELOG all current",
        "memory_benefit": "Retrieve prior documentation structure and content to maintain consistency. Cache generated docs to avoid regenerating unchanged sections.",
        "cross_agent": "Share documentation changes with all agents so they reference the latest guides and APIs.",
        "extra_features": [
            ("Agent Team: Documentation", "This skill pairs with `documentation_team` — dispatched automatically after any code change to keep docs in sync."),
        ],
    },
    "workflow": {
        "domain": "workflow/automation",
        "cache_query": "automation patterns and workflow configurations for {name}",
        "store_type": "technical",
        "store_example": "Workflow: automated data pipeline with retry logic, dead-letter queue, and Slack alerts on failure",
        "team_action": "Workflow automation deployed — pipeline processing 1000+ events/day with 99.9% success rate",
        "memory_benefit": "Cache workflow configurations and automation patterns. Retrieve prior pipeline designs to avoid re-building similar flows from scratch.",
        "cross_agent": "Share workflow state with other agents so they can trigger, monitor, or extend the automation.",
        "extra_features": [
            ("Playbook Engine", "Combine this skill with others using the Playbook Engine (`execution/workflow_engine.py`) for guided multi-step automation with progress tracking."),
        ],
    },
    "ai-agents": {
        "domain": "AI agent orchestration",
        "cache_query": "agent patterns and orchestration strategies for {name}",
        "store_type": "decision",
        "store_example": "Agent pattern: hierarchical orchestration with Control Tower dispatcher, 3 specialist sub-agents",
        "team_action": "Agent architecture designed — Control Tower + specialist agents with shared Qdrant memory",
        "memory_benefit": "Retrieve prior agent configurations, team compositions, and orchestration patterns. Critical for multi-agent system consistency.",
        "cross_agent": "This skill is inherently multi-agent. Use cross-agent context to coordinate task distribution and avoid duplicate work.",
        "extra_features": [
            ("Control Tower Integration", "Register agents and tasks with the Control Tower (`execution/control_tower.py`) for centralized orchestration across machines and LLM providers."),
            ("Blockchain Identity", "Each agent has a cryptographic Ed25519 identity. All memory writes are signed — enabling trust verification in multi-agent systems."),
        ],
    },
    "data": {
        "domain": "data engineering",
        "cache_query": "data processing patterns and pipeline configurations for {name}",
        "store_type": "technical",
        "store_example": "Data pipeline: ETL from PostgreSQL to Qdrant, 50K records/batch, incremental sync via updated_at",
        "team_action": "Data pipeline implemented — ETL processing with validation, deduplication, and error recovery",
        "memory_benefit": "Cache data schemas, transformation rules, and query patterns. BM25 excels at finding specific column names, table references, and SQL patterns.",
        "cross_agent": "Share data schema changes with backend and frontend agents so they update their models accordingly.",
        "extra_features": [],
    },
    "content": {
        "domain": "content creation",
        "cache_query": "content patterns and brand voice guidelines for {name}",
        "store_type": "decision",
        "store_example": "Content: brand voice established — professional but approachable, 8th-grade reading level, active voice",
        "team_action": "Content created and reviewed — matches brand guidelines, SEO-optimized, A/B test variant prepared",
        "memory_benefit": "Retrieve brand voice guidelines, content templates, and prior successful content patterns. Cache editorial decisions for consistency across sessions.",
        "cross_agent": "Share content guidelines with design agents (visual alignment) and development agents (copy integration).",
        "extra_features": [],
    },
    "mobile": {
        "domain": "mobile development",
        "cache_query": "mobile architecture and platform-specific patterns for {name}",
        "store_type": "decision",
        "store_example": "Mobile: React Native with Expo, offline-first with SQLite sync, push notifications via FCM",
        "team_action": "Mobile feature implemented — cross-platform component with native performance optimizations",
        "memory_benefit": "Retrieve platform-specific patterns (iOS/Android), build configurations, and device compatibility notes from prior sessions.",
        "cross_agent": "Share API contract changes with backend agents and coordinate release timing with QA agents.",
        "extra_features": [],
    },
    "blockchain": {
        "domain": "blockchain/Web3",
        "cache_query": "smart contract patterns and blockchain architecture for {name}",
        "store_type": "technical",
        "store_example": "Smart contract: ERC-721 with royalty enforcement, gas-optimized batch minting, OpenZeppelin base",
        "team_action": "Smart contract deployed — audit findings addressed, gas benchmarks documented",
        "memory_benefit": "Retrieve prior smart contract patterns, gas optimization techniques, and audit findings. Cache ABI definitions and deployment addresses.",
        "cross_agent": "Share contract ABIs and deployment addresses with frontend agents for DApp integration.",
        "extra_features": [
            ("Blockchain Trust Layer", "The framework's own blockchain identity system (Ed25519 + MultiChain anchoring) uses similar cryptographic patterns — apply learnings bidirectionally."),
        ],
    },
    "gaming": {
        "domain": "game development",
        "cache_query": "game architecture and engine patterns for {name}",
        "store_type": "technical",
        "store_example": "Game: ECS architecture with 60fps target, spatial partitioning for collision, asset pipeline with LOD",
        "team_action": "Game feature implemented — performance profiled, asset pipeline updated, QA test plan created",
        "memory_benefit": "Retrieve game design decisions, performance benchmarks, and engine configuration. Cache asset pipeline settings and build configurations.",
        "cross_agent": "Share engine decisions and performance budgets with art/design agents and QA agents.",
        "extra_features": [],
    },
}

# Default context for uncategorized skills
DEFAULT_CONTEXT = {
    "domain": "development",
    "cache_query": "prior work and patterns related to {name}",
    "store_type": "decision",
    "store_example": "Completed task with key insights documented for future reference",
    "team_action": "Task completed — results documented and shared with team",
    "memory_benefit": "Retrieve prior decisions and patterns to avoid re-discovering solutions. Cache results for instant retrieval in future sessions.",
    "cross_agent": "Share outcomes with other agents so the team stays aligned and avoids duplicate work.",
    "extra_features": [],
}


def parse_frontmatter(content: str) -> dict:
    """Extract name, description, category from YAML frontmatter."""
    result = {"name": "", "description": "", "category": ""}
    if not content.startswith("---"):
        return result
    parts = content.split("---", 2)
    if len(parts) < 3:
        return result
    for line in parts[1].strip().split("\n"):
        if ":" in line:
            key, value = line.split(":", 1)
            key = key.strip().lower()
            value = value.strip().strip("\"'")
            if key in result:
                result[key] = value
    return result


def detect_category(filepath: Path, meta: dict) -> str:
    """Detect category from path or frontmatter."""
    if meta.get("category"):
        cat = meta["category"].lower()
        # Normalize known categories
        for key in CATEGORY_CONTEXTS:
            if key in cat:
                return key
        # Common aliases
        aliases = {
            "spreadsheet": "data", "database": "data", "analytics": "data",
            "web": "frontend", "ui": "frontend", "design": "frontend",
            "api": "backend", "server": "backend", "microservice": "backend",
            "ci-cd": "devops", "deployment": "devops", "cloud": "devops",
            "monitoring": "devops", "container": "devops",
            "test": "testing", "qa": "testing",
            "debug": "debugging", "troubleshoot": "debugging",
            "automation": "workflow", "orchestration": "workflow",
            "agent": "ai-agents", "llm": "ai-agents", "ai": "ai-agents",
            "doc": "documentation", "writing": "content",
            "marketing": "content", "seo": "content",
            "game": "gaming", "unity": "gaming", "unreal": "gaming",
            "ios": "mobile", "android": "mobile", "react-native": "mobile",
            "crypto": "blockchain", "web3": "blockchain", "solidity": "blockchain",
            "compliance": "security", "audit": "security", "penetration": "security",
        }
        for alias, target in aliases.items():
            if alias in cat:
                return target

    # Detect from path
    parts = [p.lower() for p in filepath.parts]
    for key in CATEGORY_CONTEXTS:
        if key in parts:
            return key

    # Detect from skill name/description
    name_desc = f"{meta.get('name', '')} {meta.get('description', '')}".lower()
    priority_keywords = [
        ("security", "security"), ("compliance", "security"), ("audit", "security"),
        ("penetration", "security"), ("vulnerability", "security"),
        ("deploy", "devops"), ("kubernetes", "devops"), ("docker", "devops"),
        ("ci/cd", "devops"), ("aws", "devops"), ("terraform", "devops"),
        ("react", "frontend"), ("vue", "frontend"), ("css", "frontend"),
        ("ui", "frontend"), ("design", "frontend"), ("tailwind", "frontend"),
        ("api", "backend"), ("database", "backend"), ("graphql", "backend"),
        ("test", "testing"), ("tdd", "testing"), ("jest", "testing"),
        ("debug", "debugging"), ("error", "debugging"), ("troubleshoot", "debugging"),
        ("architecture", "architecture"), ("system design", "architecture"),
        ("document", "documentation"), ("readme", "documentation"),
        ("workflow", "workflow"), ("automat", "workflow"), ("pipeline", "workflow"),
        ("agent", "ai-agents"), ("llm", "ai-agents"), ("prompt", "ai-agents"),
        ("data", "data"), ("etl", "data"), ("analytics", "data"),
        ("content", "content"), ("blog", "content"), ("copy", "content"),
        ("mobile", "mobile"), ("app", "mobile"),
        ("blockchain", "blockchain"), ("smart contract", "blockchain"),
        ("game", "gaming"),
    ]
    for keyword, cat in priority_keywords:
        if keyword in name_desc:
            return cat

    return "default"


def generate_contextual_block(meta: dict, category: str, filepath: Path) -> str:
    """Generate a domain-specific AGI integration block."""
    ctx = CATEGORY_CONTEXTS.get(category, DEFAULT_CONTEXT)
    name = meta.get("name", filepath.parent.name) or filepath.parent.name
    display_name = name.replace("-", " ").replace("_", " ").title()

    cache_query = ctx["cache_query"].format(name=display_name)

    # Determine source attribution
    source_name = "antigravity-awesome-skills"
    source_url = "https://github.com/sickn33/antigravity-awesome-skills"
    # Check if it's from a different source
    path_str = str(filepath)
    if "superpowers" in path_str:
        source_name = "superpowers"
        source_url = "https://github.com/obra/superpowers"
    elif "ui-ux-pro-max" in path_str:
        source_name = "ui-ux-pro-max-skill"
        source_url = "https://github.com/nextlevelbuilder/ui-ux-pro-max-skill"
    elif "stitch" in path_str:
        source_name = "stitch-skills"
        source_url = "https://github.com/google-labs-code/stitch-skills"

    lines = []
    lines.append(AGI_START)
    lines.append("")
    lines.append("## AGI Framework Integration")
    lines.append("")
    lines.append(f"> **Adapted for [@techwavedev/agi-agent-kit](https://www.npmjs.com/package/@techwavedev/agi-agent-kit)**")
    lines.append(f"> Original source: [{source_name}]({source_url})")
    lines.append("")

    # 1. Memory-First Protocol (contextual)
    lines.append("### Memory-First Protocol")
    lines.append("")
    lines.append(f"{ctx['memory_benefit']}")
    lines.append("")
    lines.append("```bash")
    lines.append(f'# Check for prior {ctx["domain"]} context before starting')
    lines.append(f'python3 execution/memory_manager.py auto --query "{cache_query}"')
    lines.append("```")
    lines.append("")

    # 2. Store results (contextual)
    lines.append("### Storing Results")
    lines.append("")
    lines.append(f"After completing work, store {ctx['domain']} decisions for future sessions:")
    lines.append("")
    lines.append("```bash")
    lines.append(f'python3 execution/memory_manager.py store \\')
    lines.append(f'  --content "{ctx["store_example"]}" \\')
    lines.append(f'  --type {ctx["store_type"]} --project <project> \\')
    lines.append(f'  --tags {name} {category}')
    lines.append("```")
    lines.append("")

    # 3. Cross-Agent Collaboration (contextual)
    lines.append("### Multi-Agent Collaboration")
    lines.append("")
    lines.append(f"{ctx['cross_agent']}")
    lines.append("")
    lines.append("```bash")
    lines.append(f'python3 execution/cross_agent_context.py store \\')
    lines.append(f'  --agent "<your-agent>" \\')
    lines.append(f'  --action "{ctx["team_action"]}" \\')
    lines.append(f'  --project <project>')
    lines.append("```")
    lines.append("")

    # 4. Extra features (category-specific)
    for feat_name, feat_desc in ctx.get("extra_features", []):
        lines.append(f"### {feat_name}")
        lines.append("")
        lines.append(feat_desc)
        lines.append("")

    lines.append(AGI_END)
    return "\n".join(lines)


def process_file(filepath: Path, dry_run: bool = False) -> dict:
    """Process a single SKILL.md file."""
    result = {"file": str(filepath), "status": "unchanged"}

    try:
        content = filepath.read_text(encoding="utf-8", errors="ignore")
    except Exception as e:
        result["status"] = "read_error"
        result["error"] = str(e)
        return result

    meta = parse_frontmatter(content)
    category = detect_category(filepath, meta)
    result["category"] = category
    result["name"] = meta.get("name", "")

    # Generate contextual block
    new_block = generate_contextual_block(meta, category, filepath)

    # Replace existing block or append
    pattern = re.compile(
        rf"{re.escape(AGI_START)}.*?{re.escape(AGI_END)}",
        re.DOTALL
    )

    if pattern.search(content):
        new_content = pattern.sub(new_block, content)
        result["action"] = "replaced"
    else:
        # Append with separator
        new_content = content.rstrip() + f"\n\n---\n\n{new_block}\n"
        result["action"] = "appended"

    if new_content != content:
        result["status"] = "updated"
        if not dry_run:
            filepath.write_text(new_content, encoding="utf-8")
    else:
        result["status"] = "unchanged"

    return result


def main():
    parser = argparse.ArgumentParser(
        description="Generate contextual AGI integration blocks for skills"
    )
    parser.add_argument("--skills-dir", type=Path,
                        help="Directory to scan for SKILL.md files")
    parser.add_argument("--file", type=Path,
                        help="Process a single SKILL.md file")
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview changes without writing")
    parser.add_argument("--report", type=Path,
                        help="Save JSON report to file")
    args = parser.parse_args()

    if not args.skills_dir and not args.file:
        parser.error("Specify --skills-dir or --file")

    files = []
    if args.file:
        files = [args.file]
    else:
        files = sorted(args.skills_dir.rglob("SKILL.md"))
        # Exclude ui-ux-pro-max internal sub-skills
        files = [f for f in files if ".claude/skills/" not in str(f)]

    print(f"Processing {len(files)} SKILL.md files {'(dry run)' if args.dry_run else ''}...")

    results = []
    updated = 0
    by_category = {}

    for filepath in files:
        result = process_file(filepath, args.dry_run)
        results.append(result)
        cat = result.get("category", "unknown")
        by_category[cat] = by_category.get(cat, 0) + 1
        if result["status"] == "updated":
            updated += 1

    print(f"\nUpdated: {updated}/{len(files)}")
    print(f"\nBy category:")
    for cat, count in sorted(by_category.items(), key=lambda x: -x[1]):
        print(f"  {cat:20s} {count:4d}")

    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        report = {
            "total": len(files),
            "updated": updated,
            "by_category": by_category,
            "dry_run": args.dry_run,
        }
        args.report.write_text(json.dumps(report, indent=2))
        print(f"\nReport: {args.report}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
