"""Registry of source fetchers. Implementations register themselves here."""
from __future__ import annotations
from .base import Item, SourceFetcher

FETCHERS: dict[str, type[SourceFetcher]] = {}


def register(cls: type[SourceFetcher]) -> type[SourceFetcher]:
    if not cls.source_type:
        raise ValueError(f"{cls.__name__} must set a non-empty source_type")
    if cls.source_type in FETCHERS:
        raise ValueError(
            f"source_type '{cls.source_type}' already registered by "
            f"{FETCHERS[cls.source_type].__name__}"
        )
    FETCHERS[cls.source_type] = cls
    return cls


def get(source_type: str) -> type[SourceFetcher]:
    try:
        return FETCHERS[source_type]
    except KeyError as e:
        known = ", ".join(sorted(FETCHERS)) or "<none>"
        raise KeyError(
            f"No fetcher registered for source_type '{source_type}'. "
            f"Known types: {known}"
        ) from e


__all__ = ["Item", "SourceFetcher", "FETCHERS", "register", "get"]
