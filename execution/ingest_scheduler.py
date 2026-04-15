#!/usr/bin/env python3
"""
Script: ingest_scheduler.py
Purpose: Cron wiring for autonomous ingest runs (#129).

The scheduler is intentionally dumb — it installs/prints a crontab entry
that invokes `execution/ingest_dispatcher.py --config <config>` on a fixed
cadence (default: daily at 03:00 local). The DISPATCHER is responsible for
per-source cadence gating (reads `.tmp/ingest/last_run.json` and skips
sources whose `cadence` has not elapsed).

Responsibilities:
    1. Provide a standalone wrapper (`run-now`) that:
       - prunes logs older than 30 days
       - opens `.tmp/ingest/logs/YYYY-MM-DD.log` (append)
       - execs the dispatcher and tees stdout/stderr to the log
       - on failure: calls `cross_agent_context.py store` with exit code
         and last 2KB of the log, then preserves the exit code
    2. Generate / install / uninstall a crontab entry
    3. Report status via `list`

Subcommands:
    install --print-crontab   Print the crontab line (no side effects)
    install --apply           Append the line to the user's crontab (idempotent)
    uninstall                 Remove the managed line from the user's crontab
    list                      Show whether the ingest cron job is installed
    run-now                   Execute the dispatcher once, with logging + failure capture

Exit Codes:
    0 - Success
    1 - Invalid arguments / usage
    2 - Crontab not available or install failed
    3 - Dispatcher failure (exit code preserved from dispatcher when possible)
    4 - Unexpected internal error
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

# ─── Paths ────────────────────────────────────────────────────────────────────

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DISPATCHER = PROJECT_ROOT / "execution" / "ingest_dispatcher.py"
CROSS_AGENT = PROJECT_ROOT / "execution" / "cross_agent_context.py"
DEFAULT_CONFIG = PROJECT_ROOT / "config" / "ingest_sources.json"
LOG_DIR = PROJECT_ROOT / ".tmp" / "ingest" / "logs"

# Default cadence: daily at 03:00 local. Per issue #129.
DEFAULT_CRON_EXPR = "0 3 * * *"

# Marker strings so we can idempotently find/remove our crontab line.
CRON_MARKER_BEGIN = "# >>> agi-agent-kit ingest_scheduler (#129) >>>"
CRON_MARKER_END = "# <<< agi-agent-kit ingest_scheduler (#129) <<<"

LOG_RETENTION_DAYS = 30
LOG_TAIL_MAX_BYTES = 2048


# ─── Helpers ──────────────────────────────────────────────────────────────────


def _today_stamp() -> str:
    return _dt.date.today().isoformat()


def _ensure_log_dir() -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)


def prune_old_logs(retention_days: int = LOG_RETENTION_DAYS,
                   *, now: Optional[_dt.date] = None,
                   log_dir: Path = LOG_DIR) -> list[Path]:
    """Delete log files older than `retention_days`. Returns list of removed paths."""
    now = now or _dt.date.today()
    cutoff = now - _dt.timedelta(days=retention_days)
    removed: list[Path] = []
    if not log_dir.exists():
        return removed
    for p in log_dir.glob("*.log"):
        stem = p.stem  # YYYY-MM-DD
        try:
            file_date = _dt.date.fromisoformat(stem)
        except ValueError:
            # Not a dated log — skip, don't touch.
            continue
        if file_date < cutoff:
            try:
                p.unlink()
                removed.append(p)
            except OSError:
                pass
    return removed


def build_cron_line(*,
                    cron_expr: str = DEFAULT_CRON_EXPR,
                    config: Path = DEFAULT_CONFIG,
                    project_root: Path = PROJECT_ROOT,
                    python_bin: str = "python3") -> str:
    """Return the crontab line (no markers). Quotes paths for safety."""
    script = project_root / "execution" / "ingest_scheduler.py"
    cmd = (
        f'cd "{project_root}" && '
        f'{python_bin} "{script}" run-now --config "{config}" '
        f'>> .tmp/ingest/logs/cron.out 2>&1'
    )
    return f"{cron_expr} {cmd}"


def build_crontab_block(*, cron_expr: str = DEFAULT_CRON_EXPR,
                        config: Path = DEFAULT_CONFIG) -> str:
    """Return the full crontab block including begin/end markers."""
    line = build_cron_line(cron_expr=cron_expr, config=config)
    return f"{CRON_MARKER_BEGIN}\n{line}\n{CRON_MARKER_END}\n"


def _read_current_crontab() -> tuple[int, str]:
    """Return (returncode, stdout). returncode 0 = crontab exists, 1 = none."""
    try:
        res = subprocess.run(
            ["crontab", "-l"],
            capture_output=True, text=True, check=False,
        )
    except FileNotFoundError:
        return 127, ""
    return res.returncode, res.stdout or ""


def _strip_existing_block(crontab_text: str) -> str:
    """Remove any prior scheduler block (idempotent re-install / uninstall)."""
    lines = crontab_text.splitlines(keepends=False)
    out: list[str] = []
    skipping = False
    for ln in lines:
        if ln.strip() == CRON_MARKER_BEGIN:
            skipping = True
            continue
        if ln.strip() == CRON_MARKER_END:
            skipping = False
            continue
        if not skipping:
            out.append(ln)
    result = "\n".join(out)
    if result and not result.endswith("\n"):
        result += "\n"
    return result


def _write_crontab(contents: str) -> int:
    """Pipe `contents` into `crontab -`. Returns returncode."""
    try:
        proc = subprocess.run(
            ["crontab", "-"],
            input=contents, text=True,
            capture_output=True, check=False,
        )
    except FileNotFoundError:
        return 127
    if proc.returncode != 0:
        sys.stderr.write(proc.stderr or "crontab write failed\n")
    return proc.returncode


# ─── Failure notification ─────────────────────────────────────────────────────


def _log_tail(log_path: Path, max_bytes: int = LOG_TAIL_MAX_BYTES) -> str:
    try:
        size = log_path.stat().st_size
    except OSError:
        return ""
    try:
        with log_path.open("rb") as fh:
            if size > max_bytes:
                fh.seek(-max_bytes, os.SEEK_END)
            data = fh.read()
        return data.decode("utf-8", errors="replace")
    except OSError:
        return ""


def notify_failure(exit_code: int, log_path: Path,
                   *, runner=subprocess.run) -> None:
    """Emit a cross-agent note describing the failed run."""
    tail = _log_tail(log_path)
    summary = (
        f"ingest cron failure: exit={exit_code} "
        f"log={log_path} tail<<<\n{tail}\n>>>"
    )
    if not CROSS_AGENT.exists():
        # Don't crash the failure path on missing cross-agent script.
        sys.stderr.write(f"[ingest_scheduler] cross_agent_context.py missing; "
                         f"would have reported: {summary[:200]}\n")
        return
    try:
        runner(
            [
                sys.executable, str(CROSS_AGENT), "store",
                "--agent", "claude",
                "--action", summary,
                "--project", "agi-agent-kit",
            ],
            check=False, capture_output=True, text=True, timeout=30,
        )
    except Exception as exc:  # noqa: BLE001 - best-effort notification
        sys.stderr.write(f"[ingest_scheduler] failed to notify: {exc}\n")


# ─── Subcommand: run-now ──────────────────────────────────────────────────────


def _dispatcher_cmd(config: Path) -> list[str]:
    return [sys.executable, str(DISPATCHER), "--config", str(config)]


def run_now(config: Path, *, runner=subprocess.run,
            now: Optional[_dt.date] = None) -> int:
    """Execute the dispatcher once. Returns preserved exit code."""
    _ensure_log_dir()
    prune_old_logs(now=now)

    stamp = (now or _dt.date.today()).isoformat()
    log_path = LOG_DIR / f"{stamp}.log"

    header = (
        f"\n===== ingest_scheduler run-now {_dt.datetime.now().isoformat()} "
        f"config={config} =====\n"
    )
    with log_path.open("a", encoding="utf-8") as log_fh:
        log_fh.write(header)
        log_fh.flush()
        try:
            proc = runner(
                _dispatcher_cmd(config),
                stdout=log_fh,
                stderr=subprocess.STDOUT,
                check=False,
            )
            exit_code = getattr(proc, "returncode", 0) or 0
        except FileNotFoundError as exc:
            log_fh.write(f"[ingest_scheduler] dispatcher missing: {exc}\n")
            exit_code = 3
        except Exception as exc:  # noqa: BLE001
            log_fh.write(f"[ingest_scheduler] unexpected error: {exc}\n")
            exit_code = 4
        log_fh.write(f"===== exit={exit_code} =====\n")

    if exit_code != 0:
        notify_failure(exit_code, log_path, runner=runner)
    return exit_code


# ─── Subcommand: install / uninstall / list ───────────────────────────────────


def install_print(cron_expr: str, config: Path) -> int:
    """Print the crontab block to stdout. No side effects."""
    sys.stdout.write(build_crontab_block(cron_expr=cron_expr, config=config))
    return 0


def install_apply(cron_expr: str, config: Path) -> int:
    """Replace any existing managed block and write to user's crontab."""
    rc, current = _read_current_crontab()
    if rc == 127:
        sys.stderr.write("[ingest_scheduler] `crontab` not found on PATH\n")
        return 2
    stripped = _strip_existing_block(current)
    block = build_crontab_block(cron_expr=cron_expr, config=config)
    new_contents = (stripped + block) if stripped else block
    wrc = _write_crontab(new_contents)
    if wrc != 0:
        return 2
    sys.stdout.write(f"[ingest_scheduler] installed: {cron_expr}\n")
    return 0


