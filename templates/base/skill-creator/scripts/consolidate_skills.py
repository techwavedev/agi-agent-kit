#!/usr/bin/env python3
"""
Script: consolidate_skills.py
Purpose: Skill Consolidation Engine for AGI Agent Kit.
         Analyzes 1,200+ community skills to detect overlapping groups and
         merges them into fewer, more powerful condensed skills while
         maintaining full provenance mapping for upstream sync.

Usage:
    # Scan for consolidation candidates
    python3 skill-creator/scripts/consolidate_skills.py scan \
      --skills-dir templates/skills/extended \
      [--json] [--min-group-size 3] [--store]

    # Generate consolidation map
    python3 skill-creator/scripts/consolidate_skills.py map \
      --skills-dir templates/skills/extended \
      --output templates/skills/consolidation_map.json \
      [--min-group-size 2] [--store]

    # Preview a specific consolidation group
    python3 skill-creator/scripts/consolidate_skills.py preview \
      --group "azure-cosmos" \
      --skills-dir templates/skills/extended

    # Apply consolidation (creates new, keeps originals)
    python3 skill-creator/scripts/consolidate_skills.py apply \
      --map templates/skills/consolidation_map.json \
      --skills-dir templates/skills/extended \
      --output-dir templates/skills/condensed \
      [--dry-run]

Exit Codes:
    0 - Success
    1 - Partial success (some groups could not be processed)
    2 - Invalid arguments
    3 - Qdrant connection error (operation still completes, storage skipped)
    4 - Unexpected error
"""

import argparse
import json
import os
import re
import sys
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

QDRANT_URL = os.environ.get("QDRANT_URL", "http://localhost:6333")
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "nomic-embed-text")
MEMORY_COLLECTION = os.environ.get("MEMORY_COLLECTION", "agent_memory")

# Known upstream sources and their URLs
UPSTREAM_REGISTRY = {
    "antigravity-awesome-skills": "https://github.com/sickn33/antigravity-awesome-skills",
    "stitch-skills": "https://github.com/google-labs-code/stitch-skills",
    "superpowers": "https://github.com/obra/superpowers",
    "ui-ux-pro-max-skill": "https://github.com/nextlevelbuilder/ui-ux-pro-max-skill",
}

# Language suffix patterns for multi-language detection
LANGUAGE_SUFFIXES = {
    "-py": "python",
    "-ts": "typescript",
    "-java": "java",
    "-rust": "rust",
    "-dotnet": "dotnet",
    "-go": "go",
    "-js": "javascript",
    "-rb": "ruby",
    "-cs": "csharp",
}

# Merge strategy labels
STRATEGY_MULTI_LANG = "multi-language"
STRATEGY_FRAMEWORK = "framework-consolidation"
STRATEGY_PLATFORM = "platform-consolidation"
STRATEGY_DOMAIN = "domain-consolidation"


# ---------------------------------------------------------------------------
# Qdrant helpers (mirrors evaluate_skill.py pattern)
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
        "type": "consolidation",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **metadata,
    }

    body = {"points": [{"id": point_id, "vector": embedding, "payload": payload}]}

    try:
        result = _qdrant_request("PUT", f"/collections/{MEMORY_COLLECTION}/points", body)
        return {"status": "stored", "id": point_id, "qdrant_status": result.get("status")}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# ---------------------------------------------------------------------------
# YAML frontmatter parser (no external dependencies)
# ---------------------------------------------------------------------------

def _parse_simple_yaml(text: str) -> dict:
    """Minimal YAML parser for flat key-value frontmatter."""
    result = {}
    for line in text.strip().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" in line:
            key, _, value = line.partition(":")
            result[key.strip()] = value.strip().strip('"').strip("'")
    return result


def parse_frontmatter(skill_md_path: Path) -> dict | None:
    """Parse YAML frontmatter from a SKILL.md file. Returns dict or None."""
    if not skill_md_path.is_file():
        return None

    content = skill_md_path.read_text(encoding="utf-8", errors="replace")
    if not content.startswith("---"):
        return None

    match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    if not match:
        return None

    try:
        try:
            import yaml
            fm = yaml.safe_load(match.group(1))
        except ImportError:
            fm = _parse_simple_yaml(match.group(1))
        return fm if isinstance(fm, dict) else None
    except Exception:
        return None


def extract_upstream_source(skill_md_path: Path) -> tuple:
    """Extract upstream source name and URL from AGI integration block.

    Returns (source_name, source_url) or (None, None) if not found.
    """
    if not skill_md_path.is_file():
        return None, None

    content = skill_md_path.read_text(encoding="utf-8", errors="replace")

    # Look for AGI-INTEGRATION block
    block_match = re.search(
        r"<!-- AGI-INTEGRATION-START -->(.*?)<!-- AGI-INTEGRATION-END -->",
        content,
        re.DOTALL,
    )
    if not block_match:
        return None, None

    block = block_match.group(1)

    # Extract: Original source: [name](url)
    source_match = re.search(
        r"Original source:\s*\[([^\]]+)\]\(([^)]+)\)",
        block,
    )
    if source_match:
        return source_match.group(1), source_match.group(2)

    return None, None


