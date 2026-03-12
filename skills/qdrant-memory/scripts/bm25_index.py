#!/usr/bin/env python3
"""
Script: bm25_index.py
Purpose: SQLite FTS5 keyword index for BM25 full-text search.

Works as a sidecar alongside Qdrant vector search to enable true
hybrid retrieval: semantic similarity + keyword/exact matching.

Inspired by OpenClaw's hybrid memory architecture.

Usage:
    # Index a document
    python3 bm25_index.py index --doc-id "abc123" --content "ImagePullBackOff error in prod"

    # Search
    python3 bm25_index.py search --query "ImagePullBackOff" --top-k 5

    # Sync from Qdrant (bulk import)
    python3 bm25_index.py sync

    # Stats
    python3 bm25_index.py stats

Environment Variables:
    BM25_INDEX_PATH     - SQLite database path (default: ~/.agi/memory_bm25.sqlite)
    QDRANT_URL          - Qdrant server URL for sync (default: http://localhost:6333)
    MEMORY_COLLECTION   - Qdrant collection to sync from (default: agent_memory)

Exit Codes:
    0 - Success
    1 - No results
    2 - Connection error
    3 - Operation error
"""

import argparse
import json
import math
import os
import sqlite3
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib.request import Request, urlopen
from urllib.error import URLError


# Configuration
DEFAULT_INDEX_PATH = os.path.join(
    os.path.expanduser("~"), ".agi", "memory_bm25.sqlite"
)
BM25_INDEX_PATH = os.environ.get("BM25_INDEX_PATH", DEFAULT_INDEX_PATH)
QDRANT_URL = os.environ.get("QDRANT_URL", "http://localhost:6333")
COLLECTION = os.environ.get("MEMORY_COLLECTION", "agent_memory")


