#!/usr/bin/env python3
"""
Script: context_mode.py
Purpose: Context Mode — SQLite-based session context tracker with automatic
         re-injection after compaction and token savings reporting.

         Inspired by the Context Mode plugin concept: intercepts heavy data,
         persists session state in SQLite, and re-injects critical context
         when the AI's context window is compacted.

Usage:
    # Initialize a new session (creates/resets SQLite DB)
    python3 execution/context_mode.py init --session-id <id>

    # Track a context event (decision, file change, task state, etc.)
    python3 execution/context_mode.py track --type decision --content "Chose PostgreSQL" --priority high

    # Track with sandbox filtering (heavy data compressed before storage)
    python3 execution/context_mode.py track --type file_read --content "<raw file content>" --sandbox

    # Re-inject context after compaction (returns critical context summary)
    python3 execution/context_mode.py reinject [--max-tokens 2000]

    # Show token savings dashboard (ctx status equivalent)
    python3 execution/context_mode.py status

    # Collect session learnings for skills
    python3 execution/context_mode.py learnings --skill <skill-name>

    # Export session context to Qdrant before ending
    python3 execution/context_mode.py export

Arguments:
    init      - Start new session tracking
    track     - Record a context event
    reinject  - Retrieve critical context after compaction
    status    - Token savings dashboard
    learnings - Collect learnings for a specific skill
    export    - Push session context to Qdrant for cross-session persistence

Exit Codes:
    0 - Success
    1 - No data / empty result
    2 - Database error
    3 - Operation error
"""

import argparse
import hashlib
import json
import os
import re
import sqlite3
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# Configuration
PROJECT_DIR = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TMP_DIR = PROJECT_DIR / ".tmp"
DB_DIR = TMP_DIR / "context_mode"
DEFAULT_DB = DB_DIR / "session.db"
MAX_REINJECT_TOKENS = 4000  # Default max tokens for re-injection
CHARS_PER_TOKEN = 4  # Rough estimate: 1 token ≈ 4 chars


# ─── Database Setup ───────────────────────────────────────────────────────────

def get_db(db_path: str = None) -> sqlite3.Connection:
    """Get SQLite connection, creating tables if needed."""
    path = Path(db_path) if db_path else DEFAULT_DB
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    _create_tables(conn)
    return conn


