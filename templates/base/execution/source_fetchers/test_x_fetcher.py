"""Unit tests for x_fetcher.py (twscrape-based)."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from execution.source_fetchers.x_fetcher import XFetcher, COOKIE_PATH

# ── Fixtures ──────────────────────────────────────────────────────────

@pytest.fixture
def fetcher(tmp_path: Path) -> XFetcher:
    return XFetcher(
        cookie_path=tmp_path / "cookies.json",
        media_dir=tmp_path / "media",
        include_replies=False,
        include_retweets=False,
        include_media=True,
        max_items=50,
    )

def _make_tweet(tid: int, text: str, handle: str = "testuser",
                dt: datetime | None = None, reply_to: int | None = None,
                is_rt: bool = False, media=None) -> SimpleNamespace:
    user = SimpleNamespace(username=handle)
    t = SimpleNamespace(
        id=tid, rawContent=text, user=user,
        date=dt or datetime(2025, 6, 1, tzinfo=timezone.utc),
        inReplyToTweetId=reply_to,
        retweetedTweet=SimpleNamespace() if is_rt else None,
        media=media,
    )
    return t

# ── Handle cleaning ──────────────────────────────────────────────────

def test_clean_handle_plain():
    assert XFetcher._clean_handle("TestUser") == "testuser"

def test_clean_handle_at():
    assert XFetcher._clean_handle("@TestUser") == "testuser"

def test_clean_handle_url():
    assert XFetcher._clean_handle("https://x.com/TestUser") == "testuser"

# ── Thread reconstruction ────────────────────────────────────────────

def test_single_tweet_becomes_one_item(fetcher: XFetcher) -> None:
    tweets = [{"tweet_id": "1", "author": "testuser", "text": "hello",
               "published_at": datetime(2025, 6, 1, tzinfo=timezone.utc),
               "is_retweet": False, "is_reply": False, "url": "https://x.com/testuser/status/1",
               "media": [], "in_reply_to": None}]
    threads = fetcher._reconstruct_threads(tweets, "testuser")
    assert len(threads) == 1
    assert len(threads[0]) == 1

def test_self_reply_chain_stitched(fetcher: XFetcher) -> None:
    tweets = [
        {"tweet_id": "1", "author": "testuser", "text": "part 1",
         "published_at": datetime(2025, 6, 1, 10, 0, tzinfo=timezone.utc),
         "is_retweet": False, "is_reply": False, "url": "u", "media": [], "in_reply_to": None},
        {"tweet_id": "2", "author": "testuser", "text": "part 2",
         "published_at": datetime(2025, 6, 1, 10, 1, tzinfo=timezone.utc),
         "is_retweet": False, "is_reply": False, "url": "u", "media": [], "in_reply_to": "1"},
    ]
    threads = fetcher._reconstruct_threads(tweets, "testuser")
    assert len(threads) == 1
    assert len(threads[0]) == 2

def test_thread_broken_by_other_author(fetcher: XFetcher) -> None:
    tweets = [
        {"tweet_id": "1", "author": "testuser", "text": "mine",
         "published_at": datetime(2025, 6, 1, tzinfo=timezone.utc),
         "is_retweet": False, "is_reply": False, "url": "u", "media": [], "in_reply_to": None},
        {"tweet_id": "2", "author": "other", "text": "theirs",
         "published_at": datetime(2025, 6, 1, 0, 1, tzinfo=timezone.utc),
         "is_retweet": False, "is_reply": True, "url": "u", "media": [], "in_reply_to": "1"},
    ]
    # reply by other excluded by default
    threads = fetcher._reconstruct_threads(tweets, "testuser")
    assert len(threads) == 1

# ── Media ─────────────────────────────────────────────────────────────

def test_download_media_creates_file(fetcher: XFetcher, tmp_path: Path) -> None:
    img = tmp_path / "src.jpg"
    img.write_bytes(b"\xff\xd8fake")
    local = fetcher._download_media(f"file://{img}", "t1", 0)
    assert local is not None
    assert Path(local).exists()

def test_download_media_graceful_failure(fetcher: XFetcher) -> None:
    result = fetcher._download_media("http://0.0.0.0:1/nope.jpg", "t1", 0)
    assert result is None

# ── Date filtering ────────────────────────────────────────────────────

def test_date_range_filtering(fetcher: XFetcher) -> None:
    tweets = [
        {"tweet_id": "1", "author": "testuser", "text": "old",
         "published_at": datetime(2024, 1, 1, tzinfo=timezone.utc),
         "is_retweet": False, "is_reply": False, "url": "u", "media": [], "in_reply_to": None},
        {"tweet_id": "2", "author": "testuser", "text": "in range",
         "published_at": datetime(2025, 6, 15, tzinfo=timezone.utc),
         "is_retweet": False, "is_reply": False, "url": "u", "media": [], "in_reply_to": None},
    ]
    threads = fetcher._reconstruct_threads(tweets, "testuser")
    assert len(threads) == 2

# ── Item schema ───────────────────────────────────────────────────────

def test_thread_to_item_schema(fetcher: XFetcher) -> None:
    thread = [{"tweet_id": "42", "author": "testuser", "text": "hello world",
               "published_at": datetime(2025, 6, 1, tzinfo=timezone.utc),
               "url": "https://x.com/testuser/status/42", "media": []}]
    item = fetcher._thread_to_item(thread, "testuser")
    assert item is not None
    assert item.source_type == "x"
    assert item.external_id == "42"
    assert item.body == "hello world"
    d = item.to_dict()
    assert "published_at" in d

# ── Import error handling ─────────────────────────────────────────────

def test_fetch_handles_import_error(fetcher: XFetcher) -> None:
    with patch.dict("sys.modules", {"twscrape": None}):
        items = list(fetcher.fetch("testuser"))
    assert items == []

# ── Registration ──────────────────────────────────────────────────────

def test_x_fetcher_registered() -> None:
    from execution.source_fetchers import FETCHERS
    assert "x" in FETCHERS
    assert FETCHERS["x"] is XFetcher

# ── Config flags ──────────────────────────────────────────────────────

def test_retweets_excluded_by_default(fetcher: XFetcher) -> None:
    tweets = [
        {"tweet_id": "1", "author": "testuser", "text": "RT",
         "published_at": datetime(2025, 6, 1, tzinfo=timezone.utc),
         "is_retweet": True, "is_reply": False, "url": "u", "media": [], "in_reply_to": None},
    ]
    threads = fetcher._reconstruct_threads(tweets, "testuser")
    assert len(threads) == 0

def test_replies_excluded_by_default(fetcher: XFetcher) -> None:
    tweets = [
        {"tweet_id": "1", "author": "other", "text": "reply",
         "published_at": datetime(2025, 6, 1, tzinfo=timezone.utc),
         "is_retweet": False, "is_reply": True, "url": "u", "media": [], "in_reply_to": None},
    ]
    threads = fetcher._reconstruct_threads(tweets, "testuser")
    assert len(threads) == 0

def test_include_media_enabled_by_default() -> None:
    f = XFetcher()
    assert f.include_media is True

# ── Cookie expiry emits cross-agent ──────────────────────────────────

def test_cookie_expiry_emits_broadcast() -> None:
    with patch("subprocess.run") as mock_run:
        XFetcher._emit_cookie_expiry("testuser")
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert "broadcast" in args
        assert "x-fetcher" in args

# ── tweet_to_dict ─────────────────────────────────────────────────────

def test_tweet_to_dict_basic(fetcher: XFetcher) -> None:
    tweet = _make_tweet(100, "hello world")
    d = fetcher._tweet_to_dict(tweet, "testuser")
    assert d is not None
    assert d["tweet_id"] == "100"
    assert d["text"] == "hello world"
    assert d["is_retweet"] is False

def test_tweet_to_dict_retweet(fetcher: XFetcher) -> None:
    tweet = _make_tweet(200, "RT text", is_rt=True)
    d = fetcher._tweet_to_dict(tweet, "testuser")
    assert d["is_retweet"] is True

def test_tweet_to_dict_reply(fetcher: XFetcher) -> None:
    tweet = _make_tweet(300, "reply", handle="other", reply_to=100)
    d = fetcher._tweet_to_dict(tweet, "testuser")
    assert d["is_reply"] is True
    assert d["in_reply_to"] == "100"
