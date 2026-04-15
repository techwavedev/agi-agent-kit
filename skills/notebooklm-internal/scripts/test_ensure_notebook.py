#!/usr/bin/env python3
"""
Unit tests for ensure_notebook.py

Covers:
  - resolve by id (UI probe succeeds)
  - resolve by name (library scan succeeds)
  - create on missing + create_if_missing=True
  - fail on missing + create_if_missing=False (exit code 2)
  - config persistence round-trip (first run writes, second run reads)

Run standalone:
    python3 skills/notebooklm-internal/scripts/test_ensure_notebook.py
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Make sibling module importable
sys.path.insert(0, str(Path(__file__).parent))

import ensure_notebook  # noqa: E402


# ---------------------------------------------------------------------------
# Page mock helpers
# ---------------------------------------------------------------------------

def _make_element(text: str = "", href: str = "", visible: bool = True):
    el = MagicMock()
    el.inner_text.return_value = text
    el.get_attribute.side_effect = lambda attr: href if attr == "href" else None
    el.is_visible.return_value = visible
    return el


def make_page_resolving_id(notebook_id: str):
    """Page that, after goto(), reports URL = /notebook/<id>."""
    page = MagicMock()
    # Track URL state
    page._url = "https://notebooklm.google.com/"

    def _goto(url, **kwargs):
        page._url = url
    page.goto.side_effect = _goto
    type(page).url = property(lambda self: self._url)

    page.wait_for_selector.return_value = None
    page.query_selector_all.return_value = []
    return page


def make_page_with_library(cards):
    """Page whose library has the given cards (list of (text, href))."""
    page = MagicMock()
    page._url = "https://notebooklm.google.com/"

    def _goto(url, **kwargs):
        page._url = url
    page.goto.side_effect = _goto
    type(page).url = property(lambda self: self._url)

    page.wait_for_selector.return_value = None
    page.query_selector_all.return_value = [
        _make_element(text=t, href=h) for (t, h) in cards
    ]
    return page


# ---------------------------------------------------------------------------
# Tests for core primitives
# ---------------------------------------------------------------------------

class TestResolveNotebook(unittest.TestCase):
    def test_resolve_by_id_success(self):
        page = make_page_resolving_id("abc12345")
        # goto navigates to /notebook/abc12345 — page.url reports that
        orig_goto = page.goto.side_effect

        def _goto(url, **kwargs):
            page._url = url
        page.goto.side_effect = _goto

        out = ensure_notebook.resolve_notebook(page, "abc12345")
        self.assertEqual(out, "abc12345")

    def test_resolve_by_id_mismatch_returns_none(self):
        page = MagicMock()
        # After goto, url stays at library root (id invalid)
        page._url = "https://notebooklm.google.com/"

        def _goto(url, **kwargs):
            page._url = "https://notebooklm.google.com/"
        page.goto.side_effect = _goto
        type(page).url = property(lambda self: self._url)
        # library lookup also fails (no cards)
        page.wait_for_selector.side_effect = Exception("timeout")

        out = ensure_notebook.resolve_notebook(page, "deadbeef")
        self.assertIsNone(out)

    def test_resolve_by_name_found(self):
        page = make_page_with_library(
            [
                ("Other Notebook", "/notebook/zzz99999"),
                ("My Project", "/notebook/id-my-project-1"),
            ]
        )
        out = ensure_notebook.resolve_notebook(page, "My Project")
        self.assertEqual(out, "id-my-project-1")

    def test_resolve_by_name_not_found(self):
        page = make_page_with_library(
            [("Something Else", "/notebook/xxx00000")]
        )
        out = ensure_notebook.resolve_notebook(page, "Missing Project")
        self.assertIsNone(out)

    def test_resolve_by_name_case_insensitive(self):
        page = make_page_with_library(
            [("EXACT MATCH", "/notebook/nid-111")]
        )
        out = ensure_notebook.resolve_notebook(page, "exact match")
        self.assertEqual(out, "nid-111")


class TestCreateNotebook(unittest.TestCase):
    def test_create_success(self):
        page = MagicMock()
        page._url = "https://notebooklm.google.com/"

        # Clicking the create button advances URL to /notebook/newid
        button = MagicMock()
        button.is_visible.return_value = True

        def _click():
            page._url = "https://notebooklm.google.com/notebook/new-nb-42"
        button.click.side_effect = _click

        page.query_selector.return_value = button

        def _goto(url, **kwargs):
            page._url = url
        page.goto.side_effect = _goto
        type(page).url = property(lambda self: self._url)

        page.wait_for_selector.return_value = None
        page.keyboard = MagicMock()

        nid = ensure_notebook.create_notebook(page, "Brand New Notebook")
        self.assertEqual(nid, "new-nb-42")
        # We attempted to type the title
        self.assertTrue(page.keyboard.type.called or page.keyboard.press.called)

    def test_create_no_button_raises(self):
        page = MagicMock()
        page._url = "https://notebooklm.google.com/"

        def _goto(url, **kwargs):
            page._url = url
        page.goto.side_effect = _goto
        type(page).url = property(lambda self: self._url)
        page.query_selector.return_value = None  # no button found

        with self.assertRaises(RuntimeError):
            ensure_notebook.create_notebook(page, "X")


# ---------------------------------------------------------------------------
# Tests for CLI + config persistence
# ---------------------------------------------------------------------------

class TestCLIAndPersistence(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self._tmp.name)
        self.config_path = self.tmp_path / "ingest_sources.json"
        # Seed an empty config file so persist writes to it (not mirror)
        self.config_path.write_text(json.dumps({"sources": {}}))

    def tearDown(self):
        self._tmp.cleanup()

    def _patched_run(self, page):
        """Returns a context manager patching _run_with_page to call fn(page)."""
        def _fake_run(fn):
            return fn(page)
        return patch.object(ensure_notebook, "_run_with_page", side_effect=_fake_run)

    # ---- bad args ----

    def test_bad_args_no_id_no_name(self):
        rc = ensure_notebook.main(["--json"])
        self.assertEqual(rc, 1)

    def test_bad_args_both_id_and_name(self):
        rc = ensure_notebook.main(
            ["--id", "abc12345", "--name", "X", "--source-id", "s", "--json"]
        )
        self.assertEqual(rc, 1)

    def test_bad_args_name_without_source_id(self):
        rc = ensure_notebook.main(["--name", "X", "--json"])
        self.assertEqual(rc, 1)

    # ---- resolve by id ----

    def test_resolve_by_id_cli(self):
        page = make_page_resolving_id("abc12345")
        with self._patched_run(page):
            rc = ensure_notebook.main(
                ["--id", "abc12345", "--config", str(self.config_path), "--json"]
            )
        self.assertEqual(rc, 0)

    # ---- resolve by name ----

    def test_resolve_by_name_cli_persists(self):
        page = make_page_with_library(
            [("My Project", "/notebook/nid-my-project")]
        )
        with self._patched_run(page):
            rc = ensure_notebook.main(
                [
                    "--name",
                    "My Project",
                    "--source-id",
                    "src1",
                    "--config",
                    str(self.config_path),
                    "--json",
                ]
            )
        self.assertEqual(rc, 0)
        cfg = json.loads(self.config_path.read_text())
        self.assertEqual(
            cfg["sources"]["src1"]["notebook_ids"]["My Project"],
            "nid-my-project",
        )

    # ---- create on missing ----

    def test_create_if_missing_creates_and_persists(self):
        # First call resolve_notebook → None, then create_notebook → id
        call_count = {"n": 0}
        page = MagicMock()
        page._url = "https://notebooklm.google.com/"

        def _goto(url, **kwargs):
            page._url = url
        page.goto.side_effect = _goto
        type(page).url = property(lambda self: self._url)

        # Library has no matching cards
        page.wait_for_selector.return_value = None
        page.query_selector_all.return_value = []

        # Create button path
        button = MagicMock()
        button.is_visible.return_value = True

        def _click():
            page._url = "https://notebooklm.google.com/notebook/created-xyz"
        button.click.side_effect = _click
        page.query_selector.return_value = button
        page.keyboard = MagicMock()

        with self._patched_run(page):
            rc = ensure_notebook.main(
                [
                    "--name",
                    "Brand New",
                    "--source-id",
                    "src1",
                    "--create-if-missing",
                    "--config",
                    str(self.config_path),
                    "--json",
                ]
            )
        self.assertEqual(rc, 0)
        cfg = json.loads(self.config_path.read_text())
        self.assertEqual(
            cfg["sources"]["src1"]["notebook_ids"]["Brand New"],
            "created-xyz",
        )

    # ---- not found + flag off ----

    def test_not_found_exits_2(self):
        page = make_page_with_library([])
        with self._patched_run(page):
            rc = ensure_notebook.main(
                [
                    "--name",
                    "Nonexistent",
                    "--source-id",
                    "src1",
                    "--config",
                    str(self.config_path),
                    "--json",
                ]
            )
        self.assertEqual(rc, 2)

    # ---- persistence round-trip ----

    def test_persistence_round_trip(self):
        """First run creates, second run reads persisted id and skips creation."""
        # === First run: create ===
        page1 = MagicMock()
        page1._url = "https://notebooklm.google.com/"

        def _goto1(url, **kwargs):
            page1._url = url
        page1.goto.side_effect = _goto1
        type(page1).url = property(lambda self: self._url)
        page1.wait_for_selector.return_value = None
        page1.query_selector_all.return_value = []

        button = MagicMock()
        button.is_visible.return_value = True

        def _click():
            page1._url = "https://notebooklm.google.com/notebook/round-trip-id"
        button.click.side_effect = _click
        page1.query_selector.return_value = button
        page1.keyboard = MagicMock()

        with self._patched_run(page1):
            rc1 = ensure_notebook.main(
                [
                    "--name",
                    "RT Project",
                    "--source-id",
                    "src1",
                    "--create-if-missing",
                    "--config",
                    str(self.config_path),
                    "--json",
                ]
            )
        self.assertEqual(rc1, 0)

        # === Second run: persisted id gets verified, no create invoked ===
        page2 = MagicMock()
        page2._url = "https://notebooklm.google.com/"

        # goto /notebook/round-trip-id → url should reflect that id to pass id-probe
        def _goto2(url, **kwargs):
            page2._url = url
        page2.goto.side_effect = _goto2
        type(page2).url = property(lambda self: self._url)
        page2.wait_for_selector.return_value = None
        page2.query_selector_all.return_value = []
        # If query_selector is ever used for the "create" button, fail the test
        page2.query_selector.return_value = None  # not needed; create path should NOT run

        with self._patched_run(page2):
            rc2 = ensure_notebook.main(
                [
                    "--name",
                    "RT Project",
                    "--source-id",
                    "src1",
                    "--create-if-missing",  # still set — but should short-circuit
                    "--config",
                    str(self.config_path),
                    "--json",
                ]
            )
        self.assertEqual(rc2, 0)

        # Config still holds the same id
        cfg = json.loads(self.config_path.read_text())
        self.assertEqual(
            cfg["sources"]["src1"]["notebook_ids"]["RT Project"],
            "round-trip-id",
        )

    def test_persist_to_mirror_when_config_missing(self):
        """When the target config doesn't exist, writes to .tmp mirror."""
        page = make_page_with_library(
            [("Mirror Project", "/notebook/mir-999")]
        )
        missing_config = self.tmp_path / "does_not_exist.json"
        # Redirect the mirror path into tmp so we don't pollute repo .tmp/
        mirror = self.tmp_path / "mirror.json"
        with patch.object(ensure_notebook, "MIRROR_CONFIG_PATH", mirror):
            with self._patched_run(page):
                rc = ensure_notebook.main(
                    [
                        "--name",
                        "Mirror Project",
                        "--source-id",
                        "srcX",
                        "--config",
                        str(missing_config),
                        "--json",
                    ]
                )
            self.assertEqual(rc, 0)
            self.assertTrue(mirror.exists())
            cfg = json.loads(mirror.read_text())
            self.assertEqual(
                cfg["sources"]["srcX"]["notebook_ids"]["Mirror Project"],
                "mir-999",
            )


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    unittest.main(verbosity=2)