def _create_tables(conn: sqlite3.Connection):
    """Create context tracking tables."""
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            agent TEXT DEFAULT 'claude',
            project TEXT,
            started_at TEXT NOT NULL,
            ended_at TEXT,
            total_tracked INTEGER DEFAULT 0,
            total_filtered INTEGER DEFAULT 0,
            bytes_raw INTEGER DEFAULT 0,
            bytes_filtered INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS context_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            type TEXT NOT NULL,
            content TEXT NOT NULL,
            content_hash TEXT,
            priority TEXT DEFAULT 'normal',
            sandboxed INTEGER DEFAULT 0,
            raw_bytes INTEGER DEFAULT 0,
            filtered_bytes INTEGER DEFAULT 0,
            tags TEXT DEFAULT '[]',
            skill TEXT,
            FOREIGN KEY (session_id) REFERENCES sessions(id)
        );

        CREATE TABLE IF NOT EXISTS learnings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            skill TEXT NOT NULL,
            learning TEXT NOT NULL,
            severity TEXT DEFAULT 'info',
            applied INTEGER DEFAULT 0,
            FOREIGN KEY (session_id) REFERENCES sessions(id)
        );

        CREATE INDEX IF NOT EXISTS idx_events_session ON context_events(session_id);
        CREATE INDEX IF NOT EXISTS idx_events_type ON context_events(type);
        CREATE INDEX IF NOT EXISTS idx_events_priority ON context_events(priority);
        CREATE INDEX IF NOT EXISTS idx_learnings_skill ON learnings(skill);
    """)
    conn.commit()


# ─── Sandbox Filter ──────────────────────────────────────────────────────────

def sandbox_filter(content: str, content_type: str = "generic") -> dict:
    """Filter heavy content, returning only essential summary.

    This is the core of Context Mode's token saving: instead of dumping
    raw data into context, we extract key information and discard the rest.
    """
    raw_bytes = len(content.encode("utf-8"))

    # Strategy based on content type
    if content_type == "file_read":
        filtered = _filter_file_content(content)
    elif content_type == "grep_result":
        filtered = _filter_grep_results(content)
    elif content_type == "command_output":
        filtered = _filter_command_output(content)
    elif content_type == "error":
        filtered = _filter_error(content)
    else:
        filtered = _filter_generic(content)

    filtered_bytes = len(filtered.encode("utf-8"))

    return {
        "content": filtered,
        "raw_bytes": raw_bytes,
        "filtered_bytes": filtered_bytes,
        "reduction_pct": round((1 - filtered_bytes / max(raw_bytes, 1)) * 100, 1),
    }


def _filter_file_content(content: str) -> str:
    """Extract structure from file content: imports, classes, functions, key comments."""
    lines = content.split("\n")
    if len(lines) <= 50:
        return content  # Small file, keep as-is

    important = []
    important.append(f"[File: {len(lines)} lines total]")

    for i, line in enumerate(lines):
        stripped = line.strip()
        # Keep imports, class/function defs, key comments, decorators
        if any(stripped.startswith(kw) for kw in (
            "import ", "from ", "class ", "def ", "async def ",
            "export ", "const ", "function ", "interface ",
            "# ", "// ", "## ", "@", "\"\"\"", "'''",
        )):
            important.append(f"L{i+1}: {line.rstrip()}")
        elif stripped.startswith("return ") and len(stripped) < 80:
            important.append(f"L{i+1}: {line.rstrip()}")

    return "\n".join(important)


def _filter_grep_results(content: str) -> str:
    """Deduplicate and condense grep results."""
    lines = content.split("\n")
    if len(lines) <= 20:
        return content

    # Group by file, keep first 3 matches per file
    files = {}
    for line in lines:
        if ":" in line:
            parts = line.split(":", 1)
            fname = parts[0]
            if fname not in files:
                files[fname] = []
            if len(files[fname]) < 3:
                files[fname].append(line.rstrip())

    result = [f"[Grep: {len(lines)} matches across {len(files)} files]"]
    for fname, matches in files.items():
        result.extend(matches)
        if len(lines) > len(matches):
            remaining = sum(1 for l in lines if l.startswith(fname + ":")) - len(matches)
            if remaining > 0:
                result.append(f"  ... +{remaining} more in {fname}")

    return "\n".join(result)


def _filter_command_output(content: str) -> str:
    """Keep first/last lines and any errors from command output."""
    lines = content.split("\n")
    if len(lines) <= 30:
        return content

    result = [f"[Output: {len(lines)} lines total]"]
    # First 10 lines
    result.extend(lines[:10])
    # Error lines anywhere
    error_lines = [l for l in lines[10:-10] if any(kw in l.lower() for kw in ("error", "fail", "warn", "exception"))]
    if error_lines:
        result.append("--- errors/warnings ---")
        result.extend(error_lines[:10])
    result.append("--- last 10 lines ---")
    result.extend(lines[-10:])
    return "\n".join(result)


def _filter_error(content: str) -> str:
    """Keep full error — errors are always high-priority context."""
    return content


def _filter_generic(content: str) -> str:
    """Generic filter: truncate to first 100 lines with summary."""
    lines = content.split("\n")
    if len(lines) <= 100:
        return content

    result = lines[:100]
    result.append(f"\n[... truncated {len(lines) - 100} more lines]")
    return "\n".join(result)


# ─── Commands ─────────────────────────────────────────────────────────────────

def cmd_init(args):
    """Initialize a new tracking session."""
    conn = get_db(args.db)
    session_id = args.session_id or f"s-{int(time.time())}"
    now = datetime.now(timezone.utc).isoformat()

    conn.execute(
        "INSERT OR REPLACE INTO sessions (id, agent, project, started_at) VALUES (?, ?, ?, ?)",
        (session_id, args.agent, args.project, now),
    )
    conn.commit()
    conn.close()

    result = {"status": "initialized", "session_id": session_id, "started_at": now}
    print(json.dumps(result, indent=2))
    return 0


def cmd_track(args):
    """Track a context event."""
    conn = get_db(args.db)
    session_id = _get_active_session(conn)
    if not session_id:
        print(json.dumps({"error": "No active session. Run: context_mode.py init"}))
        conn.close()
        return 1

    content = args.content
    raw_bytes = len(content.encode("utf-8"))
    filtered_bytes = raw_bytes
    sandboxed = 0

    # Apply sandbox filter if requested
    if args.sandbox:
        filtered = sandbox_filter(content, args.type)
        content = filtered["content"]
        filtered_bytes = filtered["filtered_bytes"]
        sandboxed = 1

    now = datetime.now(timezone.utc).isoformat()
    content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
    tags = json.dumps(args.tags.split(",")) if args.tags else "[]"

    conn.execute(
        """INSERT INTO context_events
           (session_id, timestamp, type, content, content_hash, priority,
            sandboxed, raw_bytes, filtered_bytes, tags, skill)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (session_id, now, args.type, content, content_hash, args.priority,
         sandboxed, raw_bytes, filtered_bytes, tags, args.skill),
    )

    # Update session counters
    conn.execute(
        """UPDATE sessions SET
           total_tracked = total_tracked + 1,
           total_filtered = total_filtered + ?,
           bytes_raw = bytes_raw + ?,
           bytes_filtered = bytes_filtered + ?
           WHERE id = ?""",
        (sandboxed, raw_bytes, filtered_bytes, session_id),
    )
    conn.commit()

    saved = raw_bytes - filtered_bytes
    result = {
        "status": "tracked",
        "type": args.type,
        "priority": args.priority,
        "sandboxed": bool(sandboxed),
        "raw_bytes": raw_bytes,
        "stored_bytes": filtered_bytes,
        "bytes_saved": saved,
        "tokens_saved_estimate": saved // CHARS_PER_TOKEN,
    }
    print(json.dumps(result, indent=2))
    conn.close()
    return 0