def extract_description_keywords(description: str) -> set:
    """Extract meaningful keywords from a description for similarity scoring."""
    if not description:
        return set()
    # Remove common stop words
    stop_words = {
        "a", "an", "the", "and", "or", "for", "with", "in", "on", "to", "of",
        "is", "are", "was", "were", "be", "been", "being", "has", "have", "had",
        "do", "does", "did", "will", "would", "could", "should", "may", "might",
        "can", "this", "that", "these", "those", "it", "its", "from", "by", "as",
        "at", "into", "through", "during", "before", "after", "above", "below",
        "between", "about", "against", "using", "based", "across", "all", "each",
        "every", "both", "few", "more", "most", "other", "some", "such", "no",
        "not", "only", "own", "same", "so", "than", "too", "very",
    }
    words = set(re.findall(r"[a-z]{3,}", description.lower()))
    return words - stop_words


# ---------------------------------------------------------------------------
# Skill scanning and inventory
# ---------------------------------------------------------------------------

def scan_all_skills(skills_dir: Path) -> list:
    """Scan all skills and return a list of skill metadata dicts."""
    skills = []

    if not skills_dir.is_dir():
        return skills

    for category_dir in sorted(skills_dir.iterdir()):
        if not category_dir.is_dir() or category_dir.name.startswith("."):
            continue

        category = category_dir.name

        for skill_dir in sorted(category_dir.iterdir()):
            if not skill_dir.is_dir() or skill_dir.name.startswith("."):
                continue

            skill_md = skill_dir / "SKILL.md"
            fm = parse_frontmatter(skill_md)
            upstream_name, upstream_url = extract_upstream_source(skill_md)

            skill_name = skill_dir.name
            description = ""
            source_type = "unknown"
            date_added = ""

            if fm:
                skill_name = fm.get("name", skill_dir.name)
                description = fm.get("description", "")
                source_type = fm.get("source", "unknown")
                date_added = fm.get("date_added", "")

            # Detect language from suffix
            detected_languages = []
            for suffix, lang in LANGUAGE_SUFFIXES.items():
                if skill_dir.name.endswith(suffix):
                    detected_languages.append(lang)
                    break

            skills.append({
                "name": skill_name,
                "dir_name": skill_dir.name,
                "category": category,
                "path": f"{category}/{skill_dir.name}",
                "description": str(description),
                "source_type": str(source_type),
                "date_added": str(date_added),
                "upstream_source": upstream_name,
                "upstream_url": upstream_url,
                "languages": detected_languages,
                "keywords": extract_description_keywords(str(description)),
            })

    return skills


# ---------------------------------------------------------------------------
# Grouping algorithms
# ---------------------------------------------------------------------------

def _compute_prefix(name: str) -> str:
    """Strip language suffix to get the base prefix of a skill name.

    E.g. 'azure-cosmos-java' -> 'azure-cosmos',
         'angular-best-practices' -> 'angular'.
    """
    # Strip known language suffixes first
    for suffix in LANGUAGE_SUFFIXES:
        if name.endswith(suffix):
            return name[: -len(suffix)]

    return name


def _compute_root_prefix(name: str) -> str:
    """Get the broadest prefix (first 1-3 segments) for platform grouping.

    E.g. 'azure-cosmos-java' -> 'azure-cosmos',
         'azure-ai-contentsafety-ts' -> 'azure-ai-contentsafety',
         'angular-best-practices' -> 'angular'.
    """
    # Strip language suffix first
    base = _compute_prefix(name)
    parts = base.split("-")

    # Known platform prefixes that should keep 2+ segments
    platform_prefixes = {
        "azure-ai", "azure-cosmos", "azure-eventhub", "azure-eventgrid",
        "azure-identity", "azure-keyvault", "azure-mgmt", "azure-monitor",
        "azure-resource-manager", "azure-search", "azure-security",
        "azure-servicebus", "azure-storage", "azure-communication",
        "azure-compute", "azure-data", "azure-messaging", "azure-web",
        "azure-appconfiguration", "azure-containerregistry",
        "azure-microsoft",
        "react-native", "react-flow",
    }

    # Try longest platform prefix match first
    for i in range(min(len(parts), 5), 0, -1):
        candidate = "-".join(parts[:i])
        if candidate in platform_prefixes:
            # Include the next segment if it exists (to distinguish e.g. azure-ai-contentsafety from azure-ai-ml)
            if i < len(parts):
                return "-".join(parts[: i + 1])
            return candidate

    # For azure-* patterns, keep at least 2 segments
    if parts[0] == "azure" and len(parts) >= 2:
        # Keep first 2+ meaningful segments
        if len(parts) >= 3:
            return "-".join(parts[:3])
        return "-".join(parts[:2])

    # Default: first segment only
    return parts[0]


