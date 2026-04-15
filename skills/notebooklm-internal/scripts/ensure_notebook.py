#!/usr/bin/env python3
"""
Script: ensure_notebook.py
Purpose: Resolve-or-create a NotebookLM notebook by id or name.

Given `--id`, verify the notebook exists and return its id. Given `--name` and
`--create-if-missing`, look up the notebook in the NotebookLM UI; if not found
and the flag is set, create one headlessly via UI automation and return the new
id. The resolved id is persisted back to `config/ingest_sources.json` under
`sources[source-id].notebook_ids[name]`.

Usage:
    python3 ensure_notebook.py --id <notebook_id> [--json]
    python3 ensure_notebook.py --name <name> --source-id <src> [--create-if-missing] [--config <path>] [--json]

Exit Codes:
    0 - Resolved successfully
    1 - Bad / conflicting arguments
    2 - Not found and --create-if-missing was false
    3 - Auth / Playwright failure
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.parse import urlparse

# Allow importing sibling helpers when run as a script
sys.path.insert(0, str(Path(__file__).parent))

# Default config path (relative to repo root) — may not exist (see #128)
REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CONFIG_PATH = REPO_ROOT / "config" / "ingest_sources.json"
MIRROR_CONFIG_PATH = REPO_ROOT / ".tmp" / "ingest_sources.mirror.json"

NOTEBOOK_ID_RE = re.compile(r"^[A-Za-z0-9_-]{8,}$")
NOTEBOOK_URL_RE = re.compile(
    r"notebooklm\.google\.com/notebook/([A-Za-z0-9_-]+)"
)


# ---------------------------------------------------------------------------
# Core resolve / create primitives (importable for #127)
# ---------------------------------------------------------------------------

def resolve_notebook(page, name_or_id: str) -> Optional[str]:
    """Resolve a notebook by id or display name.

    Tries in order:
      1. If `name_or_id` looks like a notebook id, navigate to its URL and
         verify the page loads (not redirected to the library root).
      2. Otherwise scan the library page for a notebook card whose visible
         title matches `name_or_id` (case-insensitive exact match) and
         return its id.

    Args:
        page: Playwright Page (sync patchright Page) already authenticated.
        name_or_id: Either a candidate notebook id or a display name.

    Returns:
        The resolved notebook id, or None if not found.
    """
    # Branch 1: looks like an id -> probe by URL
    if NOTEBOOK_ID_RE.match(name_or_id):
        url = f"https://notebooklm.google.com/notebook/{name_or_id}"
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
        except Exception:
            return None
        current = page.url
        m = NOTEBOOK_URL_RE.search(current)
        if m and m.group(1) == name_or_id:
            # Sanity-check the notebook UI actually rendered
            try:
                page.wait_for_selector(
                    "textarea.query-box-input, project-title, [data-test-id='notebook-title']",
                    timeout=8000,
                    state="visible",
                )
                return name_or_id
            except Exception:
                return None
        # Fall through to name-based lookup if the id didn't resolve
        name_or_id_for_name_lookup = name_or_id
    else:
        name_or_id_for_name_lookup = name_or_id

    # Branch 2: lookup by display name in the library
    try:
        page.goto(
            "https://notebooklm.google.com/",
            wait_until="domcontentloaded",
            timeout=30000,
        )
    except Exception:
        return None

    target = name_or_id_for_name_lookup.strip().lower()

    # Give the library a moment to hydrate
    try:
        page.wait_for_selector(
            "project-button, a[href*='/notebook/'], [data-test-id='project-card']",
            timeout=10000,
            state="visible",
        )
    except Exception:
        # Library didn't hydrate — treat as not found
        return None

    try:
        cards = page.query_selector_all("a[href*='/notebook/']")
    except Exception:
        cards = []

    for card in cards or []:
        try:
            title = (card.inner_text() or "").strip().lower()
        except Exception:
            continue
        if not title:
            continue
        if title == target or target in title.splitlines():
            href = card.get_attribute("href") or ""
            m = NOTEBOOK_URL_RE.search(href) or re.search(
                r"/notebook/([A-Za-z0-9_-]+)", href
            )
            if m:
                return m.group(1)

    return None


def create_notebook(page, name: str) -> str:
    """Create a new NotebookLM notebook with the given display name.

    Performs UI automation against the NotebookLM library:
      1. Navigate to the library root
      2. Click the "Create new notebook" / "+" button
      3. Wait for the new notebook URL to settle, extract the id
      4. Set the notebook title to `name`

    Args:
        page: Playwright Page (sync patchright Page) already authenticated.
        name: Display name to assign the new notebook.

    Returns:
        The newly-created notebook id.

    Raises:
        RuntimeError: If creation fails or the id cannot be determined.
    """
    page.goto(
        "https://notebooklm.google.com/",
        wait_until="domcontentloaded",
        timeout=30000,
    )

    # Click "Create new notebook" — try a few selectors for robustness
    create_selectors = [
        "button:has-text('Create new notebook')",
        "button:has-text('Neues Notebook')",
        "button[aria-label*='Create' i]",
        "button[aria-label*='new notebook' i]",
        "[data-test-id='create-notebook']",
    ]
    clicked = False
    for sel in create_selectors:
        try:
            btn = page.query_selector(sel)
            if btn and btn.is_visible():
                btn.click()
                clicked = True
                break
        except Exception:
            continue
    if not clicked:
        raise RuntimeError("Could not locate 'Create new notebook' button")

    # Wait for URL to change to /notebook/<id>
    deadline = time.time() + 30
    notebook_id: Optional[str] = None
    while time.time() < deadline:
        m = NOTEBOOK_URL_RE.search(page.url)
        if m:
            notebook_id = m.group(1)
            break
        time.sleep(0.5)
    if not notebook_id:
        raise RuntimeError("Notebook created but id could not be determined from URL")

    # Wait for the notebook editor to be ready before renaming
    try:
        page.wait_for_selector(
            "project-title, [data-test-id='notebook-title'], input[aria-label*='title' i]",
            timeout=15000,
            state="visible",
        )
    except Exception:
        # Non-fatal — we still have the id
        return notebook_id

    # Rename the notebook to `name`
    title_selectors = [
        "[data-test-id='notebook-title']",
        "project-title input",
        "input[aria-label*='title' i]",
        "project-title",
    ]
    for sel in title_selectors:
        try:
            el = page.query_selector(sel)
            if not el or not el.is_visible():
                continue
            try:
                el.click()
            except Exception:
                pass
            try:
                page.keyboard.press("Control+A")
                page.keyboard.press("Delete")
                page.keyboard.type(name, delay=20)
                page.keyboard.press("Enter")
                break
            except Exception:
                continue
        except Exception:
            continue

    return notebook_id


# ---------------------------------------------------------------------------
# Config persistence
# ---------------------------------------------------------------------------

def _load_config(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except Exception:
        return {}


def _atomic_write_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(
        prefix=path.name + ".", suffix=".tmp", dir=str(path.parent)
    )
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(data, f, indent=2, sort_keys=False)
            f.write("\n")
        os.replace(tmp_path, path)
    finally:
        if os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except Exception:
                pass


def persist_notebook_id(
    config_path: Path,
    source_id: str,
    name: str,
    notebook_id: str,
) -> Path:
    """Write resolved notebook id back to config.

    Mutates `sources[source_id].notebook_ids[name] = notebook_id`. If the
    target config file does not exist, writes to a mirror path under `.tmp/`
    instead (see #128 — config/ingest_sources.json is owned by that issue).

    Returns the path actually written to.
    """
    target = config_path if config_path.exists() else MIRROR_CONFIG_PATH
    config = _load_config(target)

    sources = config.setdefault("sources", {})
    if not isinstance(sources, dict):
        raise RuntimeError(
            f"Config at {target} has a non-object 'sources' field; refusing to mutate"
        )
    entry = sources.setdefault(source_id, {})
    if not isinstance(entry, dict):
        raise RuntimeError(
            f"Config at {target} has non-object source entry {source_id!r}"
        )
    notebook_ids = entry.setdefault("notebook_ids", {})
    if not isinstance(notebook_ids, dict):
        raise RuntimeError(
            f"Config at {target} has non-object 'notebook_ids' for source {source_id!r}"
        )
    notebook_ids[name] = notebook_id

    _atomic_write_json(target, config)
    return target


def lookup_persisted_id(
    config_path: Path, source_id: str, name: str
) -> Optional[str]:
    """Return a previously persisted id if present, else None."""
    target = config_path if config_path.exists() else MIRROR_CONFIG_PATH
    if not target.exists():
        return None
    config = _load_config(target)
    try:
        return config["sources"][source_id]["notebook_ids"][name]
    except (KeyError, TypeError):
        return None


# ---------------------------------------------------------------------------
# CLI driver
# ---------------------------------------------------------------------------

def _report_auth_failure(detail: str) -> None:
    """Broadcast auth/playwright failure to cross-agent memory (best-effort)."""
    try:
        import subprocess

        subprocess.run(
            [
                sys.executable,
                str(REPO_ROOT / "execution" / "cross_agent_context.py"),
                "store",
                "--agent",
                "claude",
                "--action",
                f"notebooklm auth expired on ensure_notebook: {detail}",
            ],
            check=False,
            capture_output=True,
            timeout=10,
        )
    except Exception:
        pass


def _emit(payload: Dict[str, Any], as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload))
    else:
        status = payload.get("status")
        if status == "ok":
            print(
                f"{payload.get('action', 'resolved')}: "
                f"{payload.get('notebook_id')} "
                f"(name={payload.get('name')!r}, persisted_to={payload.get('persisted_to')})"
            )
        else:
            print(json.dumps(payload, indent=2), file=sys.stderr)


def _run_with_page(fn):
    """Launch a persistent authenticated Playwright context and call `fn(page)`.

    Lazy-imports patchright + BrowserFactory so unit tests that mock Page can
    import this module without requiring the browser stack.
    """
    from patchright.sync_api import sync_playwright  # type: ignore
    from browser_utils import BrowserFactory  # type: ignore

    playwright = None
    context = None
    try:
        playwright = sync_playwright().start()
        context = BrowserFactory.launch_persistent_context(
            playwright, headless=True
        )
        page = context.new_page()
        # Quick auth probe
        page.goto(
            "https://notebooklm.google.com/",
            wait_until="domcontentloaded",
            timeout=30000,
        )
        if urlparse(page.url).hostname == "accounts.google.com":
            raise RuntimeError(
                "NotebookLM authentication required — run auth_manager.py setup"
            )
        return fn(page)
    finally:
        if context:
            try:
                context.close()
            except Exception:
                pass
        if playwright:
            try:
                playwright.stop()
            except Exception:
                pass


def main(argv: Optional[list] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Resolve-or-create a NotebookLM notebook by id or name"
    )
    parser.add_argument("--id", dest="notebook_id", help="Existing notebook id to verify")
    parser.add_argument("--name", help="Display name to look up / create")
    parser.add_argument(
        "--create-if-missing",
        action="store_true",
        help="Create the notebook via UI automation if not found",
    )
    parser.add_argument(
        "--config",
        default=str(DEFAULT_CONFIG_PATH),
        help=f"Path to ingest_sources.json (default: {DEFAULT_CONFIG_PATH})",
    )
    parser.add_argument(
        "--source-id",
        help="Source id key in config/ingest_sources.json (required with --name)",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON output")

    args = parser.parse_args(argv)

    # Argument validation
    if not args.notebook_id and not args.name:
        _emit(
            {"status": "error", "error": "must specify --id or --name"},
            args.json,
        )
        return 1
    if args.notebook_id and args.name:
        _emit(
            {"status": "error", "error": "--id and --name are mutually exclusive"},
            args.json,
        )
        return 1
    if args.name and not args.source_id:
        _emit(
            {"status": "error", "error": "--name requires --source-id"},
            args.json,
        )
        return 1

    config_path = Path(args.config)

    # Fast path: if --name was given and we already have a persisted id, trust it
    # (re-verify it in the UI to be safe).
    if args.name:
        persisted = lookup_persisted_id(config_path, args.source_id, args.name)
    else:
        persisted = None

    try:
        def _work(page):
            if args.notebook_id:
                resolved = resolve_notebook(page, args.notebook_id)
                if resolved:
                    return {
                        "status": "ok",
                        "action": "verified",
                        "notebook_id": resolved,
                    }
                return {"status": "not_found"}

            # Name-based path
            # 1. Try persisted id first
            if persisted:
                resolved = resolve_notebook(page, persisted)
                if resolved:
                    return {
                        "status": "ok",
                        "action": "cached",
                        "notebook_id": resolved,
                        "name": args.name,
                    }
                # persisted id went stale — fall through to name lookup

            # 2. Lookup by name
            resolved = resolve_notebook(page, args.name)
            if resolved:
                return {
                    "status": "ok",
                    "action": "resolved",
                    "notebook_id": resolved,
                    "name": args.name,
                }

            # 3. Create if allowed
            if args.create_if_missing:
                new_id = create_notebook(page, args.name)
                return {
                    "status": "ok",
                    "action": "created",
                    "notebook_id": new_id,
                    "name": args.name,
                }

            return {"status": "not_found", "name": args.name}

        result = _run_with_page(_work)

    except Exception as e:
        _report_auth_failure(str(e))
        _emit(
            {
                "status": "error",
                "error": f"playwright/auth failure: {e}",
            },
            args.json,
        )
        return 3

    if result.get("status") == "not_found":
        _emit(
            {
                "status": "not_found",
                "error": (
                    f"Notebook {args.notebook_id or args.name!r} not found"
                    + (
                        " and --create-if-missing was not set"
                        if args.name and not args.create_if_missing
                        else ""
                    )
                ),
                "name": args.name,
            },
            args.json,
        )
        return 2

    # Persist on name-based resolutions / creations
    persisted_to: Optional[str] = None
    if args.name and result.get("notebook_id"):
        try:
            written = persist_notebook_id(
                config_path,
                args.source_id,
                args.name,
                result["notebook_id"],
            )
            persisted_to = str(written)
        except Exception as e:
            _emit(
                {
                    "status": "error",
                    "error": f"failed to persist id: {e}",
                    "notebook_id": result.get("notebook_id"),
                },
                args.json,
            )
            return 3

    out = {
        "status": "ok",
        "action": result.get("action"),
        "notebook_id": result["notebook_id"],
        "name": args.name,
        "source_id": args.source_id,
        "persisted_to": persisted_to,
    }
    _emit(out, args.json)
    return 0


if __name__ == "__main__":
    sys.exit(main())
