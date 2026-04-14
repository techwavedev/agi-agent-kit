"""Unit tests for execution.source_fetchers contract (#120)."""
from __future__ import annotations
import pytest
from datetime import datetime, timezone
from execution.source_fetchers import FETCHERS, get, register, Item, SourceFetcher


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_item(i: int, handle: str = "alice") -> Item:
    return Item(
        source_type="stub",
        source_handle=handle,
        external_id=str(i),
        url=f"https://example.com/{i}",
        published_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        body=f"item {i}",
    )


# ---------------------------------------------------------------------------
# Stub fetcher (registered once at module level for all tests)
# ---------------------------------------------------------------------------

@register
class StubFetcher(SourceFetcher):
    source_type = "stub"

    def fetch(self, handle, since=None, until=None):
        for i in range(3):
            yield _make_item(i, handle)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_registry_contains_stub():
    assert "stub" in FETCHERS
    assert FETCHERS["stub"] is StubFetcher


def test_get_returns_registered_class():
    assert get("stub") is StubFetcher


def test_get_unknown_raises_actionable_key_error():
    with pytest.raises(KeyError) as exc_info:
        get("nope")
    msg = str(exc_info.value)
    assert "nope" in msg
    assert "Known types" in msg


def test_fetch_yields_three_items():
    items = list(get("stub")().fetch("alice"))
    assert len(items) == 3


def test_item_round_trip():
    items = list(get("stub")().fetch("alice"))
    for it in items:
        assert Item.from_dict(it.to_dict()) == it, "round-trip failed"


def test_item_to_dict_published_at_is_string():
    item = _make_item(0)
    d = item.to_dict()
    assert isinstance(d["published_at"], str)
    assert d["published_at"] == "2026-01-01T00:00:00+00:00"


def test_item_defaults():
    item = _make_item(0)
    assert item.title is None
    assert item.body == "item 0"
    assert item.metadata == {}


def test_duplicate_registration_raises():
    with pytest.raises(ValueError, match="already registered"):
        register(StubFetcher)


def test_empty_source_type_raises():
    with pytest.raises(ValueError, match="must set a non-empty source_type"):
        @register
        class BadFetcher(SourceFetcher):
            source_type = ""

            def fetch(self, handle, since=None, until=None):
                return iter([])