def _keyword_similarity(keywords_a: set, keywords_b: set) -> float:
    """Jaccard similarity between two keyword sets."""
    if not keywords_a or not keywords_b:
        return 0.0
    intersection = keywords_a & keywords_b
    union = keywords_a | keywords_b
    return len(intersection) / len(union) if union else 0.0


def group_by_language_variants(skills: list) -> dict:
    """Group skills that are the same service in different languages.

    Returns {prefix: [skill, ...]} where len >= 2.
    """
    prefix_groups = defaultdict(list)

    for skill in skills:
        if skill["languages"]:
            prefix = _compute_prefix(skill["dir_name"])
            prefix_groups[prefix].append(skill)

    # Only return groups with 2+ members
    return {k: v for k, v in prefix_groups.items() if len(v) >= 2}


def group_by_prefix_pattern(skills: list) -> dict:
    """Group skills sharing the same root prefix (framework/platform grouping).

    Returns {root_prefix: [skill, ...]} where len >= 2.
    """
    prefix_groups = defaultdict(list)

    for skill in skills:
        root = _compute_root_prefix(skill["dir_name"])
        prefix_groups[root].append(skill)

    return {k: v for k, v in prefix_groups.items() if len(v) >= 2}


def group_by_semantic_similarity(skills: list, threshold: float = 0.35) -> list:
    """Find skills with similar descriptions that aren't caught by prefix matching.

    Returns list of (skill_a, skill_b, similarity) tuples above threshold.
    """
    pairs = []
    for i in range(len(skills)):
        for j in range(i + 1, len(skills)):
            sim = _keyword_similarity(skills[i]["keywords"], skills[j]["keywords"])
            if sim >= threshold:
                # Only include if they're in the same category (to avoid noise)
                if skills[i]["category"] == skills[j]["category"]:
                    pairs.append((skills[i], skills[j], round(sim, 3)))

    pairs.sort(key=lambda x: x[2], reverse=True)
    return pairs


def _detect_merge_strategy(group_skills: list) -> str:
    """Determine the merge strategy for a consolidation group."""
    languages_found = set()
    for s in group_skills:
        languages_found.update(s["languages"])

    if len(languages_found) >= 2:
        return STRATEGY_MULTI_LANG

    # Check if names suggest framework aspects (best-practices, patterns, state-management, etc.)
    aspect_keywords = {
        "best-practices", "patterns", "state-management", "migration",
        "ui-patterns", "architecture", "expert", "pro", "testing",
        "security", "optimization", "advanced",
    }
    names = [s["dir_name"] for s in group_skills]
    has_aspects = any(
        any(kw in name for kw in aspect_keywords)
        for name in names
    )
    if has_aspects:
        return STRATEGY_FRAMEWORK

    # Check for platform-like grouping (same vendor prefix)
    prefixes = set(_compute_prefix(s["dir_name"]).split("-")[0] for s in group_skills)
    if len(prefixes) == 1 and prefixes.pop() in ("azure", "aws", "gcp", "fal", "apify"):
        return STRATEGY_PLATFORM

    return STRATEGY_DOMAIN


def _score_group(group_skills: list) -> float:
    """Score a consolidation group by quality/confidence (0.0 - 1.0).

    Higher scores mean the group is a better consolidation candidate.
    """
    score = 0.0

    # Size bonus (more skills = stronger signal, diminishing returns)
    size = len(group_skills)
    score += min(size / 10.0, 0.3)

    # Same upstream source bonus
    upstreams = set(s["upstream_source"] for s in group_skills if s["upstream_source"])
    if len(upstreams) == 1:
        score += 0.2
    elif upstreams:
        score += 0.1

    # Language variant bonus (strongest signal)
    all_langs = set()
    for s in group_skills:
        all_langs.update(s["languages"])
    if len(all_langs) >= 2:
        score += 0.3

    # Description similarity bonus
    if len(group_skills) >= 2:
        total_sim = 0.0
        pairs = 0
        for i in range(len(group_skills)):
            for j in range(i + 1, len(group_skills)):
                total_sim += _keyword_similarity(
                    group_skills[i]["keywords"],
                    group_skills[j]["keywords"],
                )
                pairs += 1
        if pairs > 0:
            avg_sim = total_sim / pairs
            score += avg_sim * 0.2

    return round(min(score, 1.0), 3)


def _estimate_token_savings(group_skills: list) -> str:
    """Estimate token savings from consolidating a group."""
    count = len(group_skills)
    if count <= 1:
        return "none"
    if count <= 3:
        return f"{count}x reduction"
    if count <= 6:
        return f"{count}x reduction (significant)"
    return f"{count}x reduction (major)"


def _generate_condensed_name(prefix: str, group_skills: list) -> str:
    """Generate a good condensed skill name for a group."""
    languages = set()
    for s in group_skills:
        languages.update(s["languages"])

    # If it's a multi-language group, just use the prefix
    if len(languages) >= 2:
        return prefix

    # Check if the prefix itself is a skill name already
    dir_names = [s["dir_name"] for s in group_skills]
    if prefix in dir_names:
        return f"{prefix}-expert"

    return prefix


