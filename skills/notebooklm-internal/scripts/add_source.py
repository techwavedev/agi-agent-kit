#!/usr/bin/env python3
"""
Script: add_source.py
Purpose: Headless-Playwright add-source workflow for NotebookLM. Adds a primary
         source (text / url / file / pdf / image) plus optional attachments to a
         single notebook, within one browser session, and appends an audit record
         to skill-local `library.jsonl` (one JSON line per add for atomic safety).

Usage:
    python add_source.py \
        (--notebook-id <id> | --notebook-url <url> | --notebook-name <name>) \
        --source-type {text,url,file,pdf,image} \
        (--content <path> | --url <url>) \
        [--title <str>] \
        [--attachments <path> ...] \
        [--config <path>] \
        [--timeout <sec>] \
        [--dry-run] [--json]

Exit Codes:
    0 - Success
    1 - Invalid arguments / cannot resolve notebook
    2 - Input file not found
    3 - Authentication expired (cookies invalid)
    4 - Processing / browser error
    5 - Processing timeout (partial; record still written)
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Make this script import-safe from the skill's scripts directory.
SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))

LIBRARY_JSONL = SKILL_DIR / "library.jsonl"

VALID_SOURCE_TYPES = {"text", "url", "file", "pdf", "image"}

DEFAULT_TIMEOUT_SECONDS = 120


# ---------------------------------------------------------------------------
# Notebook resolution
# ---------------------------------------------------------------------------

NOTEBOOK_URL_ID_RE = re.compile(
    r"notebooklm\.google\.com/notebook/(?P<id>[A-Za-z0-9_\-]+)"
)


def parse_notebook_id_from_url(url: str) -> Optional[str]:
    """Extract the notebook id segment from a NotebookLM URL."""
    if not url:
        return None
    m = NOTEBOOK_URL_ID_RE.search(url)
    return m.group("id") if m else None


def resolve_notebook_id(
    notebook_id: Optional[str],
    notebook_url: Optional[str],
    notebook_name: Optional[str],
) -> Tuple[Optional[str], Optional[str]]:
    """
    Resolve notebook id using precedence: --notebook-id → --notebook-url →
    --notebook-name (via ensure_notebook, lazy-imported).

    Returns (notebook_id, error_message). If id is None, error_message explains
    why and callers should exit 1.
    """
    if notebook_id:
        return notebook_id, None

    if notebook_url:
        nid = parse_notebook_id_from_url(notebook_url)
        if nid:
            return nid, None
        return None, f"Could not parse notebook id from --notebook-url: {notebook_url}"

    if notebook_name:
        try:
            # Lazy import — sibling script may not exist yet in this tree.
            from ensure_notebook import resolve_notebook  # type: ignore
        except Exception:
            return (
                None,
                "Cannot resolve --notebook-name: ensure_notebook.resolve_notebook "
                "is not available. Please pass --notebook-id or --notebook-url.",
            )
        try:
            resolved = resolve_notebook(notebook_name)  # type: ignore[misc]
        except Exception as exc:
            return None, f"resolve_notebook failed: {exc}"
        if isinstance(resolved, str) and resolved:
            return resolved, None
        if isinstance(resolved, dict):
            nid = resolved.get("id") or resolved.get("notebook_id")
            if nid:
                return nid, None
        return None, f"resolve_notebook did not return an id for: {notebook_name}"

    return None, "One of --notebook-id / --notebook-url / --notebook-name is required."


def notebook_url_from_id(notebook_id: str) -> str:
    return f"https://notebooklm.google.com/notebook/{notebook_id}"


# ---------------------------------------------------------------------------
# Library audit log
# ---------------------------------------------------------------------------


def append_library_record(record: Dict[str, Any], path: Path = LIBRARY_JSONL) -> None:
    """
    Append a single JSON line to library.jsonl. Uses a single write() with a
    trailing newline — POSIX guarantees atomicity for writes smaller than
    PIPE_BUF, and for regular files this append pattern is the standard
    append-safe approach used for JSONL logs.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n"
    # Open in append-binary to avoid any platform newline translation and keep
    # the write a single syscall.
    with open(path, "ab") as fh:
        fh.write(line.encode("utf-8"))