def cmd_reinject(args):
    """Re-inject critical context after compaction.

    Prioritizes: high-priority events > decisions > errors > recent events.
    Returns a structured summary that fits within max_tokens.
    """
    conn = get_db(args.db)
    session_id = _get_active_session(conn)
    if not session_id:
        print(json.dumps({"error": "No active session"}))
        conn.close()
        return 1

    max_chars = args.max_tokens * CHARS_PER_TOKEN

    # Fetch events ordered by priority and recency
    rows = conn.execute(
        """SELECT type, content, priority, timestamp, skill, tags
           FROM context_events
           WHERE session_id = ?
           ORDER BY
             CASE priority
               WHEN 'critical' THEN 0
               WHEN 'high' THEN 1
               WHEN 'normal' THEN 2
               WHEN 'low' THEN 3
             END,
             timestamp DESC""",
        (session_id,),
    ).fetchall()

    if not rows:
        print(json.dumps({"status": "empty", "message": "No context events to reinject"}))
        conn.close()
        return 1

    # Build re-injection payload
    sections = {
        "decisions": [],
        "errors": [],
        "current_task": [],
        "file_changes": [],
        "other": [],
    }

    for row in rows:
        entry = f"[{row['type']}] {row['content']}"
        if row["skill"]:
            entry = f"[{row['type']}|{row['skill']}] {row['content']}"

        if row["type"] in ("decision", "architecture"):
            sections["decisions"].append(entry)
        elif row["type"] in ("error", "fix"):
            sections["errors"].append(entry)
        elif row["type"] in ("task", "goal", "progress"):
            sections["current_task"].append(entry)
        elif row["type"] in ("file_read", "file_change", "edit"):
            sections["file_changes"].append(entry)
        else:
            sections["other"].append(entry)

    # Assemble within token budget
    output_parts = []
    chars_used = 0

    header = "=== CONTEXT RE-INJECTION (post-compaction recovery) ===\n"
    chars_used += len(header)
    output_parts.append(header)

    section_order = ["current_task", "decisions", "errors", "file_changes", "other"]
    section_labels = {
        "current_task": "Current Task & Progress",
        "decisions": "Key Decisions",
        "errors": "Errors & Fixes",
        "file_changes": "Files Touched",
        "other": "Other Context",
    }

    for section_key in section_order:
        items = sections[section_key]
        if not items:
            continue

        label = f"\n## {section_labels[section_key]}\n"
        if chars_used + len(label) > max_chars:
            break

        output_parts.append(label)
        chars_used += len(label)

        for item in items:
            line = f"- {item}\n"
            if chars_used + len(line) > max_chars:
                output_parts.append(f"  ... ({len(items) - items.index(item)} more truncated)\n")
                break
            output_parts.append(line)
            chars_used += len(line)

    payload = "".join(output_parts)

    result = {
        "status": "reinjected",
        "events_total": len(rows),
        "chars_used": chars_used,
        "tokens_estimate": chars_used // CHARS_PER_TOKEN,
        "max_tokens": args.max_tokens,
        "payload": payload,
    }
    print(json.dumps(result, indent=2))
    conn.close()
    return 0


