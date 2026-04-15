#!/usr/bin/env python3
"""
Tests for skills/notebooklm-internal/scripts/add_source.py

Standalone: no third-party test runner required. Exercises the core
`add_source` coroutine against a mocked Playwright Page, plus library.jsonl
append safety, auth-expiry detection, and CLI-level notebook resolution.

Run:
    python3 skills/notebooklm-internal/scripts/test_add_source.py
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
import tempfile
import traceback
import unittest
from pathlib import Path
from typing import Any, Dict, List, Optional

# Make the script importable regardless of cwd.
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import add_source as mod  # noqa: E402


# ---------------------------------------------------------------------------
# Mock Playwright Page
# ---------------------------------------------------------------------------


class MockPage:
    """
    Minimal async Playwright-like Page for unit testing add_source().

    Behaviour is controlled by a small scenario dict:
        - ready_after: seconds-of-monotonic delay before the new source is
          reported as ready (default 0 → ready immediately).
        - ready_source_id: id to return when polling.
        - never_ready: if True, _evaluate never returns a ready source.
    """

    def __init__(
        self,
        ready_source_id: str = "src_123",
        never_ready: bool = False,
    ) -> None:
        self.ready_source_id = ready_source_id
        self.never_ready = never_ready
        self.actions: List[Dict[str, Any]] = []
        self.upload_files: List[str] = []
        self._eval_calls = 0

    async def goto(self, url: str, wait_until: str = "domcontentloaded") -> None:
        self.actions.append({"type": "goto", "url": url, "wait_until": wait_until})

    async def click(self, selector: str) -> None:
        self.actions.append({"type": "click", "selector": selector})

    async def fill(self, selector: str, value: str) -> None:
        self.actions.append({"type": "fill", "selector": selector, "value": value})

    async def set_input_files(self, selector: str, path: str) -> None:
        self.actions.append({"type": "set_input_files", "selector": selector, "path": path})
        self.upload_files.append(path)

    async def evaluate(self, script: str) -> Optional[Dict[str, Any]]:
        self._eval_calls += 1
        if self.never_ready:
            return None
        return {"id": self.ready_source_id, "state": "ready"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _read_jsonl(path: Path) -> List[Dict[str, Any]]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class AddSourceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self.tmp.name)
        self.jsonl_path = self.tmp_path / "library.jsonl"
        # Redirect library log for tests.
        self._orig_jsonl = mod.LIBRARY_JSONL
        mod.LIBRARY_JSONL = self.jsonl_path

    def tearDown(self) -> None:
        mod.LIBRARY_JSONL = self._orig_jsonl
        self.tmp.cleanup()

    # -- (a) text happy path + JSONL record -------------------------------
    def test_a_text_happy_path_writes_jsonl(self):
        md = self.tmp_path / "doc.md"
        md.write_bytes(b"# Title\n" + b"x" * 10_000)  # ~10KB

        page = MockPage(ready_source_id="src_text_1")
        result = asyncio.run(
            mod.add_source(
                page,
                notebook_id="nb_abc",
                source_type="text",
                content_or_url=str(md),
                title="My Doc",
                attachments=None,
                timeout=5,
            )
        )
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["source_id"], "src_text_1")
        self.assertGreaterEqual(result["bytes"], 10_000)

        rec = mod.build_record(
            notebook_id="nb_abc",
            source_id=result["source_id"],
            title="My Doc",
            source_type="text",
            bytes_count=result["bytes"],
            attachment_count=0,
        )
        mod.append_library_record(rec, path=self.jsonl_path)
        records = _read_jsonl(self.jsonl_path)
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["notebook_id"], "nb_abc")
        self.assertEqual(records[0]["source_id"], "src_text_1")
        self.assertEqual(records[0]["attachment_count"], 0)

    # -- (b) file upload ---------------------------------------------------
    def test_b_file_upload(self):
        f = self.tmp_path / "report.pdf"
        f.write_bytes(b"%PDF-1.4 fake")

        page = MockPage(ready_source_id="src_pdf_1")
        result = asyncio.run(
            mod.add_source(
                page, "nb1", "pdf", str(f), title="R", attachments=None, timeout=5
            )
        )
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["source_id"], "src_pdf_1")
        # The file path should have been handed to set_input_files.
        self.assertIn(str(f), page.upload_files)

    # -- (c) attachments reuse single session -----------------------------
    def test_c_attachments_reuse_same_page(self):
        primary = self.tmp_path / "primary.md"
        primary.write_text("hi")
        att1 = self.tmp_path / "a1.png"
        att1.write_bytes(b"img1")
        att2 = self.tmp_path / "a2.txt"
        att2.write_bytes(b"txt2")

        page = MockPage(ready_source_id="src_main")
        result = asyncio.run(
            mod.add_source(
                page,
                "nb2",
                "text",
                str(primary),
                title="Primary",
                attachments=[str(att1), str(att2)],
                timeout=5,
            )
        )
        self.assertEqual(result["status"], "success")
        self.assertEqual(len(result["attachments"]), 2)
        # All uploads must have used the same MockPage (single session).
        self.assertEqual(set(page.upload_files), {str(att1), str(att2)})

    # -- (d) url source ---------------------------------------------------
    def test_d_url_source(self):
        page = MockPage(ready_source_id="src_url_1")
        result = asyncio.run(
            mod.add_source(
                page,
                "nb3",
                "url",
                "https://example.com/article",
                title="Example",
                timeout=5,
            )
        )
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["source_id"], "src_url_1")
        # URL bytes counted, not a file size.
        self.assertEqual(result["bytes"], len(b"https://example.com/article"))

    # -- (e) processing timeout graceful ----------------------------------
    def test_e_processing_timeout_graceful(self):
        md = self.tmp_path / "doc.md"
        md.write_text("hello")
        page = MockPage(never_ready=True)
        result = asyncio.run(
            mod.add_source(
                page, "nb4", "text", str(md), title="T", attachments=None, timeout=1
            )
        )
        self.assertEqual(result["status"], "timeout")
        self.assertTrue(result["partial"])
        self.assertIsNone(result["source_id"])

    # -- (f) auth expiry exit 3 ------------------------------------------
    def test_f_auth_expired_detection(self):
        self.assertTrue(
            mod.is_auth_expired_error(RuntimeError("Authentication required for request"))
        )
        self.assertTrue(
            mod.is_auth_expired_error(Exception("redirected to accounts.google.com"))
        )
        self.assertFalse(mod.is_auth_expired_error(Exception("selector not found")))

    # -- (g) two sequential adds produce two JSONL lines ------------------
    def test_g_append_safety_two_sequential(self):
        rec1 = mod.build_record(
            notebook_id="nb5",
            source_id="s1",
            title="one",
            source_type="text",
            bytes_count=10,
            attachment_count=0,
        )
        rec2 = mod.build_record(
            notebook_id="nb5",
            source_id="s2",
            title="two",
            source_type="text",
            bytes_count=20,
            attachment_count=1,
        )
        mod.append_library_record(rec1, path=self.jsonl_path)
        mod.append_library_record(rec2, path=self.jsonl_path)

        lines = self.jsonl_path.read_text().splitlines()
        self.assertEqual(len(lines), 2)
        parsed = [json.loads(ln) for ln in lines]
        self.assertEqual(parsed[0]["source_id"], "s1")
        self.assertEqual(parsed[1]["source_id"], "s2")
        # Every line must end with exactly one newline (append-safety).
        raw = self.jsonl_path.read_bytes()
        self.assertTrue(raw.endswith(b"\n"))
        self.assertEqual(raw.count(b"\n"), 2)


class NotebookResolutionTests(unittest.TestCase):
    def test_id_precedence(self):
        nid, err = mod.resolve_notebook_id("nb_direct", None, None)
        self.assertEqual(nid, "nb_direct")
        self.assertIsNone(err)

    def test_url_parse(self):
        url = "https://notebooklm.google.com/notebook/abc123?foo=bar"
        nid, err = mod.resolve_notebook_id(None, url, None)
        self.assertEqual(nid, "abc123")
        self.assertIsNone(err)

    def test_url_parse_bad(self):
        nid, err = mod.resolve_notebook_id(None, "https://example.com/foo", None)
        self.assertIsNone(nid)
        self.assertIn("Could not parse", err or "")

    def test_name_without_ensure_notebook(self):
        # ensure_notebook.resolve_notebook isn't in this tree → should return
        # an instructive error, not crash.
        nid, err = mod.resolve_notebook_id(None, None, "My Notebook")
        self.assertIsNone(nid)
        self.assertIn("ensure_notebook", err or "")

    def test_none_provided(self):
        nid, err = mod.resolve_notebook_id(None, None, None)
        self.assertIsNone(nid)
        self.assertIn("required", err or "")


def _run() -> int:
    loader = unittest.TestLoader()
    suite = unittest.TestSuite(
        [
            loader.loadTestsFromTestCase(AddSourceTests),
            loader.loadTestsFromTestCase(NotebookResolutionTests),
        ]
    )
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    try:
        sys.exit(_run())
    except Exception:
        traceback.print_exc()
        sys.exit(2)