class BM25Index:
    """SQLite FTS5-based BM25 keyword index for memory search."""

    def __init__(self, db_path: str = BM25_INDEX_PATH):
        """
        Initialize BM25 index.

        Args:
            db_path: Path to SQLite database. Use ':memory:' for testing.
        """
        self.db_path = db_path

        # Ensure directory exists (skip for in-memory)
        if db_path != ":memory:":
            os.makedirs(os.path.dirname(db_path), exist_ok=True)

        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self):
        """Create FTS5 virtual table and metadata table if not exists."""
        cursor = self.conn.cursor()

        # FTS5 virtual table for full-text search
        # content, type, project, tags are all searchable
        cursor.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS memory_fts USING fts5(
                doc_id UNINDEXED,
                content,
                memory_type,
                project,
                tags,
                tokenize='porter unicode61'
            )
        """)

        # Metadata table for tracking sync state and extra fields
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memory_meta (
                doc_id TEXT PRIMARY KEY,
                content_hash TEXT,
                indexed_at TEXT,
                source TEXT DEFAULT 'direct'
            )
        """)

        # Index stats
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS index_stats (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)

        self.conn.commit()

    def index_document(
        self,
        doc_id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Index a document for BM25 search.

        Args:
            doc_id: Unique document identifier (Qdrant point ID as string)
            content: Document text content
            metadata: Optional metadata (type, project, tags)

        Returns:
            Indexing result with status
        """
        metadata = metadata or {}
        content_hash = str(hash(content))

        cursor = self.conn.cursor()

        # Check if already indexed with same content
        cursor.execute(
            "SELECT content_hash FROM memory_meta WHERE doc_id = ?",
            (doc_id,)
        )
        existing = cursor.fetchone()

        if existing and existing["content_hash"] == content_hash:
            return {"status": "unchanged", "doc_id": doc_id}

        # Remove old entry if exists (update case)
        if existing:
            cursor.execute(
                "DELETE FROM memory_fts WHERE doc_id = ?", (doc_id,)
            )
            cursor.execute(
                "DELETE FROM memory_meta WHERE doc_id = ?", (doc_id,)
            )

        # Extract searchable fields
        memory_type = metadata.get("type", "")
        project = metadata.get("project", "")
        tags = " ".join(metadata.get("tags", [])) if isinstance(
            metadata.get("tags"), list
        ) else str(metadata.get("tags", ""))

        # Insert into FTS5
        cursor.execute(
            "INSERT INTO memory_fts (doc_id, content, memory_type, project, tags) "
            "VALUES (?, ?, ?, ?, ?)",
            (doc_id, content, memory_type, project, tags)
        )

        # Insert metadata
        cursor.execute(
            "INSERT INTO memory_meta (doc_id, content_hash, indexed_at, source) "
            "VALUES (?, ?, ?, ?)",
            (doc_id, content_hash, datetime.utcnow().isoformat(), "direct")
        )

        self.conn.commit()

        return {
            "status": "indexed",
            "doc_id": doc_id,
            "content_length": len(content)
        }

    @staticmethod
    def _sanitize_fts_query(query: str) -> str:
        """
        Sanitize a query string for safe FTS5 MATCH syntax.

        FTS5 operators: AND, OR, NOT, -, *, NEAR, ^
        Hyphens in tokens like 'sg-018f20ea' are treated as NOT.
        Wrapping each token in double-quotes forces literal matching.
        """
        if not query or not query.strip():
            return ""

        # If query contains FTS5 special chars, quote the entire thing
        special_chars = set('-*:"(){}[]^~')
        tokens = query.strip().split()
        quoted = []
        for token in tokens:
            # Skip empty tokens
            if not token:
                continue
            # If token contains special chars or is an FTS5 keyword, quote it
            if any(c in special_chars for c in token) or token.upper() in ("AND", "OR", "NOT", "NEAR"):
                # Escape any internal double-quotes
                safe = token.replace('"', '""')
                quoted.append(f'"{safe}"')
            else:
                quoted.append(token)

        return " ".join(quoted)

    def search(
        self,
        query: str,
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search using BM25 ranking.

        Args:
            query: Search query (keywords, error codes, IDs, etc.)
            top_k: Maximum number of results

        Returns:
            List of results with doc_id, content snippet, and normalized score
        """
        cursor = self.conn.cursor()

        try:
            # Sanitize query for FTS5 MATCH syntax
            # FTS5 treats - as NOT, * as prefix, etc.
            # Quote each token to force literal matching
            safe_query = self._sanitize_fts_query(query)
            if not safe_query:
                return []

            # FTS5 MATCH query with BM25 ranking
            # bm25() returns negative values where lower = better match
            cursor.execute("""
                SELECT
                    doc_id,
                    snippet(memory_fts, 1, '>>>', '<<<', '...', 64) as snippet,
                    content,
                    memory_type,
                    project,
                    tags,
                    bm25(memory_fts) as bm25_rank
                FROM memory_fts
                WHERE memory_fts MATCH ?
                ORDER BY bm25_rank
                LIMIT ?
            """, (safe_query, top_k))

            results = []
            for row in cursor.fetchall():
                # Normalize BM25 rank to 0..1 score
                # bm25() returns negative values, lower = better
                # Formula from OpenClaw: textScore = 1 / (1 + max(0, abs(rank)))
                raw_rank = abs(row["bm25_rank"])
                text_score = 1.0 / (1.0 + raw_rank)

                results.append({
                    "doc_id": str(row["doc_id"]),
                    "content": row["content"],
                    "snippet": row["snippet"],
                    "type": row["memory_type"],
                    "project": row["project"],
                    "tags": row["tags"].split() if row["tags"] else [],
                    "bm25_rank": row["bm25_rank"],
                    "text_score": round(text_score, 4)
                })

            return results

        except sqlite3.OperationalError as e:
            if "no such table" in str(e):
                return []
            raise

    def remove(self, doc_id: str) -> Dict[str, Any]:
        """Remove a document from the BM25 index."""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM memory_fts WHERE doc_id = ?", (doc_id,))
        cursor.execute("DELETE FROM memory_meta WHERE doc_id = ?", (doc_id,))
        self.conn.commit()
        deleted = cursor.rowcount > 0
        return {"status": "removed" if deleted else "not_found", "doc_id": doc_id}

    def sync_from_qdrant(
        self,
        batch_size: int = 100
    ) -> Dict[str, Any]:
        """
        Bulk sync all Qdrant points into the FTS index.

        Scrolls through the entire Qdrant collection and indexes
        all documents that aren't already in the BM25 index.

        Returns:
            Sync result with counts
        """
        indexed = 0
        skipped = 0
        errors = 0
        offset = None

        while True:
            # Scroll through Qdrant collection
            scroll_payload = {
                "limit": batch_size,
                "with_payload": True
            }
            if offset is not None:
                scroll_payload["offset"] = offset

            try:
                req = Request(
                    f"{QDRANT_URL}/collections/{COLLECTION}/points/scroll",
                    data=json.dumps(scroll_payload).encode(),
                    headers={"Content-Type": "application/json"},
                    method="POST"
                )

                with urlopen(req, timeout=30) as response:
                    result = json.loads(response.read().decode())

                points = result.get("result", {}).get("points", [])
                next_offset = result.get("result", {}).get("next_page_offset")

                for point in points:
                    try:
                        payload = point.get("payload", {})
                        content = payload.get("content", "")
                        if not content:
                            # Try response field (cache entries)
                            content = payload.get("response", "")
                        if not content:
                            skipped += 1
                            continue

                        doc_id = str(point["id"])
                        metadata = {
                            "type": payload.get("type", ""),
                            "project": payload.get("project", ""),
                            "tags": payload.get("tags", [])
                        }

                        result_entry = self.index_document(
                            doc_id, content, metadata
                        )
                        if result_entry["status"] == "indexed":
                            indexed += 1
                        else:
                            skipped += 1

                    except Exception as e:
                        errors += 1

                if not next_offset or not points:
                    break
                offset = next_offset

            except URLError as e:
                return {
                    "status": "error",
                    "message": f"Cannot connect to Qdrant: {e}",
                    "indexed": indexed,
                    "skipped": skipped,
                    "errors": errors
                }

        # Update sync timestamp
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO index_stats (key, value) VALUES (?, ?)",
            ("last_sync", datetime.utcnow().isoformat())
        )
        self.conn.commit()

        return {
            "status": "synced",
            "indexed": indexed,
            "skipped": skipped,
            "errors": errors,
            "total": indexed + skipped
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get index statistics."""
        cursor = self.conn.cursor()

        # Document count
        cursor.execute("SELECT COUNT(*) as count FROM memory_meta")
        doc_count = cursor.fetchone()["count"]

        # Last sync
        cursor.execute(
            "SELECT value FROM index_stats WHERE key = 'last_sync'"
        )
        row = cursor.fetchone()
        last_sync = row["value"] if row else None

        # DB file size
        db_size = 0
        if self.db_path != ":memory:" and os.path.exists(self.db_path):
            db_size = os.path.getsize(self.db_path)

        return {
            "documents": doc_count,
            "last_sync": last_sync,
            "db_path": self.db_path,
            "db_size_bytes": db_size,
            "db_size_human": _human_size(db_size)
        }

    def close(self):
        """Close the database connection."""
        self.conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


def _human_size(size_bytes: int) -> str:
    """Convert bytes to human readable string."""
    if size_bytes == 0:
        return "0 B"
    units = ["B", "KB", "MB", "GB"]
    i = int(math.floor(math.log(size_bytes, 1024)))
    i = min(i, len(units) - 1)
    s = round(size_bytes / (1024 ** i), 1)
    return f"{s} {units[i]}"


def main():
    parser = argparse.ArgumentParser(
        description="BM25 keyword index for hybrid memory search"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Index command
    idx_parser = subparsers.add_parser("index", help="Index a document")
    idx_parser.add_argument("--doc-id", required=True, help="Document ID")
    idx_parser.add_argument("--content", required=True, help="Document content")
    idx_parser.add_argument("--type", default="", help="Memory type")
    idx_parser.add_argument("--project", default="", help="Project name")
    idx_parser.add_argument("--tags", nargs="*", default=[], help="Tags")

    # Search command
    search_parser = subparsers.add_parser("search", help="BM25 search")
    search_parser.add_argument("--query", required=True, help="Search query")
    search_parser.add_argument(
        "--top-k", type=int, default=10, help="Number of results"
    )

    # Sync command
    subparsers.add_parser("sync", help="Sync from Qdrant collection")

    # Stats command
    subparsers.add_parser("stats", help="Show index statistics")

    # Remove command
    rm_parser = subparsers.add_parser("remove", help="Remove a document")
    rm_parser.add_argument("--doc-id", required=True, help="Document ID")

    args = parser.parse_args()

    try:
        with BM25Index() as index:
            if args.command == "index":
                metadata = {
                    "type": args.type,
                    "project": args.project,
                    "tags": args.tags
                }
                result = index.index_document(
                    args.doc_id, args.content, metadata
                )
                print(json.dumps(result, indent=2))
                sys.exit(0)

            elif args.command == "search":
                results = index.search(args.query, args.top_k)
                output = {
                    "query": args.query,
                    "results": results,
                    "total": len(results),
                    "search_type": "bm25"
                }
                print(json.dumps(output, indent=2))
                sys.exit(0 if results else 1)

            elif args.command == "sync":
                result = index.sync_from_qdrant()
                print(json.dumps(result, indent=2))
                sys.exit(
                    0 if result["status"] == "synced" else 2
                )

            elif args.command == "stats":
                stats = index.get_stats()
                print(json.dumps(stats, indent=2))
                sys.exit(0)

            elif args.command == "remove":
                result = index.remove(args.doc_id)
                print(json.dumps(result, indent=2))
                sys.exit(0)

    except sqlite3.Error as e:
        print(json.dumps({
            "status": "error",
            "type": "sqlite_error",
            "message": str(e)
        }), file=sys.stderr)
        sys.exit(3)
    except Exception as e:
        print(json.dumps({
            "status": "error",
            "type": type(e).__name__,
            "message": str(e)
        }), file=sys.stderr)
        sys.exit(3)


if __name__ == "__main__":
    main()
