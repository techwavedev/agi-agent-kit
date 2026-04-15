"""Tests for execution/ingest_dispatcher.py + execution/ingest_config.py (#128)."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from execution import ingest_config, ingest_dispatcher  # noqa: E402
from execution.source_fetchers.base import Item  # noqa: E402


def _mk_item(external_id: str, source_type: str = "x", handle: str = "alice") -> Item:
    return Item(
        source_type=source_type, source_handle=handle,
        external_id=external_id,
        url=f"https://example.test/{external_id}",
        published_at=datetime(2026, 4, 14, 12, 0, tzinfo=timezone.utc),
        title=f"post {external_id}", body=f"body for {external_id}",
    )


def _valid_config(tmp: Path, include_disabled: bool = True) -> Path:
    cfg = {
        "version": 1,
        "sources": [
            {
                "id": "alice-x", "type": "x", "handle": "alice",
                "notebooks": ["NB-A"], "enabled": True, "cadence": "daily",
            },
        ],
    }
    if include_disabled:
        cfg["sources"].append({
            "id": "bob-yt", "type": "youtube", "handle": "@bob",
            "notebooks": ["NB-B"], "enabled": False, "cadence": "weekly",
        })
    p = tmp / "ingest_sources.json"
    p.write_text(json.dumps(cfg, indent=2))
    return p


class ConfigValidatorTests(unittest.TestCase):
    def test_valid_config_loads(self):
        with tempfile.TemporaryDirectory() as td:
            res = ingest_config.load_config(_valid_config(Path(td)))
            self.assertTrue(res.ok)
            self.assertEqual(len(res.config["sources"]), 2)

    def test_missing_file(self):
        res = ingest_config.load_config(Path("/tmp/nonexistent-ingest.json"))
        self.assertFalse(res.ok)
        self.assertTrue(any("config not found" in e for e in res.errors))

    def test_bad_version(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "c.json"
            p.write_text(json.dumps({"version": 2, "sources": []}))
            res = ingest_config.load_config(p)
            self.assertFalse(res.ok)

    def test_duplicate_ids(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "c.json"
            p.write_text(json.dumps({
                "version": 1,
                "sources": [
                    {"id": "a", "type": "x", "handle": "h",
                     "notebooks": ["N"], "enabled": True},
                    {"id": "a", "type": "x", "handle": "h",
                     "notebooks": ["N"], "enabled": True},
                ],
            }))
            res = ingest_config.load_config(p)
            self.assertFalse(res.ok)
            self.assertTrue(any("duplicate" in e for e in res.errors))

    def test_enabled_without_cadence_warns(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "c.json"
            p.write_text(json.dumps({
                "version": 1,
                "sources": [{"id": "a", "type": "x", "handle": "h",
                             "notebooks": ["N"], "enabled": True}],
            }))
            res = ingest_config.load_config(p)
            self.assertTrue(res.ok)
            self.assertTrue(any("cadence/schedule" in w for w in res.warnings))

    def test_persist_notebook_id(self):
        with tempfile.TemporaryDirectory() as td:
            p = _valid_config(Path(td))
            ingest_config.persist_notebook_id(p, "alice-x", "NB-A", "abc123")
            cfg = json.loads(p.read_text())
            s = cfg["sources"][0]
            self.assertEqual(s["notebook_ids"]["NB-A"], "abc123")


class _StubFetcher:
    source_type = "x"

    def __init__(self, items):
        self._items = items

    def fetch(self, handle, since=None, until=None, **kwargs):
        return list(self._items)


class DispatcherTests(unittest.TestCase):
    def test_dry_run_lists_enabled_only(self):
        with tempfile.TemporaryDirectory() as td:
            p = _valid_config(Path(td))
            rc = ingest_dispatcher.main(["dry-run", "--config", str(p)])
            self.assertEqual(rc, 0)

    def test_validate_reports_errors(self):
        with tempfile.TemporaryDirectory() as td:
            bad = Path(td) / "c.json"
            bad.write_text(json.dumps({"version": 1, "sources": "nope"}))
            rc = ingest_dispatcher.main(["validate", "--config", str(bad)])
            self.assertEqual(rc, 2)

    def test_run_source_happy_path_no_upload(self):
        with tempfile.TemporaryDirectory() as td:
            tdp = Path(td)
            p = _valid_config(tdp)
            items = [_mk_item("1"), _mk_item("2")]
            source = json.loads(p.read_text())["sources"][0]

            with mock.patch.object(ingest_dispatcher, "_load_fetcher",
                                   return_value=_StubFetcher(items)), \
                 mock.patch("execution.ingest_dedup.filter_new",
                            return_value=items) as mock_filter, \
                 mock.patch("execution.format_items_for_notebooklm.write_rollup") as mock_write:
                summary = ingest_dispatcher.run_source(
                    source, config_path=p, upload=False
                )
            self.assertEqual(summary["fetched"], 2)
            self.assertEqual(summary["new"], 2)
            self.assertIsNotNone(summary["artifact_path"])
            self.assertEqual(summary["errors"], [])
            mock_filter.assert_called_once()
            mock_write.assert_called_once()

    def test_run_source_unknown_type_logs_error(self):
        source = {"id": "bogus-x", "type": "made-up-protocol",
                  "handle": "h", "notebooks": ["N"], "enabled": True}
        with mock.patch.object(ingest_dispatcher, "FETCHERS", {}):
            summary = ingest_dispatcher.run_source(
                source, config_path=Path("/nonexistent"), upload=False
            )
        self.assertEqual(summary["fetched"], 0)
        self.assertTrue(any("no registered fetcher" in e for e in summary["errors"]))

    def test_run_all_parallel_isolates_per_source_failure(self):
        with tempfile.TemporaryDirectory() as td:
            tdp = Path(td)
            cfg = {
                "version": 1,
                "sources": [
                    {"id": "ok-x", "type": "x", "handle": "a",
                     "notebooks": ["N"], "enabled": True, "cadence": "daily"},
                    {"id": "fail-x", "type": "x", "handle": "b",
                     "notebooks": ["N"], "enabled": True, "cadence": "daily"},
                ],
            }
            p = tdp / "c.json"
            p.write_text(json.dumps(cfg, indent=2))

            class FlakyFetcher(_StubFetcher):
                def fetch(self, handle, since=None, until=None, **kw):
                    if handle == "b":
                        raise RuntimeError("boom")
                    return list(self._items)

            items = [_mk_item("1")]
            with mock.patch.object(ingest_dispatcher, "_load_fetcher",
                                   return_value=FlakyFetcher(items)), \
                 mock.patch("execution.ingest_dedup.filter_new", return_value=items), \
                 mock.patch("execution.format_items_for_notebooklm.write_rollup"):
                summaries = ingest_dispatcher.run_all(p, parallel=2, upload=False)
            by_id = {s["source_id"]: s for s in summaries}
            self.assertEqual(by_id["ok-x"]["errors"], [])
            self.assertTrue(by_id["fail-x"]["errors"])
            self.assertIn("boom", by_id["fail-x"]["errors"][0])


class RunOneCLITests(unittest.TestCase):
    def test_run_one_missing_source_exits_2(self):
        with tempfile.TemporaryDirectory() as td:
            p = _valid_config(Path(td))
            rc = ingest_dispatcher.main([
                "run-one", "missing-id", "--config", str(p), "--no-upload",
            ])
            self.assertEqual(rc, 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