def cmd_status(args):
    """Token savings dashboard — equivalent to ctx status."""
    conn = get_db(args.db)
    session_id = _get_active_session(conn)

    if not session_id:
        print(json.dumps({"error": "No active session"}))
        conn.close()
        return 1

    session = conn.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()
    events = conn.execute(
        "SELECT type, COUNT(*) as cnt, SUM(raw_bytes) as raw, SUM(filtered_bytes) as filtered "
        "FROM context_events WHERE session_id = ? GROUP BY type",
        (session_id,),
    ).fetchall()

    learnings_count = conn.execute(
        "SELECT COUNT(*) FROM learnings WHERE session_id = ?", (session_id,)
    ).fetchone()[0]

    total_raw = session["bytes_raw"] or 0
    total_filtered = session["bytes_filtered"] or 0
    total_saved = total_raw - total_filtered
    savings_pct = round((total_saved / max(total_raw, 1)) * 100, 1)

    breakdown = []
    for e in events:
        raw = e["raw"] or 0
        filt = e["filtered"] or 0
        breakdown.append({
            "type": e["type"],
            "count": e["cnt"],
            "raw_bytes": raw,
            "stored_bytes": filt,
            "saved_bytes": raw - filt,
        })

    result = {
        "session_id": session_id,
        "agent": session["agent"],
        "project": session["project"],
        "started_at": session["started_at"],
        "events_tracked": session["total_tracked"] or 0,
        "events_sandboxed": session["total_filtered"] or 0,
        "total_raw_bytes": total_raw,
        "total_stored_bytes": total_filtered,
        "total_saved_bytes": total_saved,
        "token_savings_estimate": total_saved // CHARS_PER_TOKEN,
        "savings_percentage": savings_pct,
        "learnings_recorded": learnings_count,
        "breakdown": breakdown,
    }

    if args.json_output:
        print(json.dumps(result, indent=2))
    else:
        print()
        print(f"  Context Mode Status — session [{session_id}]")
        print(f"  Agent: {session['agent']}  |  Project: {session['project'] or 'n/a'}")
        print(f"  Started: {session['started_at']}")
        print()
        print(f"  Events tracked:    {result['events_tracked']}")
        print(f"  Events sandboxed:  {result['events_sandboxed']}")
        print(f"  Learnings:         {learnings_count}")
        print()
        print(f"  Raw data processed:  {_fmt_bytes(total_raw)}")
        print(f"  Data stored:         {_fmt_bytes(total_filtered)}")
        print(f"  Data filtered out:   {_fmt_bytes(total_saved)}")
        print(f"  Token savings:       ~{result['token_savings_estimate']} tokens ({savings_pct}% reduction)")
        print()
        if breakdown:
            print("  Breakdown by type:")
            for b in breakdown:
                saved_b = b["saved_bytes"]
                print(f"    {b['type']:20s}  {b['count']:4d} events  {_fmt_bytes(b['raw_bytes']):>10s} raw  {_fmt_bytes(saved_b):>10s} saved")
        print()

    conn.close()
    return 0


