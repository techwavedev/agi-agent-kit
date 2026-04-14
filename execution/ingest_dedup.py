"""SQLite dedup layer for ingest pipeline (#119, techwavedev/agi-agent-kit#123).

Tracks which (source_type, external_id) items have been fetched and which
notebooks each has been pushed to. One table for every source type — uniqueness
is `(source_type, external_id)`.
"""
from __future__ import annotations
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Iterator

from execution.source_fetchers import Item

DEFAULT_DB_PATH = Path(".tmp/ingest/seen.db")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS seen_items (
    source_type TEXT NOT NULL,
    external_id TEXT NOT NULL,
    handle      TEXT NOT NULL,
    fetched_at  TEXT NOT NULL,
    pushed_at   TEXT,
    PRIMARY KEY (source_type, external_id)
);

CREATE TABLE IF NOT EXISTS pushed_to (
    source_type TEXT NOT NULL,
    external_id TEXT NOT NULL,
    notebook_id TEXT NOT NULL,
    pushed_at   TEXT NOT NULL,
    PRIMARY KEY (source_type, external_id, notebook_id),
    FOREIGN KEY (source_type, external_id)
        REFERENCES seen_items(source_type, external_id)
);
"""


@contextmanager
def _connect(db_path: Path) -> Iterator[sqlite3.Connection]:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def ensure_schema(db_path: Path = DEFAULT_DB_PATH) -> None:
    """Idempotent — safe to call every run."""
    with _connect(db_path) as conn:
        conn.executescript(_SCHEMA)


def filter_new(
    items: Iterable[Item],
    db_path: Path = DEFAULT_DB_PATH,
) -> list[Item]:
    """Return only items not yet present in seen_items.

    Also inserts the kept items into seen_items with fetched_at=now (UTC).
    """
    ensure_schema(db_path)
    new: list[Item] = []
    now = datetime.now(timezone.utc).isoformat()
    with _connect(db_path) as conn:
        for it in items:
            row = conn.execute(
                "SELECT 1 FROM seen_items WHERE source_type=? AND external_id=?",
                (it.source_type, it.external_id),
            ).fetchone()
            if row is None:
                conn.execute(
                    "INSERT INTO seen_items "
                    "(source_type, external_id, handle, fetched_at) "
                    "VALUES (?, ?, ?, ?)",
                    (it.source_type, it.external_id, it.source_handle, now),
                )
                new.append(it)
    return new


def mark_pushed(
    items: Iterable[Item],
    notebook_id: str,
    db_path: Path = DEFAULT_DB_PATH,
) -> None:
    """Record that each item was pushed to the given notebook."""
    ensure_schema(db_path)
    now = datetime.now(timezone.utc).isoformat()
    with _connect(db_path) as conn:
        for it in items:
            conn.execute(
                "INSERT OR IGNORE INTO pushed_to "
                "(source_type, external_id, notebook_id, pushed_at) "
                "VALUES (?, ?, ?, ?)",
                (it.source_type, it.external_id, notebook_id, now),
            )
            conn.execute(
                "UPDATE seen_items SET pushed_at=? "
                "WHERE source_type=? AND external_id=? AND pushed_at IS NULL",
                (now, it.source_type, it.external_id),
            )


def needs_push(
    items: Iterable[Item],
    notebook_id: str,
    db_path: Path = DEFAULT_DB_PATH,
) -> list[Item]:
    """Return items not yet pushed to the given notebook."""
    ensure_schema(db_path)
    out: list[Item] = []
    with _connect(db_path) as conn:
        for it in items:
            row = conn.execute(
                "SELECT 1 FROM pushed_to "
                "WHERE source_type=? AND external_id=? AND notebook_id=?",
                (it.source_type, it.external_id, notebook_id),
            ).fetchone()
            if row is None:
                out.append(it)
    return out


__all__ = ["ensure_schema", "filter_new", "mark_pushed", "needs_push", "DEFAULT_DB_PATH"]