def _generate_group_description(prefix: str, group_skills: list, strategy: str) -> str:
    """Generate a description for a condensed group."""
    languages = set()
    for s in group_skills:
        languages.update(s["languages"])

    categories = set(s["category"] for s in group_skills)

    if strategy == STRATEGY_MULTI_LANG:
        lang_list = ", ".join(sorted(lang.title() for lang in languages))
        # Use the first skill's description as base, but generalize
        base_desc = group_skills[0]["description"]
        # Truncate to first sentence
        first_sentence = base_desc.split(".")[0] if "." in base_desc else base_desc
        return f"{first_sentence} across all languages ({lang_list})."

    if strategy == STRATEGY_FRAMEWORK:
        return (
            f"Consolidated {prefix} skill covering: "
            + ", ".join(s["dir_name"] for s in group_skills[:5])
            + (f" and {len(group_skills) - 5} more" if len(group_skills) > 5 else "")
            + "."
        )

    if strategy == STRATEGY_PLATFORM:
        return (
            f"{prefix.replace('-', ' ').title()} platform skills: "
            + ", ".join(s["dir_name"] for s in group_skills[:5])
            + (f" and {len(group_skills) - 5} more" if len(group_skills) > 5 else "")
            + "."
        )

    return (
        f"Consolidated {prefix} domain expertise from {len(group_skills)} skills"
        + f" in {', '.join(sorted(categories))}."
    )


# ---------------------------------------------------------------------------
# Build consolidated groups (main analysis pipeline)
# ---------------------------------------------------------------------------

def build_consolidation_groups(skills: list, min_group_size: int = 2) -> list:
    """Run all grouping algorithms and merge results into consolidation groups.

    Returns a deduplicated list of consolidation group dicts.
    """
    # Track which skills have been assigned to a group
    assigned = set()  # dir_names
    groups = []

    # Pass 1: Multi-language variants (highest confidence)
    lang_groups = group_by_language_variants(skills)
    for prefix, members in sorted(lang_groups.items(), key=lambda x: -len(x[1])):
        if len(members) < min_group_size:
            continue

        strategy = _detect_merge_strategy(members)
        condensed_name = _generate_condensed_name(prefix, members)

        groups.append({
            "condensed_name": condensed_name,
            "condensed_category": members[0]["category"],
            "description": _generate_group_description(prefix, members, strategy),
            "original_skills": _build_original_skills_list(members),
            "merge_strategy": strategy,
            "confidence": _score_group(members),
            "token_savings_estimate": _estimate_token_savings(members),
        })

        for m in members:
            assigned.add(m["dir_name"])

    # Pass 2: Prefix pattern grouping (framework/platform)
    prefix_groups = group_by_prefix_pattern(skills)
    for prefix, members in sorted(prefix_groups.items(), key=lambda x: -len(x[1])):
        # Filter out already-assigned skills
        remaining = [m for m in members if m["dir_name"] not in assigned]
        if len(remaining) < min_group_size:
            continue

        strategy = _detect_merge_strategy(remaining)
        condensed_name = _generate_condensed_name(prefix, remaining)

        groups.append({
            "condensed_name": condensed_name,
            "condensed_category": remaining[0]["category"],
            "description": _generate_group_description(prefix, remaining, strategy),
            "original_skills": _build_original_skills_list(remaining),
            "merge_strategy": strategy,
            "confidence": _score_group(remaining),
            "token_savings_estimate": _estimate_token_savings(remaining),
        })

        for m in remaining:
            assigned.add(m["dir_name"])

    # Sort by confidence descending, then by group size
    groups.sort(key=lambda g: (-g["confidence"], -len(g["original_skills"])))

    return groups


def _build_original_skills_list(members: list) -> list:
    """Build the original_skills array for a consolidation group."""
    result = []
    for m in members:
        result.append({
            "name": m["name"],
            "dir_name": m["dir_name"],
            "path": m["path"],
            "upstream_source": m["upstream_source"],
            "upstream_url": m["upstream_url"],
            "source_type": m["source_type"],
            "date_added": m["date_added"],
            "languages": m["languages"],
        })
    return result


# ---------------------------------------------------------------------------
# Subcommand: scan
# ---------------------------------------------------------------------------

