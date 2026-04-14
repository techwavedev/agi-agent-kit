"""Pytest-runnable acceptance tests for execution.ingest_dedup (#123)."""
from __future__ import annotations
from datetime import datetime, timezone
from pathlib import Path

import pytest

from execution.source_fetchers import Item
from execution.ingest_dedup import ensure_schema, filter_new, mark_pushed, needs_push


def _mk(i: int) -> Item:
    return Item(
        source_type="x",
        source_handle="alice",
        external_id=str(i),
        url=f"https://x.com/alice/status/{i}",
        published_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        body=f"t{i}",
    )


def test_ensure_schema_is_idempotent(tmp_path: Path) -> None:
    db = tmp_path / "seen.db"
    ensure_schema(db)
    ensure_schema(db)  # must not raise


def test_filter_new_returns_all_on_first_run(tmp_path: Path) -> None:
    db = tmp_path / "seen.db"
    batch = [_mk(1), _mk(2), _mk(3)]
    new = filter_new(batch, db)
    assert len(new) == 3


def test_filter_new_returns_zero_on_second_run(tmp_path: Path) -> None:
    db = tmp_path / "seen.db"
    batch = [_mk(1), _mk(2), _mk(3)]
    filter_new(batch, db)
    new2 = filter_new(batch, db)
    assert len(new2) == 0, f"expected 0 new on rerun, got {len(new2)}"


def test_mark_pushed_and_needs_push_notebook_a(tmp_path: Path) -> None:
    db = tmp_path / "seen.db"
    batch = [_mk(1), _mk(2), _mk(3)]
    filter_new(batch, db)
    mark_pushed(batch, "nb-A", db)
    assert needs_push(batch, "nb-A", db) == []


def test_needs_push_notebook_b_after_push_to_a(tmp_path: Path) -> None:
    db = tmp_path / "seen.db"
    batch = [_mk(1), _mk(2), _mk(3)]
    filter_new(batch, db)
    mark_pushed(batch, "nb-A", db)
    need_b = needs_push(batch, "nb-B", db)
    assert len(need_b) == 3, f"expected 3 needing push to nb-B, got {len(need_b)}"


def test_needs_push_empty_after_push_to_both(tmp_path: Path) -> None:
    db = tmp_path / "seen.db"
    batch = [_mk(1), _mk(2), _mk(3)]
    filter_new(batch, db)
    mark_pushed(batch, "nb-A", db)
    mark_pushed(batch, "nb-B", db)
    assert needs_push(batch, "nb-A", db) == []
    assert needs_push(batch, "nb-B", db) == []


def test_mark_pushed_idempotent(tmp_path: Path) -> None:
    db = tmp_path / "seen.db"
    batch = [_mk(1)]
    filter_new(batch, db)
    mark_pushed(batch, "nb-A", db)
    mark_pushed(batch, "nb-A", db)  # second call must not raise
    assert needs_push(batch, "nb-A", db) == []


def test_filter_new_partial_overlap(tmp_path: Path) -> None:
    db = tmp_path / "seen.db"
    batch1 = [_mk(1), _mk(2)]
    filter_new(batch1, db)
    batch2 = [_mk(2), _mk(3)]  # item 2 already seen
    new = filter_new(batch2, db)
    assert len(new) == 1
    assert new[0].external_id == "3"
