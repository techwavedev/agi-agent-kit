"""Unit tests for YouTubeFetcher (#122)."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from execution.source_fetchers.youtube_fetcher import YouTubeFetcher
from execution.source_fetchers.base import Item


# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------

def _stub_entry(
    video_id: str = "abc123",
    duration: int = 300,
    url: str = "https://www.youtube.com/watch?v=abc123",
) -> dict:
    return {
        "id": video_id,
        "title": f"Video {video_id}",
        "upload_date": "20240601",
        "duration": duration,
        "webpage_url": url,
        "description": "Test description",
        "chapters": None,
    }


@pytest.fixture
def fetcher(tmp_path: Path) -> YouTubeFetcher:
    """YouTubeFetcher with yt-dlp mocked as present, using a temp media dir."""
    with patch("shutil.which", return_value="/usr/bin/yt-dlp"):
        return YouTubeFetcher(media_dir=tmp_path, transcripts=True)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_channel_url_handle_normalization(fetcher: YouTubeFetcher) -> None:
    assert "/@foo/videos" in fetcher._channel_url("@foo")
    assert "/@bar/videos" in fetcher._channel_url("bar")
    full = "https://www.youtube.com/@channel/videos"
    assert fetcher._channel_url(full) == full


def test_is_short_by_duration(fetcher: YouTubeFetcher) -> None:
    assert fetcher._is_short({"duration": 30}) is True
    assert fetcher._is_short({"duration": 59}) is True
    assert fetcher._is_short({"duration": 60}) is False
    assert fetcher._is_short({"duration": 600}) is False


def test_is_short_by_url(fetcher: YouTubeFetcher) -> None:
    assert fetcher._is_short(
        {"webpage_url": "https://youtube.com/shorts/xyz", "duration": 600}
    ) is True
    assert fetcher._is_short(
        {"webpage_url": "https://www.youtube.com/watch?v=abc", "duration": 600}
    ) is False


def test_entry_to_item_basic(fetcher: YouTubeFetcher) -> None:
    entry = _stub_entry()
    with patch.object(fetcher, "_download_thumbnail", return_value=None), \
         patch.object(fetcher, "_fetch_transcript", return_value=("transcript text", "manual")):
        item = fetcher._entry_to_item("@testchannel", entry)

    assert isinstance(item, Item)
    assert item.source_type == "youtube"
    assert item.external_id == "abc123"
    assert item.url == "https://www.youtube.com/watch?v=abc123"
    assert item.published_at == datetime(2024, 6, 1, tzinfo=timezone.utc)
    assert item.source_handle == "@testchannel"
    # Required metadata keys
    for key in ("thumbnail_path", "transcript_quality", "duration_seconds", "chapters", "description"):
        assert key in item.metadata, f"metadata missing key: {key}"
    assert item.metadata["transcript_quality"] == "manual"
    assert item.metadata["duration_seconds"] == 300


def test_fetch_calls_list_then_maps(fetcher: YouTubeFetcher) -> None:
    entries = [
        _stub_entry("vid1", url="https://www.youtube.com/watch?v=vid1"),
        _stub_entry("vid2", url="https://www.youtube.com/watch?v=vid2"),
    ]

    def _fake_to_item(handle: str, entry: dict) -> Item:
        return Item(
            source_type="youtube",
            source_handle=handle,
            external_id=entry["id"],
            url=entry["webpage_url"],
            published_at=datetime(2024, 6, 1, tzinfo=timezone.utc),
        )

    with patch.object(fetcher, "_list_videos", return_value=entries), \
         patch.object(fetcher, "_entry_to_item", side_effect=_fake_to_item):
        items = list(fetcher.fetch("@channel"))

    assert len(items) == 2
    assert {i.external_id for i in items} == {"vid1", "vid2"}


def test_shorts_filtered_when_disabled(fetcher: YouTubeFetcher) -> None:
    short_entry = _stub_entry(
        video_id="short1",
        duration=30,
        url="https://youtube.com/shorts/short1",
    )
    long_entry = _stub_entry(
        video_id="long1",
        duration=600,
        url="https://www.youtube.com/watch?v=long1",
    )
    # include_shorts defaults to False in our fixture
    with patch.object(fetcher, "_list_videos", return_value=[short_entry, long_entry]), \
         patch.object(fetcher, "_download_thumbnail", return_value=None), \
         patch.object(fetcher, "_fetch_transcript", return_value=("", "description_only")):
        items = list(fetcher.fetch("@channel"))

    assert len(items) == 1
    assert items[0].external_id == "long1"


def test_missing_yt_dlp_raises() -> None:
    with patch("shutil.which", return_value=None):
        with pytest.raises(RuntimeError, match="yt-dlp"):
            YouTubeFetcher()
