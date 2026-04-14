"""Formatter for X (Twitter) items — renders a markdown rollup for NotebookLM."""
from __future__ import annotations

from datetime import datetime
from typing import List

from execution.source_fetchers import Item


def _render_item(item: Item) -> str:
    lines: List[str] = []
    lines.append(f"## {item.published_at.isoformat()} — {item.url}")
    lines.append("")
    lines.append(item.body)

    media = item.metadata.get("media")
    if media:
        lines.append("")
        lines.append("**Media:**")
        for entry in media:
            path = entry.get("path", "")
            alt = entry.get("alt", "")
            lines.append(f"- ![{alt}]({path}) — `{path}`")

    return "\n".join(lines)


def render_rollup(
    items: List[Item],
    handle: str,
    window_start: datetime,
    window_end: datetime,
) -> str:
    """Return a full markdown rollup string for a list of X items."""
    sorted_items = sorted(items, key=lambda it: it.published_at)

    urls_yaml = "\n".join(f"  - {it.url}" for it in sorted_items)

    frontmatter = (
        f"---\n"
        f"source_type: x\n"
        f"handle: {handle}\n"
        f"window_start: {window_start.isoformat()}\n"
        f"window_end: {window_end.isoformat()}\n"
        f"item_count: {len(sorted_items)}\n"
        f"urls:\n{urls_yaml}\n"
        f"---"
    )

    heading = (
        f"# X posts by @{handle} "
        f"({window_start.date().isoformat()} \u2192 {window_end.date().isoformat()})"
    )

    item_blocks = "\n\n---\n\n".join(_render_item(it) for it in sorted_items)

    return "\n\n".join([frontmatter, heading, item_blocks])
