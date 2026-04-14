"""Formatter for YouTube items — renders a markdown rollup for NotebookLM."""
from __future__ import annotations

from datetime import datetime
from typing import List

from execution.source_fetchers import Item


def _render_item(item: Item) -> str:
    meta = item.metadata
    title = item.title or "(untitled)"
    lines: List[str] = []

    lines.append(f"## {title} — {item.published_at.isoformat()}")
    lines.append("")
    lines.append(f"- **URL:** {item.url}")
    lines.append(f"- **Channel:** {item.source_handle}")

    duration = meta.get("duration_seconds")
    if duration is not None:
        lines.append(f"- **Duration:** {duration}s")

    quality = meta.get("transcript_quality")
    if quality is not None:
        lines.append(f"- **Transcript quality:** {quality}")

    thumbnail = meta.get("thumbnail_path")
    if thumbnail:
        lines.append(f"- ![thumbnail]({thumbnail})")

    chapters = meta.get("chapters")
    if chapters:
        lines.append("")
        lines.append("### Chapters")
        lines.append("")
        for ch in chapters:
            lines.append(f"- {ch.get('start', 0)}s \u2014 {ch.get('title', '(untitled)')}")

    description = meta.get("description")
    if description:
        lines.append("")
        lines.append("### Description")
        lines.append("")
        lines.append(description)

    lines.append("")
    lines.append("### Transcript")
    lines.append("")
    lines.append(item.body)

    return "\n".join(lines)


def render_rollup(
    items: List[Item],
    handle: str,
    window_start: datetime,
    window_end: datetime,
) -> str:
    """Return a full markdown rollup string for a list of YouTube items."""
    sorted_items = sorted(items, key=lambda it: it.published_at)

    urls_yaml = "\n".join(f"  - {it.url}" for it in sorted_items)

    frontmatter = (
        f"---\n"
        f"source_type: youtube\n"
        f"handle: {handle}\n"
        f"window_start: {window_start.isoformat()}\n"
        f"window_end: {window_end.isoformat()}\n"
        f"item_count: {len(sorted_items)}\n"
        f"urls:\n{urls_yaml}\n"
        f"---"
    )

    heading = (
        f"# YouTube videos by {handle} "
        f"({window_start.date().isoformat()} \u2192 {window_end.date().isoformat()})"
    )

    item_blocks = "\n\n---\n\n".join(_render_item(it) for it in sorted_items)

    return "\n\n".join([frontmatter, heading, item_blocks])
