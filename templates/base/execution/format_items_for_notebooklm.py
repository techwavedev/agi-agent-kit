"""Dispatch Items to per-source-type formatters and write markdown rollups."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Iterable

from execution.source_fetchers import Item
from execution.formatters import format_x, format_youtube

ROLLUP_DIR = Path(".tmp/ingest/rollups")

FORMATTERS = {
    "x": format_x.render_rollup,
    "youtube": format_youtube.render_rollup,
}


def write_rollup(
    items: list[Item],
    source_type: str,
    handle: str,
    window_start: datetime,
    window_end: datetime,
    rollup_dir: Path = ROLLUP_DIR,
) -> Path:
    """Render items via the matching formatter and write to disk.

    Returns the path to the written markdown file.
    Output path: <rollup_dir>/<source_type>/<handle>/<window_start..end>.md
    """
    if source_type not in FORMATTERS:
        raise KeyError(
            f"No formatter for source_type '{source_type}'. "
            f"Known: {sorted(FORMATTERS)}"
        )
    if not items:
        raise ValueError("Cannot render rollup of zero items")
    if any(it.source_type != source_type for it in items):
        raise ValueError(
            f"All items must have source_type='{source_type}'; "
            "mixed-type rollups are not allowed"
        )
    body = FORMATTERS[source_type](items, handle, window_start, window_end)
    out_dir = rollup_dir / source_type / handle
    out_dir.mkdir(parents=True, exist_ok=True)
    fname = f"{window_start.date().isoformat()}_{window_end.date().isoformat()}.md"
    out_path = out_dir / fname
    out_path.write_text(body, encoding="utf-8")
    return out_path