def cmd_scan(args):
    """Analyze all skills and detect consolidation candidates."""
    skills_dir = Path(args.skills_dir).resolve()
    if not skills_dir.is_dir():
        print(json.dumps({"status": "error", "message": f"Skills directory not found: {skills_dir}"}), file=sys.stderr)
        sys.exit(2)

    skills = scan_all_skills(skills_dir)
    if not skills:
        print(json.dumps({"status": "error", "message": "No skills found"}), file=sys.stderr)
        sys.exit(2)

    groups = build_consolidation_groups(skills, min_group_size=args.min_group_size)

    # Compute summary stats
    total_skills_in_groups = sum(len(g["original_skills"]) for g in groups)
    upstream_counts = defaultdict(int)
    for g in groups:
        for s in g["original_skills"]:
            if s["upstream_source"]:
                upstream_counts[s["upstream_source"]] += 1

    result = {
        "status": "success",
        "total_skills_scanned": len(skills),
        "consolidation_groups_found": len(groups),
        "total_skills_in_groups": total_skills_in_groups,
        "skills_not_grouped": len(skills) - total_skills_in_groups,
        "upstream_sources": dict(upstream_counts),
        "groups": groups,
    }

    # Optional Qdrant storage
    if getattr(args, "store", False):
        store_content = (
            f"Skill consolidation scan: {len(skills)} skills scanned, "
            f"{len(groups)} groups found, {total_skills_in_groups} skills groupable"
        )
        store_meta = {
            "project": "agi-agent-kit",
            "tags": ["consolidation", "scan", "skills"],
            "groups_count": len(groups),
            "skills_scanned": len(skills),
        }
        try:
            qdrant_result = _store_to_qdrant(store_content, store_meta)
            result["qdrant_store"] = qdrant_result
        except Exception as e:
            result["qdrant_store"] = {"status": "error", "message": str(e)}

    if args.json_output:
        print(json.dumps(result, indent=2, default=str))
    else:
        _print_scan_human(result, groups)

    sys.exit(0)


def _print_scan_human(result: dict, groups: list):
    """Print scan results in human-readable format."""
    print(f"\n{'='*70}")
    print(f"  Skill Consolidation Scan")
    print(f"{'='*70}")
    print(f"  Total skills scanned:     {result['total_skills_scanned']}")
    print(f"  Consolidation groups:     {result['consolidation_groups_found']}")
    print(f"  Skills in groups:         {result['total_skills_in_groups']}")
    print(f"  Ungrouped skills:         {result['skills_not_grouped']}")
    print()

    if result["upstream_sources"]:
        print("  Upstream Sources:")
        for source, count in sorted(result["upstream_sources"].items(), key=lambda x: -x[1]):
            print(f"    {source}: {count} skills")
        print()

    if not groups:
        print("  No consolidation candidates found.")
        print(f"{'='*70}\n")
        return

    print(f"  Top Consolidation Groups:")
    print(f"  {'-'*66}")

    for i, g in enumerate(groups[:30], 1):
        members = g["original_skills"]
        strategy_label = g["merge_strategy"].replace("-", " ").title()
        print(
            f"  {i:3d}. {g['condensed_name']:<40s} "
            f"[{len(members)} skills] "
            f"conf={g['confidence']:.2f} "
            f"({strategy_label})"
        )
        for m in members[:5]:
            lang = f" ({', '.join(m['languages'])})" if m["languages"] else ""
            print(f"       - {m['dir_name']}{lang}")
        if len(members) > 5:
            print(f"       ... and {len(members) - 5} more")

    if len(groups) > 30:
        print(f"\n  ... and {len(groups) - 30} more groups (use --json for full list)")

    print(f"\n{'='*70}\n")


# ---------------------------------------------------------------------------
# Subcommand: map
# ---------------------------------------------------------------------------

def cmd_map(args):
    """Generate the consolidation map JSON file."""
    skills_dir = Path(args.skills_dir).resolve()
    output_path = Path(args.output).resolve()

    if not skills_dir.is_dir():
        print(json.dumps({"status": "error", "message": f"Skills directory not found: {skills_dir}"}), file=sys.stderr)
        sys.exit(2)

    skills = scan_all_skills(skills_dir)
    if not skills:
        print(json.dumps({"status": "error", "message": "No skills found"}), file=sys.stderr)
        sys.exit(2)

    groups = build_consolidation_groups(skills, min_group_size=args.min_group_size)

    # Build upstream registry with counts
    upstream_registry = {}
    for source_name, source_url in UPSTREAM_REGISTRY.items():
        count = sum(
            1 for s in skills
            if s["upstream_source"] == source_name
        )
        if count > 0:
            upstream_registry[source_name] = {
                "url": source_url,
                "skills_count": count,
                "last_synced": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            }

    consolidation_map = {
        "version": "1.0",
        "generated": datetime.now(timezone.utc).isoformat(),
        "total_skills_scanned": len(skills),
        "consolidation_groups": groups,
        "upstream_registry": upstream_registry,
    }

    # Write output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(consolidation_map, indent=2, default=str), encoding="utf-8")

    result = {
        "status": "success",
        "output": str(output_path),
        "groups_count": len(groups),
        "total_skills_mapped": sum(len(g["original_skills"]) for g in groups),
    }

    # Optional Qdrant storage
    if getattr(args, "store", False):
        store_content = (
            f"Consolidation map generated: {len(groups)} groups, "
            f"output at {output_path}"
        )
        store_meta = {
            "project": "agi-agent-kit",
            "tags": ["consolidation", "map", "skills"],
            "output_path": str(output_path),
            "groups_count": len(groups),
        }
        try:
            qdrant_result = _store_to_qdrant(store_content, store_meta)
            result["qdrant_store"] = qdrant_result
        except Exception as e:
            result["qdrant_store"] = {"status": "error", "message": str(e)}

    print(json.dumps(result, indent=2))
    sys.exit(0)


