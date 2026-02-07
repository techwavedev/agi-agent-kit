#!/usr/bin/env python3
"""
research_query.py — Research Question Generator for NotebookLM RAG

Generates structured research questions from a user's intent.
Outputs JSON array of questions designed for iterative NotebookLM querying.

Usage:
    python3 research_query.py --intent "migrate auth to OAuth 2.1" --mode deep
    python3 research_query.py --intent "what ports does Kafka use" --mode quick
    python3 research_query.py --intent "rollback procedure for EKS" --mode cross-ref --notebooks "infra,runbooks"

Arguments:
    --intent     The user's research intent (required)
    --mode       Research mode: quick | deep | cross-ref | plan (default: deep)
    --notebooks  Comma-separated notebook names for cross-ref mode (optional)
    --max-questions  Maximum questions to generate (default: 5)

Output:
    JSON object with structured research plan

Exit Codes:
    0 - Success
    1 - Invalid arguments
"""

import argparse
import json
import sys
from datetime import datetime


def generate_questions(intent: str, mode: str, max_questions: int, notebooks: list[str] | None = None) -> dict:
    """Generate structured research questions based on intent and mode."""

    research_plan = {
        "intent": intent,
        "mode": mode,
        "generated_at": datetime.now().isoformat(),
        "questions": [],
        "strategy": {},
    }

    if mode == "quick":
        # Single focused question
        research_plan["questions"] = [
            {
                "order": 1,
                "question": intent,
                "purpose": "Direct answer to user query",
                "depth": "surface",
                "follow_up_if": "answer is partial or references other topics",
            }
        ]
        research_plan["strategy"] = {
            "session": "new",
            "max_queries": 1,
            "expected_time": "5-10s",
        }

    elif mode == "deep":
        # Multi-question iterative investigation
        questions = [
            {
                "order": 1,
                "question": f"What documentation exists about: {intent}",
                "purpose": "Broad context discovery — understand coverage",
                "depth": "surface",
                "follow_up_if": "topics mentioned need deeper investigation",
            },
            {
                "order": 2,
                "question": f"What are the specific technical details, configurations, or requirements documented for: {intent}",
                "purpose": "Technical deep dive — extract specifics",
                "depth": "medium",
                "follow_up_if": "implementation details reference other systems",
            },
            {
                "order": 3,
                "question": f"What constraints, limitations, known issues, or edge cases are documented regarding: {intent}",
                "purpose": "Risk discovery — find gotchas and blockers",
                "depth": "deep",
                "follow_up_if": "critical constraints found that need mitigation",
            },
            {
                "order": 4,
                "question": f"What dependencies, prerequisites, or related systems are mentioned in connection to: {intent}",
                "purpose": "Dependency mapping — understand blast radius",
                "depth": "deep",
                "follow_up_if": "dependencies have their own documentation",
            },
            {
                "order": 5,
                "question": f"Based on everything documented, what would be the recommended approach or best practice for: {intent}",
                "purpose": "Synthesis — actionable recommendation from docs",
                "depth": "synthesis",
                "follow_up_if": "recommendation has caveats or alternatives",
            },
        ]
        research_plan["questions"] = questions[:max_questions]
        research_plan["strategy"] = {
            "session": "reuse (same session_id for context chain)",
            "max_queries": max_questions,
            "expected_time": f"{max_questions * 8}-{max_questions * 15}s",
            "budget_remaining": f"~{50 - max_questions} queries after this research",
        }

    elif mode == "cross-ref":
        # Multi-notebook comparison
        base_question = f"What information exists about: {intent}"
        questions = [
            {
                "order": 1,
                "question": base_question,
                "purpose": f"Query each relevant notebook with same question",
                "depth": "medium",
                "target_notebooks": notebooks or ["auto-detect from library"],
                "follow_up_if": "answers differ across notebooks",
            },
            {
                "order": 2,
                "question": f"Are there any specific recommendations, warnings, or constraints about: {intent}",
                "purpose": "Compare guidance across sources",
                "depth": "deep",
                "target_notebooks": notebooks or ["auto-detect from library"],
                "follow_up_if": "contradictions found between sources",
            },
        ]
        research_plan["questions"] = questions
        research_plan["strategy"] = {
            "session": "separate per notebook",
            "max_queries": len(questions) * len(notebooks or ["auto"]),
            "expected_time": "15-45s",
            "note": "Compare answers across notebooks, flag contradictions",
        }

    elif mode == "plan":
        # Planning-oriented research
        questions = [
            {
                "order": 1,
                "question": f"What is the current documented state/architecture for: {intent}",
                "purpose": "Baseline understanding — what exists today",
                "depth": "medium",
                "planning_phase": "analysis",
            },
            {
                "order": 2,
                "question": f"What documented requirements, standards, or policies apply to: {intent}",
                "purpose": "Constraint identification — what must be followed",
                "depth": "deep",
                "planning_phase": "requirements",
            },
            {
                "order": 3,
                "question": f"Have there been any previous attempts, migrations, or changes documented for: {intent}",
                "purpose": "Historical context — learn from past attempts",
                "depth": "deep",
                "planning_phase": "history",
            },
            {
                "order": 4,
                "question": f"What risks, rollback procedures, or failure modes are documented for changes to: {intent}",
                "purpose": "Risk assessment — safety net discovery",
                "depth": "deep",
                "planning_phase": "risk",
            },
            {
                "order": 5,
                "question": f"What testing, validation, or verification approaches are documented for: {intent}",
                "purpose": "Verification strategy — how to confirm success",
                "depth": "medium",
                "planning_phase": "verification",
            },
        ]
        research_plan["questions"] = questions[:max_questions]
        research_plan["strategy"] = {
            "session": "reuse (single session for full context)",
            "max_queries": max_questions,
            "expected_time": f"{max_questions * 10}-{max_questions * 20}s",
            "output_format": "grounded plan with doc citations",
        }

    return research_plan


def main():
    parser = argparse.ArgumentParser(
        description="Generate structured research questions for NotebookLM RAG",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--intent", required=True, help="The user's research intent")
    parser.add_argument(
        "--mode",
        choices=["quick", "deep", "cross-ref", "plan"],
        default="deep",
        help="Research mode (default: deep)",
    )
    parser.add_argument(
        "--notebooks",
        help="Comma-separated notebook names for cross-ref mode",
    )
    parser.add_argument(
        "--max-questions",
        type=int,
        default=5,
        help="Maximum questions to generate (default: 5)",
    )
    args = parser.parse_args()

    notebooks = args.notebooks.split(",") if args.notebooks else None

    plan = generate_questions(
        intent=args.intent,
        mode=args.mode,
        max_questions=args.max_questions,
        notebooks=notebooks,
    )

    print(json.dumps(plan, indent=2))
    sys.exit(0)


if __name__ == "__main__":
    main()