def cmd_learnings(args):
    """Record or retrieve learnings for a skill."""
    conn = get_db(args.db)
    session_id = _get_active_session(conn)

    if not session_id:
        print(json.dumps({"error": "No active session"}))
        conn.close()
        return 1

    if args.add:
        # Store a new learning
        now = datetime.now(timezone.utc).isoformat()
        conn.execute(
            "INSERT INTO learnings (session_id, timestamp, skill, learning, severity) VALUES (?, ?, ?, ?, ?)",
            (session_id, now, args.skill, args.add, args.severity or "info"),
        )
        conn.commit()
        print(json.dumps({"status": "stored", "skill": args.skill, "learning": args.add}))
    else:
        # Retrieve learnings for skill
        rows = conn.execute(
            "SELECT * FROM learnings WHERE skill = ? ORDER BY timestamp DESC",
            (args.skill,),
        ).fetchall()

        items = [{"learning": r["learning"], "severity": r["severity"],
                   "timestamp": r["timestamp"], "applied": bool(r["applied"])} for r in rows]
        print(json.dumps({"skill": args.skill, "learnings": items, "count": len(items)}, indent=2))

    conn.close()
    return 0


def cmd_export(args):
    """Export session context to Qdrant for cross-session persistence."""
    conn = get_db(args.db)
    session_id = _get_active_session(conn)

    if not session_id:
        print(json.dumps({"error": "No active session"}))
        conn.close()
        return 1

    # Gather high-priority context
    rows = conn.execute(
        """SELECT type, content, priority, skill
           FROM context_events
           WHERE session_id = ? AND priority IN ('critical', 'high')
           ORDER BY timestamp DESC
           LIMIT 20""",
        (session_id,),
    ).fetchall()

    # Gather learnings
    learnings_rows = conn.execute(
        "SELECT skill, learning, severity FROM learnings WHERE session_id = ?",
        (session_id,),
    ).fetchall()

    # Build export summary
    decisions = [r["content"] for r in rows if r["type"] in ("decision", "architecture")]
    errors = [r["content"] for r in rows if r["type"] in ("error", "fix")]
    learnings_list = [f"[{r['skill']}] {r['learning']}" for r in learnings_rows]

    export_content = []
    if decisions:
        export_content.append("Decisions: " + "; ".join(decisions[:10]))
    if errors:
        export_content.append("Errors/Fixes: " + "; ".join(errors[:5]))
    if learnings_list:
        export_content.append("Learnings: " + "; ".join(learnings_list[:10]))

    if not export_content:
        print(json.dumps({"status": "empty", "message": "No high-priority context to export"}))
        conn.close()
        return 1

    # Call memory_manager.py to store in Qdrant
    import subprocess
    memory_script = PROJECT_DIR / "execution" / "memory_manager.py"
    content_str = " | ".join(export_content)

    try:
        cmd = [
            "python3", str(memory_script), "store",
            "--content", content_str,
            "--type", "conversation",
            "--tags", "context-mode,session-export",
        ]
        if args.project:
            cmd.extend(["--project", args.project])

        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=15, cwd=str(PROJECT_DIR))
        if proc.returncode == 0:
            result = {"status": "exported", "events": len(rows), "learnings": len(learnings_rows)}
            try:
                result["qdrant_response"] = json.loads(proc.stdout)
            except json.JSONDecodeError:
                result["raw_output"] = proc.stdout.strip()
        else:
            result = {"status": "error", "stderr": proc.stderr.strip()}
    except Exception as e:
        result = {"status": "error", "message": str(e)}

    # Mark session as ended
    now = datetime.now(timezone.utc).isoformat()
    conn.execute("UPDATE sessions SET ended_at = ? WHERE id = ?", (now, session_id))
    conn.commit()
    conn.close()

    print(json.dumps(result, indent=2))
    return 0


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _get_active_session(conn: sqlite3.Connection) -> str:
    """Get the most recent active (non-ended) session ID."""
    row = conn.execute(
        "SELECT id FROM sessions WHERE ended_at IS NULL ORDER BY started_at DESC LIMIT 1"
    ).fetchone()
    return row["id"] if row else None


