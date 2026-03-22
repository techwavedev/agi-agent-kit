#!/usr/bin/env python3
"""
Context Mode — PostToolUse Hook (Sandbox Filter)

Intercepts heavy tool outputs (Read, Grep, WebFetch, Glob, Bash) and:
1. Compresses content before it enters the context window
2. Tracks the event in SQLite (context_mode.py)
3. Optionally stores high-value context in Qdrant for cross-session persistence

Reads JSON from stdin (Claude Code hook protocol), outputs JSON to stdout.
Exit 0 = allow (with optional modifications), exit 2 = block with feedback.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

# ─── Configuration ────────────────────────────────────────────────────────────

# Threshold in bytes: only filter outputs larger than this
COMPRESSION_THRESHOLD = int(os.environ.get("CTX_COMPRESSION_THRESHOLD", "8192"))  # 8KB default

# Tools to apply sandbox filtering
COMPRESSIBLE_TOOLS = {"Read", "Grep", "WebFetch", "Glob", "Bash"}

# Tools whose output should also be persisted to Qdrant
QDRANT_PERSIST_TOOLS = {"Read", "Grep"}

# Max lines to keep from head/tail for file reads
HEAD_LINES = 60
TAIL_LINES = 20

# Project root (relative to this hook's location)
HOOK_DIR = Path(__file__).resolve().parent
PROJECT_DIR = HOOK_DIR.parent.parent  # .claude/hooks -> .claude -> project root
CONTEXT_MODE_SCRIPT = PROJECT_DIR / "execution" / "context_mode.py"
MEMORY_MANAGER_SCRIPT = PROJECT_DIR / "execution" / "memory_manager.py"


# ─── Compression Strategies ──────────────────────────────────────────────────

def compress_read(output: str, file_path: str = "") -> str:
    """Compress file read output: keep structure, trim bulk."""
    lines = output.split("\n")
    total = len(lines)

    if total <= HEAD_LINES + TAIL_LINES:
        return output  # Small enough, keep as-is

    ext = Path(file_path).suffix if file_path else ""
    header = f"[CTX-FILTERED] {file_path} ({total} lines, showing head+tail)"

    head = lines[:HEAD_LINES]
    tail = lines[-TAIL_LINES:]
    omitted = total - HEAD_LINES - TAIL_LINES

    return "\n".join([header, *head, f"\n... [{omitted} lines omitted] ...\n", *tail])


def compress_grep(output: str) -> str:
    """Compress grep results: group by file, limit matches."""
    lines = output.split("\n")
    total = len(lines)

    if total <= 30:
        return output

    # Group by file path
    files = {}
    for line in lines:
        if ":" in line and not line.startswith(" "):
            fpath = line.split(":")[0]
            if fpath not in files:
                files[fpath] = []
            if len(files[fpath]) < 3:
                files[fpath].append(line.rstrip())
        elif files:
            # Continuation line, add to last file
            last_file = list(files.keys())[-1]
            if len(files[last_file]) < 3:
                files[last_file].append(line.rstrip())

    result = [f"[CTX-FILTERED] {total} grep matches across {len(files)} files"]
    for fpath, matches in list(files.items())[:15]:
        result.extend(matches)
        file_total = sum(1 for l in lines if l.startswith(fpath + ":"))
        if file_total > len(matches):
            result.append(f"  ... +{file_total - len(matches)} more in {fpath}")

    if len(files) > 15:
        result.append(f"  ... +{len(files) - 15} more files")

    return "\n".join(result)


def compress_bash(output: str) -> str:
    """Compress command output: head + errors + tail."""
    lines = output.split("\n")
    total = len(lines)

    if total <= 40:
        return output

    result = [f"[CTX-FILTERED] Command output ({total} lines)"]
    result.extend(lines[:15])

    # Scan for errors/warnings in the middle
    middle = lines[15:-15]
    errors = [l for l in middle if any(kw in l.lower() for kw in ("error", "fail", "warn", "exception", "traceback"))]
    if errors:
        result.append("--- errors/warnings ---")
        result.extend(errors[:10])

    result.append("--- last 15 lines ---")
    result.extend(lines[-15:])
    return "\n".join(result)


def compress_glob(output: str) -> str:
    """Compress glob results: keep all but add summary."""
    lines = output.split("\n")
    if len(lines) <= 50:
        return output

    result = [f"[CTX-FILTERED] {len(lines)} files matched"]
    result.extend(lines[:50])
    result.append(f"... +{len(lines) - 50} more files")
    return "\n".join(result)


def compress_webfetch(output: str) -> str:
    """Compress web content: first 3KB."""
    if len(output) <= 3072:
        return output

    return output[:3072] + f"\n[CTX-FILTERED] Truncated from {len(output)} to 3072 chars"


# ─── SQLite Tracking ─────────────────────────────────────────────────────────

def track_in_sqlite(tool_name: str, content: str, raw_bytes: int, filtered_bytes: int, priority: str = "normal"):
    """Track the filtering event in context_mode.py SQLite."""
    if not CONTEXT_MODE_SCRIPT.exists():
        return

    type_map = {
        "Read": "file_read",
        "Grep": "grep_result",
        "Bash": "command_output",
        "Glob": "file_read",
        "WebFetch": "file_read",
    }

    try:
        subprocess.run(
            [
                "python3", str(CONTEXT_MODE_SCRIPT), "track",
                "--type", type_map.get(tool_name, "generic"),
                "--content", content[:500],  # Store summary only
                "--priority", priority,
                "--sandbox",
            ],
            capture_output=True, text=True, timeout=5,
            cwd=str(PROJECT_DIR),
        )
    except Exception:
        pass  # Non-blocking: don't fail the hook if tracking fails


def persist_to_qdrant(tool_name: str, content: str, file_path: str = ""):
    """Store high-value context in Qdrant for cross-session memory."""
    if not MEMORY_MANAGER_SCRIPT.exists():
        return

    # Only persist meaningful content (decisions, architecture, key code)
    summary = content[:300]
    if file_path:
        summary = f"[{file_path}] {summary}"

    try:
        subprocess.run(
            [
                "python3", str(MEMORY_MANAGER_SCRIPT), "store",
                "--content", summary,
                "--type", "technical",
                "--tags", f"context-mode,auto-tracked,{tool_name.lower()}",
            ],
            capture_output=True, text=True, timeout=10,
            cwd=str(PROJECT_DIR),
        )
    except Exception:
        pass  # Non-blocking


# ─── Main Hook Logic ─────────────────────────────────────────────────────────

def main():
    try:
        hook_input = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, EOFError):
        sys.exit(0)  # Can't parse input, allow through

    tool_name = hook_input.get("tool_name", "")
    tool_input = hook_input.get("tool_input", {})
    tool_response = hook_input.get("tool_response", {})

    # Only process compressible tools
    if tool_name not in COMPRESSIBLE_TOOLS:
        sys.exit(0)

    # Get the output content
    output = ""
    if isinstance(tool_response, dict):
        output = tool_response.get("output", "") or tool_response.get("content", "") or ""
    elif isinstance(tool_response, str):
        output = tool_response

    if not output:
        sys.exit(0)

    raw_bytes = len(output.encode("utf-8"))

    # Skip if below threshold
    if raw_bytes <= COMPRESSION_THRESHOLD:
        # Still track in SQLite (no compression needed)
        track_in_sqlite(tool_name, output[:200], raw_bytes, raw_bytes)
        sys.exit(0)

    # Apply compression strategy
    file_path = tool_input.get("file_path", "") or tool_input.get("path", "")

    if tool_name == "Read":
        compressed = compress_read(output, file_path)
    elif tool_name == "Grep":
        compressed = compress_grep(output)
    elif tool_name == "Bash":
        compressed = compress_bash(output)
    elif tool_name == "Glob":
        compressed = compress_glob(output)
    elif tool_name == "WebFetch":
        compressed = compress_webfetch(output)
    else:
        compressed = output

    filtered_bytes = len(compressed.encode("utf-8"))
    saved = raw_bytes - filtered_bytes
    saved_pct = round((saved / max(raw_bytes, 1)) * 100, 1)

    # Track in SQLite
    track_in_sqlite(tool_name, compressed[:200], raw_bytes, filtered_bytes, "normal")

    # Optionally persist to Qdrant (for high-value reads)
    qdrant_enabled = os.environ.get("CTX_QDRANT_PERSIST", "false").lower() == "true"
    if qdrant_enabled and tool_name in QDRANT_PERSIST_TOOLS and raw_bytes > COMPRESSION_THRESHOLD * 2:
        persist_to_qdrant(tool_name, compressed, file_path)

    # If no meaningful compression, allow through unchanged
    if saved_pct < 10:
        sys.exit(0)

    # Return modified output
    hook_output = {
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": (
                f"[Context Mode] {tool_name} output compressed: "
                f"{raw_bytes // 1024}KB -> {filtered_bytes // 1024}KB "
                f"({saved_pct}% reduction, ~{saved // 4} tokens saved)"
            ),
        }
    }

    print(json.dumps(hook_output))
    sys.exit(0)


if __name__ == "__main__":
    main()
