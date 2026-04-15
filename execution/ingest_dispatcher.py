"""Ingest pipeline dispatcher (#128).

Per-source pipeline:
  fetcher → ingest_dedup.filter_new → format_items_for_notebooklm.write_rollup
  → for each notebook name in source.notebooks:
        ensure_notebook.resolve_or_create → add_source (markdown file)
        → ingest_dedup.mark_pushed

Sequential by default. `--parallel N` uses a thread pool over sources.

Subcommands: run | run-one <id> | dry-run | validate
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import importlib
import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
ARTIFACT_ROOT = ROOT / ".tmp" / "ingest"
LOG = logging.getLogger("ingest_dispatcher")

# Defer imports so the module stays importable even when optional parts
# (playwright/twscrape/etc.) aren't installed on the current machine.
from execution import ingest_config  # noqa: E402
from execution.source_fetchers import FETCHERS  # noqa: E402
from execution.source_fetchers.base import Item  # noqa: E402


# ─── Fetcher resolution ───────────────────────────────────────────────────────


def _load_fetcher(source_type: str):
    """Return a fetcher instance for the given type, or raise KeyError."""
    # Registrations live as import side-effects on submodules.
    for mod in ("x_fetcher", "youtube_fetcher"):
        try:
            importlib.import_module(f"execution.source_fetchers.{mod}")
        except ImportError as e:
            LOG.debug("skipped %s fetcher import: %s", mod, e)
    cls = FETCHERS.get(source_type)
    if not cls:
        raise KeyError(f"no registered fetcher for type={source_type!r}")
    return cls()


# ─── Per-source pipeline ──────────────────────────────────────────────────────


def _iso(dt_str: str | None) -> datetime | None:
    return datetime.fromisoformat(dt_str) if dt_str else None


def run_source(source: dict[str, Any], *, config_path: Path,
               upload: bool = True) -> dict[str, Any]:
    """Run the pipeline for a single source dict. Returns a summary."""
    sid = source["id"]
    stype = source["type"]
    handle = source["handle"]
    summary: dict[str, Any] = {
        "source_id": sid, "type": stype, "handle": handle,
        "fetched": 0, "new": 0, "uploaded": 0,
        "artifact_path": None, "errors": [],
    }
    t0 = time.time()

    try:
        fetcher = _load_fetcher(stype)
    except KeyError as e:
        summary["errors"].append(str(e))
        summary["duration_ms"] = int((time.time() - t0) * 1000)
        return summary

    cfg = source.get("config", {}) or {}
    since = _iso(source.get("since"))
    until = _iso(source.get("until"))

    try:
        items: list[Item] = list(fetcher.fetch(handle, since=since, until=until, **cfg)) \
            if cfg else list(fetcher.fetch(handle, since=since, until=until))
    except TypeError:
        # Fetcher didn't accept **cfg — retry without
        items = list(fetcher.fetch(handle, since=since, until=until))
    except Exception as e:  # pragma: no cover — defensive
        summary["errors"].append(f"fetch failed: {e}")
        summary["duration_ms"] = int((time.time() - t0) * 1000)
        return summary

    summary["fetched"] = len(items)
    if not items:
        summary["duration_ms"] = int((time.time() - t0) * 1000)
        return summary

    # Dedup
    from execution import ingest_dedup
    new_items = ingest_dedup.filter_new(items)
    summary["new"] = len(new_items)
    if not new_items:
        summary["duration_ms"] = int((time.time() - t0) * 1000)
        return summary

    # Format → markdown rollup artifact
    try:
        from execution import format_items_for_notebooklm as fmt
    except ImportError as e:
        summary["errors"].append(f"formatter not available: {e}")
        summary["duration_ms"] = int((time.time() - t0) * 1000)
        return summary
    out_dir = ARTIFACT_ROOT / sid
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y-%m-%dT%H%M%S")
    artifact = out_dir / f"{stamp}.md"
    try:
        fmt.write_rollup(new_items, artifact)
    except Exception as e:
        summary["errors"].append(f"format failed: {e}")
        summary["duration_ms"] = int((time.time() - t0) * 1000)
        return summary
    summary["artifact_path"] = str(artifact)

    if not upload:
        summary["duration_ms"] = int((time.time() - t0) * 1000)
        return summary

    # Resolve + upload for each notebook
    try:
        from skills.notebooklm_internal.scripts import ensure_notebook, add_source  # type: ignore
    except ImportError:
        summary["errors"].append(
            "notebooklm-internal scripts not importable — artifact ready but not uploaded. "
            "Run ensure_notebook.py + add_source.py manually, or ensure skills/ is on PYTHONPATH."
        )
        summary["duration_ms"] = int((time.time() - t0) * 1000)
        return summary

    from execution import ingest_dedup as dedup
    for notebook_name in source.get("notebooks", []):
        try:
            persisted = ensure_notebook.lookup_persisted_id(config_path, sid, notebook_name)
            if persisted:
                notebook_id = persisted
            else:
                # Delegate to ensure_notebook's CLI-less helpers
                notebook_id = ensure_notebook.ensure_by_name(  # type: ignore[attr-defined]
                    notebook_name, create_if_missing=True,
                    config_path=config_path, source_id=sid,
                )
            # Upload artifact as source
            add_source.add_source_sync(  # type: ignore[attr-defined]
                notebook_id=notebook_id,
                source_type="file",
                content=artifact,
                title=f"{sid}@{stamp}",
            )
            dedup.mark_pushed(new_items, notebook_id)
            summary["uploaded"] += 1
        except AttributeError as e:
            summary["errors"].append(
                f"notebook {notebook_name!r}: upload helpers missing a convenience entry point "
                f"({e}) — run add_source.py CLI against artifact_path"
            )
        except Exception as e:  # pragma: no cover — network/UI flakes
            summary["errors"].append(f"notebook {notebook_name!r}: {e}")

    summary["duration_ms"] = int((time.time() - t0) * 1000)
    return summary


# ─── CLI ──────────────────────────────────────────────────────────────────────


def run_all(config_path: Path, *, parallel: int = 1, upload: bool = True) -> list[dict[str, Any]]:
    res = ingest_config.load_config(config_path)
    if not res.ok:
        for e in res.errors:
            LOG.error(e)
        raise SystemExit(2)
    sources = ingest_config.enabled_sources(res.config)
    if parallel <= 1 or len(sources) <= 1:
        return [run_source(s, config_path=config_path, upload=upload) for s in sources]

    with cf.ThreadPoolExecutor(max_workers=min(parallel, len(sources))) as ex:
        futs = {ex.submit(run_source, s, config_path=config_path, upload=upload): s for s in sources}
        return [f.result() for f in cf.as_completed(futs)]


def _emit(summary: dict[str, Any]) -> None:
    print(json.dumps(summary, separators=(",", ":")))


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--config", type=Path, default=ingest_config.DEFAULT_CONFIG)
    common.add_argument("--json", action="store_true", help="Emit JSON-lines per source")

    p_run = sub.add_parser("run", parents=[common], help="Run all enabled sources")
    p_run.add_argument("--parallel", type=int, default=1, help="Thread pool size (default 1)")
    p_run.add_argument("--no-upload", action="store_true", help="Prepare artifacts only; skip NotebookLM upload")

    p_one = sub.add_parser("run-one", parents=[common], help="Run a single source by id")
    p_one.add_argument("source_id")
    p_one.add_argument("--no-upload", action="store_true")

    sub.add_parser("dry-run", parents=[common], help="List what would run; no fetches")
    sub.add_parser("validate", parents=[common], help="Validate config and exit")

    args = p.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="[dispatcher] %(message)s")

    if args.cmd == "validate":
        res = ingest_config.load_config(args.config)
        payload = {"ok": res.ok, "errors": res.errors, "warnings": res.warnings}
        print(json.dumps(payload, indent=2))
        return 0 if res.ok else 2

    if args.cmd == "dry-run":
        res = ingest_config.load_config(args.config)
        if not res.ok:
            print(json.dumps({"ok": False, "errors": res.errors}), file=sys.stderr)
            return 2
        plan = [
            {"id": s["id"], "type": s["type"], "handle": s["handle"], "notebooks": s["notebooks"]}
            for s in ingest_config.enabled_sources(res.config)
        ]
        print(json.dumps({"ok": True, "enabled": plan, "warnings": res.warnings}, indent=2))
        return 0

    if args.cmd == "run-one":
        res = ingest_config.load_config(args.config)
        if not res.ok:
            print(json.dumps({"ok": False, "errors": res.errors}), file=sys.stderr)
            return 2
        src = ingest_config.find_source(res.config, args.source_id)
        if not src:
            print(json.dumps({"ok": False, "error": f"source not found: {args.source_id}"}), file=sys.stderr)
            return 2
        summary = run_source(src, config_path=args.config, upload=not args.no_upload)
        _emit(summary)
        return 0 if not summary["errors"] else 4

    if args.cmd == "run":
        summaries = run_all(args.config, parallel=args.parallel, upload=not args.no_upload)
        for s in summaries:
            _emit(s)
        any_err = any(s.get("errors") for s in summaries)
        return 0 if not any_err else 4

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