def _fmt_bytes(n: int) -> str:
    """Format bytes to human-readable."""
    if n < 1024:
        return f"{n} B"
    elif n < 1024 * 1024:
        return f"{n / 1024:.1f} KB"
    else:
        return f"{n / (1024 * 1024):.1f} MB"


# ─── CLI Entry Point ─────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Context Mode: SQLite session tracker with sandbox filtering and re-injection"
    )
    parser.add_argument("--db", help="Path to SQLite database (default: .tmp/context_mode/session.db)")
    sub = parser.add_subparsers(dest="command")

    # init
    p_init = sub.add_parser("init", help="Initialize a new tracking session")
    p_init.add_argument("--session-id", help="Custom session ID")
    p_init.add_argument("--agent", default="claude", help="Agent name")
    p_init.add_argument("--project", help="Project name")

    # track
    p_track = sub.add_parser("track", help="Track a context event")
    p_track.add_argument("--type", required=True,
                         help="Event type: decision, error, fix, task, goal, progress, "
                              "file_read, file_change, edit, architecture, command_output, grep_result")
    p_track.add_argument("--content", required=True, help="Event content")
    p_track.add_argument("--priority", default="normal",
                         choices=["critical", "high", "normal", "low"],
                         help="Event priority for re-injection ordering")
    p_track.add_argument("--sandbox", action="store_true",
                         help="Apply sandbox filter to compress content before storing")
    p_track.add_argument("--tags", help="Comma-separated tags")
    p_track.add_argument("--skill", help="Associated skill name")

    # reinject
    p_reinject = sub.add_parser("reinject", help="Re-inject context after compaction")
    p_reinject.add_argument("--max-tokens", type=int, default=MAX_REINJECT_TOKENS,
                            help=f"Max tokens for re-injection payload (default: {MAX_REINJECT_TOKENS})")

    # status
    p_status = sub.add_parser("status", help="Token savings dashboard")
    p_status.add_argument("--json", action="store_true", dest="json_output",
                          help="JSON output only")

    # learnings
    p_learn = sub.add_parser("learnings", help="Record or retrieve skill learnings")
    p_learn.add_argument("--skill", required=True, help="Skill name")
    p_learn.add_argument("--add", help="Add a new learning")
    p_learn.add_argument("--severity", choices=["info", "warning", "critical"],
                         help="Learning severity")

    # export
    p_export = sub.add_parser("export", help="Export session context to Qdrant")
    p_export.add_argument("--project", help="Project name for Qdrant tag")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    commands = {
        "init": cmd_init,
        "track": cmd_track,
        "reinject": cmd_reinject,
        "status": cmd_status,
        "learnings": cmd_learnings,
        "export": cmd_export,
    }

    try:
        exit_code = commands[args.command](args)
        sys.exit(exit_code or 0)
    except sqlite3.Error as e:
        print(json.dumps({"error": f"Database error: {e}"}), file=sys.stderr)
        sys.exit(2)
    except Exception as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        sys.exit(3)


if __name__ == "__main__":
    main()
