"""Unit tests for formatter dispatch and markdown rollups (#124)."""
from __future__ import annotations

import pytest
from datetime import datetime, timezone
from pathlib import Path

from execution.source_fetchers import Item
from execution.formatters import format_x, format_youtube
from execution.format_items_for_notebooklm import write_rollup

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_T0 = datetime(2026, 1, 1, tzinfo=timezone.utc)
_T1 = datetime(2026, 1, 31, tzinfo=timezone.utc)


def _x_item(
    i: int,
    handle: str = "alice",
    dt: datetime = _T0,
    metadata: dict | None = None,
) -> Item:
    return Item(
        source_type="x",
        source_handle=handle,
        external_id=str(i),
        url=f"https://x.com/{handle}/status/{i}",
        published_at=dt,
        body=f"tweet body {i}",
        metadata=metadata or {},
    )


def _yt_item(
    i: int,
    handle: str = "mychannel",
    dt: datetime = _T0,
    metadata: dict | None = None,
) -> Item:
    return Item(
        source_type="youtube",
        source_handle=handle,
        external_id=f"vid{i}",
        url=f"https://youtube.com/watch?v=vid{i}",
        published_at=dt,
        title=f"Video {i}",
        body=f"transcript of video {i}",
        metadata=metadata or {},
    )


# ---------------------------------------------------------------------------
# write_rollup — error cases
# ---------------------------------------------------------------------------


def test_write_rollup_unknown_source_type_raises(tmp_path: Path) -> None:
    items = [_x_item(1)]
    with pytest.raises(KeyError) as exc_info:
        write_rollup(items, "nope", "alice", _T0, _T1, rollup_dir=tmp_path)
    msg = str(exc_info.value)
    assert "nope" in msg
    assert "Known:" in msg


def test_write_rollup_empty_items_raises(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        write_rollup([], "x", "alice", _T0, _T1, rollup_dir=tmp_path)


def test_write_rollup_mixed_source_types_raises(tmp_path: Path) -> None:
    items = [_x_item(1), _yt_item(2)]
    with pytest.raises(ValueError):
        write_rollup(items, "x", "alice", _T0, _T1, rollup_dir=tmp_path)


# ---------------------------------------------------------------------------
# write_rollup — success: X
# ---------------------------------------------------------------------------


def test_write_rollup_x_writes_file_with_frontmatter(tmp_path: Path) -> None:
    items = [_x_item(1), _x_item(2)]
    out = write_rollup(items, "x", "alice", _T0, _T1, rollup_dir=tmp_path)
    assert out.exists()
    content = out.read_text(encoding="utf-8")
    assert "source_type: x" in content
    assert "handle: alice" in content
    assert "item_count: 2" in content


# ---------------------------------------------------------------------------
# write_rollup — success: YouTube
# ---------------------------------------------------------------------------


def test_write_rollup_youtube_writes_file_with_transcript_section(
    tmp_path: Path,
) -> None:
    items = [_yt_item(1)]
    out = write_rollup(items, "youtube", "mychannel", _T0, _T1, rollup_dir=tmp_path)
    assert out.exists()
    content = out.read_text(encoding="utf-8")
    assert "### Transcript" in content


# ---------------------------------------------------------------------------
# format_x.render_rollup — ordering and media
# ---------------------------------------------------------------------------


def test_format_x_orders_items_chronologically() -> None:
    older = _x_item(1, dt=datetime(2026, 1, 5, tzinfo=timezone.utc))
    newer = _x_item(2, dt=datetime(2026, 1, 10, tzinfo=timezone.utc))
    # Pass newer first — output must still show older first
    result = format_x.render_rollup([newer, older], "alice", _T0, _T1)
    pos_older = result.index(older.published_at.isoformat())
    pos_newer = result.index(newer.published_at.isoformat())
    assert pos_older < pos_newer, "Older item should appear before newer item"


def test_format_x_includes_media_when_present() -> None:
    item = _x_item(
        1,
        metadata={"media": [{"path": "images/photo.jpg", "alt": "A photo"}]},
    )
    result = format_x.render_rollup([item], "alice", _T0, _T1)
    assert "**Media:**" in result
    assert "images/photo.jpg" in result
    assert "A photo" in result


# ---------------------------------------------------------------------------
# format_youtube.render_rollup — chapters
# ---------------------------------------------------------------------------


def test_format_youtube_omits_chapters_when_absent() -> None:
    item = _yt_item(1, metadata={})
    result = format_youtube.render_rollup([item], "mychannel", _T0, _T1)
    assert "### Chapters" not in result


def test_format_youtube_includes_chapters_when_present() -> None:
    item = _yt_item(
        1,
        metadata={"chapters": [{"start": 0, "title": "Intro"}, {"start": 60, "title": "Main"}]},
    )
    result = format_youtube.render_rollup([item], "mychannel", _T0, _T1)
    assert "### Chapters" in result
    assert "Intro" in result
    assert "Main" in result