# ---------------------------------------------------------------------------
# Subcommand: preview
# ---------------------------------------------------------------------------

def cmd_preview(args):
    """Preview what a specific consolidation group would look like."""
    skills_dir = Path(args.skills_dir).resolve()
    group_name = args.group.lower().strip()

    if not skills_dir.is_dir():
        print(json.dumps({"status": "error", "message": f"Skills directory not found: {skills_dir}"}), file=sys.stderr)
        sys.exit(2)

    skills = scan_all_skills(skills_dir)
    groups = build_consolidation_groups(skills, min_group_size=2)

    # Find the matching group
    target_group = None
    for g in groups:
        if g["condensed_name"].lower() == group_name:
            target_group = g
            break

    # Fallback: try partial match
    if not target_group:
        candidates = [g for g in groups if group_name in g["condensed_name"].lower()]
        if len(candidates) == 1:
            target_group = candidates[0]
        elif len(candidates) > 1:
            names = [c["condensed_name"] for c in candidates]
            print(json.dumps({
                "status": "error",
                "message": f"Ambiguous group name '{group_name}'. Matches: {names}",
            }), file=sys.stderr)
            sys.exit(2)

    if not target_group:
        print(json.dumps({
            "status": "error",
            "message": f"Group '{group_name}' not found. Use 'scan' to see available groups.",
        }), file=sys.stderr)
        sys.exit(2)

    # Generate a preview of the condensed SKILL.md
    preview_content = _generate_condensed_skill_md(target_group, skills_dir)

    result = {
        "status": "success",
        "group": target_group,
        "preview_skill_md": preview_content,
    }

    if args.json_output:
        print(json.dumps(result, indent=2, default=str))
    else:
        _print_preview_human(target_group, preview_content)

    sys.exit(0)


def _extract_key_sections(content: str) -> str:
    """Extract key sections from long skill content for progressive disclosure.

    Pulls out 'When to Use', 'Installation', 'Core Workflow', 'Quick Start',
    and 'Commands' sections. Returns them concatenated, keeping total output
    manageable while preserving all functional guidance.
    """
    key_patterns = [
        r"##\s*When to Use[^\n]*\n(.*?)(?=\n##\s|\Z)",
        r"##\s*Installation[^\n]*\n(.*?)(?=\n##\s|\Z)",
        r"##\s*Quick\s*Start[^\n]*\n(.*?)(?=\n##\s|\Z)",
        r"##\s*Core\s*Workflow[^\n]*\n(.*?)(?=\n##\s|\Z)",
        r"##\s*Commands?[^\n]*\n(.*?)(?=\n##\s|\Z)",
        r"##\s*Usage[^\n]*\n(.*?)(?=\n##\s|\Z)",
        r"##\s*Configuration[^\n]*\n(.*?)(?=\n##\s|\Z)",
    ]

    extracted_parts = []
    for pattern in key_patterns:
        match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
        if match:
            section_text = match.group(0).strip()
            # Cap each section at 40 lines to prevent bloat
            section_lines = section_text.splitlines()
            if len(section_lines) > 40:
                section_text = "\n".join(section_lines[:40]) + "\n\n> _(truncated — see full reference)_"
            extracted_parts.append(section_text)

    if not extracted_parts:
        # Fallback: take the first 60 lines of content
        fallback = "\n".join(content.splitlines()[:60])
        return fallback + "\n\n> _(truncated — see full reference)_"

    return "\n\n".join(extracted_parts)


