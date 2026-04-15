"""X (Twitter) fetcher using twscrape (#121).

Pulls tweets from an X profile within a date range using twscrape
(async Twitter scraper with cookie-jar auth).  No official API key
needed — just a logged-in cookie jar at `.tmp/ingest/x_cookies.json`.
"""
from __future__ import annotations

import asyncio
import json
import logging
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from . import register
from .base import Item, SourceFetcher

logger = logging.getLogger(__name__)

COOKIE_PATH = Path(".tmp/ingest/x_cookies.json")
MEDIA_DIR = Path(".tmp/ingest/media/x")


@register
class XFetcher(SourceFetcher):
    """Scrape an X profile timeline using twscrape."""

    source_type = "x"

    def __init__(
        self,
        cookie_path: Path = COOKIE_PATH,
        media_dir: Path = MEDIA_DIR,
        include_replies: bool = False,
        include_retweets: bool = False,
        include_media: bool = True,
        max_items: int = 200,
    ):
        self.cookie_path = cookie_path
        self.media_dir = media_dir
        self.include_replies = include_replies
        self.include_retweets = include_retweets
        self.include_media = include_media
        self.max_items = max_items

    # ------------------------------------------------------------------
    # Public API (SourceFetcher contract)
    # ------------------------------------------------------------------

    def fetch(
        self,
        handle: str,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> Iterable[Item]:
        try:
            import twscrape  # noqa: F401
        except ImportError:
            logger.error("twscrape is required: pip install twscrape")
            return

        handle_clean = self._clean_handle(handle)
        try:
            raw = asyncio.run(self._fetch_tweets(handle_clean, since, until))
        except Exception as exc:
            logger.error("Failed to fetch tweets for @%s: %s", handle_clean, exc)
            return

        for thread in self._reconstruct_threads(raw, handle_clean):
            item = self._thread_to_item(thread, handle_clean)
            if item is not None:
                yield item

    # ------------------------------------------------------------------
    # twscrape async internals
    # ------------------------------------------------------------------

    async def _fetch_tweets(
        self, handle: str, since: datetime | None, until: datetime | None,
    ) -> list[dict]:
        from twscrape import API

        api = API()

        if self.cookie_path.exists():
            try:
                cookies = json.loads(self.cookie_path.read_text(encoding="utf-8"))
                if isinstance(cookies, list):
                    cookie_dict = {c["name"]: c["value"] for c in cookies
                                   if "name" in c and "value" in c}
                elif isinstance(cookies, dict):
                    cookie_dict = cookies
                else:
                    cookie_dict = {}
                if cookie_dict:
                    await api.pool.set_cookies("x_cookies", cookie_dict)
            except Exception as exc:
                logger.warning("Cookie load failed %s: %s", self.cookie_path, exc)
                self._emit_cookie_expiry(handle)
                return []

        try:
            user = await api.user_by_login(handle)
        except Exception as exc:
            logger.error("Cannot resolve @%s (cookies expired?): %s", handle, exc)
            self._emit_cookie_expiry(handle)
            return []

        if not user:
            logger.error("User @%s not found", handle)
            return []

        collected: list[dict] = []
        try:
            async for tweet in api.user_tweets(user.id, limit=self.max_items):
                data = self._tweet_to_dict(tweet, handle)
                if data is None:
                    continue
                ts = data.get("published_at")
                if ts and since and ts < since:
                    continue
                if ts and until and ts > until:
                    continue
                collected.append(data)
        except Exception as exc:
            logger.error("Error streaming tweets for @%s: %s", handle, exc)
            if "auth" in str(exc).lower() or "login" in str(exc).lower():
                self._emit_cookie_expiry(handle)

        return collected

    def _tweet_to_dict(self, tweet: Any, handle: str) -> dict | None:
        try:
            tid = str(tweet.id)
            author = (tweet.user.username or "").lower() if tweet.user else ""
            is_rt = hasattr(tweet, "retweetedTweet") and tweet.retweetedTweet is not None
            is_reply = bool(tweet.inReplyToTweetId) and author != handle.lower()
            pub = tweet.date
            if pub and pub.tzinfo is None:
                pub = pub.replace(tzinfo=timezone.utc)

            media: list[dict] = []
            if self.include_media and hasattr(tweet, "media") and tweet.media:
                media = self._extract_media(tweet, tid)

            return {
                "tweet_id": tid, "author": author, "text": tweet.rawContent or "",
                "published_at": pub, "is_retweet": is_rt, "is_reply": is_reply,
                "url": f"https://x.com/{author}/status/{tid}",
                "media": media,
                "in_reply_to": str(tweet.inReplyToTweetId) if tweet.inReplyToTweetId else None,
            }
        except Exception as exc:
            logger.debug("Tweet parse error: %s", exc)
            return None

    def _extract_media(self, tweet: Any, tweet_id: str) -> list[dict]:
        media: list[dict] = []
        if not tweet.media:
            return media
        for i, m in enumerate(tweet.media.photos or []):
            url = m.url if hasattr(m, "url") else str(m)
            local = self._download_media(url, tweet_id, i)
            media.append({"type": "image", "url": url,
                          "alt": getattr(m, "altText", "") or "", "local_path": local})
        for v in tweet.media.videos or []:
            url = ""
            if hasattr(v, "variants") and v.variants:
                best = max(v.variants, key=lambda x: getattr(x, "bitrate", 0) or 0)
                url = best.url if hasattr(best, "url") else ""
            media.append({"type": "video", "url": url, "alt": "", "local_path": None})
        return media

    def _download_media(self, url: str, tweet_id: str, idx: int) -> str | None:
        try:
            d = self.media_dir / tweet_id
            d.mkdir(parents=True, exist_ok=True)
            ext = Path(url.split("?")[0]).suffix or ".jpg"
            target = d / f"{idx}{ext}"
            urllib.request.urlretrieve(url, target)  # noqa: S310
            return str(target)
        except Exception as exc:
            logger.debug("Media download failed %s: %s", url, exc)
            return None

    # ------------------------------------------------------------------
    # Thread reconstruction
    # ------------------------------------------------------------------

    def _reconstruct_threads(self, tweets: list[dict], handle: str) -> list[list[dict]]:
        if not tweets:
            return []
        tweets.sort(key=lambda t: t.get("published_at") or datetime.min.replace(tzinfo=timezone.utc))

        filtered = [t for t in tweets
                    if not (t["is_retweet"] and not self.include_retweets)
                    and not (t["is_reply"] and not self.include_replies)]

        by_id = {t["tweet_id"]: t for t in filtered}
        used: set[str] = set()
        threads: list[list[dict]] = []

        for t in filtered:
            if t["tweet_id"] in used:
                continue
            chain = [t]
            used.add(t["tweet_id"])
            cur = t["tweet_id"]
            while True:
                nxt = next((c for c in filtered
                           if c["tweet_id"] not in used
                           and c.get("in_reply_to") == cur
                           and c["author"].lower() == handle.lower()), None)
                if nxt is None:
                    break
                chain.append(nxt)
                used.add(nxt["tweet_id"])
                cur = nxt["tweet_id"]
            threads.append(chain)
        return threads

    def _thread_to_item(self, thread: list[dict], handle: str) -> Item | None:
        if not thread:
            return None
        first = thread[0]
        body = "\n\n---\n\n".join(t["text"] for t in thread if t["text"])
        all_media = [m for t in thread for m in t.get("media", [])]
        pub = first.get("published_at") or datetime.now(tz=timezone.utc)
        return Item(
            source_type="x", source_handle=handle, external_id=first["tweet_id"],
            url=first["url"], published_at=pub, title=None, body=body,
            metadata={"tweet_count": len(thread),
                      "media": all_media or None, "is_thread": len(thread) > 1},
        )

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    @staticmethod
    def _clean_handle(handle: str) -> str:
        if handle.startswith("http"):
            return handle.rstrip("/").split("/")[-1].lower()
        return handle.lstrip("@").lower()

    @staticmethod
    def _emit_cookie_expiry(handle: str) -> None:
        logger.error("X cookie jar expired for @%s. Re-export to %s", handle, COOKIE_PATH)
        try:
            import subprocess
            subprocess.run(
                ["python3", "execution/cross_agent_context.py", "broadcast",
                 "--agent", "x-fetcher",
                 "--message", f"X cookie jar expired for @{handle}. Re-export to {COOKIE_PATH}",
                 "--project", "agi-agent-kit"],
                timeout=10, capture_output=True,
            )
        except Exception:
            pass