def build_record(
    *,
    notebook_id: str,
    source_id: Optional[str],
    title: Optional[str],
    source_type: str,
    bytes_count: int,
    attachment_count: int,
    role: str = "primary",
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    record: Dict[str, Any] = {
        "notebook_id": notebook_id,
        "source_id": source_id,
        "title": title,
        "source_type": source_type,
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "bytes": int(bytes_count),
        "attachment_count": int(attachment_count),
        "role": role,
    }
    if extra:
        record.update(extra)
    return record


# ---------------------------------------------------------------------------
# Core async add_source
# ---------------------------------------------------------------------------


async def add_source(
    page: Any,
    notebook_id: str,
    source_type: str,
    content_or_url: str,
    title: Optional[str] = None,
    attachments: Optional[List[str]] = None,
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
) -> Dict[str, Any]:
    """
    Add a single primary source (+ optional attachments) to a notebook in the
    current page/session.

    Returns a dict:
      {
        "status": "success" | "timeout" | "error",
        "notebook_id": ...,
        "source_id": str|None,
        "title": str|None,
        "bytes": int,
        "attachments": [{"path":..., "bytes":...}, ...],
        "duration_seconds": float,
        "error": str|None,
        "partial": bool,
      }

    The function is designed to be friendly to unit tests with a mocked page.
    It never deletes partial work on timeout — the caller is responsible for
    logging a record with status="timeout".
    """
    if source_type not in VALID_SOURCE_TYPES:
        raise ValueError(
            f"Invalid source_type {source_type!r}; expected one of {sorted(VALID_SOURCE_TYPES)}"
        )

    attachments = attachments or []
    start = time.monotonic()

    # Navigate to the notebook.
    await page.goto(notebook_url_from_id(notebook_id), wait_until="domcontentloaded")

    # Open the "Add source" dialog. Selectors are best-effort and conservative;
    # NotebookLM's DOM evolves — callers should self-anneal on real failures.
    try:
        await page.click('button[aria-label="Add source"]')
    except Exception:
        # Try alternative well-known triggers.
        try:
            await page.click("text=Add source")
        except Exception as exc:
            return {
                "status": "error",
                "notebook_id": notebook_id,
                "source_id": None,
                "title": title,
                "bytes": 0,
                "attachments": [],
                "duration_seconds": time.monotonic() - start,
                "error": f"Could not open Add-source dialog: {exc}",
                "partial": False,
            }

    bytes_count = 0
    source_id: Optional[str] = None

    try:
        if source_type == "text":
            # content_or_url is a path to a text/markdown file.
            text_path = Path(content_or_url)
            if not text_path.exists():
                raise FileNotFoundError(f"Text content file not found: {text_path}")
            text = text_path.read_text(encoding="utf-8")
            bytes_count = len(text.encode("utf-8"))
            await page.click('button[role="tab"][aria-label*="Text"]')
            await page.fill('textarea[aria-label*="Paste text"]', text)
            if title:
                # Best-effort title field.
                try:
                    await page.fill('input[aria-label*="Title"]', title)
                except Exception:
                    pass
            await page.click('button:has-text("Insert")')

        elif source_type == "url":
            await page.click('button[role="tab"][aria-label*="Website"]')
            await page.fill('input[aria-label*="URL"]', content_or_url)
            bytes_count = len(content_or_url.encode("utf-8"))
            await page.click('button:has-text("Insert")')

        elif source_type in {"file", "pdf", "image"}:
            file_path = Path(content_or_url)
            if not file_path.exists():
                raise FileNotFoundError(f"Source file not found: {file_path}")
            bytes_count = file_path.stat().st_size
            await page.click('input[type="file"]')
            await page.set_input_files('input[type="file"]', str(file_path))

        else:  # pragma: no cover — guarded above.
            raise ValueError(f"Unhandled source_type {source_type!r}")

        # Wait for the new source to appear / be marked ready.
        source_id = await _wait_for_new_source_ready(page, timeout=timeout)

        # Attachments — reuse the same session/page.
        attachment_records: List[Dict[str, Any]] = []
        for att_path in attachments:
            ap = Path(att_path)
            if not ap.exists():
                raise FileNotFoundError(f"Attachment not found: {ap}")
            try:
                await page.click('button[aria-label="Add attachment"]')
            except Exception:
                # Fallback to the primary "Add source" control if no dedicated
                # attachment button is exposed by the current UI.
                await page.click('button[aria-label="Add source"]')
            await page.set_input_files('input[type="file"]', str(ap))
            # Wait briefly for each attachment, but cap with remaining timeout.
            remaining = max(5, int(timeout - (time.monotonic() - start)))
            await _wait_for_new_source_ready(page, timeout=remaining)
            attachment_records.append({"path": str(ap), "bytes": ap.stat().st_size})

        return {
            "status": "success",
            "notebook_id": notebook_id,
            "source_id": source_id,
            "title": title,
            "bytes": bytes_count,
            "attachments": attachment_records,
            "duration_seconds": time.monotonic() - start,
            "error": None,
            "partial": False,
        }

    except asyncio.TimeoutError as exc:
        return {
            "status": "timeout",
            "notebook_id": notebook_id,
            "source_id": source_id,
            "title": title,
            "bytes": bytes_count,
            "attachments": [],
            "duration_seconds": time.monotonic() - start,
            "error": f"Processing timeout after {timeout}s: {exc}",
            "partial": True,
        }
    except FileNotFoundError:
        raise
    except Exception as exc:
        return {
            "status": "error",
            "notebook_id": notebook_id,
            "source_id": source_id,
            "title": title,
            "bytes": bytes_count,
            "attachments": [],
            "duration_seconds": time.monotonic() - start,
            "error": f"{type(exc).__name__}: {exc}",
            "partial": source_id is not None,
        }


async def _wait_for_new_source_ready(page: Any, timeout: int) -> Optional[str]:
    """
    Poll the sources panel for a newly-added source with a "ready" state. Returns
    the new source id or None if the id cannot be read (we still count it as
    ready so callers can proceed).

    Raises asyncio.TimeoutError if the poll exceeds `timeout`.
    """
    deadline = time.monotonic() + max(1, int(timeout))
    poll_interval = 0.5
    while time.monotonic() < deadline:
        try:
            state = await page.evaluate(
                """() => {
                    const el = document.querySelector('[data-source-id][data-source-state="ready"]');
                    return el ? { id: el.getAttribute('data-source-id'), state: 'ready' } : null;
                }"""
            )
        except Exception:
            state = None
        if state and isinstance(state, dict) and state.get("state") == "ready":
            return state.get("id")
        await asyncio.sleep(poll_interval)
    raise asyncio.TimeoutError(f"Source did not reach 'ready' within {timeout}s")


# ---------------------------------------------------------------------------
# Auth / session helpers
# ---------------------------------------------------------------------------


def broadcast_cookie_expiry(notebook_id: Optional[str]) -> None:
    """Log a cross-agent context entry noting auth expiry; best-effort, no prompt."""
    try:
        # Import lazily so tests don't need the dep.
        import subprocess

        action = (
            "notebooklm-internal add_source: auth/cookies expired — "
            f"notebook_id={notebook_id or 'unknown'}"
        )
        subprocess.run(
            [
                "python3",
                "execution/cross_agent_context.py",
                "store",
                "--agent",
                "claude",
                "--action",
                action,
                "--project",
                "agi-agent-kit",
            ],
            check=False,
            capture_output=True,
            timeout=15,
        )
    except Exception:
        # Never let telemetry block the exit path.
        pass


def is_auth_expired_error(exc: BaseException) -> bool:
    msg = str(exc).lower()
    needles = (
        "authentication required",
        "accounts.google.com",
        "session expired",
        "cookie",
        "unauthorized",
        "401",
    )
    return any(n in msg for n in needles)


# ---------------------------------------------------------------------------
# CLI / orchestration
# ---------------------------------------------------------------------------


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    # Notebook selectors (one required).
    parser.add_argument("--notebook-id")
    parser.add_argument("--notebook-url")
    parser.add_argument("--notebook-name")

    parser.add_argument(
        "--source-type",
        required=True,
        choices=sorted(VALID_SOURCE_TYPES),
    )
    parser.add_argument("--content", help="Path to content file (for text/file/pdf/image)")
    parser.add_argument("--url", help="URL (for source-type=url)")
    parser.add_argument("--title", default=None)
    parser.add_argument("--attachments", nargs="*", default=[])

    parser.add_argument("--config", default=None, help="Optional config file path")
    parser.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT_SECONDS,
        help=f"Processing timeout in seconds (default: {DEFAULT_TIMEOUT_SECONDS})",
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--json", action="store_true", help="Force JSON-only stdout")
    return parser.parse_args(argv)


def _emit(payload: Dict[str, Any], json_only: bool) -> None:
    if json_only:
        sys.stdout.write(json.dumps(payload) + "\n")
    else:
        sys.stdout.write(json.dumps(payload, indent=2) + "\n")
    sys.stdout.flush()


def _content_or_url_for(args: argparse.Namespace) -> Tuple[Optional[str], Optional[str]]:
    """Validate that the caller supplied --content or --url appropriately."""
    if args.source_type == "url":
        if not args.url:
            return None, "--url is required when --source-type=url"
        return args.url, None
    if not args.content:
        return None, f"--content is required when --source-type={args.source_type}"
    return args.content, None


async def _run_async(args: argparse.Namespace) -> Tuple[int, Dict[str, Any]]:
    notebook_id, err = resolve_notebook_id(
        args.notebook_id, args.notebook_url, args.notebook_name
    )
    if err:
        return 1, {"status": "error", "error": err}

    content_or_url, err = _content_or_url_for(args)
    if err:
        return 1, {"status": "error", "error": err}

    # Validate local files exist up-front where applicable (clearer errors).
    if args.source_type in {"text", "file", "pdf", "image"}:
        p = Path(content_or_url)  # type: ignore[arg-type]
        if not p.exists():
            return 2, {"status": "error", "error": f"File not found: {p}"}
    for att in args.attachments:
        ap = Path(att)
        if not ap.exists():
            return 2, {"status": "error", "error": f"Attachment not found: {ap}"}

    if args.dry_run:
        payload = {
            "status": "dry-run",
            "notebook_id": notebook_id,
            "source_type": args.source_type,
            "content_or_url": content_or_url,
            "title": args.title,
            "attachments": args.attachments,
            "timeout": args.timeout,
        }
        return 0, payload

    # Real browser session — import here so test runs avoid the dependency.
    try:
        from patchright.async_api import async_playwright  # type: ignore
    except Exception as exc:
        return 4, {
            "status": "error",
            "error": f"Playwright import failed: {type(exc).__name__}: {exc}",
        }

    try:
        from config import BROWSER_PROFILE_DIR  # type: ignore
    except Exception:
        BROWSER_PROFILE_DIR = SKILL_DIR / "data" / "browser_state" / "browser_profile"

    BROWSER_PROFILE_DIR.mkdir(parents=True, exist_ok=True)

    try:
        async with async_playwright() as pw:
            context = await pw.chromium.launch_persistent_context(
                user_data_dir=str(BROWSER_PROFILE_DIR),
                headless=True,
            )
            page = await context.new_page()
            try:
                result = await add_source(
                    page,
                    notebook_id=notebook_id,
                    source_type=args.source_type,
                    content_or_url=content_or_url,  # type: ignore[arg-type]
                    title=args.title,
                    attachments=list(args.attachments),
                    timeout=args.timeout,
                )
            finally:
                await context.close()
    except Exception as exc:
        if is_auth_expired_error(exc):
            broadcast_cookie_expiry(notebook_id)
            return 3, {
                "status": "auth_expired",
                "notebook_id": notebook_id,
                "error": str(exc),
            }
        return 4, {
            "status": "error",
            "notebook_id": notebook_id,
            "error": f"{type(exc).__name__}: {exc}",
        }

    # Persist audit record(s).
    primary_record = build_record(
        notebook_id=notebook_id,
        source_id=result.get("source_id"),
        title=args.title,
        source_type=args.source_type,
        bytes_count=int(result.get("bytes") or 0),
        attachment_count=len(result.get("attachments") or []),
        role="primary",
        extra={
            "status": result.get("status"),
            "duration_seconds": result.get("duration_seconds"),
        },
    )
    append_library_record(primary_record)

    for att in result.get("attachments") or []:
        att_record = build_record(
            notebook_id=notebook_id,
            source_id=None,
            title=Path(att["path"]).name,
            source_type="attachment",
            bytes_count=int(att.get("bytes") or 0),
            attachment_count=0,
            role="attachment",
            extra={"parent_source_id": result.get("source_id"), "path": att["path"]},
        )
        append_library_record(att_record)

    payload = {
        "status": result.get("status"),
        "notebook_id": notebook_id,
        "source_id": result.get("source_id"),
        "title": args.title,
        "bytes": result.get("bytes"),
        "attachments": result.get("attachments"),
        "duration_seconds": result.get("duration_seconds"),
        "partial": result.get("partial"),
        "library_jsonl": str(LIBRARY_JSONL),
    }

    if result.get("status") == "timeout":
        return 5, payload
    if result.get("status") != "success":
        return 4, payload
    return 0, payload


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    try:
        code, payload = asyncio.run(_run_async(args))
    except KeyboardInterrupt:
        print(json.dumps({"status": "error", "error": "interrupted"}), file=sys.stderr)
        return 4
    _emit(payload, json_only=bool(args.json))
    return code


if __name__ == "__main__":
    sys.exit(main())