def uninstall() -> int:
    rc, current = _read_current_crontab()
    if rc == 127:
        sys.stderr.write("[ingest_scheduler] `crontab` not found on PATH\n")
        return 2
    if CRON_MARKER_BEGIN not in current:
        sys.stdout.write("[ingest_scheduler] no managed block to remove\n")
        return 0
    stripped = _strip_existing_block(current)
    wrc = _write_crontab(stripped)
    if wrc != 0:
        return 2
    sys.stdout.write("[ingest_scheduler] uninstalled\n")
    return 0


def list_status() -> int:
    """Show whether the ingest cron job is installed."""
    rc, current = _read_current_crontab()
    installed = CRON_MARKER_BEGIN in current
    payload = {
        "installed": installed,
        "cron_expr": DEFAULT_CRON_EXPR if installed else None,
        "config": str(DEFAULT_CONFIG),
        "log_dir": str(LOG_DIR),
        "crontab_available": rc != 127,
    }
    if installed:
        # Extract the actual line(s) inside the block for display.
        in_block = False
        lines: list[str] = []
        for ln in current.splitlines():
            if ln.strip() == CRON_MARKER_BEGIN:
                in_block = True
                continue
            if ln.strip() == CRON_MARKER_END:
                in_block = False
                continue
            if in_block:
                lines.append(ln)
        payload["entries"] = lines
    sys.stdout.write(json.dumps(payload, indent=2) + "\n")
    return 0


