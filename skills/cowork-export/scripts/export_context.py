#!/usr/bin/env python3
"""
Script: export_context.py
Purpose: Export current session context as a portable briefing document for Claude
         on claude.ai (Cowork). Gathers git state, Qdrant memory, and user-specified
         files into a single markdown document suitable for pasting into a remote
         Claude instance.

Usage:
    python3 skills/cowork-export/scripts/export_context.py \
        --project myapp \
        --task "Review the auth module changes and suggest improvements" \
        --output .tmp/cowork_briefing.md

    python3 skills/cowork-export/scripts/export_context.py \
        --git-only --task "Summarize changes" --clipboard

Arguments:
    --project        Project name for Qdrant query (auto-detect from git if omitted)
    --task           Task assignment for the remote agent (required)
    --output         Output file path (default: stdout)
    --clipboard      Copy to macOS clipboard via pbcopy
    --git-only       Skip Qdrant, use git context only
    --include-files  Space-separated file paths to embed inline
    --since          Qdrant lookback in minutes (default: 120)
    --max-memory     Max Qdrant chunks to include (default: 10)
    --deadline       Deadline for the task
    --priority       Priority: low, medium, high (default: medium)
    --constraints    Additional constraints or guidelines
    --compact        Shorter output format

Exit Codes:
    0 - Success
    1 - Invalid arguments
    2 - Git error
    3 - Qdrant error (non-fatal if --git-only)
    4 - File I/O error
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(os.path.dirname(os.path.abspath(__file__))).parent.parent.parent
QDRANT_URL = os.environ.get("QDRANT_URL", "http://localhost:6333")


def run_git(args: list, cwd: str = None) -> str:
    """Run a git command and return stdout, or empty string on error."""
    try:
        result = subprocess.run(
            ["git"] + args,
            capture_output=True, text=True, timeout=15,
            cwd=cwd or str(PROJECT_ROOT),
        )
        return result.stdout.strip() if result.returncode == 0 else ""
    except Exception:
        return ""


def get_git_context(compact: bool = False) -> dict:
    """Gather git state: branch, remote, recent commits, changed files."""
    ctx = {}

    # Branch
    ctx["branch"] = run_git(["rev-parse", "--abbrev-ref", "HEAD"])

    # Remote URL → project name
    remote = run_git(["remote", "get-url", "origin"])
    if remote:
        # Extract repo name from URL
        name = remote.rstrip("/").split("/")[-1]
        if name.endswith(".git"):
            name = name[:-4]
        ctx["repo_name"] = name
        ctx["remote_url"] = remote
    else:
        ctx["repo_name"] = PROJECT_ROOT.name
        ctx["remote_url"] = ""

    # Recent commits
    log_count = "5" if not compact else "3"
    ctx["recent_commits"] = run_git([
        "log", f"-{log_count}", "--oneline", "--no-decorate"
    ])

    # Changed files (staged + unstaged)
    ctx["diff_stat"] = run_git(["diff", "--stat", "HEAD"])

    # Untracked files
    ctx["untracked"] = run_git(["ls-files", "--others", "--exclude-standard"])

    # Staged files
    ctx["staged"] = run_git(["diff", "--cached", "--name-only"])

    # Full diff (limited to avoid huge outputs)
    diff = run_git(["diff", "HEAD"])
    if len(diff) > 15000:
        diff = diff[:15000] + "\n\n... [diff truncated at 15000 chars] ..."
    ctx["diff"] = diff

    return ctx


def get_qdrant_context(project: str = None, since_minutes: int = 120, max_chunks: int = 10) -> list:
    """Retrieve recent decisions and learnings from Qdrant."""
    try:
        from urllib.request import Request, urlopen

        scroll_body = {
            "limit": 100,
            "with_payload": True,
            "with_vector": False,
        }

        if project:
            scroll_body["filter"] = {
                "must": [{"key": "project", "match": {"value": project}}]
            }

        req = Request(
            f"{QDRANT_URL}/collections/agent_memory/points/scroll",
            data=json.dumps(scroll_body).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        from urllib.request import urlopen
        with urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())

        points = data.get("result", {}).get("points", [])

        # Filter by recency
        from datetime import timedelta
        cutoff = (datetime.now(timezone.utc) - timedelta(minutes=since_minutes)).isoformat()

        recent = []
        for point in points:
            payload = point.get("payload", {})
            ts = payload.get("timestamp", "")
            if ts and ts >= cutoff:
                recent.append({
                    "content": payload.get("content", ""),
                    "type": payload.get("type", "unknown"),
                    "timestamp": ts,
                    "tags": payload.get("tags", []),
                })

        # Sort by timestamp descending
        recent.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return recent[:max_chunks]

    except Exception as e:
        print(f"Warning: Could not query Qdrant: {e}", file=sys.stderr)
        return []


def read_files(file_paths: list) -> dict:
    """Read specified files and return their contents."""
    contents = {}
    for fp in file_paths:
        path = Path(fp)
        if not path.is_absolute():
            path = PROJECT_ROOT / path
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
            # Truncate large files
            if len(text) > 10000:
                text = text[:10000] + "\n\n... [truncated at 10000 chars] ..."
            contents[str(Path(fp))] = text
        except Exception as e:
            contents[str(Path(fp))] = f"[Error reading file: {e}]"
    return contents


def build_briefing(
    git_ctx: dict,
    memory_chunks: list,
    file_contents: dict,
    task: str,
    deadline: str = None,
    priority: str = "medium",
    constraints: str = None,
    compact: bool = False,
) -> str:
    """Assemble the full briefing document."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = []

    # Header
    lines.append(f"# Cowork Briefing: {git_ctx.get('repo_name', 'project')}")
    lines.append(f"")
    lines.append(f"> Exported: {now}")
    lines.append(f"> Branch: `{git_ctx.get('branch', 'unknown')}`")
    if deadline:
        lines.append(f"> Deadline: {deadline}")
    lines.append(f"> Priority: {priority}")
    lines.append("")

    # Task assignment (most important — top of document)
    lines.append("## Task Assignment")
    lines.append("")
    lines.append(task)
    lines.append("")

    if constraints:
        lines.append("### Constraints")
        lines.append("")
        lines.append(constraints)
        lines.append("")

    # Project context
    lines.append("## Project Context")
    lines.append("")
    if git_ctx.get("remote_url"):
        lines.append(f"- **Repository**: {git_ctx['remote_url']}")
    lines.append(f"- **Branch**: `{git_ctx.get('branch', 'unknown')}`")
    lines.append("")

    # Recent commits
    if git_ctx.get("recent_commits"):
        lines.append("### Recent Commits")
        lines.append("")
        lines.append("```")
        lines.append(git_ctx["recent_commits"])
        lines.append("```")
        lines.append("")

    # Changed files
    has_changes = git_ctx.get("diff_stat") or git_ctx.get("untracked") or git_ctx.get("staged")
    if has_changes:
        lines.append("### Current Changes")
        lines.append("")
        if git_ctx.get("diff_stat"):
            lines.append("```")
            lines.append(git_ctx["diff_stat"])
            lines.append("```")
        if git_ctx.get("untracked"):
            lines.append("")
            lines.append("**Untracked files:**")
            for f in git_ctx["untracked"].split("\n")[:20]:
                if f.strip():
                    lines.append(f"- `{f.strip()}`")
        lines.append("")

    # Diff (if not compact)
    if not compact and git_ctx.get("diff"):
        lines.append("### Diff")
        lines.append("")
        lines.append("```diff")
        lines.append(git_ctx["diff"])
        lines.append("```")
        lines.append("")

    # Memory / decisions
    if memory_chunks:
        lines.append("## Session Context (from Memory)")
        lines.append("")
        for i, chunk in enumerate(memory_chunks, 1):
            content = chunk["content"]
            # Strip agent prefix
            if content.startswith("[") and "]" in content:
                content = content[content.index("]") + 1:].strip()
            mem_type = chunk.get("type", "")
            if compact:
                lines.append(f"{i}. [{mem_type}] {content[:200]}")
            else:
                lines.append(f"### {i}. {mem_type.capitalize()}")
                lines.append("")
                lines.append(content[:500])
                tags = chunk.get("tags", [])
                if tags:
                    lines.append(f"")
                    lines.append(f"*Tags: {', '.join(tags)}*")
                lines.append("")

    # Inline file contents
    if file_contents:
        lines.append("## Code Context")
        lines.append("")
        for filepath, content in file_contents.items():
            lines.append(f"### `{filepath}`")
            lines.append("")
            # Detect language for syntax highlighting
            ext = Path(filepath).suffix.lstrip(".")
            lang = {"py": "python", "js": "javascript", "ts": "typescript",
                     "md": "markdown", "sh": "bash", "json": "json",
                     "yaml": "yaml", "yml": "yaml"}.get(ext, ext)
            lines.append(f"```{lang}")
            lines.append(content)
            lines.append("```")
            lines.append("")

    # Footer with instructions for the remote agent
    lines.append("---")
    lines.append("")
    lines.append("## Instructions for Remote Agent")
    lines.append("")
    lines.append("You are acting as a remote sub-agent for a local Claude Code session.")
    lines.append("The context above represents the current state of work. Your task is")
    lines.append("described in the **Task Assignment** section above.")
    lines.append("")
    lines.append("Guidelines:")
    lines.append("- Focus exclusively on the assigned task")
    lines.append("- Reference specific files and line numbers when making suggestions")
    lines.append("- If you produce code, make it copy-pasteable")
    lines.append("- If you need information not provided, state what's missing")
    lines.append(f"- When done, summarize your output so it can be fed back to the local session")
    lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Export session context as a Cowork briefing document",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--project", help="Project name for Qdrant query (auto-detect from git)")
    parser.add_argument("--task", required=True, help="Task for the remote agent")
    parser.add_argument("--output", help="Output file path (default: stdout)")
    parser.add_argument("--clipboard", action="store_true", help="Copy to macOS clipboard")
    parser.add_argument("--git-only", action="store_true", help="Skip Qdrant, git context only")
    parser.add_argument("--include-files", nargs="+", default=[], help="Files to embed inline")
    parser.add_argument("--since", type=int, default=120, help="Qdrant lookback minutes (default: 120)")
    parser.add_argument("--max-memory", type=int, default=10, help="Max Qdrant chunks (default: 10)")
    parser.add_argument("--deadline", help="Task deadline")
    parser.add_argument("--priority", default="medium", choices=["low", "medium", "high"])
    parser.add_argument("--constraints", help="Additional constraints")
    parser.add_argument("--compact", action="store_true", help="Shorter output")
    args = parser.parse_args()

    # 1. Git context
    git_ctx = get_git_context(args.compact)

    # Auto-detect project name
    project = args.project or git_ctx.get("repo_name", "")

    # 2. Qdrant memory (unless --git-only)
    memory_chunks = []
    if not args.git_only:
        memory_chunks = get_qdrant_context(project, args.since, args.max_memory)

    # 3. Read included files
    file_contents = {}
    if args.include_files:
        file_contents = read_files(args.include_files)

    # 4. Build briefing
    briefing = build_briefing(
        git_ctx=git_ctx,
        memory_chunks=memory_chunks,
        file_contents=file_contents,
        task=args.task,
        deadline=args.deadline,
        priority=args.priority,
        constraints=args.constraints,
        compact=args.compact,
    )

    # 5. Output
    if args.clipboard:
        try:
            proc = subprocess.run(
                ["pbcopy"], input=briefing.encode(), timeout=5,
            )
            if proc.returncode == 0:
                # Also print stats
                line_count = briefing.count("\n")
                char_count = len(briefing)
                print(json.dumps({
                    "status": "copied_to_clipboard",
                    "lines": line_count,
                    "chars": char_count,
                    "project": project,
                    "memory_chunks": len(memory_chunks),
                    "files_included": len(file_contents),
                }))
                sys.exit(0)
            else:
                print("Error: pbcopy failed", file=sys.stderr)
                sys.exit(4)
        except FileNotFoundError:
            print("Error: pbcopy not found (macOS only)", file=sys.stderr)
            sys.exit(4)

    if args.output:
        output_path = Path(args.output)
        if not output_path.is_absolute():
            output_path = PROJECT_ROOT / output_path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(briefing, encoding="utf-8")
        print(json.dumps({
            "status": "exported",
            "path": str(output_path),
            "lines": briefing.count("\n"),
            "chars": len(briefing),
            "project": project,
            "memory_chunks": len(memory_chunks),
            "files_included": len(file_contents),
        }))
        sys.exit(0)
    else:
        # stdout
        print(briefing)
        sys.exit(0)


if __name__ == "__main__":
    main()