def _generate_condensed_skill_md(group: dict, skills_dir: Path) -> str:
    """Generate the content of a condensed SKILL.md from a consolidation group."""
    name = group["condensed_name"]
    description = group["description"]
    strategy = group["merge_strategy"]
    originals = group["original_skills"]

    # Collect all languages
    all_languages = set()
    for s in originals:
        all_languages.update(s["languages"])

    # Collect all upstream sources
    sources = set()
    for s in originals:
        if s["upstream_source"]:
            sources.add(s["upstream_source"])

    # Build frontmatter
    lines = [
        "---",
        f"name: {name}",
        f"description: {description}",
        "risk: unknown",
        f"source: {'community' if sources else 'self'}",
        f"date_added: '{datetime.now(timezone.utc).strftime('%Y-%m-%d')}'",
        f"consolidated_from: {len(originals)} skills",
        f"merge_strategy: {strategy}",
        "---",
        "",
        f"# {name.replace('-', ' ').title()}",
        "",
        description,
        "",
    ]

    # When to use
    lines.append("## When to Use This Skill")
    lines.append("")
    if strategy == STRATEGY_MULTI_LANG:
        lang_list = ", ".join(sorted(lang.title() for lang in all_languages))
        lines.append(f"- Working with {name.replace('-', ' ').title()} in any supported language ({lang_list})")
    else:
        for s in originals[:6]:
            lines.append(f"- Tasks related to {s['name']}")
    lines.append("")

    # Consolidated from section
    lines.append("## Consolidated Skills")
    lines.append("")
    lines.append("This skill consolidates the following original skills:")
    lines.append("")
    lines.append("| Original Skill | Language | Source |")
    lines.append("|---|---|---|")
    for s in originals:
        lang = ", ".join(s["languages"]) if s["languages"] else "general"
        source = s["upstream_source"] or s["source_type"]
        lines.append(f"| {s['name']} | {lang} | {source} |")
    lines.append("")

    # Aggregate content from each original skill — NEVER lose functionality
    for s in originals:
        skill_md = skills_dir / s["path"] / "SKILL.md"
        if not skill_md.is_file():
            continue

        content = skill_md.read_text(encoding="utf-8", errors="replace")
        # Remove frontmatter
        content = re.sub(r"^---\n.*?\n---\n?", "", content, flags=re.DOTALL)
        # Remove AGI integration block
        content = re.sub(
            r"<!-- AGI-INTEGRATION-START -->.*?<!-- AGI-INTEGRATION-END -->",
            "",
            content,
            flags=re.DOTALL,
        )
        # Remove redundant top-level heading (# Title)
        content = re.sub(r"^#\s+[^\n]+\n+", "", content.strip())
        content = content.strip()

        if not content:
            continue

        # Section header varies by strategy
        if strategy == STRATEGY_MULTI_LANG:
            lang_label = ", ".join(s["languages"]) if s["languages"] else s["dir_name"]
            section_title = lang_label.title()
        else:
            section_title = s["name"].replace("-", " ").title()

        lines.append(f"## {section_title}")
        lines.append("")
        lines.append(f"> Sourced from `{s['path']}`")
        lines.append("")

        # For progressive disclosure: if content is over 100 lines,
        # extract key sections only and note the full reference path
        content_lines = content.splitlines()
        if len(content_lines) > 100:
            # Extract "When to Use", "Installation", "Core" sections
            extracted = _extract_key_sections(content)
            if extracted:
                lines.append(extracted)
            lines.append("")
            lines.append(f"> Full reference: `{s['path']}/SKILL.md` ({len(content_lines)} lines)")
        else:
            lines.append(content)
        lines.append("")

    # Provenance / AGI integration block
    lines.append("<!-- AGI-INTEGRATION-START -->")
    lines.append("")
    lines.append("## AGI Framework Integration")
    lines.append("")
    lines.append("> **Adapted for [@techwavedev/agi-agent-kit](https://www.npmjs.com/package/@techwavedev/agi-agent-kit)**")
    if sources:
        for src in sorted(sources):
            url = UPSTREAM_REGISTRY.get(src, "")
            if url:
                lines.append(f"> Original source: [{src}]({url})")
            else:
                lines.append(f"> Original source: {src}")
    lines.append(f"> Consolidated from {len(originals)} skills on {datetime.now(timezone.utc).strftime('%Y-%m-%d')}")
    lines.append("")
    lines.append("### Provenance Map")
    lines.append("")
    for s in originals:
        lines.append(f"- `{s['path']}` ({s['source_type']})")
    lines.append("")
    lines.append("<!-- AGI-INTEGRATION-END -->")
    lines.append("")

    return "\n".join(lines)


def _print_preview_human(group: dict, preview_content: str):
    """Print preview in human-readable format."""
    print(f"\n{'='*70}")
    print(f"  Preview: {group['condensed_name']}")
    print(f"{'='*70}")
    print(f"  Strategy:   {group['merge_strategy']}")
    print(f"  Confidence: {group['confidence']}")
    print(f"  Savings:    {group['token_savings_estimate']}")
    print(f"  Members:    {len(group['original_skills'])}")
    print()
    print("  Original Skills:")
    for s in group["original_skills"]:
        lang = f" ({', '.join(s['languages'])})" if s["languages"] else ""
        print(f"    - {s['path']}{lang}")
    print()
    print(f"  {'~'*66}")
    print("  Generated SKILL.md Preview:")
    print(f"  {'~'*66}")
    print()
    for line in preview_content.splitlines():
        print(f"  {line}")
    print()
    print(f"{'='*70}\n")


# ---------------------------------------------------------------------------
# Subcommand: apply
# ---------------------------------------------------------------------------