# ─── CLI ──────────────────────────────────────────────────────────────────────


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="ingest_scheduler",
        description="Cron wiring for autonomous ingest runs (#129).",
    )
    sub = p.add_subparsers(dest="command", required=True)

    p_install = sub.add_parser("install", help="Install or print the crontab entry")
    mode = p_install.add_mutually_exclusive_group(required=True)
    mode.add_argument("--print-crontab", action="store_true",
                      help="Print the crontab line; do not modify user crontab")
    mode.add_argument("--apply", action="store_true",
                      help="Apply the crontab line to the user's crontab")
    p_install.add_argument("--cron-expr", default=DEFAULT_CRON_EXPR,
                           help=f"Cron expression (default: '{DEFAULT_CRON_EXPR}')")
    p_install.add_argument("--config", type=Path, default=DEFAULT_CONFIG,
                           help="Path to ingest_sources.json")

    sub.add_parser("uninstall", help="Remove the managed crontab entry")
    sub.add_parser("list", help="Show installed status")

    p_run = sub.add_parser("run-now", help="Invoke the dispatcher once, with logging")
    p_run.add_argument("--config", type=Path, default=DEFAULT_CONFIG,
                       help="Path to ingest_sources.json")

    return p


def main(argv: Optional[list[str]] = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "install":
            if args.print_crontab:
                return install_print(args.cron_expr, args.config)
            return install_apply(args.cron_expr, args.config)
        if args.command == "uninstall":
            return uninstall()
        if args.command == "list":
            return list_status()
        if args.command == "run-now":
            return run_now(args.config)
    except Exception as exc:  # noqa: BLE001
        sys.stderr.write(json.dumps({"status": "error", "message": str(exc)}) + "\n")
        return 4
    return 1


if __name__ == "__main__":
    sys.exit(main())
