"""YouTube channel fetcher using yt-dlp (#122).

Pulls videos from a channel within a date range, including transcripts
(manual subs → auto-captions → description-only fallback) and thumbnails.
No API quota — yt-dlp scrapes public metadata.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from . import register
from .base import Item, SourceFetcher

MEDIA_DIR = Path(".tmp/ingest/media/youtube")


@register
class YouTubeFetcher(SourceFetcher):
    source_type = "youtube"

    def __init__(
        self,
        media_dir: Path = MEDIA_DIR,
        include_shorts: bool = False,
        transcripts: bool = True,
    ):
        self.media_dir = media_dir
        self.include_shorts = include_shorts
        self.transcripts = transcripts
        if not shutil.which("yt-dlp"):
            raise RuntimeError("yt-dlp is required: pip install yt-dlp")

    def fetch(
        self,
        handle: str,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> Iterable[Item]:
        """Yield Items for the channel between since and until (inclusive)."""
        channel_url = self._channel_url(handle)
        entries = self._list_videos(channel_url, since, until)
        for entry in entries:
            if not self.include_shorts and self._is_short(entry):
                continue
            yield self._entry_to_item(handle, entry)

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _channel_url(self, handle: str) -> str:
        """Normalize handle to a channel URL.

        Accepts: '@handle', 'handle', full URL.
        """
        if handle.startswith("http://") or handle.startswith("https://"):
            return handle
        if not handle.startswith("@"):
            handle = f"@{handle}"
        return f"https://www.youtube.com/{handle}/videos"

    def _list_videos(
        self, channel_url: str, since: datetime | None, until: datetime | None
    ) -> list[dict]:
        """Run `yt-dlp --flat-playlist --dump-json [--dateafter --datebefore]`
        and parse JSON-lines output. One dict per video."""
        cmd = [
            "yt-dlp",
            "--flat-playlist",
            "--dump-json",
            "--no-warnings",
        ]
        if since:
            cmd += ["--dateafter", since.strftime("%Y%m%d")]
        if until:
            cmd += ["--datebefore", until.strftime("%Y%m%d")]
        cmd.append(channel_url)

        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        entries: list[dict] = []
        for line in result.stdout.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return entries

    def _is_short(self, entry: dict) -> bool:
        """Heuristic: duration < 60s OR url contains '/shorts/'."""
        duration = entry.get("duration") or 0
        if duration < 60:
            return True
        url = entry.get("webpage_url") or entry.get("url") or ""
        return "/shorts/" in url

    def _entry_to_item(self, handle: str, entry: dict) -> Item:
        """Map a yt-dlp entry to an Item, downloading thumbnail and
        fetching transcript via _fetch_transcript."""
        video_id = entry.get("id", "")
        video_url = (
            entry.get("webpage_url")
            or entry.get("url")
            or f"https://www.youtube.com/watch?v={video_id}"
        )

        # Parse publish date from YYYYMMDD string
        upload_date = entry.get("upload_date", "")
        if upload_date and len(upload_date) == 8:
            published_at = datetime(
                int(upload_date[:4]),
                int(upload_date[4:6]),
                int(upload_date[6:8]),
                tzinfo=timezone.utc,
            )
        else:
            # Sentinel: epoch zero indicates the upload date was unavailable
            published_at = datetime(1970, 1, 1, tzinfo=timezone.utc)

        thumbnail_path: str | None = None
        transcript_text = entry.get("description") or ""
        transcript_quality = "description_only"

        if video_id:
            video_dir = self.media_dir / video_id
            video_dir.mkdir(parents=True, exist_ok=True)
            thumbnail_path = self._download_thumbnail(video_id, video_url, video_dir)
            if self.transcripts:
                text, quality = self._fetch_transcript(video_id)
                if text:
                    transcript_text = text
                    transcript_quality = quality

        return Item(
            source_type="youtube",
            source_handle=handle,
            external_id=video_id,
            url=video_url,
            published_at=published_at,
            title=entry.get("title"),
            body=transcript_text,
            metadata={
                "thumbnail_path": thumbnail_path,
                "transcript_quality": transcript_quality,
                "duration_seconds": int(entry.get("duration") or 0),
                "chapters": entry.get("chapters"),
                "description": entry.get("description") or "",
            },
        )

    def _download_thumbnail(
        self, video_id: str, video_url: str, video_dir: Path
    ) -> str | None:
        """Download thumbnail for a video; return local path or None on failure."""
        cmd = [
            "yt-dlp",
            "--write-thumbnail",
            "--skip-download",
            "--no-warnings",
            "-o", str(video_dir / "%(id)s"),
            video_url,
        ]
        try:
            subprocess.run(cmd, capture_output=True, text=True, check=True)
        except subprocess.CalledProcessError:
            return None
        # Find the downloaded thumbnail by checking for common image extensions
        _IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
        for f in video_dir.iterdir():
            if f.stem == video_id and f.suffix.lower() in _IMAGE_SUFFIXES:
                return str(f)
        return None

    def _fetch_transcript(self, video_id: str) -> tuple[str, str]:
        """Return (transcript_text, quality) where quality is
        'manual', 'auto', or 'description_only'."""
        video_url = f"https://www.youtube.com/watch?v={video_id}"
        video_dir = self.media_dir / video_id

        # Try manual subtitles first, then auto-generated captions
        for is_auto in (False, True):
            quality = "auto" if is_auto else "manual"
            flag = "--write-auto-subs" if is_auto else "--write-subs"
            cmd = [
                "yt-dlp",
                flag,
                "--skip-download",
                "--sub-langs", "en",
                "--sub-format", "vtt",
                "--no-warnings",
                "-o", str(video_dir / "%(id)s"),
                video_url,
            ]
            try:
                subprocess.run(cmd, capture_output=True, text=True, check=True)
            except subprocess.CalledProcessError:
                continue

            vtt_files = list(video_dir.glob("*.vtt"))
            if vtt_files:
                text = self._parse_vtt(vtt_files[0].read_text(encoding="utf-8"))
                if text:
                    return text, quality

        return "", "description_only"

    @staticmethod
    def _parse_vtt(vtt_text: str) -> str:
        """Strip VTT timestamps and tags; return clean deduplicated text."""
        lines: list[str] = []
        prev = ""
        for line in vtt_text.splitlines():
            # Skip header, blank lines, and timestamp cue lines
            if not line.strip() or "-->" in line or line.startswith("WEBVTT"):
                continue
            # Skip structural blocks
            if re.match(r"^(NOTE|STYLE|REGION)\b", line):
                continue
            # Strip inline timing tags like <00:00:00.000> and <c></c>
            line = re.sub(r"<[^>]+>", "", line).strip()
            if line and line != prev:
                lines.append(line)
                prev = line
        return " ".join(lines)
