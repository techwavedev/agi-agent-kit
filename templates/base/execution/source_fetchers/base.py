"""Pluggable source-fetcher contract for the ingest pipeline (#119)."""
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Iterable


@dataclass
class Item:
    source_type: str           # "x" | "youtube" | ...
    source_handle: str         # handle / channel id (stable per source)
    external_id: str           # tweet id / video id — unique per (source_type)
    url: str                   # canonical permalink
    published_at: datetime
    title: str | None = None
    body: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["published_at"] = self.published_at.isoformat()
        return d

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Item":
        data = dict(d)
        data["published_at"] = datetime.fromisoformat(data["published_at"])
        return cls(**data)


class SourceFetcher(ABC):
    source_type: str = ""

    @abstractmethod
    def fetch(
        self,
        handle: str,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> Iterable[Item]:
        """Yield Items for the given handle within the optional date range."""