def cmd_apply(args):
    """Apply consolidation — create condensed skills from the map."""
    map_path = Path(args.map).resolve()
    skills_dir = Path(args.skills_dir).resolve()
    output_dir = Path(args.output_dir).resolve()
    dry_run = args.dry_run

    if not map_path.is_file():
        print(json.dumps({"status": "error", "message": f"Map file not found: {map_path}"}), file=sys.stderr)
        sys.exit(2)

    if not skills_dir.is_dir():
        print(json.dumps({"status": "error", "message": f"Skills directory not found: {skills_dir}"}), file=sys.stderr)
        sys.exit(2)

    # Load consolidation map
    try:
        consolidation_map = json.loads(map_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        print(json.dumps({"status": "error", "message": f"Failed to read map: {e}"}), file=sys.stderr)
        sys.exit(2)

    groups = consolidation_map.get("consolidation_groups", [])
    if not groups:
        print(json.dumps({"status": "error", "message": "No consolidation groups in map"}), file=sys.stderr)
        sys.exit(2)

    created = []
    errors = []

    for group in groups:
        condensed_name = group["condensed_name"]
        category = group.get("condensed_category", "other")

        try:
            # Generate the condensed SKILL.md
            content = _generate_condensed_skill_md(group, skills_dir)

            # Target directory
            target_dir = output_dir / category / condensed_name

            if dry_run:
                created.append({
                    "condensed_name": condensed_name,
                    "target_path": str(target_dir),
                    "original_count": len(group["original_skills"]),
                    "content_lines": len(content.splitlines()),
                    "dry_run": True,
                })
            else:
                target_dir.mkdir(parents=True, exist_ok=True)
                skill_md_path = target_dir / "SKILL.md"
                skill_md_path.write_text(content, encoding="utf-8")

                created.append({
                    "condensed_name": condensed_name,
                    "target_path": str(target_dir),
                    "original_count": len(group["original_skills"]),
                    "content_lines": len(content.splitlines()),
                })
        except Exception as e:
            errors.append({
                "condensed_name": condensed_name,
                "error": str(e),
            })

    result = {
        "status": "success" if not errors else "partial",
        "dry_run": dry_run,
        "created": len(created),
        "errors": len(errors),
        "output_dir": str(output_dir),
        "details": created,
    }

    if errors:
        result["error_details"] = errors

    print(json.dumps(result, indent=2))
    sys.exit(0 if not errors else 1)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Skill Consolidation Engine for AGI Agent Kit",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Subcommands:
  scan     Analyze all skills and detect consolidation candidates
  map      Generate the consolidation map (provenance mapping)
  preview  Show what a specific consolidation group would look like
  apply    Merge skills into condensed versions (creates new, keeps originals)

Examples:
  python3 skill-creator/scripts/consolidate_skills.py scan \\
    --skills-dir templates/skills/extended --json

  python3 skill-creator/scripts/consolidate_skills.py map \\
    --skills-dir templates/skills/extended \\
    --output templates/skills/consolidation_map.json

  python3 skill-creator/scripts/consolidate_skills.py preview \\
    --group "azure-cosmos" \\
    --skills-dir templates/skills/extended

  python3 skill-creator/scripts/consolidate_skills.py apply \\
    --map templates/skills/consolidation_map.json \\
    --skills-dir templates/skills/extended \\
    --output-dir templates/skills/condensed --dry-run
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Subcommand to run")
    subparsers.required = True

    # --- scan ---
    scan_parser = subparsers.add_parser("scan", help="Analyze skills and detect consolidation candidates")
    scan_parser.add_argument("--skills-dir", required=True, help="Path to skills/extended directory")
    scan_parser.add_argument("--json", action="store_true", dest="json_output", help="JSON-only output")
    scan_parser.add_argument("--min-group-size", type=int, default=3, help="Minimum skills per group (default: 3)")
    scan_parser.add_argument("--store", action="store_true", help="Store results in Qdrant")

    # --- map ---
    map_parser = subparsers.add_parser("map", help="Generate consolidation map JSON")
    map_parser.add_argument("--skills-dir", required=True, help="Path to skills/extended directory")
    map_parser.add_argument("--output", required=True, help="Output path for consolidation_map.json")
    map_parser.add_argument("--min-group-size", type=int, default=2, help="Minimum skills per group (default: 2)")
    map_parser.add_argument("--store", action="store_true", help="Store results in Qdrant")

    # --- preview ---
    preview_parser = subparsers.add_parser("preview", help="Preview a consolidation group")
    preview_parser.add_argument("--group", required=True, help="Condensed group name to preview")
    preview_parser.add_argument("--skills-dir", required=True, help="Path to skills/extended directory")
    preview_parser.add_argument("--json", action="store_true", dest="json_output", help="JSON-only output")

    # --- apply ---
    apply_parser = subparsers.add_parser("apply", help="Apply consolidation (create condensed skills)")
    apply_parser.add_argument("--map", required=True, help="Path to consolidation_map.json")
    apply_parser.add_argument("--skills-dir", required=True, help="Path to skills/extended directory")
    apply_parser.add_argument("--output-dir", required=True, help="Output directory for condensed skills")
    apply_parser.add_argument("--dry-run", action="store_true", help="Show what would be created without writing")

    args = parser.parse_args()

    try:
        if args.command == "scan":
            cmd_scan(args)
        elif args.command == "map":
            cmd_map(args)
        elif args.command == "preview":
            cmd_preview(args)
        elif args.command == "apply":
            cmd_apply(args)
    except KeyboardInterrupt:
        print("\nInterrupted.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(json.dumps({"status": "error", "message": str(e), "type": type(e).__name__}), file=sys.stderr)
        sys.exit(4)


if __name__ == "__main__":
    main()
